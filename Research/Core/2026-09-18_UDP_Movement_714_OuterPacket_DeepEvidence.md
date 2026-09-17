# 2026-09-18 UDP Movement／714／Outer Packet Deep Evidence

> Target: 日本版 PaperMan 2016 年服務終了時的最終 Client。
> Purpose: 集中記錄本輪由 `PaperMan.exe.c` 直接重新驗證出的新證據；不取代既有 Network／Gameplay 主文件。

## 1. 26-byte UDP movement record：再確認 parser 邊界

`sub_602E30()` 對每個 actor record 的讀取順序：

```text
+00  u8
+01  u8
+02  u8
+03  u32
+07  u32
+0B  u8[4]
+0F  u16
+11  u16
+13  u16
+15  u8
+16  u8
+17  u8
+18  u8
+19  u8
+1A  u32
```

總長：`0x1A = 26 bytes`。

其中 position-like 三個 `u16` 均在 Client 端 `/3.0` 後形成 3D vector；`sub_5E2570()` 則進一步把 nested type 1/2/3 與 type 4 materialize 成 pooled runtime event/effect-like object。

### 1.1 nested event object 的新直接證據

`sub_5E2570()` 首 byte `n2_1` 決定 wire subtype：

```text
Subtype 1
  u8 participant/resource-like value
  u8 state-like value
  6 × u16 / 3D values
  -> runtime object type 1

Subtype 2
  u16 participant/resource-like value
  u8 state-like value
  6 × u16 / 3D values
  -> runtime object type 1

Subtype 3
  u8 state-like value
  6 × u16 / 3D values
  -> runtime object type 1

Subtype 4
  u32 + u32
  6 × float values
  -> runtime object type 2
```

對 type 1 object，C 直接寫入：

```text
+00 = 1
+04 = actor identity (`n16`)
+05 = subtype-1-specific value, otherwise -1
+06 = subtype-2-specific value, otherwise -1
+07 = outer `a6`
+08..+10 = first 3D vector
+11..+13 = second 3D vector
```

並呼叫 `sub_59E490(this + 5387, ..., &object)` 進入另一層 queue/list。

對 type 2 object：

```text
+00 = 2
+02 = caller-provided `a7`
+04 = actor identity
+08..+10 = 3D vector-like data
+56 = (u32 value != 0)
+57 = (u32 value != 0)
```

**語意仍不能直接命名為某個 public gameplay event。** 但已可確定這不是單純 movement scalar；它會建立持續存在於 runtime queue 的 typed event/effect node。

Evidence: `PaperMan.exe.c`, `sub_5E2570`, direct field writes.

## 2. Outer Packet framing：目前只保留已直接證明的部分

Packet object 在初始化時建立：

```text
packet data area  = this + 24
payload buffer    = this + 32
```

多個 accessor 直接操作 Packet 內部的 16-bit 控制／length state：

```text
sub_591EC0(...) → 寫入 opcode accessor 所對應的 16-bit state
sub_591EE0(...) → 讀取同一 opcode state
sub_591F00(...) → 讀取 framing length state
sub_591F20(...) → 更新 payload-related length state
sub_591F90(...) → 更新另一個 length/transform state
```

TCP send path 直接使用：

```text
buffer = packet + 24
length = sub_591F00(packet) + 8
```

TCP receive path 同樣以：

```text
frame_size = sub_591F00(packet) + 8
```

作為 frame consumption boundary。

因此可以 **Confirmed**：

```text
TCP/UDP Packet wire framing overhead = 8 bytes
frame size = declared length accessor + 8
opcode = Packet opcode accessor consumed by dispatcher
```

但由於 Hex-Rays 對 `sub_591EC0/sub_591F00/sub_591F20/sub_591F90` 的 parameter pointer type 有不同程度的猜測，**目前不應僅靠 C 反編譯把 opcode／length state 固定寫成 raw wire relative offsets `+0/+2/+4/+6`，也不應把四個 16-bit state 全部直接命名成 public header fields。**

目前採用保守命名：

```text
Packet Opcode State          = sub_591EE0 / sub_591EC0 domain
Packet Declared-Length State = sub_591F00 domain
Packet Payload-Length State  = sub_591F20 domain
Packet Transform-Length State= sub_591F90 domain
```

要把它們提升成「wire header 每一個 raw byte offset」仍需 ASM／原始 EXE／runtime capture 直接閉合。

Evidence: `sub_591DA0`, `sub_591EC0`, `sub_591EE0`, `sub_591F00`, `sub_591F20`, `sub_591F90`, `sub_555090`, TCP receive path。

## 3. Packet stream framing：TCP 已直接證明可處理 sticky / partial frame

