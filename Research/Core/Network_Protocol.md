# PaperMan 2016 JP — 網路、封包傳輸、Dispatcher 與 UDP Movement 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-18。
> 本文件是 Network／Packet／UDP Movement 的 canonical wire truth；具體 gameplay semantic 仍回對應 domain 文件。
> 本輪已直接回查原始 `PaperMan.exe`，並以 machine-code／raw data 與 `PaperMan.exe.c` 交叉驗證。

## 1. 一眼看懂

```text
TCP stream / UDP datagram
        ↓
Packet internal buffer
        ↓
8-byte outer frame
        ↓
integrity / XOR / transform
        ↓
opcode dispatch
        ↓
packet parser
        ↓
state / gameplay consumer
```

TCP 與 UDP transport 不同，但兩者都使用同一族 `Packet` framing / transform machinery。[C][EXE]

---

## 2. TCP socket / connection

已確認至少存在：

```text
dword_131F730 → Login / Account TCP
dword_1321D00 → Lobby / Gameplay TCP
```

兩者建立為：

```text
AF_INET
SOCK_STREAM
IPPROTO_TCP
```

`dword_1321D00` 是主要 Lobby / Gameplay send path；`sub_555090()` 最終以 `WSASend()` 傳輸完整 Packet frame。[C]

---

## 3. Packet outer frame：8-byte wire header

`sub_591DA0()` 將 Packet object 的內部資料區與四個 16-bit state accessor 建立固定關係；physical frame 起點為 `Packet + 24`，payload 起點為 `Packet + 32`。[C]

以 physical frame `P = Packet + 24` 表示：

```text
P+0x00  u16  current/declared length state
P+0x02  u16  opcode
P+0x04  u16  integrity / checksum word
P+0x06  u16  transform previous-length state
P+0x08  byte payload
```

直接 accessor：

```text
sub_591EC0(packet, opcode) → P+0x02
sub_591EE0(packet)         → P+0x02
sub_591F00(packet)         → P+0x04
sub_591F20(packet, len)    → P+0x00
sub_591F90(packet, value)  → P+0x06
```

Physical frame length：

```text
frame_bytes = declared/current length + 8
```

TCP send 與 UDP generic send 都直接以 `packet + 24` 為 frame 起點，並使用 `length + 8`。[C][EXE]

### Naming discipline

`P+0x00..0x06` 是目前已由 Packet object pointer／accessor 與 send/receive boundary 閉合的 wire-relative layout；semantic naming 仍採保守名稱：

```text
P+0x00 = CurrentLength
P+0x02 = Opcode
P+0x04 = IntegrityWord
P+0x06 = TransformPreviousLength
```

不要把 `P+0x04` 自行命名成 encryption key、CRC 或 MAC；不要把 `P+0x06` 固定解釋成 plaintext/uncompressed length。[C][OPEN]

---

## 4. TCP stream reassembly

`sub_591FB0()` 將收到的 bytes append 到 persistent Packet/receive buffer；`sub_591D50()` 驗證：

```text
frame length >= 8
buffered bytes >= declared frame size
```

完成一個 frame 後，TCP receive loop 只消費該 frame，剩餘 bytes 會前移並繼續解析。[C]

因此 Client 明確支援：

```text
partial frame across multiple recv
multiple frames in one recv
```

Server framing 不能使用：

```text
one recv == one Packet
```

---

## 5. Integrity / checksum / XOR

目前已閉合的流程為：

```text
sub_592220
    → 對 payload bytes 計算 set-bit 數量並累加到 16-bit

sub_5923D0
    → 產生 checksum / integrity value
    → 進入 XOR stage

sub_592470
    → payload bytes XOR P+0x04 的 low byte

sub_592420
    → reverse XOR
    → 重新計算 checksum
    → compare P+0x04
```

安全命名：

```text
PayloadBitCountChecksum : u16
P+0x04                  : IntegrityWord
```

