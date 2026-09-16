# Gameplay Network Events — Y_TCP_INF_ACK / UDP Gameplay

> 研究日期：2026-09-16  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA Hex-Rays C export + cross-function data flow  
> Confidence：除特別標示外，直接 Client code evidence = A

本文件承接 `Network_Dispatch.md`，集中記錄 gameplay 階段的 TCP `166 Y_TCP_INF_ACK` 與 UDP dispatcher。重點是保留 raw subtype，避免在證據尚未閉合前把數值硬命名成 guessed enum。

---

## 1. TCP 166 的實際入口

```text
ClientSocket TCP receive
    ↓
sub_58B010(...)
    ↓
case 166
    ↓
sub_58D820(packet)
    ↓
sub_749B90(dword_1D37560, packet)
```

`sub_58B010` 對 `166` 有明確 case；`sub_58D820` 只是轉呼叫 `sub_749B90`。因此 `sub_749B90` 是 166 receive-side 的核心 parser / dispatcher。

---

## 2. 166 packet 的第一層 wire fields

`sub_749B90` 在 gameplay gate：

```c
if (sub_5376F0(byte_EE8968) == 10)
```

成立後立即讀：

```text
field 0: u8 n16
field 1: u8 n18
```

其中 `n18` 直接成為第二級 event discriminator。

因此目前最可靠的抽象不是固定 struct，而是：

```text
Y_TCP_INF_ACK (166)
    + actor/player id : u8
    + event subtype   : u8
    + subtype-specific payload
```

`n16` 很多路徑會送入 `sub_67DF70(n16)` / `sub_67DF00(n16)`，因此它與 player/object identity 強相關；在沒有 object 時仍存在少數特殊 subtype 路徑，所以不要直接定義為 slot index。

---

## 3. 166 raw subtype dispatch

目前直接從 C 確認：

| subtype | handler | 已知 payload / 行為 |
|---:|---|---|
| 1 | `sub_746360` | 讀 u8 另一 player id；對 player state / controller 做 reset-like 操作 |
| 2 | `sub_7463E0(..., a4=0)` | 大型 gameplay event；涉及 player object、resource、`OnDeadCtrl`、stat counters、local effect/state |
| 3 | `sub_747980` | impact/event record |
| 4 | `sub_748860` | u32 + u16 + u32 + 6 個 `sub_592B40` 4-byte units；進 `sub_61BA90` |
| 5 | `sub_748A50` | u32 + u8 + u32 + 6 個 `sub_592B40` units；resource category branch |
| 6 | `sub_748CD0` | u32 + u16 + u32 + 6 個 `sub_592B40` units + u8；resource category 10/15 branch |
| 7 | `sub_748E40` | remaining payload 以 `sub_592730` 讀取，交 UI/text layer |
| 8 | `sub_748EB0` | object vtable event callback |
| 9 | `sub_748EB0` | object vtable event callback |
| 10 | `sub_749230` / `sub_749520` | additional u8 後再分支；明確涉及 `FIRE_BOMB` resource |
| 11 | `sub_7494B0` / `sub_749810` | additional u8；state/timer reset/update |
| 12 | `sub_749A30` | 2×u16；進 `sub_67CD20` |
| 13 | inline bulk reset/state path | 16-slot state reset + local/global gameplay lifecycle work |
| 14 | `sub_749AB0` | server transform/interpolation-like update |
| 15 | `sub_748420` | player/object state + resource transition |
| 16 | `sub_7463E0(..., a4=1)` | 與 subtype 2 共用大型 gameplay/death-state parser，但 control flag 不同 |
| 17 | `sub_748FF0` | object vtable event callback |
| 18 | `sub_748EB0` | object vtable event callback + special follow-up |
| 19 | `sub_74D150` | handler 未閉合 |
| 20 | `sub_747980` | 與 subtype 3 共用 parser |
| 21 | `sub_747DD0` | compact state/update，最終進 `sub_747B90` |
| 22 | `sub_747AB0` | compact impact/state update |
| 23 | `sub_74D410` | handler 未閉合 |
| 24 | inline time parsing + `sub_7498E0` | u32 time-like value，換算分鐘/秒 |
| 25 | `sub_748EB0` | 與 8/9/18 共用 event callback |
| 26 | `sub_745F50` | handler 未閉合 |
| 27 | `sub_746060` | handler |
| 29 | `sub_746060` | player object 有/無時皆有 special route |
| 30 | `sub_74D510` | handler 未閉合 |
| 31 | `sub_74D5D0` | handler |
| 32 | `sub_74D5D0` | handler |

