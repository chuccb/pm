# 2026-09-18 UDP Movement／714／Outer Packet Deep Evidence

> Target: 日本版 PaperMan 2016 年服務終了時的最終 Client。
> Purpose: 集中記錄本輪由 `PaperMan.exe.c` 直接重新驗證出的新證據；不取代既有 Network／Gameplay 主文件。

## 1. 26-byte UDP movement record：再確認 parser 邊界

`sub_602E30()` 對每個 actor record 的讀取順序仍是：

```text
u8
u8
u8
u32
u32
u8[4?]
u16
u16
u16
u8
u8
u8
u8
u8
u32
```

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
+04 = actor identity
+56 = (u32 value != 0)
+57 = (u32 value != 0)
+08..+10 = one 3D vector
+02 = caller-provided `a7`
```

**語意仍不能直接命名為某個 public gameplay event。** 但已可確定這不是單純 movement scalar；它會建立持續存在於 runtime queue 的 typed event/effect node。

Evidence: `PaperMan.exe.c`, `sub_5E2570`, direct field writes.

## 2. Outer Packet header：目前最可靠的 binary model

`Packet` internal object 的 data buffer 從 `this + 24` 開始，而四個 16-bit header/control locations 為：

```text
+24 = word pointed by Packet field +8
+26 = word pointed by Packet field +12
+28 = word pointed by Packet field +16
+30 = word pointed by Packet field +20
+32 = payload / transformed data buffer
```

直接 accessor：

```text
sub_591EC0(packet, opcode) -> [packet+26] = opcode
sub_591EE0(packet)         -> opcode
sub_591F00(packet)         -> [packet+28]
sub_591F90(packet, value)  -> [packet+30] = value
sub_591F20(packet, len)    -> [packet+24] = len
```

TCP send path：

```text
send buffer = packet + 24
send length = sub_591F00(packet) + 8
```

因此 wire frame 的固定 header 至少是 **8 bytes**，且 opcode 位於 header 的第二個 `u16`（即 relative offset `+2`）。

**重要：不要把 `[+24]`、`[+28]`、`[+30]` 的語意直接等同成「目前 length／payload length／uncompressed length」而不保留 transform state。**

理由是：

- `+24` 由 writer payload length 更新；
- `+28` 是 send/receive framing 的主要 declared-length accessor；
- `+30` 在 compression／padding-like transforms 中保存另一個 length state；
- `sub_593280()`、`sub_592D30()`、`sub_592F60()`、`sub_5930C0()` 會互相操作這三個值。

因此目前最安全的命名是：

```text
HeaderWord0 / TransformedLengthState = +24
Opcode                                 = +26
DeclaredLengthState                    = +28
TransformAuxLengthState                = +30
```

等 ASM／runtime capture 或完整 transform contract 關閉後再升級 public naming。

Evidence: `sub_591DA0`, `sub_591EC0`, `sub_591F20`, `sub_591F90`, `sub_555090`, `sub_554BC0`, `sub_555280`.

## 3. Packet stream framing：TCP 已直接證明可處理 sticky / partial frame

`sub_554BC0()` 與 `sub_555280()` 的 TCP receive path：

```text
WSARecv into persistent buffer
    ↓
Packet copy from buffer
    ↓
v3 = sub_591F00(packet) + 8
    ↓
validate enough bytes
    ↓
(optional transform/decompression)
    ↓
sub_58B010(..., packet)
    ↓
consume exactly v3 bytes
    ↓
memmove remaining bytes to buffer front
    ↓
repeat
```

因此 client TCP receive side 明確支援：

```text
multiple frames in one recv
partial frame across recv calls
```

它不是「一次 `recv` == 一個 Packet」。

`sub_591FB0()` 可把當前接收緩衝區複製到 Packet；`sub_591D50()` 至少檢查：

```text
packet internal state valid
frame length >= 8
stored bytes >= declared frame size
```

這是 Client-side sticky/half-packet 的直接證據。

## 4. Compression transform：目前可確認的部分

`sub_591600()` 是 byte-oriented LZ-style compressor：

- 掃描 input；
- 使用 1024-entry dictionary-like state；
- 對最長匹配寫 compact 2-byte reference；
- 每 8 個輸出 decision bits 使用 control byte。

`sub_591900()` 是其對應 decompressor：

- 讀 control bits；
- reference length = `(*src >> 2) + 3`；
- reference distance = `_byteswap_ushort(*src) & 0x3FF`；
- 從已生成 output 回拷。

因此可以把這一層正式記為：

```text
sub_591600 = compression encoder
sub_591900 = compression decoder
```

目前還不能把其全部 transform flag（`19252` bits 1/2/4/8）各自直接命名成完整公開協定功能；但至少 flag-driven transform pipeline 是 confirmed。

## 5. 714：先前 wire-width 結論需要修正

`GG_INVALIDWPDATA_REQ` 的 protocol registration 對應 opcode `714`；`GG_INVALIDWPDATA_ACK` 對應 `715`。

`sub_548E80()` 的 714 serializer 是：

```text
Opcode = 714

+0  u8   local/player identity
+1  u8   `a3` = local byte/context state
+2  u8   actor-local value (`this+240596`)
+3  C-string / null-terminated ANSI string (`this+64`)
+N  u32  `a2` = Resource/Action Identity candidate
```

**因此先前將前三個欄位寫成 `u16` 的記錄是錯誤的，必須以本證據修正為 `u8/u8/u8`.**

原因不是 caller prototype，而是 serializer helper `sub_592920()` 的直接定義：

```text
sub_592920 -> sub_592580(..., 1 byte)
```

最後一個 resource/action identity 由 `sub_592A20()` 寫入 4 bytes。

## 6. 714 semantic：比單純「unknown report」更具體，但仍不過度命名

`sub_548E80()` 的 control flow：

```text
if already reported:
    return