這不是證據足以命名為 CRC、MD5、HMAC 或其他 cryptographic MAC。[C]

---

## 6. Packet transform pipeline

Packet object 的 transform flag byte 位於：

```text
Packet + 0x4B34
```

已確認的 bit：

```text
0x01 → compression stage marker
0x02 → decompression stage marker
0x04 → block-cipher transform marker
0x08 → inverse block-cipher transform marker
```

### 6.1 Compression

`sub_591600()` 是 dictionary/LZ-style compressor：

```text
1024-distance domain
control bits per 8 decisions
compact back-reference token
```

`sub_591900()` 為對應 decoder：

```text
reference length   = (*src >> 2) + 3
reference distance = byteswap(u16) & 0x3FF
```

`sub_592D30()` 只在壓縮結果更小時取代 payload，並用 `P+0x06` 保存前一層 length。[C]

### 6.2 Outbound transform order

`sub_593280()` 的主要流程：

```text
save initial length into transform-length state when needed
        ↓
optional compression
        ↓
block transform
        ↓
integrity / send path
```

### 6.3 Receive transform order

`sub_593320()` 的主要流程：

```text
inverse block transform
        ↓
optional decompression
        ↓
dispatch / parse
```

`P+0x06` 是 stage-to-stage previous-length storage；在多段 transform 中不能簡化成單一「原始長度」欄位。[C][OPEN]

---

## 7. AES/Rijndael-128：由原始 EXE 直接閉合

原始 `PaperMan.exe` 為 PE32/i386、`ImageBase=0x00400000`。關鍵 routine：

```text
0x403430  key schedule initialization
0x403650  AES block encrypt
0x403A20  AES inverse block
0x403DE0  block-encrypt wrapper
0x404040  inverse-block wrapper
0x4042A0  multi-block mode wrapper
0x404470  inverse multi-block mode wrapper
```

`0x403430`：

```text
block size = 16 bytes
round count = 10
round-key words = 44 × u32
key material input = 16 bytes
```

同一 code path 使用標準 AES S-box / T-table data 與 Rcon sequence，因此 algorithm-level classification 為：

```text
AES / Rijndael-128-class
block size = 128 bits
key size   = 128 bits
rounds     = 10
```

Confidence：**Confirmed**。[C][EXE]

### 7.1 Static key material

原始 EXE 在 `VA 0x00B69E88` 可直接讀到 key-schedule input 的 16 bytes：

```text
c6 ae b7 b7 c5 a9 c1 a1 b7 c9 c0 fc b8 d3 c1 f6
```

這是 binary-level fact；它不應與 Packet header `IntegrityWord` 混為一談。[EXE]

### 7.2 Packet transform 與 AES 的直接關係

`sub_592FB0()` 並非單純使用一般 crypto library；它直接呼叫：

```text
sub_4042A0(payload, scratch, block_aligned_length, mode=2)
```

因此 Packet 的 `0x04` transform stage 確實進入上述 AES/Rijndael primitive。[C][EXE]

---

## 8. Exact block mode：mode=2 = CFB-128，已解除 OPEN

原始 machine code 已閉合 `0x4042A0` / `0x404470` 的 mode branches：

```text
mode 0 → ECB
mode 1 → CBC
mode 2 → CFB (full 128-bit segment / CFB-128)
```

Packet path 的 global mode value 為：

```text
2
```

而對應 `sub_4042A0()` / `sub_404470()` 每次 invocation 都先建立 **16-byte zero chain**，因此：

```text
mode = CFB-128
IV / initial chain = 16 zero bytes
chain scope = one transform invocation
```

原始 binary 的 mode=2 branch 結構是標準 full-block CFB：

```text
S0 = AES(K, zero_IV)
C0 = P0 XOR S0
S1 = AES(K, C0)
C1 = P1 XOR S1
...
```

inverse branch 使用相同前向 AES keystream construction：

