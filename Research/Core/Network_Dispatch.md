# TCP / UDP Packet 分發與 Handler 路徑

> 研究日期：2026-09-16
>
> 本文件先固定網路 receive architecture，再往下追 gameplay Packet。重點是避免把 `Y_TCP_INF_REQ (165)`、`Y_TCP_INF_ACK (166)` 與 UDP / Room packet 混成同一層。

## 1. ClientSocket TCP receive：真正的入口

`ClientSocket` 收到 TCP bytes 後，先依 Packet framing 建立 `Packet`，檢查完整長度與有效性，然後呼叫：

```c
sub_58B010(byte_13242F8, a2, a3, v9);
```

TCP receive loop 明確位於 `sub_554BC0` / `sub_555280` 路徑；兩者都把完整 Packet 交給 `sub_58B010`。[C]

TCP stream 本身是有 framing / sticky-packet handling 的：

```text
WSARecv
  ↓
receive buffer
  ↓
Packet parse (`sub_591FB0`)
  ↓
`sub_591F00(packet) + 8` = frame size
  ↓
validate complete packet
  ↓
`sub_58B010`
  ↓
consume frame
  ↓
memmove remaining bytes
```

因此 `sub_58B010` 是比 Socket read 更高一層的 **TCP logical Packet dispatcher**。

---

## 2. `sub_58B010` 的共通 receive hook

函式開頭固定先做：

```c
sub_407360(dword_BEFEF0, a4);
CGameRule::sub_67CF90(n9_0, a4);
n110 = sub_591EE0(a4);
```

[C]

所以目前可以安全建立：

```text
TCP Packet
    ↓
sub_407360(...)
    ↓
CGameRule::sub_67CF90(...)
    ↓
opcode = sub_591EE0(packet)
    ↓
switch(opcode)
    ↓
concrete handler
```

### `CGameRule::sub_67CF90` 本身

其實作為：

```c
bool __thiscall CGameRule::sub_67CF90(_DWORD *this, int a2)
{
    return *(this + 16) != 0
        && (*(*(*(this + 16) + 48) + 24))(*(this + 16) + 48, a2) != 0;
}
```

所以它不是單純的空函式；它會透過 `this + 16` 的物件再進一次 virtual-style callback。

目前這一層應命名為：

```text
CGameRule receive pre-hook
```

而不要誤命名成某個固定 opcode handler。

---

## 3. TCP opcode direction：165 / 166 的關鍵結論

`sub_58B010` 的 switch 明確存在：

```c
case 160u:
    sub_58D790();
    break;

case 166u:
    sub_58D820(a4);
    break;

case 168u:
    sub_56F410(a4);
    break;

case 170u:
    sub_56F4F0(a4);
    break;

case 172u:
    sub_56F5D0(a4);
    break;

case 174u:
    sub_56F6B0(a4);
    break;

case 176u:
    sub_56F790(a4);
    break;
```

但該 switch 沒有 `case 165u`。[C]

因此結合 packet registration：

```text
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
167 GR_CHANGEUSER_REQ
168 GR_CHANGEUSER_ACK
169 GR_RULECHANGE_REQ
170 GR_RULECHANGE_ACK
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
```

目前最穩健的方向性解釋是：

```text
REQ / odd opcode
    = client-originated path

ACK / even opcode
    = server-originated receive path
```

這與 165/166、159/160、167/168 等配對一致。

### 但要注意

這不是由 opcode parity 單獨證明的 protocol 規則；真正可證明的是：

```text
165 does not appear as incoming case in `sub_58B010`
166 does appear as incoming case
```

以及其它 request/ack pair 也呈現相同結構。[C]

---

## 4. `166 Y_TCP_INF_ACK` 的第一層 Handler

TCP dispatcher：

```c
case 166u:
    sub_58D820(a4);
    break;
```

`sub_58D820`：

```c
void __stdcall sub_58D820(LPCSTR *a1)
{
    sub_749B90(dword_1D37560, a1);
}
```

因此確定鏈是：

```text
TCP
  ↓
sub_58B010
  ↓ opcode 166
sub_58D820
  ↓
sub_749B90(dword_1D37560, packet)
```

[C]

這就是目前 `Y_TCP_INF_ACK` 的真正 receive-side entry chain。

---

## 5. `sub_749B90`：166 之下的第二層 dispatch

`sub_749B90` 首先要求：

```c
if (sub_5376F0(byte_EE8968) == 10)
{
    n18 = 0;
    sub_592940(a2, &n16);
    sub_592940(v2, &n18);
    switch (n18)
    {
        ...
    }
}
```

即 receive packet 的前兩個可直接觀察欄位是：

```text
field0 = n16  (u8)
field1 = n18  (u8)
```

然後 `n18` 再作第二級 subtype / event dispatch。[C]

### 目前可見的 `n18` routes