if sub_548C80(this, a2) says allowed/common identity:
    return

++counter
if counter <= 40:
    return

build opcode 714
send
mark already reported
```

所以可確認：

```text
714 = client-side invalid/unsupported weapon-data-style report
```

而 protocol registration 的正式名字：

```text
GG_INVALIDWPDATA_REQ
```

因此相較於泛稱 `anomaly telemetry`，目前可以提高語意精度到：

```text
GG_INVALIDWPDATA_REQ
= Client → Server report triggered by an invalid/unrecognized weapon-data/resource identity path
```

但仍不應把 `WPDATA` 自行解釋成某個沒有 binary 直接證據的完整 public phrase。

## 7. 715：直接閉合成 Server → Client invalid-WP-data rejection / disconnect path

`sub_55D990()`：

```text
sub_555030(&dword_1321D00)
    -> WSACloseEvent
    -> shutdown(socket, 2)
    -> closesocket(socket)
    -> connection state = 0

sub_408080(..., 0x320)
sub_9A7DE0(message, 20, 1)
```

dispatcher 又明確：

```text
715 -> sub_55D990
```

而 protocol registration 是：

```text
GG_INVALIDWPDATA_ACK = 715
```

所以 **715 的 client-side behaviour 已可 Confirmed 為：收到 Server-side ACK 後關閉 Client 的 TCP socket，並顯示/觸發 message id `0x320` 對應的訊息流程。**

目前沒有證據證明 715 body 有任何 semantic payload；因 `sub_55D990()` 完全沒有讀 Packet payload。

因此不能新增假欄位。

## 8. 714 ↔ 715 interaction model

目前可建立：

```text
Client detects repeated invalid weapon/resource-data identity
    ↓
GG_INVALIDWPDATA_REQ (714)
    payload:
      u8 local identity
      u8 context byte
      u8 actor-local byte/value
      ANSI string
      u32 resource/action identity
    ↓
Server processing [server implementation not present]
    ↓
GG_INVALIDWPDATA_ACK (715)
    ↓
Client closes TCP connection
    ↓
Client message/UI path id 0x320
```

Server-side validation implementation本身仍不可由 Client 單方面還原；但 `714 → 715 → socket close` 的 client-side contract 已閉合。

## 9. UDP health timeout：697 的 client-side meaning 可更精確

`sub_5934B0()`：

```text
if stored timestamp == 0:
    healthy

if elapsed <= 30000 ms:
    healthy

else:
    clear timestamp
    return false
```

`sub_593510()` 在特定 internal state `n15 == 13` 且 timeout 成立時：

```text
Packet opcode = 697
write u16/word value = 1
sub_58D7D0(...)
```

protocol registration 又確認：

```text
697 = GG_CHEATER_REPORT_REQ
```

因此現階段可提升為：

```text
30-second timeout path
    ↓
client-generated GG_CHEATER_REPORT_REQ (697)
```

但不能把 timeout 本身解釋為「作弊」；真正 trigger state `n15 == 13` 與 Server receiver semantics 仍需更深層證據。

## 10. Revised confidence table

| Conclusion | Confidence | Evidence |
|---|---|---|
| TCP frame fixed header = 8 bytes | Confirmed | `sub_555090`, `sub_554BC0`, `sub_555280` |
| opcode is header word at relative offset +2 | Confirmed | `sub_591EC0/sub_591EE0` |
| client TCP handles partial + multiple frames | Confirmed | persistent receive buffer + consume/move loop |
| `sub_591600` is compressor | Strongly Supported → Confirmed at algorithm level | matching dictionary/reference encoder |
| `sub_591900` is matching decompressor | Confirmed | inverse back-reference decoder |
| 714 first 3 fields are 1 byte each | Confirmed | `sub_592920` direct width |
| 714 last field is 4-byte value | Confirmed | `sub_592A20` direct width |
| protocol name 714 = `GG_INVALIDWPDATA_REQ` | Confirmed | protocol registration |
| protocol name 715 = `GG_INVALIDWPDATA_ACK` | Confirmed | protocol registration |
| 715 closes TCP socket client-side | Confirmed | `sub_55D990 → sub_555030` |
| 715 has no client-side parsed payload | Confirmed | handler contains no Packet reader |
| 714 → 715 likely forms validation/rejection cycle | Strongly Supported | request/ack names + client close path |
| 697 = `GG_CHEATER_REPORT_REQ` | Confirmed | protocol registration |
| 697 trigger includes 30 s timeout | Confirmed | `sub_5934B0` + `sub_593510` |

## 11. Remaining high-value OPEN

```text
1. Server-side implementation of 714/715/697.
2. Exact meaning of Packet header words +24/+28/+30 under every transform flag.
3. Exact transform order between compression and the other flag-driven transforms.
4. 714 string field source (`this+64`) and whether it is weapon/resource name, player string, or another WP-data field.
5. `sub_548C80()` complete whitelist/category mapping.
6. UDP 8/24 serializers generating the 26-byte actor record.
7. Exact semantic of nested type 1/2/3/4 event objects produced by `sub_5E2570()`.
8. R+00/R+01/R+03/R+07/R+11/R+18..R+21 exact movement semantics.
```
