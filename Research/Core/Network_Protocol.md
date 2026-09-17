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

## 14. Movement ActorRecord：27 bytes

這裡是本輪最重要的 correction：舊研究中的 **26-byte ActorRecord 錯誤已正式撤銷**。

`sub_602E30()` 每筆 fixed actor record 的實際 fixed-width read consumption 為：

```text
R+00  u8
R+01  u8
R+02  u8
R+03  u32
R+07  u32
R+0B  u8
R+0C  u16
R+0E  u16
R+10  u16
R+12  u8
R+13  u8
R+14  u8
R+15  u8
R+16  u8
R+17  u32
```

合計：

```text
27 bytes = 0x1B
```

因此：

```text
u8 actor_count
N × 27-byte fixed ActorRecord
```

舊 26-byte 結論的錯誤來源是把 Hex-Rays local scratch array／variable layout 誤當成 wire consumption；`v25` 雖宣告為較大的 local array，但實際 reader 只消費其中 1 byte。[C]

### 14.1 Fixed schema

```text
R+00  u8   v28                       [OPEN]
R+01  u8   v19                       [OPEN]
R+02  u8   n16 / actor identity      [Strongly Supported]
R+03  u32  v30                       [OPEN]
R+07  u32  v16                       [OPEN]
R+0B  u8   v25[0] / actor state byte  [Strongly Supported]
R+0C  u16  v35                       [spatial]
R+0E  u16  v36                       [spatial]
R+10  u16  v37                       [spatial]
R+12  u8   v23                       [OPEN]
R+13  u8   v38                       [OPEN]
R+14  u8   v14                       [OPEN]
R+15  u8   v15                       [OPEN]
R+16  u8   n0x1C                     [generic state/action selector]
R+17  u32  v29                       [Resource/Action identity candidate]
```

Spatial decode：

```text
float0 = R+0C / 3.0
float1 = R+0E / 3.0
float2 = R+10 / 3.0
```

`R+02` 進入 `sub_67DF00()` / `sub_67D7D0()`，並在 valid remote-slot range `<16` 內尋找 actor/player runtime object；所以高度支持 player/actor identity，但 exact identity namespace 仍 `[OPEN]`。[C]

`R+0B` 進 `sub_5B3180(actor, byte)`，並寫入 actor runtime `+233`，所以不是 padding。[C]

`R+16` 進 `sub_5B34B0()` generic actor state machinery；其 16..25 子範圍與 Emotion table 重疊，但整欄不能命名成 EmotionId。[C]

`R+17` 進 `sub_548E80()`；`sub_548C80()` 對其做 Resource/Action whitelist tests，包含：

```text
0
BOMBPLANT
Pulp_A
Pulp_B
magic_finger
Escape
```

以及 actor weapon/resource identity entries；exact namespace 仍 `[OPEN]`。[C]

### 14.2 Opcode 23：Client-side 27-byte fixed-record producer

`sub_744450()` 直接建立 Packet opcode 23，writer 與 inbound 8/24 parser 形成 offset/width 對稱：

| Offset | 8/24 inbound | 23 outbound |
|---:|---|---|
| +00 | `u8 v28` | `u8 *sub_417D00()` |
| +01 | `u8 v19` | `u8 byte_EE896D` |
| +02 | `u8 n16` | `u8 sub_67D010()` |
| +03 | `u32 v30` | `u32 dword_EE8CB4` |
| +07 | `u32 v16` | `u32 n0x64_0` |
| +0B | `u8 v25[0]` | `u8 sub_720AA0(1,0)` |
| +0C | `u16 v35` | `(this+16)*3+0.5` |
| +0E | `u16 v36` | `(this+20)*3+0.5` |
| +10 | `u16 v37` | `(this+24)*3+0.5` |
| +12 | `u8 v23` | `sub_744310()` packed state |
| +13 | `u8 v38` | derived/directional state |
| +14 | `u8 v14` | derived/directional state |
| +15 | `u8 v15` | `this+848` |
| +16 | `u8 n0x1C` | derived movement/action state |
| +17 | `u32 v29` | `sub_5AA5C0(n9)` |

Fixed payload size：

```text
27 bytes
```

因此目前 confidence：**Strongly Supported / effectively bidirectional fixed-schema evidence**。[C][X]

### 14.3 Movement state bits

`sub_744310()`：

