# PaperMan 2016 JP — 網路、封包傳輸、Dispatcher 與 UDP Movement 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、packet submission、opcode dispatcher，以及 UDP `Y_UDP_S_MOVE_INF` 的 Queue／actor record 證據。具體 gameplay semantic 仍回對應主題文件。

## 1. 一眼看懂

```text
Socket / stream
    ↓
receive buffer / queue
    ↓
outer frame / Packet
    ↓
integrity / transform
    ↓
opcode dispatcher
    ↓
packet-specific parser
    ↓
state / gameplay consumer
```

TCP 與 UDP 在 transport/dispatch 層分開：

```text
TCP
→ stream reassembly
→ frame
→ sub_58B010

UDP
→ recvfrom
→ sub_595E80
→ opcode handler
→ movement queue
→ central update consumer
```

## 2. TCP socket 與 connection

至少存在兩個主要 TCP ClientSocket：

```text
dword_131F730 → Login / Account TCP
dword_1321D00 → Lobby / Gameplay TCP
```

兩者都是：

```text
AF_INET
SOCK_STREAM
IPPROTO_TCP
```

具體 Login、Room、Gameplay packet semantic 不在此重複。[C]

## 3. TCP frame reassembly

一次 `WSARecv()` 可能得到：

```text
部分 frame
一個完整 frame
多個連續 frame
```

outer frame：

```text
+0x00 u16 logical_length
+0x02 u16 opcode
+0x04 u16 integrity / XOR field
+0x06 u16 auxiliary field
+0x08 payload
```

總傳送長度：

```text
logical_length + 8
```

Client 只有在 buffer 至少具備完整 frame 時才處理；完成後移除恰好一個 frame，餘下 bytes 留給下一個 frame。[C]

因此 Server 不得假設：

```text
一次 recv = 一個 packet
```

## 4. Integrity / XOR / checksum

共用流程：

```text
sub_592220
    → payload bit-popcount checksum

sub_5923D0
    → checksum setup
    → sub_592470

sub_592470
    → payload byte XOR header +0x04 low byte

sub_592420
    → reverse XOR
    → recompute checksum
    → compare header +0x04
```

因此：

```text
header +0x04
    = integrity value + XOR mask source
```

尚無充分證據稱它是 cryptographic key。[C][OPEN]

### 4.1 Checksum

`sub_592220()` 對每個 payload byte 計算 bit-popcount，再累加成 16-bit value。[C]

安全名稱：

```text
PayloadBitCountChecksum : ushort
```

不可自行替換成 CRC/MD5 等其它 checksum。

### 4.2 Header +0x06

`+0x06` 參與壓縮／解壓縮或 validation path，但正式 semantic 尚未閉合。[C][OPEN]

暫名：

```text
header_aux_u16
```

## 5. 共用 fixed-width codec

目前主要 helper：

```text
u8 read/write → sub_592900 / sub_592920 / sub_592940
u16 read/write → sub_5929C0 / sub_5929E0 / sub_592A00
u32 read/write → sub_592A20 / sub_592A40 / sub_592AA0 / sub_592AC0 / sub_592B20 / sub_592B40
u64/raw8       → sub_592AE0 / sub_592B00
string         → sub_5926F0 / sub_592730
raw            → sub_592500 / sub_592580
```

特別重要：

```text
sub_592B20 = 實際寫 4 bytes
sub_592B40 = 實際讀 4 bytes
sub_592AE0 = 實際寫 8 bytes
```

所以：

```text
Hex-Rays local prototype ≠ wire width
```

## 6. TCP receive dispatcher

frame 完成後進：

```text
sub_58B010(..., packet)
```

共通 receive hook 還會經：

```text
sub_407360
CGameRule::sub_67CF90
opcode = sub_591EE0(packet)
```

主要 server-originated route 目前可見：

```text
160 → sub_58D790
166 → sub_58D820
168 → sub_56F410
170 → sub_56F4F0
172 → sub_56F5D0
174 → sub_56F6B0
176 → sub_56F790
```

另承接 `193–221`、`223–245`、`269` 等 family；精確 payload 由各主題文件維護。[C]

## 7. TCP submission

主要 submission：

```text
packet
  → sub_58D7D0
  → sub_555090(&dword_1321D00, packet)
  → socket / send queue
```

`sub_602E00()` 是 conditional front-end：

```text
sub_602E00
    → special-condition check
    → normal case sub_58D7D0
```

不是另一套 transport。[C]

## 8. UDP receive architecture

UDP 不經 `sub_58B010`：

```text
CUDPNetworkManager
    ↓
sub_595A60
    ↓
sub_595E80
    ↓
opcode switch
    ↓
UDP handler
```

目前已直接觀察的主要 routes：

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

## 9. UDP `Y_UDP_S_MOVE_INF`：8/24

`sub_596940()` 有明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

且只有 `n15 == 13` 時進入 `sub_593750()`。[C]

完整 queue chain：

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom
    → validity checks
    → sub_595E80
    → opcode 8 / 24
    → sub_596940
    → sub_593750
    → queue node
    → sub_593510
    → sub_602E30
    → per-player movement/state decode
```

### 9.1 `sub_593510()` 是 central update consumer

中央更新：

```text
sub_406830
    → sub_58AFD0
        → sub_593510(&byte_1324330)
