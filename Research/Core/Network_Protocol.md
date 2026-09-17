# PaperMan 2016 JP — 網路、封包傳輸、Dispatcher 與 UDP Movement 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-18。
> 本文件是 Network／Packet／UDP Movement 的 canonical protocol truth；具體 gameplay semantic 仍回對應 domain 文件。
> 本輪已直接重新檢查上傳的 `PaperMan.exe` 原始二進位，並以其 PE／machine-code 與 `PaperMan.exe.c` 交叉驗證。

## 1. 一眼看懂

```text
TCP stream / UDP datagram
        ↓
Packet internal buffer
        ↓
8-byte outer frame
        ↓
checksum / XOR / transform
        ↓
opcode dispatch
        ↓
packet parser
        ↓
state / gameplay consumer
```

TCP 與 UDP 在 transport 層不同，但兩者都使用 `Packet` family 的 fixed-width codec 與外層 frame machinery。[C][EXE]

---

## 2. TCP socket / connection

至少存在：

```text
dword_131F730 → Login / Account TCP
dword_1321D00 → Lobby / Gameplay TCP
```

兩者均使用：

```text
AF_INET
SOCK_STREAM
IPPROTO_TCP
```

`dword_1321D00` 是主要 Lobby / Gameplay send path；`sub_555090()` 最終以 `WSASend()` 完整送出 Packet frame。[C]

---

## 3. Packet outer frame：raw layout 已可確認

`Packet::sub_591DA0()` 直接建立 pointer：

```text
this + 8  → this + 24
this + 12 → this + 26
this + 16 → this + 28
this + 20 → this + 30
this + 19232 → this + 32
```

因此以 physical frame 起點 `P = Packet + 24`：

```text
P+0x00  u16  logical/current payload length
P+0x02  u16  opcode
P+0x04  u16  integrity/checksum-related word
P+0x06  u16  transform auxiliary / previous-length state
P+0x08  payload / transformed bytes
```

直接 accessor：

```text
sub_591EC0(packet, opcode) → *(P+0x02) = opcode
sub_591EE0(packet)         → read *(P+0x02)
sub_591F00(packet)         → read *(P+0x04)
sub_591F20(packet, len)    → write current length at *(P+0x00)
sub_591F90(packet, value)  → write auxiliary length at *(P+0x06)
```

這些不是 Hex-Rays local-field 猜測；pointer target 在 `sub_591DA0()` 中直接指向 `P+0/P+2/P+4/P+6`。[C]

Physical frame length：

```text
frame_bytes = logical/current_length + 8
```

TCP sender `sub_555090()` 與 UDP generic sender `sub_595900()` 都直接使用：

```text
buffer = packet + 24
length = sub_591F00(packet) + 8
```

[C][EXE]

---

## 4. TCP stream reassembly：sticky / partial frame confirmed

`sub_591FB0()` 把新收到的 bytes append 到 persistent Packet buffer；`sub_591D50()` 檢查：

```text
frame length >= 8
buffered bytes >= declared frame size
```

TCP receive loop 在 frame 完成後只消費該 frame，剩餘 bytes 留在 receive buffer 並前移，因此 Client 明確支援：

```text
partial frame across multiple recv
multiple frames in one recv
```

所以 Server 不可使用：

```text
one recv == one packet
```

作為 framing 假設。[C]

---

## 5. Checksum / XOR integrity

共用完整性流程：

```text
sub_592220
    → 對 payload bytes 做 bit-popcount 累加

sub_5923D0
    → 計算 checksum
    → sub_592470

sub_592470
    → payload byte XOR header P+0x04 low byte

sub_592420
    → reverse XOR
    → 重新計算 checksum
    → compare P+0x04
```

`sub_592220()` 的 checksum 演算法是每 byte 計數 set bits，再累加到 16-bit。[C]

安全命名：

```text
PayloadBitCountChecksum : ushort
```

不能命名成 CRC、MD5 或 cryptographic MAC。[C]

目前最保守的 `P+0x04` 名稱：

```text
IntegrityWord
```

它同時參與 XOR mask 與 integrity 驗證；目前沒有證據把它命名為真正的 encryption key。[C][OPEN]

---

## 6. Packet transform flags：compression + block cipher 已直接閉合