目前不能因數值鄰近或 handler 形狀而直接命名 subtype；名稱應等 downstream evidence 完成後再升級。

---

## 4. subtype 2 / 16：目前最重要的死亡 / 結果狀態鏈

`sub_7463E0` 共用於：

```text
n18 == 2 → sub_7463E0(..., 0)
n18 == 16 → sub_7463E0(..., 1)
```

它會讀取多個 scalar、player id、resource id 與 state values，解析 player object：

```text
sub_67DF00(player)
    ↓
player runtime object
    ↓
resource lookup (`sub_5F5450(dword_1CC95A0, resourceId)`)
```

非 local target 的重要路徑：

```c
sub_9BC470(player, 1, timeLike, 0, 0);
```

`sub_9BC470` 的直接效果包括：

```text
player controller/render state reset
player runtime health-like field = 0
state timestamps updated
controller callback (`sub_5B7AF0`)
```

特別是它明確將 player runtime object 所持 controller 的 `+16` 寫成 `0`。這與死亡/重設生命狀態高度吻合，但 `+16` 在這個物件層的正式欄位名稱仍未建立，因此研究文件仍保留 raw offset。

另外，`sub_7463E0` 包含明確的：

```text
CViewObj::OnDeadCtrl
```

診斷字串路徑；條件是 player team 關係及 resource category 4/5 的組合。這是目前 Client 內直接把這條 event path 與「dead control」連起來的最強語義證據。

### 4.1 round/stat counters

在同一條 subtype 2/16 路徑中可見：

```c
++byte_F33120[240780 * v68 + 240600];

if (a4 == 0)
    ++byte_F33120[240780 * v67 + 240604];
```

初始化時這兩個欄位皆為 0。

進一步 cross-reference 兩個欄位後，可以確認它們會被結果 / scoreboard UI 直接使用：

```c
v17 = player->field_240600;
v20 = player->field_240604;
```

並進入 round/stat presentation。

**目前不要把 +240600 / +240604 直接命名成 KILL / DEATH。** 它們確實是該大型 per-player state 裡的兩個 gameplay result counters，而且在 dead-event 路徑被遞增，但完整 team/mode context 尚未足以固定兩者各自的公開語義。

### 4.2 已證實的另一組 K/D fields

與上述 round counters 不同，per-player state 的另一組 offset 已經可以直接命名：

```text
+60150 → MY_KILL
+60151 → MY_DEATH
```

證據鏈：

```text
byte_F33120[playerStride * player + 60150]
    ↓
SOLO_RESULT_R_MY_KILL

byte_F33120[playerStride * player + 60151]
    ↓
SOLO_RESULT_R_MY_DEATH
```

因此這兩個欄位是直接由 result UI 使用的 KILL / DEATH counters；confidence A。

這也說明：

```text
+240600 / +240604
```

與：

```text
+60150 / +60151
```

不能混為同一組資料。前者目前更接近 round / mode-local result counters，後者是明確的 MY_KILL / MY_DEATH result counters。

---

## 5. `sub_9BC470`：死亡狀態物件層的實際 mutation

核心實作：