| `n18` | Handler | 現階段可確認的事 |
|---:|---|---|
| 7 | `sub_748E40(n16, a2)` | player-like byte + payload |
| 8 | `sub_748EB0(this, n16, a2, n18)` | event route |
| 9 | `sub_748EB0(this, n16, a2, n18)` | event route |
| 0x12 (18) | `sub_748EB0(this, n16, a2, n18)` | event route；另有 special follow-up |
| 0x19 (25) | `sub_748EB0(this, n16, a2, n18)` | event route；另有 special follow-up |
| 0x0C (12) | `sub_749A30(this, a2)` | payload + local state update |
| 0x0D (13) | bulk player/game-state reset/update path | 見下節 |
| 0x11 (17) | `sub_748FF0(this, n16, a2, n18)` | event route |
| 0x18 (24) | time payload + `sub_7498E0(...)` | server-driven timer/time state |
| 其它 1.. | `sub_746xxx` / `sub_747xxx` / `sub_748xxx` / `sub_749xxx` / `sub_74Dxxx` | 再依 `n18` 分層 |

[C]

這一層是目前最重要的發現：**166 並不是只有一個固定 payload。它本身還包了一個第二級 `n18` event discriminator。**

---

## 6. `n18` 預設分派表目前已扒出的部分

在 `v36 != nullptr` 的情況下，`sub_749B90` 對 `n18` 再分支：

```text
n18 == 1
    → sub_746360(n16, a2)

n18 == 2
    → sub_7463E0(this, n16, a2, 0)

n18 == 3 or 20
    → sub_747980(this, n16, a2, n18)

n18 == 4
    → sub_748860(n16, a2)

n18 == 5
    → sub_748A50(this, n16, a2)

n18 == 6
    → sub_748CD0(n16, a2)

n18 == 10
    → 讀 additional u8 / branch：
         n13 == 1 → sub_749230(...)
         else      → sub_749520(...)

n18 == 11
    → 讀 additional u8：
         n7 == 1 → sub_7494B0(v36)
         else    → sub_749810(v36, n7, n16)

n18 == 14
    → sub_749AB0(n16, v36, a2)

n18 == 15
    → sub_748420(this, n16, a2, n18)

n18 == 16
    → sub_7463E0(this, n16, a2, 1)

n18 == 19
    → sub_74D150(a2)

n18 == 21
    → sub_747DD0(n16, a2)

n18 == 22
    → sub_747AB0(this, n16, a2, n18)

n18 == 23
    → sub_74D410(this, n16, a2, n18)

n18 == 26
    → sub_745F50(n16, a2)

n18 == 27 or 29
    → sub_746060(this, n16, a2, n18)

n18 == 30
    → sub_74D510(this, n16, a2, n18)

n18 == 31 or 32
    → sub_74D5D0(this, n16, a2, n18)

n18 == 29 with `v36 == nullptr`
    → `sub_746060(this, 0, a2, 29)`
```

[C]

目前不將 `1/2/3/...` 改名成 guessed semantic enum；先保持 raw subtype，直到 downstream state/resource/packet evidence 完成。

---

## 7. `n18 == 13`：這條路特別值得優先追

`sub_749B90` 在 `n18 == 13` 時會：

```c
sub_568540(dword_1CCB674);
sub_71F830();

for (n0x10 = 0; n0x10 < 16; ++n0x10)
{
    byte_F6DD11[240780 * n0x10] = 0;
    sub_95EC00(n0x10);

    n0x10_1 = sub_67D110();
    ...
    v4 = sub_4382E0();
    sub_9942D0(v4, n0x10, n0x10_2);
}

v5 = sub_67F2F0();
sub_718000(v5);

if (sub_67EB70())
    sub_7603A0(*(n0x10_0 + 12), a2);

sub_67B5C0(n9_0, 0, 0, 0, -1);
sub_62D570(&dword_1D09130);
sub_720A10(&dword_1D12428, n2 == 2);
```

這表示 `166 + n18=13` 明顯不是單純 UI event，而可能涉及：

```text
16-slot player/gameplay state reset
→ player local/remote state synchronization
→ game-rule restart/start lifecycle
```

這條線應與 `CGameRule::NewGameStart`、player slot state、mode lifecycle 一起追，而不是單獨看成某個 packet。

[C]

---

## 8. `n18 == 24`：server-driven time payload

這條 route 直接讀：

```c
v6 = sub_592A00(a2, v22);
v7 = sub_592A00(v6, v21);
v8 = sub_592AC0(v7, &v24);
sub_592900(v8, &v23);

v20 = v24 / 1000 / 60;
v25 = v24 / 1000 % 60;
```

並設定：

```c
dword_1D0A970 = 1;
dword_1D0A974 = 0;
...
sub_7498E0(this, n18, n16, &v20, &v25, v23);
```

因此：

```text
n18 = 24
    → nested payload
    → millisecond-like integer `v24`
    → minute/second conversion
    → gameplay/UI time state
```

這是 server authoritative timer/state 的強候選；精確 public semantic 仍需把 `sub_7498E0` 及 caller/resource 串起來。

[C]

---