Packet 內部 flag byte 位於：

```text
Packet + 0x4B34
```

目前已直接確認：

```text
bit 0x01 → compression stage already applied
bit 0x02 → decompression stage already applied
bit 0x04 → block-cipher transform stage already applied
bit 0x08 → inverse block-cipher transform stage already applied
```

### 6.1 Compression

`sub_592D30()`：

```text
if bit 1 already set → no-op
count = current length
sub_591600(payload, dst, count)
if compressed result is smaller:
    copy dst back to payload
    P+0x06 = old length
    P+0x00 = compressed length
set flag 0x01
```

`sub_591600()` 是 dictionary/LZ-style compressor，使用 1024-distance domain 與 compact reference token；每 8 個 token 使用 control bits。[C]

`sub_591900()` 是對應 decompressor：

```text
reference length   = (*src >> 2) + 3
reference distance = _byteswap_ushort(*src) & 0x3FF
```

### 6.2 AES/Rijndael block cipher：已由原始 EXE 直接驗證

上傳的原始 `PaperMan.exe`：

```text
PE32 / i386
ImageBase = 0x00400000
```

原始 machine code 中：

```text
0x403430  → key-schedule initialization
0x403650  → 16-byte block encrypt path
0x403A20  → inverse block path
0x403DE0  → block transform wrapper
0x404040  → inverse block transform wrapper
0x4042A0  → multi-block mode wrapper
0x404470  → inverse multi-block mode wrapper
```

`0x403430` 直接設定：

```text
n16 = 16
n16_0 = 16
n10 = 10
```

並產生 **44 個 32-bit round-key words**。

同一區域使用的 `byte_B66C08` 是標準 AES S-box；四組 `dword_B68E08/B69208/B69608/B69A08` 是 AES T-table style round tables。`0x403650`/`0x403A20` 每次處理 16-byte block。[C][EXE]

因此目前 algorithm-level 結論：

```text
block size = 16 bytes
key size   = 128 bits
rounds     = 10
algorithm  = AES / Rijndael-128 class implementation
```

Confidence：**Confirmed at algorithm level**。

原始 EXE 還可直接看到 key-schedule 的 16-byte static key material 位於 `VA 0x00B69E88`；其後使用標準 AES Rcon sequence `01 02 04 08 10 20 40 80 ...`。[EXE]

> Exact key bytes 可由原始 EXE 直接重建；此文件只記錄其存在與用途，避免把「static key material」與 packet header field 混為一談。

### 6.3 Packet 與 AES 的直接關係

不是單純「EXE 有 AES library」。`sub_592FB0()` 直接呼叫：

```text
sub_4042A0(
    packet payload,
    temporary buffer,
    block-aligned length,
    global mode = 2
)
```

因此 Packet 的 `bit 0x04` stage **確實進入這套 16-byte AES/Rijndael class block cipher**。[C][EXE]

`sub_593110()` 是對應 inverse stage，並要求 block-aligned length；它將 transform 前保存的 length state 恢復到 Packet length machinery。[C]

目前尚不能在沒有更多 runtime/ASM context 前，把 `mode = 2` 直接命名成 CBC/CTR/CFB/OFB 某一標準模式；其實作包含自訂 mode wrapper。故：

```text
AES block transform = Confirmed
exact mode/IV semantics = OPEN
```

### 6.4 Transform order

Outbound `sub_593280()`：

```text
initial auxiliary length state
    ↓
optional compression (bit 0x01)
    ↓
block cipher transform (bit 0x04)
    ↓
checksum / send validation
```

Receive `sub_593320()`：

```text
inverse block transform (bit 0x08)
    ↓
optional decompression (bit 0x02)
    ↓
final dispatch
```

Flag order本身可由 caller graph 建立；但 `P+0x06` 在不同 transform stage 中保存前一層 length，故不應僅將它固定命名成「uncompressed length」或「plaintext length」。安全名稱是：

```text
TransformPreviousLength : u16
```

其具體數值在每一 stage 的生命週期仍需逐 branch 關閉。[C][OPEN]

---

## 7. Send / receive submission

主要 TCP send：

```text
packet
 → sub_58D7D0
 → sub_555090(&dword_1321D00, packet)
 → WSASend loop
```