```c
if (a5 == 1 || a4 == 0 && *(this + 212) == 8)
{
    *(this + 308) = 1;
    sub_9BC620(this, &savedregs);
}

if (*(this + 320) != 0)
{
    if (a2 != 0)
        *(*(this + 320) + 56) = 1;

    ...

    *(this + 480) = 0;
    ...

    memset(this + 672, 0, 0x2A);
    memset(this + 336, 0, 0x54);
    *(this + 424) = timeGetTime();
    *(this + 436) = timeGetTime();

    *(*(this + 320) + 136) = a2;
    *(*(this + 320) + 16) = 0;
    *(*(this + 320) + 60) = a3;
    *(*(this + 320) + 64) = timeGetTime();
    sub_5B7AF0(*(this + 320));
}
```

因此 `sub_9BC470` 不是純 visual helper；它是會實際改變 player runtime/controller state 的 state-transition function。

**Server reconstruction implication：** 收到等價 death/state event 時，server side 至少要能表達：victim/player identity、death state、transition time / timing token，以及後續結果/stat mutation；但目前尚不能只靠這個 function 反推出完整 wire fields。

---

## 6. subtype 14：server transform / interpolation candidate

`sub_749AB0` 讀：

```text
u32 timeLike
u16 a
u16 b
u16 c
u16 d
u8  flag
```

並呼叫：

```c
sub_5B3DD0(playerController,
           timeLike,
           a,
           b,
           c,
           d,
           flag,
           0,
           0);
```

`sub_5B3DD0`：

```text
+116 = a3
+117 = a6
+118 = a5
+117 = +1.0
+112 = 1
+119 = timeGetTime()
```

同時以：

```text
timeLike

timeLike + (a4 - a6) * 10.0
```

安排兩筆 `sub_9BCA50` state samples。

更重要的是 `IPaperCtrl::sub_9BCBD0` 對這些資料的使用：

```text
old sample + current sample
    ↓
interpolate position/vector by 1/2
interpolate angle byte
    ↓
write to controller transform
```

它對：

```text
controller +488 : current transform/sample
controller +652/+656/+660/+664/+668/+669/+670 : queued/previous sample state
```

進行插值。

因此目前 `166 subtype 14` 可高信心描述為：

> **server → client 的 actor transform / interpolation state update candidate**

而不是普通 UI event。

公開 semantic 的三個向量分量、角度欄位、time unit 仍需進一步用 caller/resource/ASM 對照。

---

## 7. subtype 24：server-driven elapsed-time presentation

這條路徑會解析一個 u32 time-like 值：

```text
minutes = value / 1000 / 60
seconds = value / 1000 % 60
```

並：

```text
dword_1D0A970 = 1
dword_1D0A974 = 0
sub_7498E0(this, 24, actor, &minutes, &seconds, byte)
```

因此可以確定它把 server payload 中的 time-like integer 轉成 gameplay time presentation。

目前不把 1000 單位直接命名為毫秒協議常數；程式計算顯示其輸入在此處以「每 1000 為 1 秒」使用，但完整 wire semantics 仍應以更多 callsite / packet source 驗證。

---

## 8. subtype 10：FIRE_BOMB 特殊分支

`sub_749230` / `sub_749520` 中直接存在：

```text
sub_5F54A0(..., L"FIRE_BOMB")
```

以及 resource category / subtype 9、10、13 的特殊分支。

當 `n13 == 13` 時會：

```text
player +79 = 1
player +316 = 1
resource-derived effect/timing setup
sub_5ABE70(...)
sub_5B3350(...)
sub_716E30(...)
resource vtable +120(time)
```

因此至少可確定：

```text
166 subtype 10
    ↳ FIRE_BOMB related gameplay event/state
```

但尚不能把 n13=9/10/13 對應到公開技能名或完整 bomb state enum。

---

## 9. UDP receive architecture

UDP receive thread：

```text
sub_595A60
    ↓ recvfrom
Packet validity checks
    ↓
sub_595E80(byte_1326958, packet)
```

`sub_595E80` 是 UDP 自己的 opcode dispatcher，與 TCP `sub_58B010` 分開。

目前直接確認的 routes：

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

這組 opcode 表是直接 dispatcher evidence，不是 semantic name inference。