```text
S0 = AES(K, zero_IV)
P0 = C0 XOR S0
S1 = AES(K, C0)
P1 = C1 XOR S1
...
```

因此不是 CBC/CTR/OFB；`mode=2` 應以 CFB-128 實作。[EXE]

### 8.1 Zero-IV / stateless property

初始 chain 是 wrapper 內部 local buffer，並在每次 call 重新清為 zero；沒有證據顯示 chain 跨 Packet 保存。

所以：

```text
packet A encryption
packet B encryption
```

不共享前一個 Packet 的 CFB state。

Confidence：**Confirmed**。[EXE]

### 8.2 Padding / length behavior

`sub_592FB0()` / `sub_592FB0`-related path 會把目前 payload length round-up 到 16-byte boundary，並將 transform 前 length 保存到 `P+0x06`；`sub_593110()` 再按 saved length 恢復。[C][EXE]

因此目前可確定：

```text
transform length = ceil(length / 16) * 16
```

但不是證據足以稱為：

```text
PKCS#5
PKCS#7
zero padding
```

因此 server compatibility implementation 不應自行加上標準 PKCS padding；應忠實複製 Client 的 length-rounding / buffer semantics。[C][EXE]

### 8.3 Mode global

Raw data：

```text
VA 0x00BEFAD0 = 16
VA 0x00BEFAD4 = 16
VA 0x00BEFAD8 = 2
```

`0xBEFAD8` 在已檢查的 transform path 中是 mode read；沒有找到後續改寫它的 static store。對本 Client packet path，mode 固定為 `2`。[EXE]

---

## 9. Send / receive submission

主要 TCP send chain：

```text
packet
 → sub_58D7D0
 → sub_555090(&dword_1321D00, packet)
 → WSASend loop
```

`sub_555090()` 會根據 `NumberOfBytesSent` 推進 buffer/length，直到整個 frame 傳完；`WSAEWOULDBLOCK` 走 `Sleep(1)` retry，其他 network error 走 error handler。[C]

這證明 Client 自身也不假定一次 send 完成整個 frame。

---

## 10. UDP architecture

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

constructor 的 port-like default 為 `27000`；實際 bind 使用 runtime local-port member，因此 `27000` 不是「已確認的最終 server UDP port`」。

`sub_596DA0()`：

```text
local bind = 0.0.0.0 : configured local port
configured destination = supplied endpoint
```

Send wrappers：

```text
sub_596EB0 → sendto(this+24)
sub_596F00 → sendto(this+40)
sub_596F50 → sendto(caller sockaddr)
```

Receive wrappers：

```text
sub_596F90 → recvfrom(this+60)
sub_596FF0 → recvfrom(caller sockaddr)
```

---

## 11. UDP Packet framing / dispatcher

`sub_595A60()`：

```text
recvfrom(..., 9600)
→ sub_591FB0
→ sub_591D50
→ transform / validation
→ sub_595E80
```

UDP datagram 同樣走 Packet outer frame；不是裸 gameplay payload。[C]

Direct UDP receive cases：

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

完整 TCP opcode → handler map 維護於 `Network_Dispatcher_Inventory.md`。

---

## 12. UDP peer / endpoint architecture

Client 維護 16-entry player/peer table。identity 先 lookup slot，不能假設 identity == slot。[C]

```text
unk_F6D584 + 240780*slot
    = learned peer endpoint/address blob
    = 16 bytes

unk_F6D594 + 240780*slot
    = source/local sockaddr captured for peer response
    = 16 bytes

dword_F6DCF4[slot]
    = player/actor identity mapping
```

### 12.1 Endpoint maintenance

```text
opcode 4 inbound
  u8 count
  count × (u8 identity + 16-byte endpoint)
  → update F6D584
  → fan-out opcode 5

opcode 5 inbound
  u8 identity + u32 timing-like value
  → capture source endpoint on first path
  → emit opcode 6