`sub_555090()` 不假設一次 WSASend 就完成全部 bytes；它會：

```text
Buffers.buf += NumberOfBytesSent
Buffers.len -= NumberOfBytesSent
```

直到整個 frame 送完。[C]

失敗時會區分：

```text
WSAEWOULDBLOCK → Sleep(1) → retry
other network errors → error handler
```

這是 client-side partial-send evidence。[C]

---

## 8. UDP architecture

UDP manager：

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom
    → Packet validation / transform
    → sub_595E80
    → UDP opcode handler
```

`CUDPSocket`：

```text
socket(AF_INET, SOCK_DGRAM, 0)
```

constructor 中 default port-like member：

```text
27000
```

`sub_596DA0()`：

```text
local bind = 0.0.0.0 : configured local port
remote configured sockaddr = supplied IP/port
```

`sub_596E60()` 儲存另一組 configured destination sockaddr。

send wrappers：

```text
sub_596EB0 → sendto(this+24)
sub_596F00 → sendto(this+40)
sub_596F50 → sendto(caller sockaddr)
```

receive wrappers：

```text
sub_596F90 → recvfrom(this+60)
sub_596FF0 → recvfrom(caller sockaddr)
```

[C][EXE]

---

## 9. UDP Packet framing

`sub_595A60()`：

```text
recvfrom(..., 9600)
→ sub_591FB0(Packet, bytes, received_length)
→ sub_591D50(Packet)
→ received_length >= frame length
→ sub_5930C0(Packet)
→ sub_595E80(..., Packet)
```

因此 UDP datagram 亦不是裸 gameplay body；它仍受 `Packet` outer frame 與 transform machinery 處理。[C]

UDP receive manager direct cases：

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

完整 TCP dispatcher map 另存於 `Network_Dispatcher_Inventory.md`。[C]

---

## 10. UDP peer / endpoint architecture

Client maintains a 16-player endpoint table keyed by player/actor identity，不能假設 identity == slot。[C]

Per-slot endpoint areas：

```text
unk_F6D584 + 240780*slot
    → learned peer endpoint/address state
    → 16 bytes

unk_F6D594 + 240780*slot
    → local/source sockaddr captured for peer-response path
    → 16 bytes
```

identity lookup：

```text
dword_F6DCF4[60195*slot]
```

UDP peer-addressed traffic uses caller-supplied sockaddr and `sendto()`。[C]

### 10.1 Endpoint maintenance family

```text
opcode 4 inbound
    = u8 count + count × (u8 identity + 16-byte endpoint)
    → update F6D584
    → fan-out opcode 5

opcode 5 inbound
    = u8 identity + u32 timing-like value
    → capture source endpoint
    → first-arrival state transition
    → emit opcode 6

opcode 6 inbound
    = u8 identity + u32 timing-like value
    → finalize/capture peer source endpoint state

opcode 10 inbound
    = u8 identity + 16-byte endpoint
    → update F6D584
    → emit opcode 13

opcode 12 inbound
    = u8 count + count × (u8 identity + 16-byte endpoint)
    → bulk F6D584 update
    → emit opcode 13 fan-out

opcode 13 inbound
    = u8 identity + u32 timing-like value
    → capture source endpoint
    → emit opcode 14 on first arrival

opcode 14 inbound
    = u8 identity + u32 timing-like value
    → terminal receive-side state update
```

Peer response packets 5/6/13/14 constructed by Client all use：

```text
u8 local identity
u32 timing-like value = n0x3E8_3
```

`n0x3E8_3` originates from elapsed-time calculations based on `timeGetTime() - dword_F2563C`; its exact protocol meaning is still `[OPEN]` — do not call it RTT, nonce, sequence or timestamp without additional evidence.[C]

Peer readiness logic has distinct `3000 ms` and `5000 ms` timeout checks.[C]

### 10.2 Ping / player quality side channel

UDP opcode `22`：

```text
u8 mode/record flag
if flag == 1:
    u8 count
    count × (u8 player identity + u32 ping-like value)
```

UDP opcode `154`：

```text
u8 count
count × (u8 player identity + u8 ping-like value)
```

Both write the same per-player table：

```text
dword_F6D9E8[slot]
```

UI consumer：

```text
sub_9A8F40(value)
    → Ping_%d