```text
bit0 = (this+860 != 0 && this+860 != 4)
bit1 = (this+865 != 0)
bit2 = (this+867 == 0)
bit3 = (this+869 != 0 && this+1584 == 0)
bit4 = (this+871 != 0 && this+1584 == 0)
bit5 = not set by this function
bit6 = (this+866 != 0)
bit7 = (this+868 != 0)
```

安全名稱：

```text
MoveStateFlags : u8
```

各 bit 的 public semantic 仍 `[OPEN]`。

### 14.4 Movement identity/state relations

`sub_417D00()` 回傳 `&byte_EDBF58`；`PM_CONNECT_ACK (142)` handler `sub_5565D0()` 會把其一個 u8 欄位寫入該位置，因此 opcode 23 `+00` 是 connection/bootstrap-derived 1-byte identity/context value。[C]

`sub_67D010()`：

```text
n2 == 2 → -2
otherwise → local n0x10
```

並可由 `sub_67D110()` 映射到 16-entry identity table；因此 opcode 23 `+02` 是 local slot/actor identity domain，但 exact public namespace 仍 `[OPEN]`。[C]

`dword_EE8CB4` 在多處以 32-bit local player identity/value 使用，與 incoming player number comparisons 等行為一致；目前命名為 local playerNo/identity candidate，**不是** confirmed account ID。[C]

`n0x64_0` 在 movement producer 與 current gameplay timestamp path 中使用；安全名稱為 time/tick-like value，exact unit `[OPEN]`。[C]

---

## 15. Nested movement event/effect segment

`sub_5E2570()` 在 movement-related decode 中讀取 nested type：

```text
type 0 → none
```

### Type 1

```text
u8 type=1
u8 value
u8 value
6 × u16
```

15 bytes。

### Type 2

```text
u8 type=2
u16 value
u8 value
6 × u16
```

16 bytes。

### Type 3

```text
u8 type=3
u8 value
6 × u16
```

14 bytes。

### Type 4

```text
u8 type=4
u32 value
u32 value
6 × float
```

33 bytes。

Type 1/2/3 materialize runtime node type 1；type 4 materialize runtime node type 2。node 會經：

```text
sub_59E490(this+5387, this+5387, ..., &node)
```

進入 persistent linked-list / pooled queue。[C]

`sub_5E1D50()` 又會將 runtime node 重新 encode：

```text
node type 2 → wire type 4
node type 1 + flags → wire type 1/2/3
```

Type 1 path 還存在 vector difference → normalize → length+10 → offset 的 geometry correction。這使 nested segment 形成真正的 decode/encode bidirectional evidence；但 public gameplay event names 仍 `[OPEN]`。[C]

---

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

## 17. TCP gameplay event 165 / 166

165 有多個 Client-side producer：

```text
sub_55CAB0 → damage/event branch
sub_55D090 → mine/bomb branch
sub_55D530 → multi-damage branch, subtype 16
sub_55C9F0 → subtype 24/22
sub_55D440 → subtype 15
```

所以 165 應視為 polymorphic GameplayEvent envelope，而不是單一 DamagePacket。[C]

166：

```text
sub_58D820
    → sub_749B90
    → subtype dispatch
```

已看到多個 subtype group：`1`, `2/16`, `3/20`, `4`, `5`, `6`, `7`, `8/9/18/25`, `10`, `11`, `12`, `14`, `15`, `17`, `19`, `21`, `22`, `23`, `24`, `26`, `27/29`, `30`, `31/32`；完整 schema 回 `Gameplay_Combat.md`。[C]

---

## 18. 714 / 715 invalid-resource report

Protocol registration：

```text
714 = GG_INVALIDWPDATA_REQ
715 = GG_INVALIDWPDATA_ACK
```

`sub_548E80()`：

```text
already reported → return
accepted/common Resource/Action identity → return
otherwise increment anomaly counter
counter <= 40 → return
counter > 40 → send 714
```

714 fixed payload：

```text
u8 local/player identity
u8 local context/state byte
u8 actor-local value
ANSI NUL-terminated string
u32 Resource/Action identity candidate
```

前三欄經 `sub_592920()`，明確各寫 1 byte；最後欄經 `sub_592A20()`，寫 4 bytes。[C]

715：

```text
sub_55D990
  → shutdown(socket, 2)
  → closesocket
  → connection reset
  → UI/message path 0x320
```

handler 本身沒有 Packet reader，因此 715 body fields 在本 Client 中 `[OPEN]`。[C]