opcode 6 inbound
  u8 identity + u32 timing-like value
  → endpoint/source state finalize path

opcode 10 inbound
  u8 identity + 16-byte endpoint
  → update F6D584
  → emit opcode 13

opcode 12 inbound
  u8 count
  count × (u8 identity + 16-byte endpoint)
  → bulk F6D584 update
  → fan-out opcode 13

opcode 13 inbound
  u8 identity + u32 timing-like value
  → capture source endpoint
  → emit opcode 14 on first path

opcode 14 inbound
  u8 identity + u32 timing-like value
  → terminal state path
```

Client response packets 5/6/13/14 use：

```text
u8 local identity
u32 n0x3E8_3
```

`n0x3E8_3` 來源為 `timeGetTime() - dword_F2563C` 類 elapsed-time 計算；精確 protocol meaning 仍 `[OPEN]`，不能直接叫 RTT、nonce、sequence 或 absolute timestamp。[C]

Peer readiness 有至少兩個 distinct timeout：`3000 ms` 與 `5000 ms`。[C]

### 12.2 Ping / quality side channel

UDP 22：

```text
u8 mode/record flag
if == 1:
    u8 count
    count × (u8 identity + u32 ping-like value)
```

UDP 154：

```text
u8 count
count × (u8 identity + u8 ping-like value)
```

兩者都寫：

```text
dword_F6D9E8[slot]
```

UI：

```text
sub_9A8F40(value)
    → Ping_%d
```

thresholds：

```text
<100       → 5
100–199    → 4
200–299    → 3
300–999    → 2
1000–4999  → 1
>=5000     → 0
```

故 per-player ping/latency classification 是 Client-side confirmed consumer behavior；opcode 154 的 raw one-byte unit 尚 `[OPEN]`。[C]

---

## 13. UDP `Y_UDP_S_MOVE_INF`: opcode 8 / 24

`sub_596940()` 的明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

只有 gameplay gate `n15 == 13` 時才 enqueue movement data。[C]

Chain：

```text
recvfrom
 → Packet validation / transform
 → opcode 8 / 24
 → sub_596940
 → sub_593750
 → movement queue
 → sub_602E30