`sub_554BC0()` / `sub_555280()` 的 TCP receive path 具備持久 receive buffer：

```text
WSARecv into persistent buffer
    ↓
Packet copy from received bytes
    ↓
frame_size = sub_591F00(packet) + 8
    ↓
validate enough bytes
    ↓
(optional transform/decompression)
    ↓
sub_58B010(..., packet)
    ↓
consume exactly frame_size bytes
    ↓
move remaining bytes to buffer front
    ↓
repeat
```

因此 Client TCP receive side 明確支援：

```text
multiple frames in one recv
partial frame across recv calls
```

不能使用：

```text
one recv = one Packet
```

作為 Server framing 模型。

`sub_591FB0()` 可把當前接收緩衝區複製到 Packet；`sub_591D50()` 又在 dispatch 前做 frame validity checks。[C]

## 4. Compression transform：目前可確認的部分

`sub_591600()` 是 byte-oriented dictionary/LZ-style compressor：

- 使用 1024-entry distance domain；
- 每 8 個 decision 使用 control bits；
- match reference 使用 compact 2-byte representation；
- decompressor 可用相同 10-bit distance domain 反向展開。

`sub_591900()` 是對應 decompressor：

```text
reference length  = (*src >> 2) + 3
reference distance = _byteswap_ushort(*src) & 0x3FF
```

並從已產生 output 回拷。

因此可確認：

```text
sub_591600 = compression encoder
sub_591900 = compression decoder
```

另外 `sub_592D30/sub_592E90/sub_592FB0/sub_593110` 顯示 Packet 內存在 flag-driven transform stages（bits `1/2/4/8`），但目前不應將每一 bit 直接命名成完整 public protocol feature；transform order 與各 flag 的 wire contract 仍 `[OPEN]`。

## 5. 714：先前 wire-width 結論需要修正

Protocol registration：

```text
714 = GG_INVALIDWPDATA_REQ
715 = GG_INVALIDWPDATA_ACK
```

`sub_548E80()` 的 714 serializer：

```text
Opcode = 714

+0  u8   local/player identity
+1  u8   `a3` = local byte/context state
+2  u8   actor-local value (`this+240596`)
+3  ANSI null-terminated string (`this+64`)
+N  u32  `a2` = Resource/Action Identity candidate
```

這三個前導欄位是透過 `sub_592920()` 寫入；其 helper 明確只寫 1 byte：

```text
sub_592920 -> sub_592580(..., 1 byte)
```

最後一欄透過 `sub_592A20()` 寫入 4 bytes。

**因此先前將前三個欄位記成 `u16/u16/u16` 的研究結果是錯誤的，應永久以 `u8/u8/u8` 為準。**

## 6. 714 semantic：更具體但仍不過度命名

`sub_548E80()`：

```text
if already reported:
    return

if sub_548C80(this, a2) says common/allowed identity:
    return

++actor-local counter

if counter <= 40:
    return

construct 714
send
mark already-reported
```

而 `sub_548C80()` 明確接受：

```text
0
BOMBPLANT
Pulp_A
Pulp_B
magic_finger
Escape
```

以及目前 actor 四個 weapon/resource identity entries 中匹配的值。

因此目前較精確名稱為：

```text
714 / GG_INVALIDWPDATA_REQ
= Client → Server invalid/unrecognized weapon-data/resource-identity report
```

`WPDATA` 的完整英文 public 展開仍不自行猜測。

## 7. 715：Server-side ACK 到 Client disconnect 的 contract

`sub_55D990()` 執行：

```text
sub_555030(&dword_1321D00)
    -> shutdown(socket, 2)
    -> closesocket(socket)
    -> connection state reset

sub_408080(..., 0x320)
sub_9A7DE0(message, 20, 1)
```

dispatcher 明確：

```text
715 -> sub_55D990
```

protocol registration：

```text
715 = GG_INVALIDWPDATA_ACK
```

因此可 **Confirmed**：

```text
Client receives 715
    ↓
TCP socket is closed
    ↓
Client invokes message/UI path id 0x320
```

`sub_55D990()` 本身完全沒有 Packet reader，因此沒有證據支持 715 body 存在可解析的 semantic payload。

## 8. 714 ↔ 715 interaction model

```text
Client detects repeated invalid/unrecognized weapon-data/resource identity
    ↓
GG_INVALIDWPDATA_REQ (714)
    payload:
      u8 local identity
      u8 context/state byte
      u8 actor-local value
      ANSI string
      u32 resource/action identity
    ↓
Server processing [implementation absent]
    ↓
GG_INVALIDWPDATA_ACK (715)
    ↓
Client closes TCP connection
    ↓
Client message/UI path 0x320
```