```

`sub_593510()` 會 lock queue、逐 node 處理、呼叫 `sub_602E30(node Packet)`，最後清除 processed list。[C]

Shutdown cleanup 則走其它 path，例如 `sub_58AF90 → sub_595D50`；因此 `sub_593510()` 不是單純 destructor/cleanup。[C]

### 9.2 Queue node

`sub_593750()`：

```text
EnterCriticalSection(queue +20)
→ node creation
→ LeaveCriticalSection
```

node 重要欄位：

```text
+0 iterator/link
+4 list/link
+8 Packet object
```

node +8 的 Packet 最終交給 `sub_602E30()`。[C]

### 9.3 `sub_602E30()` body

開頭讀：

```text
u8 count = N
```

之後解析 N 筆 actor record，再套用 actor/controller state。[C]

單筆 record 精確 wire layout：

```text
u8  field_00
u8  field_01
u8  field_02
u32 field_03
u32 field_04
u8  field_05
u16 field_06
u16 field_07
u16 field_08
u8  field_09
u8  field_0A
u8  field_0B
u8  field_0C
u8  field_0D
u32 field_0E
```

合計：

```text
27 bytes / actor
```

因此 movement body：

```text
u8 N
N × 27-byte actor record
```

也就是 body consumption = `1 + 27×N`；這不是完整 UDP datagram length。[C]

## 10. UDP actor record semantics

### `field_02`

送入：

```text
sub_67DF00(field_02)
sub_67D7D0(field_02)
```

最後映射到 `<16` player slot，故目前只能叫：

```text
ActorId / PlayerId candidate
```

不能直接等同 SlotIndex / session id。[C][OPEN]

### `field_04`

u32，進 movement/controller sample path。[C]

目前不能命名 timestamp、sequence 或 velocity。[OPEN]

### `field_05`

進：

```text
sub_5B3180(actor, field_05)
```

寫入 actor/player state `+233`；因此不是 padding。

目前：

```text
controller state byte candidate
```

[C][OPEN]

### `field_06..08`

各除以 `3.0`：

```text
x = field_06 / 3.0
y = field_07 / 3.0
z = field_08 / 3.0
```

再經 `sub_9BCB00()` 與 `IPaperCtrl::sub_9BCBD0()` 做 sample interpolation / averaging。[C]

因此是高度支持的 3D spatial/transform components；正式軸名稱與單位仍 `[OPEN]`。

### `field_09..0D`

都會進 gameplay/controller state path；不能只猜成 crouch/fire/jump/stance/weapon。[C][OPEN]

### `field_0E`

最重要的 Resource/Action candidate：

```text
sub_5E2570(..., field_0E, ...)
sub_548E80(player, field_0E, ...)
```

`sub_548E80()` / `sub_548C80()` 會直接比對：

```text
BOMBPLANT
Pulp_A
Pulp_B
magic_finger
Escape
```

以及 actor 內多組 action/resource identities。[C]

因此目前最安全：

```text
field_0E = ResourceOrActionId candidate
```

### 10.1 field_0E → TCP 714 report

當 player conditions 滿足時，`field_0E` 還會造成 counter 累積，超過 40 後建 TCP 714，內容至少包含：

```text
u8 local player/network id
u8 byte_EE896D
u8 player +240596
string player +64
u32 field_0E
```

再由 `sub_55D960()` 發送。[C]

因此 714 是另一條 Client→Server report path，但**不能僅此命名成 anti-cheat/cheat report**。[C][OPEN]

## 11. UDP queue lifecycle

初始化／destruction：

```text
sub_58ED30
    → sub_595C90
    → sub_593460

sub_593460
    → queue reset
    → InitializeCriticalSection(queue +20)

sub_5933F0
    → static constructor path

sub_ADC370
    → sub_593410
    → static destructor path
```

支持：

```text
UDP receive
→ enqueue
→ central update dequeue
```

的架構。[C]

## 12. Transport 與 payload 邊界

UDP movement：

```text
Packet body
    = u8 count + N × 27-byte actor record
```

但：

```text
body length
    ≠
datagram length
```

同樣，TCP：

```text
payload length
    ≠
logical frame length
    ≠
physical send length
```

Server codec 必須在 transport 與 packet schema 間保持明確邊界。[C]

## 13. Server reconstruction

Network layer：

```text
TCP
├─ StreamReader / frame reassembly
├─ Integrity / XOR / checksum
├─ OpcodeRouter
└─ Packet codec

UDP
├─ Datagram receive
├─ OpcodeRouter
├─ MovementQueue
└─ MovementPacket codec
```

Gameplay semantic 再交給：

```text
Room_GameRule_Mode.md
Gameplay_Combat.md
Result_Quest_Stats.md
Character_Inventory_Equipment.md
```

## 14. 目前 OPEN

```text
TCP header +0x06 semantic
compression / validation complete conditions
extra ordering / sequence state
transport error / retry paths
unmapped incoming opcode semantics
virtual callback concrete targets

UDP field_02 exact ID namespace
UDP field_03 semantics
UDP field_04 semantics
UDP field_05 formal state enum
UDP field_09..0D formal meanings
UDP field_0E exact Resource/Action namespace
UDP field_0E → TCP 714 purpose
UDP actor-record initialization / sender path
UDP datagram-level extra framing
```

## 15. 最高價值後續追查

```text
A. TCP +0x06 → compression / validation / ASM
B. 所有 sub_592B20 caller → exact field pairing
C. UDP 8/24 sender / producer
D. field_02 → sub_67D7D0 → exact identity namespace
E. field_0E → Extracted resource/action concrete mapping
F. 714 receive counterpart / server role
G. 166 subtype 14 ↔ UDP movement ordering
```