```

---

## 14. UDP Movement wire schema

### Server → Client: opcode 8 / 24

sub_596940 的 diagnostic 明確使用 Y_UDP_S_MOVE_INF；在 gameplay gate 成立時交給 sub_602E30 解析。[C]

Payload：

    u8 actor_count
    actor_count × 27-byte ActorRecord

ActorRecord：

| Offset | Width | Canonical name |
|---:|---:|---|
| +0x00 | u8 | field00 |
| +0x01 | u8 | field01 |
| +0x02 | u8 | ActorKey / PlayerKey candidate |
| +0x03 | u32 | field03 |
| +0x07 | u32 | field07 |
| +0x0B | u8 | ActorStateByte |
| +0x0C | u16 | Spatial0 |
| +0x0E | u16 | Spatial1 |
| +0x10 | u16 | Spatial2 |
| +0x12 | u8 | state/controller byte |
| +0x13 | u8 | state/controller byte |
| +0x14 | u8 | state/controller byte |
| +0x15 | u8 | state/controller byte |
| +0x16 | u8 | StateCode |
| +0x17 | u32 | WeaponNum / GunIndex candidate |

Spatial0/1/2 在 Client 端各自以 u16 / 3.0 解碼。[C]

R+16 的已知子域：

    16..25 = Emotion command/state IDs

整個 R+16 仍屬 generic state-transition domain，不應全欄命名成 EmotionId。[C]

R+17 已有 CGunDataCtrl index evidence；完整 function-level provenance 由 UDP_Movement_Control_Evidence_2026-09-18.md 維護。[C]

### Client → UDP destination: opcode 23

sub_744450 固定建立 opcode 23，payload 為 27 bytes。[C]

| Offset | Width | Source / current naming |
|---:|---:|---|
| +0x00 | u8 | sub_417D00-derived value |
| +0x01 | u8 | byte_EE896D |
| +0x02 | u8 | sub_67D010 |
| +0x03 | u32 | dword_EE8CB4 |
| +0x07 | u32 | n0x64_0 |
| +0x0B | u8 | sub_720AA0(1,0) |
| +0x0C | u16 | position × 3 + 0.5 |
| +0x0E | u16 | position × 3 + 0.5 |
| +0x10 | u16 | position × 3 + 0.5 |
| +0x12 | u8 | sub_744310 |
| +0x13 | u8 | derived state/angle |
| +0x14 | u8 | derived state/angle |
| +0x15 | u8 | this+848 |
| +0x16 | u8 | state/action byte |
| +0x17 | u32 | sub_5AA5C0 → WeaponNum / GunIndex |

兩方向共享 identity/state/position/weapon-value families，但不是同一 binary struct；完整 function-level provenance 見 UDP_Movement_Control_Evidence_2026-09-18.md。[C][X]

## 15. Movement nested segment

Movement-related packet 後方可有 optional nested event/effect segment。[C]

| Type | Wire form | Size |
|---:|---|---:|
| 0 | none | 0 |
| 1 | u8 type + u8 + u8 + 6×u16 | 15 |
| 2 | u8 type + u16 + u8 + 6×u16 | 16 |
| 3 | u8 type + u8 + 6×u16 | 14 |
| 4 | u8 type + u32 + u32 + 6×float | 33 |

sub_5E2570 解碼，sub_5E1D50 將 runtime node 再編碼回相同四類 wire form；因此 schema 已有雙向證據。[C]

public gameplay event name 仍為 [OPEN]。

## 16. UDP recovery / health control

`sub_5934B0()`：

```text
stored timestamp == 0 → healthy
elapsed <= 30000 ms → healthy
elapsed > 30000 ms → clear + unhealthy
```

`sub_593510()` 在 `n15 == 13` 且 timeout failure 時建立：

```text
TCP opcode 697
u16 payload = 1
```

Protocol registration：

```text
697 = GG_CHEATER_REPORT_REQ
```

所以 Client-side direct fact 是：

```text
30-second UDP/transport health timeout
    → client emits 697