因此 `714 → 715 → disconnect` 是 **Strongly Supported client/server interaction model**；Server-side implementation本身仍 `[OPEN]`。

## 9. UDP health timeout：697 的 client-side trigger

`sub_5934B0()`：

```text
stored timestamp == 0
    → healthy

elapsed <= 30000 ms
    → healthy

elapsed > 30000 ms
    → clear timestamp
    → return false
```

`sub_593510()` 在：

```text
n15 == 13
AND sub_5934B0(this) == 0
```

時建立：

```text
Packet opcode = 697
u16 payload = 1
```

並交給 UDP/TCP reporting send path。

Protocol registration：

```text
697 = GG_CHEATER_REPORT_REQ
```

因此可確認：

```text
30-second timeout
    ↓
client generates GG_CHEATER_REPORT_REQ (697)
```

但不能把「30 秒 timeout」本身解釋成 cheating；`n15 == 13` 的完整狀態語意與 Server receiver 仍需另外閉合。

## 10. UDP peer／latency side finding

Peer family 已直接閉合以下 schema：

```text
4  inbound  = u8 count + count × (u8 identity + 16-byte endpoint)
5  inbound  = u8 identity + u32 timing-like value
6  inbound  = u8 identity + u32 timing-like value
10 inbound  = u8 identity + 16-byte endpoint
12 inbound  = u8 count + count × (u8 identity + 16-byte endpoint)
13 inbound  = u8 identity + u32 timing-like value
14 inbound  = u8 identity + u32 timing-like value
```

而 outbound peer responses 都使用：

```text
u8 local identity + u32 timing-like value
```

另外：

```text
22 → u8 flag + u8 count + count × (u8 identity + u32 ping-like value)
154 → u8 count + count × (u8 identity + u8 ping-like value)
```

兩者均寫入：

```text
dword_F6D9E8[slot]
```

UI consumer：

```text
sub_9A8F40(value)
    ↓
Ping_%d
```

`sub_9A8F40()` 的直接門檻：

```text
<100      → 5
100–199   → 4
200–299   → 3
300–999   → 2
1000–4999 → 1
>=5000    → 0
```

因此 per-player ping/latency classification state 已不是單純猜測；但 opcode 154 的 1-byte wire value 的原始 unit 仍 `[OPEN]`。

## 11. Revised confidence table

| Conclusion | Confidence | Evidence |
|---|---|---|
| TCP frame consumption uses `declared length + 8` | Confirmed | TCP send/receive paths |
| Client TCP supports multiple/partial frames | Confirmed | persistent buffer + exact frame consumption |
| `sub_591600` = dictionary/LZ-style compressor | Confirmed at algorithm level | direct encoder control/reference logic |
| `sub_591900` = matching decompressor | Confirmed | inverse back-reference decode |
| 714 first three fields = `u8/u8/u8` | Confirmed | `sub_592920` direct width |
| 714 final identity field = `u32` | Confirmed | `sub_592A20` direct width |
| 714 = `GG_INVALIDWPDATA_REQ` | Confirmed | protocol registration |
| 715 = `GG_INVALIDWPDATA_ACK` | Confirmed | protocol registration |
| 715 causes TCP close on Client | Confirmed | `sub_55D990 → sub_555030` |
| 715 client handler has no parsed body | Confirmed | no Packet read in handler |
| 714→715 is validation/rejection interaction | Strongly Supported | protocol names + client disconnect behavior |
| 697 = `GG_CHEATER_REPORT_REQ` | Confirmed | protocol registration |
| 697 has 30s timeout trigger | Confirmed | `sub_5934B0/sub_593510` |
| opcode 22/154 populate ping-like state | Strongly Supported | shared table + `Ping_%d` UI consumer |
| raw header fields at exact byte offsets +0/+2/+4/+6 | Unknown | C pointer typing still ambiguous |

## 12. Remaining high-value OPEN

```text
1. Server-side implementation of 714/715/697.
2. Exact raw wire offsets for Packet header words via ASM/EXE/runtime capture.
3. Exact transform order and flag semantics for Packet bits 1/2/4/8.
4. 714 string field source (`this+64`) and exact WPDATA meaning.
5. `sub_548C80()` four weapon/resource block namespace closure.
6. UDP 8/24 server-side producer and 26-byte serializer.
7. Movement R+00/R+01/R+03/R+07/R+0B/R+15..R+19/R+1A exact semantics.
8. `sub_5E2570()` event/effect node public event mapping.
9. UDP 155/156 producer/consumer and exact hole-information schema.
10. Opcode 161 `UDP_TCP_LIVE_REQ` producer/receiver.
```