Client-side interaction：

```text
repeated invalid/resource identity
    → 714
    → Server [not present in Client binary]
    → 715
    → TCP disconnect
```

Confidence：**Strongly Supported** for the interaction; server implementation `[OPEN]`。

---

## 19. Client / Server responsibility boundary

Current evidence-compatible abstraction：

```text
Client
├─ local input / movement sampling
├─ local simulation / visual state
├─ resource/action lookup
├─ packet encode / decode
├─ integrity / XOR / compression / CFB-128 transform
├─ UDP endpoint / peer maintenance
└─ report / gameplay-event submission

Server
├─ authoritative session / room / player state
├─ packet validation
├─ resource / action validation
├─ authoritative gameplay resolution
├─ result / quest / reward state
└─ persistence / economy
```

只有 Client binary 能證明的 responsibility 才可直接寫成 confirmed Client behavior；Server implementation 需另外的 server evidence。[C][OPEN]

---

## 20. Server reconstruction rules

### TCP

```text
async stream reader
→ persistent receive buffer
→ 8-byte frame parse
→ declared-length validation
→ inverse transform
→ opcode dispatch
→ typed parser
```

必須支援：

```text
fragmentation
coalescing
partial send
```

### UDP

```text
datagram receive
→ Packet framing / validation
→ inverse transform
→ opcode dispatch
```

### Movement

Server-side movement producer 尚未取得，因此不要從 Client parser 假定 server serializer 的實作細節；目前可安全採用的 wire contract 是：

```text
S→C opcode 8/24
u8 actor_count
N × 27-byte fixed ActorRecord
+ optional nested event/effect segment
```

Client→peer opcode 23 是 27-byte fixed-record producer；在正常 gameplay context 下 current peer 指向 server-configured UDP endpoint，因此 server reconstruction 應保留 opcode 23 receive path。[C][OPEN]

### Crypto

Client-compatible block transform：

```text
AES/Rijndael-128-class
16-byte block
128-bit static key material
10 rounds
CFB-128
zero IV per transform invocation
no PKCS#7 padding
length rounded to 16-byte boundary
```

這些均已達到 binary-level evidence；但 checksum / transform ordering 中 `P+0x04`、`P+0x06` 的完整 lifecycle、以及 exact compressed/encrypted buffer byte semantics 仍需按 branch 持續驗證。

---

## 21. Evidence / Confidence

```text
[C]     PaperMan.exe.c direct code evidence
[EXE]   original PaperMan.exe machine-code / raw-binary evidence
[RES]   Extracted resource evidence
[WIKI]  historical Wiki / player-observable evidence
[X]     independent evidence classes agree
[OPEN]  unresolved
```

核心 rules：

```text
Parser/serializer > Hex-Rays guessed local type
Raw EXE/ASM > decompiler surface type
Same numeric value ≠ same semantic
Runtime offset ≠ wire offset
Opcode ≠ subtype
Resource ID ≠ packet semantic without data-flow
Client behavior ≠ Server implementation
```

---

## 22. Current unresolved questions

```text
1. P+0x04 IntegrityWord 的完整 sender/receiver lifecycle
2. P+0x06 TransformPreviousLength 在 compression + CFB 組合下每一 branch 的精確演化
3. compression + CFB combined frame 的 exact byte-level order / checksum scope
4. AES key schedule 的完整 runtime initialization caller / timing
5. UDP 8/24 server-side producer
6. UDP 23 formal protocol symbol/name
7. Movement R+00/R+01/R+03/R+07/R+12/R+13/R+14/R+15 exact semantics
8. Movement R+02 exact identity namespace
9. Movement R+16 complete non-Emotion enum/state domain
10. Movement R+17 exact Resource/Action namespace
11. nested event type 1/2/3/4 exact public gameplay event mapping
12. UDP 155/156 hole-information producer/consumer
13. UDP 17/19 exact periodic semantics
14. UDP 697 server counterpart
15. TCP 165/166 complete subtype wire schema
16. TCP 714 server receiver / 715 policy implementation
17. UDP opcode 154 one-byte ping unit
18. 3s / 5s peer readiness state-machine formal labels
```

---

## 23. Cross-reference

```text
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
```

本文件統一保存 Network／Packet／Movement 的 canonical wire truth；domain 文件保存 semantic truth。相同 Packet / schema 不得在不同文件各維護一套互相衝突的版本。