```

Thresholds in `sub_9A8F40()`：

```text
<100       → 5
100–199    → 4
200–299    → 3
300–999    → 2
1000–4999  → 1
>=5000     → 0
```

因此 per-player latency/ping classification state 已有 Client-side direct consumer 證據；opcode 154 的 raw one-byte unit 仍 `[OPEN]`。[C]

---

## 11. UDP `Y_UDP_S_MOVE_INF`: 8 / 24

`sub_596940()` 包含明文：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

僅在：

```text
n15 == 13
```

時把 Packet 放進 movement queue。[C]

完整 chain：

```text
recvfrom
 → Packet validation / transform
 → opcode 8 / 24
 → sub_596940
 → sub_593750
 → movement queue
 → sub_593510
 → sub_602E30
 → actor record parser
```

`sub_593750()` 在 critical section 內 enqueue；central path 再 dequeue、解析、cleanup。[C]

---

## 12. Movement actor record：27 bytes，舊 26-byte 結論已永久修正

`sub_602E30()` 先讀：

```text
u8 actor_count = N
```

每個 actor 的固定部分依 fixed-width helpers 實際消耗：

```text
+00  u8   v28
+01  u8   v19
+02  u8   n16
+03  u32  v30
+07  u32  v16
+0B  u8   v25[0]
+0C  u16  v35
+0E  u16  v36
+10  u16  v37
+12  u8   v23
+13  u8   v38
+14  u8   v14
+15  u8   v15
+16  u8   n0x1C
+17  u32  v29
```

總長：

```text
27 bytes = 0x1B
```

完整 fixed actor payload：

```text
u8 N
N × 27-byte fixed actor record
```

**26 bytes 的舊結論是錯誤的；錯誤來源是把 Hex-Rays local scratch array size 當成 wire consumption。** 例如 `v25[16]` 只經一次 `sub_592940()`，實際只讀 1 byte。[C]

### 12.1 Actor record fixed-field evidence

```text
R+00 → unknown
R+01 → unknown
R+02 → actor/player identity candidate
R+03 → unknown u32
R+07 → movement/sample scalar candidate
R+0B → actor state byte candidate
R+0C → spatial component
R+0E → spatial component
R+10 → spatial component
R+12 → controller/state byte
R+13 → controller/state byte
R+14 → controller/state byte
R+15 → controller/state byte
R+16 → generic PState/action-state selector candidate
R+17 → Resource/Action identity candidate
```

位置三分量直接：

```text
v20 = v35 / 3.0
v21 = v36 / 3.0
v22 = v37 / 3.0
```

然後進 actor transform/snapshot state，因此 `R+0C/R+0E/R+10` 已可安全命名為 quantized spatial components。[C]

`R+02` 進：

```text
sub_67DF00(n16)
sub_67D7D0(n16)
```

並在 valid remote slot range `<16` 下取得 player runtime object，因此高度支持 actor/player identity；仍不可直接把 wire value 命名成 SlotIndex。[C]

`R+0B` 直接進：

```text
sub_5B3180(actor, v25[0])
```

並寫 actor runtime state `+233`，故它不是 padding。[C]

`R+16` 進：

```text
sub_5B34B0(actor, v29, n0x1C, v38, v34, n16)
```

值 `16..25` 有另外的 10-entry Emotion command/state mapping；但整個欄位是 generic actor action/state machinery，不能全域稱 Emotion。[C]

`R+17` 進 `sub_548E80()`，而 `sub_548C80()` 對它做 Resource/Action whitelist checks：

```text
0
BOMBPLANT
Pulp_A
Pulp_B
magic_finger
Escape
```

以及 actor weapon/resource identity blocks。[C]

### 12.2 Opcode 23：Client-side fixed-record producer，27 bytes

`sub_744450()` 直接建立：

```text
Packet opcode = 23
```

並以 fixed-width writer 寫出：

```text
+00  u8   *sub_417D00()
+01  u8   byte_EE896D
+02  u8   sub_67D010()
+03  u32  dword_EE8CB4
+07  u32  n0x64_0
+0B  u8   sub_720AA0(1,0)
+0C  u16  (this+16) * 3 + 0.5
+0E  u16  (this+20) * 3 + 0.5
+10  u16  (this+24) * 3 + 0.5
+12  u8   sub_744310() packed state
+13  u8   derived/directional state
+14  u8   derived/directional state
+15  u8   this+848
+16  u8   derived movement/action state
+17  u32  sub_5AA5C0(n9)
```

逐欄 offset/width 與 inbound 8/24 parser 完全對齊：[C]

| Offset | 8/24 inbound parser | 23 outbound producer |
|---:|---|---|
| +00 | `u8 v28` | `u8 *sub_417D00()` |
| +01 | `u8 v19` | `u8 byte_EE896D` |
| +02 | `u8 n16` | `u8 sub_67D010()` |
| +03 | `u32 v30` | `u32 dword_EE8CB4` |
| +07 | `u32 v16` | `u32 n0x64_0` |
| +0B | `u8 v25[0]` | `u8 sub_720AA0(1,0)` |
| +0C | `u16 v35` | quantized X-like component |
| +0E | `u16 v36` | quantized Y-like component |
| +10 | `u16 v37` | quantized Z-like component |
| +12 | `u8 v23` | packed movement state |
| +13 | `u8 v38` | directional/state value |
| +14 | `u8 v14` | directional/state value |
| +15 | `u8 v15` | `this+848` |
| +16 | `u8 n0x1C` | derived movement/action state |
| +17 | `u32 v29` | `sub_5AA5C0(n9)` |

因此：

```text
8/24 fixed actor schema
    ↕ exact offset/width symmetry