## 9. UDP：入口確實不同，不能與 TCP 混線

`CUDPNetworkManager` 的 receive 入口是：

```c
sub_595A60(this)
    → recv/Packet parse
    → sub_595E80(byte_1326958, packet)
```

`sub_595E80` 再依 `sub_591EE0(a2)` 做自己的 switch。[C]

目前已直接確認 UDP opcode routes：

```text
2   → sub_593A60
4   → sub_593AB0
5   → sub_593E60
6   → sub_5940E0
8   → sub_596940
24  → sub_596940
10  → sub_594460
12  → sub_5946C0
13  → sub_594A10
14  → sub_594CA0
15  → sub_593DF0
18  → sub_596300
20  → sub_5968C0
22  → sub_5964E0
26  → unknown_libname_107
28  → sub_594E80
29  → sub_593E20
31  → sub_594EA0
33  → sub_594EC0
34  → sub_594F20
154 → sub_5965D0
158 → sub_596910
```

[C]

因此：

```text
TCP
  ClientSocket
      └─ sub_58B010

UDP
  CUDPNetworkManager
      └─ sub_595E80
```

是目前已經可以直接固定下來的雙入口架構。

---

## 10. UDP 也有自己的 gameplay state mutation

例如 UDP `sub_5964E0` / `sub_5965D0` 會從 payload 讀：

```text
u8 count
repeat:
    u8 player-like id
    nested integer
```

然後以：

```c
dword_F6DCF4[60195 * j]
```

尋找 16 個 player slot，並寫：

```c
dword_F6D9E8[60195 * j] = value;
```

[C]

這說明 UDP 並不是單純 position transport；它同樣會更新 per-player gameplay state。

所以往後追 packet 時，應先按 transport layer 分組：

```text
TCP → sub_58B010
UDP → sub_595E80
```

再各自建立 opcode / subtype / field map。

---

## 11. `TCP_UDP_DEAD_ACK (160)` 的現階段結論

`160` 在 TCP dispatcher：

```c
case 160u:
    sub_58D790();
```

而 `sub_58D790()`：

```c
sub_58AF90(byte_13242F8);
v0 = sub_408140();
ArgList = sub_408080(v0, 0x126u);
sub_9A7DE0(ArgList, 66, 1);
```

也就是：

```text
160 receive
    → sub_58D790
    → local/network error-status handling
```

目前還不能直接把 `160` 稱成「死亡確認成功」或「玩家死亡事件」，只能確認它是 `TCP_UDP_DEAD_ACK` 的 incoming handler，而且 handler 本身主要做 error/status path。[C]

---

## 12. `165 Y_TCP_INF_REQ` 與 `166 Y_TCP_INF_ACK` 的正確模型

目前證據支持：

```text
Outgoing:

165 Y_TCP_INF_REQ
   ├─ normal damage
   ├─ MultiDamage
   ├─ Mine/Bomb damage
   └─ BotSuicide
```

Incoming:

```text
166 Y_TCP_INF_ACK
   ↓
sub_58D820
   ↓
sub_749B90
   ↓
field0 = n16
field1 = n18
   ↓
second-level gameplay dispatch
   ├─ sub_746xxx
   ├─ sub_747xxx
   ├─ sub_748xxx
   ├─ sub_749xxx
   └─ sub_74Dxxx
```

因此現在最適合的 protocol abstraction 是：

```text
YTcpInfReq
    Opcode = 165
    Subtype = byte1
    Payload = subtype-specific

YTcpInfAck
    Opcode = 166
    ActorOrPlayer = byte0-like
    Subtype = byte1
    Payload = subtype-specific
```

而不是：

```text
165 = DamagePacket
166 = DamageAck
```

後者已經被 receive-side data flow 直接否證為過度簡化。

---

## 13. 接下來追 Handler 的順序

優先級應固定成：

```text
1. 166 → sub_749B90
       ↓
   把每個 `n18` handler 全部追乾淨

2. 對每個 handler 找：
   - parser read sequence
   - state writes
   - player-slot lookup
   - Kill/Death mutation
   - HP / death / respawn
   - mode/round transition

3. 將 165 outgoing 的 subtype
   與 166 incoming 的 subtype / state effect 做 cross-link

4. 再追 UDP `sub_595E80`
   的 gameplay handlers，尤其與 death / movement / state sync 有交集者

5. 最後才把 raw field rename 成 public semantic
```

這個順序能最大限度避免因為單一 send path 或單一 Wiki 名稱而過早定義錯誤 protocol enum。

---

## 14. Evidence policy

本文件遵守：

```text
[C] IDA / Hex-Rays C：wire/parser/control-flow 的第一級證據
[Wiki] public game mechanic：只拿來驗證外部可觀察行為
[RES] Extracted resource：用來閉合 object / key / data identity
```

遇到：

```text
C 有、Wiki 沒有、RES 也沒有
```

就保留 raw name / raw field，例如：

```text
n16
n18
field0
field1
```

而不是填入猜測值。