```

這不能單獨被解讀為「偵測到作弊」；`n15==13` full semantic 與 server counterpart 仍 `[OPEN]`。[C]

---

## 17. Cross-domain packet references

165 / 166 的完整 gameplay-event / combat semantic → Gameplay_Combat.md。

714 / 715 的 function-level evidence → UDP_Movement_Control_Evidence_2026-09-18.md。

141–144 PM_CONNECT / PM_UDPSTART bootstrap 的 function-level evidence → UDP_Movement_Control_Evidence_2026-09-18.md。

本文件只保存 Network layer 所需的名稱與關係，不複製各 domain 的完整 packet schema。

## 18. Invalid-resource report reference

714 = GG_INVALIDWPDATA_REQ
715 = GG_INVALIDWPDATA_ACK

本文件只保留 opcode-level relationship；欄位寬度、counter、whitelist、715 disconnect 行為等 function-level evidence 統一維護於 UDP_Movement_Control_Evidence_2026-09-18.md。

## 19. Client / Server responsibility boundary

Client binary 直接證明的責任包括 packet encode/decode、TCP stream framing、checksum/XOR、compression、AES/CFB-128 transform、movement/input sampling、UDP endpoint/peer maintenance，以及部分 gameplay-event / validation report submission。[C]

沒有 Server binary/PDB 時，不把 Client behaviour 直接當作 Server implementation。

## 20. Server reconstruction rules

### TCP

    persistent stream buffer
    → 8-byte frame parse
    → declared-length validation
    → inverse transform
    → opcode dispatch
    → typed parser

必須支援 fragmentation、coalescing 與 partial send。

### UDP

    datagram
    → Packet framing / validation / transform
    → opcode dispatch

### Movement

    8/24 → u8 actor_count + N × 27-byte ActorRecord
    23   → fixed 27-byte Client movement/state record

### Crypto

    AES / Rijndael-128 class
    block = 16 bytes
    key = 128 bits
    rounds = 10
    mode = CFB-128
    IV = 16 zero bytes per transform invocation
    transform length = round-up to 16 bytes

P+0x04 / P+0x06 的完整 lifecycle 仍屬 OPEN。

## 21. Evidence / Confidence

### Confirmed

- Packet outer frame is 8 bytes.
- TCP framing uses declared length + 8 and supports fragmented/coalesced stream data.
- Payload checksum uses set-bit count accumulation; IntegrityWord is checked after reverse XOR.
- Packet transform uses an AES/Rijndael-128-class primitive.
- Packet mode 2 is CFB-128 with a per-invocation zero IV.
- UDP 8/24 is Y_UDP_S_MOVE_INF.
- UDP 8/24 fixed ActorRecord is 27 bytes.
- UDP 23 fixed Client record is 27 bytes.
- Movement spatial fields use u16 ↔ /3.0 conversion.
- R+16 contains the confirmed Emotion subdomain 16..25.
- UDP 22 carries u32 per-player values; UDP 154 carries u8 per-player values.
- UDP 18 triggers TCP PM_CONNECT_REQ (141) with empty payload.
- 697 is generated by the observed 30-second health-timeout path.
- 714/715 names are registered; 715 closes the Client TCP connection.

### Strongly Supported

- R+02 belongs to the actor/player identity domain, exact public namespace unresolved.
- R+17 maps to WeaponNum / GunIndex in the CGunDataCtrl domain.
- Client maintains a 16-entry identity → peer-endpoint table.
- 8/24 and 23 share movement/state/position/weapon-value families but are separate wire schemas.

### Open

Detailed unresolved questions remain in the next section; function-level evidence belongs in the UDP movement/control appendix.

## 22. Current unresolved questions

    1. P+0x04 IntegrityWord complete sender/receiver lifecycle
    2. P+0x06 TransformPreviousLength complete combined-transform lifecycle
    3. compression + CFB exact buffer/length semantics
    4. AES key initialization runtime caller/timing
    5. UDP 8/24 server-side producer
    6. opcode 23 formal protocol symbol/name
    7. Movement R+00/R+01/R+03/R+07 semantics
    8. Movement R+02 exact identity namespace
    9. Movement R+12/R+13/R+14/R+15 exact public semantics
    10. Movement R+16 non-Emotion state domain
    11. Movement R+17 exact CGunData public namespace
    12. nested event type 1/2/3/4 public gameplay mapping
    13. UDP 155/156 producer/consumer
    14. UDP 17/19/20 exact semantics
    15. UDP 154 one-byte value unit
    16. 3s / 5s peer state-machine labels
    17. TCP 165/166 complete subtype schemas
    18. TCP 714 server receiver / 715 server policy

## 23. Cross-reference

    Network_Dispatcher_Inventory.md
    UDP_Movement_Control_Evidence_2026-09-18.md
    Login_ClientData_Protocol.md
    Room_Channel_GameRule_101_221_Field_Evidence.md
    Character_Inventory_Equipment.md
    Room_GameRule_Mode.md
    Gameplay_Combat.md
    Result_Quest_Stats.md
    Resource_Pack_Model.md
    Server_State_Model.md
    KickVote/Research.md

Canonical ownership:

    Network_Protocol.md
        = Network / Packet wire truth

    UDP_Movement_Control_Evidence_2026-09-18.md
        = UDP movement/control function-level deep evidence

    Network_Dispatcher_Inventory.md
        = complete TCP opcode → direct handler inventory

    Domain files
        = gameplay / room / character / result semantic truth

同一 Packet / State / Domain 不得在不同文件維護第二套互相衝突的定義。