23 fixed actor schema
```

confidence：**Strongly Supported → effectively bidirectional fixed-schema evidence**。

注意：23 的 nested segment 不一定存在；若 `this+1364 != 0`，會再呼叫 `sub_5E1D50()`。[C]

---

## 13. Movement-adjacent nested event/effect segment

### 13.1 `sub_5E2570()` parser

fixed actor record 後，`sub_5E2570()` 先讀：

```text
u8 nested_type
```

若為 0：

```text
no nested event segment
```

### Type 1

```text
u8 type = 1
u8 value
u8 value
6 × u16 spatial values
```

Wire size：

```text
1 + 1 + 1 + 12 = 15 bytes
```

### Type 2

```text
u8 type = 2
u16 value
u8 value
6 × u16 spatial values
```

Wire size：

```text
1 + 2 + 1 + 12 = 16 bytes
```

### Type 3

```text
u8 type = 3
u8 value
6 × u16 spatial values
```

Wire size：

```text
1 + 1 + 12 = 14 bytes
```

### Type 4

```text
u8 type = 4
u32 value
u32 value
6 × float values
```

Wire size：

```text
1 + 4 + 4 + 24 = 33 bytes
```

這四種 nested forms 都會建立 pooled runtime node：

```text
runtime node type 1 ← wire type 1/2/3
runtime node type 2 ← wire type 4
```

Type 1/2/3 node：

```text
node +00 = 1
node +01 = outer a4
node +02 = caller a7
node +04 = actor identity n16
node +05 = subtype-1 value or -1
node +06 = subtype-2 value or -1
node +07 = outer a6
node +08..+10 = one 3D vector
node +11..+13 = second 3D vector
```

Type 4 node：

```text
node +00 = 2
node +02 = caller a7
node +04 = actor identity
node +56 = (first u32 != 0)
node +57 = (second u32 != 0)
node +08..+10 = 3D float data
```

每個 node 最終經：

```text
sub_59E490(this + 5387, this + 5387, v17, &node)
```

進入持續存在的 linked-list / pooled queue，不是 parser local temporary。[C]

### 13.2 `sub_5E1D50()` producer：現在可由兩端交叉驗證

`sub_744450()` 在 `this+1364 != 0` 時：

```text
sub_5E1D50(this+1364, packet, n0x64)
```

`sub_5E1D50()` 從同一 runtime queue 選出 node，再重新序列化成 Type 1/2/3/4 nested segment。

Producer branch：

```text
runtime node type 2
    → wire type 4
    → 1 byte type
    → 2 × u32
    → 6 × float

runtime node type 1
    + flags
    → wire type 1 / 2 / 3
    → subtype-specific leading byte/word fields
    → 6 × quantized u16 coordinates