---

## 10. UDP movement：已確認 event name，但 wire body 尚未閉合

UDP case：

```text
8  → sub_596940
24 → sub_596940
```

`sub_596940` 包含明確 diagnostic string：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

並只在 gameplay state `n15 == 13` 下接受；否則進 error/reset path。

因此：

```text
UDP opcode 8 / 24
    = Y_UDP_S_MOVE_INF family
```

confidence A。

但 `sub_596940` 本身不立即解 payload，而是：

```text
sub_593750(packet)
    ↓
critical section
    ↓
sub_5951C0(...)
    ↓
queue node / packet copy
```

`sub_5951C0` 再透過 `sub_595320` 建立 queue node，保存並 copy packet。

所以目前不能從 `sub_596940` 本身推出 position/rotation schema。

**Next trace：** 找出這個 queue 的 consumer，以及何處從 queue node 重新讀 `sub_591EE0` / `sub_5929C0` / `sub_592A40` / `sub_592B40`，才能閉合 movement wire fields。

---

## 11. UDP per-player state side channel

已知兩條 parser：

### `sub_5964E0`

```text
u8 player id
u32 value
    ↓
find slot by player-id mapping
    ↓
dword_F6D9E8[slot] = value
```

### `sub_5965D0`

```text
u8 count
repeat:
    u8 player id
    u8 value
    ↓
find slot
    ↓
dword_F6D9E8[slot] = value
```

這些欄位是獨立於 TCP 166 的 real-time synchronization state；不能把 `dword_F6D9E8` 直接當 HP / position，因為目前 data flow 尚不足。

---

## 12. Current evidence model for server reconstruction

目前 gameplay server state 至少應能抽象出：

```text
PlayerIdentity
PlayerSlot
Team
PlayerRuntimeState
    ├─ transform / interpolation samples
    ├─ dead/alive transition state
    ├─ health/state controller
    ├─ current gameplay timing
    ├─ weapon/resource state
    └─ mode-specific state

Round/Result State
    ├─ per-player result counters (+240600 / +240604; semantics still open)
    ├─ MY_KILL (+60150)
    └─ MY_DEATH (+60151)

Network Event
    ├─ TCP 166 actor id + subtype + subtype payload
    └─ UDP real-time state/events
```

### Still unresolved

1. `166 subtype 2/16` 完整 wire schema，尤其每個 scalar 的 semantic。
2. `sub_7463E0` 的 `a4=0/1` 精確意義。
3. `+240600 / +240604` 的正式 mode/result semantic。
4. Kill/assist/stat mutation 與 166 subtype 的一一對應。
5. UDP 8/24 movement queue consumer 與完整 position/rotation payload。
6. 166 subtype 3/5/6/21/22 等 effect / impact event 的 resource mapping。
7. 166 subtype 13 與 GameRule `Start/End/Respawn` lifecycle 的精確關係。
8. packet header / sequence / encryption / checksum 與 gameplay event payload 的邊界。

---

## 13. Provenance / raw evidence references

主要 IDA C 路徑：

```text
sub_58B010        TCP dispatcher
sub_58D820        166 wrapper
sub_749B90        166 subtype dispatcher
sub_7463E0        subtype 2/16 large gameplay/death event
sub_9BC470        player runtime state transition
sub_9BC620        state rebuild/render synchronization
sub_749AB0        subtype 14 transform/interpolation event
sub_5B3DD0        interpolation sample storage
sub_9BC940        transform sample queueing
IPaperCtrl::sub_9BCBD0  interpolation into current transform
sub_595A60        UDP recv loop
sub_595E80        UDP opcode dispatcher
sub_596940        Y_UDP_S_MOVE_INF family
sub_593750        UDP packet queue insertion
sub_5951C0/sub_595320 queue node construction
sub_5964E0/sub_5965D0 UDP player state side channels
```

This document intentionally keeps unresolved names and raw offsets rather than promoting unverified interpretations into facts.