```

Quantization：

```text
float coordinate × 3.0 + 0.5
→ u16 writer
```

Type 1 有一條額外幾何修正 branch：

```text
vector difference
→ length
→ normalize
→ length + 10
→ offset along normalized direction
→ update node position
→ serialize as type 2-like subtype branch
```

這表示 nested event data 不是單純顯示資料；producer 端會根據 runtime node state 重新計算幾何資料。[C]

因此：

```text
sub_5E2570 (decode)
        ↕
sub_5E1D50 (encode)
```

已形成真正的 bidirectional schema evidence。exact public gameplay event names 仍 `[OPEN]`。

---

## 14. UDP timeout / health control

`sub_5934B0()`：

```text
stored timestamp == 0
    → healthy

elapsed <= 30000 ms
    → healthy

elapsed > 30000 ms
    → clear timestamp
    → unhealthy
```

`sub_593510()` 在：

```text
n15 == 13
AND timeout check fails
```

時建立：

```text
TCP opcode 697
u16 payload = 1
```

Protocol registration：

```text
697 = GG_CHEATER_REPORT_REQ
```

因此 Client-side direct fact 是：

```text
30-second UDP/transport health timeout
    → client emits GG_CHEATER_REPORT_REQ (697)
```

但 `n15 == 13` 的 full state meaning 與 Server receiver semantics 仍 `[OPEN]`；不能把 timeout 本身等同於 cheating。[C]

---

## 15. TCP gameplay event family: 165 / 166

TCP opcode 165 有多個 Client-side sender，包含：

```text
sub_55CAB0  → damage/event branch
sub_55D090  → mine/bomb damage branch
sub_55D530  → multi-damage branch, subtype 16
sub_55C9F0  → subtype 24 / 22
sub_55D440  → subtype 15
```

所以 165 應建模成：

```text
GameplayEvent165
    = source + subtype + subtype-specific payload
```

不是一個固定 `DamagePacket` class。[C]

目前 166 server→client 又進：

```text
sub_58D820
    → sub_749B90
    → subtype dispatch
```

166 subtype map 包含：

```text
1       → sub_746360
2/16    → sub_7463E0
3/20    → sub_747980
4       → sub_748860
5       → sub_748A50
6       → sub_748CD0
7       → sub_748E40
8/9/18/25 → sub_748EB0
10      → sub_749230 / sub_749520
11      → sub_7494B0 / sub_749810
12      → sub_749A30
14      → sub_749AB0
15      → sub_748420
17      → sub_748FF0
19      → sub_74D150
21      → sub_747DD0
22      → sub_747AB0
23      → sub_74D410
24      → time/round handling
26      → sub_745F50
27/29   → sub_746060
30      → sub_74D510
31/32   → sub_74D5D0
```

因此 165/166 是 polymorphic gameplay event envelope；完整 subtype schema 仍在 `Gameplay_Combat.md` 維護。[C]

---

## 16. Opcode 714 / 715

Protocol registration：

```text
714 = GG_INVALIDWPDATA_REQ
715 = GG_INVALIDWPDATA_ACK
```

`sub_548E80()`：

```text
if already reported → stop
if identity is accepted/common → stop
otherwise increment anomaly counter
counter <= 40 → stop
counter > 40 → construct/send 714
```

714 fixed payload width：

```text
u8  local/player identity
u8  local context/state byte
u8  actor-local value
ANSI null-terminated string
u32 Resource/Action Identity candidate
```

其中前三欄直接經 `sub_592920()`，因此必為 1 byte；最後欄經 `sub_592A20()`，因此為 4 bytes。[C]

714 的安全語意：

```text
Client → Server invalid/unrecognized weapon-data/resource-identity report
```

715 handler：

```text
sub_55D990
    → sub_555030(&dword_1321D00)
    → shutdown(socket, 2)
    → closesocket(socket)
    → message/UI path id 0x320
```

715 handler 本身沒有 Packet reader，因此 client-side 目前沒有證據支持它存在 body fields。[C]

Interaction model：

```text
repeated invalid/resource identity path
    → 714
    → Server [implementation unavailable]
    → 715
    → Client TCP disconnect
```

confidence：**Strongly Supported** for the complete Client-side interaction；Server-side implementation仍 `[OPEN]`。

---

## 17. Client / Server responsibility boundary

目前 evidence-compatible architecture：

```text
Client
├─ local simulation / visual state
├─ input / movement sampling
├─ local resource/action lookup
├─ packet encode / decode
├─ checksum / XOR / transform
├─ UDP peer endpoint maintenance
└─ report / gameplay event submission

Server
├─ authoritative session / room / player state
├─ packet validation
├─ weapon/action/resource validation
├─ gameplay authoritative resolution
├─ result / quest / reward state
└─ persistence / economy
```

Client-only evidence 可以直接證明 Client-side responsibilities；Server authoritative behavior 若沒有 Server binary/PDB，不得寫成「Client C 已證實」。

---

## 18. Server reconstruction rules derived from this file

### TCP

```text
async stream reader
→ persistent receive buffer
→ header parse
→ frame-size validation
→ inverse transform
→ dispatcher
→ typed packet parser
```

必須處理：

```text
fragmentation
coalescing
partial send
WSAEWOULDBLOCK retry
```

### UDP

```text
datagram receive
→ outer Packet validation
→ inverse transform
→ UDP opcode dispatch
→ movement queue / peer handler
```

### Movement

```text
u8 actor_count
→ N × 27-byte fixed actor record
→ optional variable nested event segment
```

Server serializer 若需要與 Client 23→8/24 family 相容，fixed record 必須維持：

```text
27-byte exact offsets
```

不能從舊版 26-byte research 或 local array size 生成 schema。

### Packet transform

當 Client-compatible encryption required：

```text
16-byte block cipher
AES/Rijndael-128-class
10 rounds
Packet transform flag 0x04/0x08
```

但 exact custom mode / IV / interaction with compression and `P+0x06` length lifecycle 仍 `[OPEN]`；不要自行替換成標準 AES-CBC/CTR 實作，直到最後一層 evidence 關閉。

---

## 19. 目前主要 unresolved

```text
1. Packet P+0x04 IntegrityWord 的完整 sender/receiver lifecycle
2. Packet P+0x06 TransformPreviousLength 在每個 transform branch 的精確語意
3. AES mode=2 的 exact IV/mode semantics
4. AES key initialization 的完整 runtime initialization path
5. compression + AES combined frame 的 exact length evolution
6. UDP 8/24 server-side producer
7. UDP 23 formal protocol symbol/name
8. Movement R+00/R+01/R+03/R+07/R+12/R+13/R+14/R+15 exact semantics
9. Movement R+02 exact identity namespace
10. Movement R+16 generic state selector完整 enum
11. Movement R+17 exact Resource/Action namespace
12. nested event type 1/2/3/4 exact public gameplay event mapping
13. UDP 155/156 hole-information producer/consumer
14. UDP 17/19 exact periodic semantics
15. UDP 697 server counterpart
16. TCP 165/166 complete subtype wire schema
17. TCP 714 server receiver / 715 policy implementation
```

---

## 20. Evidence discipline

```text
[C]     PaperMan.exe.c direct code evidence
[EXE]   original PaperMan.exe machine-code / raw-binary evidence
[RES]   Extracted game-resource evidence
[WIKI]  historical Wiki / player-observable evidence
[X]     independent evidence classes agree
[OPEN]  unresolved
```

Rules：

```text
Parser/serializer > Hex-Rays guessed prototype
Raw EXE/ASM > surface decompiler type
Same numeric value ≠ same semantic
Runtime offset ≠ wire offset
Opcode ≠ subtype
Resource ID ≠ packet semantic without data-flow evidence
Client behavior ≠ Server implementation
```

未知欄位永遠保留 `[OPEN]`，除非直接證據、反向資料流、Resource 或可靠歷史資料足以解鎖。

---

## 21. Cross-reference

```text
Network_Dispatcher_Inventory.md
Login_ClientData_Protocol.md
Room_Channel_GameRule_101_221_Field_Evidence.md
Character_Inventory_Equipment.md
Room_GameRule_Mode.md
Gameplay_Combat.md
Result_Quest_Stats.md
Resource_Pack_Model.md
Server_State_Model.md
KickVote/Research.md
```

本文件保存 Network／Packet／Movement 的 canonical wire truth；domain 文件保存 semantic truth；不要讓兩份文件各自維護不同版本的同一 Packet schema。