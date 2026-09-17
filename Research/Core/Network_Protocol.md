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

`sub_591FB0()` 將新收到的 bytes append 到 `Packet` 的 internal buffer；`sub_591D50()` 檢查目前 buffered bytes 是否至少包含完整 frame；完成 dispatch 後 receive loop 會扣除該 frame 長度並將剩餘 bytes 前移，故 TCP parser 必須支援 fragmentation 與 coalescing。[C]

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

`+0x06` 參與 transform / validation path；`sub_592E50()`、`sub_592E90()`、`sub_592F60()`、`sub_5930C0()` 代表另外的 data transform / validation stages，但目前尚未有足夠證據把 `+0x06` 單獨命名成 compression length、sequence 或 crypto field。[C][OPEN]

暫名：

```text
header_aux_u16
```

## 5. 共用 fixed-width codec

目前主要 helper：

```text
u8 read/write → sub_592900 / sub_592920 / sub_592940 / sub_592960 / sub_592980
u16 read/write → sub_5929C0 / sub_5929E0 / sub_592A00
u32 read/write → sub_592A20 / sub_592A40 / sub_592A60 / sub_592A80 / sub_592AA0 / sub_592AC0 / sub_592B20 / sub_592B40
u64/raw8       → sub_592AE0 / sub_592B00 / sub_592B60 / sub_592B80
string         → sub_5926F0 / sub_592730
raw            → sub_592500 / sub_592580
```

直接 source 已重新核對：

```text
sub_592900 / 920 / 940 / 960 / 980 = 1 byte
sub_5929C0 / 9E0 / A00             = 2 bytes
sub_592A20 / A40 / A60 / A80 / AA0 / AC0 = 4 bytes
sub_592AE0 / B00 / B60 / B80       = 8 bytes
sub_592B20 / B40                    = 4 bytes
```

特別重要：

```text
Hex-Rays local prototype ≠ wire width
```

例如 `sub_592B20()` 的表面 prototype 看起來只接 `char`，實際呼叫 `sub_592580(..., 4u)`，所以 wire width 是 4 bytes。[C]

同樣，local array 大小也不能當成 wire width。`sub_602E30()` 的 `_BYTE v25[16]` 並不代表一次讀取 16 bytes；該 call-site 只呼叫一次 `sub_592940()`，實際只消耗 1 byte。[C]

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

目前直接看到的主要 server-originated route：

```text
160 → sub_58D790
166 → sub_58D820 → sub_749B90
168 → sub_56F410
170 → sub_56F4F0
172 → sub_56F5D0
174 → sub_56F6B0
176 → sub_56F790
```

另承接 `101–221`、`223–245`、`269` 等 family；精確 payload 由各主題文件維護。[C]

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

## 8. UDP transport architecture

UDP 不經 `sub_58B010`：

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom
    → sub_595E80
    → UDP opcode handler
```

UDP socket 明確建立為：

```text
socket(AF_INET, SOCK_DGRAM, 0)
```

`CUDPSocket` constructor 的預設 port-like member 為 `27000`；`sub_596DA0()` 建立/儲存 local bind 與 remote address，`sub_596EB0()` / `sub_596F00()` / `sub_596F50()` 是 sendto wrappers，`sub_596F90()` / `sub_596FF0()` 是 recvfrom wrappers。[C]

`CUDPManager::sub_595840()` 為永久 thread loop，持續呼叫 `sub_595A60()` 後 `_sleep(1)`。[C]

### 8.1 UDP packet framing

`sub_595A60()` 收到 datagram 後：

```text
recvfrom(..., 9600)
→ sub_591FB0(Packet, bytes, received_length)
→ sub_591D50(Packet)
→ received_length >= logical_length + 8
→ sub_5930C0(Packet)
→ sub_595E80(...)
```

因此 UDP 在這個 client 中仍使用與 `Packet` 類似的內部 frame/transform model；不能把 UDP gameplay record 直接當成裸 payload 而跳過這層驗證。[C]

### 8.2 UDP receive dispatch

`sub_595E80()` 的 direct switch：

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

因此 UDP opcode/type space 明顯不只一種 movement packet。[C]

## 9. UDP `Y_UDP_S_MOVE_INF`：8/24

`sub_596940()` 有明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

且只有 `n15 == 13` 時進入 `sub_593750()`；否則會記錄錯誤並中止該 path。[C]

完整 queue chain：

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom / Packet validation
    → sub_595E80
    → opcode 8 / 24
    → sub_596940
    → sub_593750
    → queue node
    → sub_593510
    → sub_602E30
    → per-actor movement/state decode
```

### 9.1 `sub_593750()` / queue

`sub_593750()` 在 critical section 內將 Packet 插入 queue。[C]

`sub_593510()` 由 central update path 呼叫：

```text
lock queue
→ dequeue node
→ sub_602E30(Packet)
→ free/cleanup node
```

另外 `sub_5934B0()` 有 `0x7530 = 30000 ms` 的 timeout test；在指定狀態下 `sub_593510()` 會建立 TCP opcode 697。此 697 path 應視為 UDP/transport health-related control path；其更精確語意仍由 higher-level protocol file 維護。[C][OPEN]

## 10. UDP movement body：目前已重新精確落位

### 10.1 `sub_602E30()` 的 parser

開頭先讀：

```text
u8 actor_count = N
```

每一筆 actor record **不是 27 bytes 的舊版猜測表，也不是 43 bytes**。逐一按 helper 的真實 read width 計算後，確定為：

```text
26 bytes / actor
```

原因是：

```text
_BYTE v25[16]
```

只是 local scratch buffer；source 實際只有：

```c
sub_592940(a1, v25);
```

而 `sub_592940()` 實際只讀 1 byte。[C]

### 10.2 精確 wire layout

以 actor record 起始位置為 `R`：

```text
R+00  u8   v28
R+01  u8   v19
R+02  u8   n16
R+03  u32  v30
R+07  u32  v16
R+11  u8   v25[0]
R+12  u16  v35
R+14  u16  v36
R+16  u16  v37
R+18  u8   v23
R+19  u8   v38
R+20  u8   v14
R+21  u8   v15[0]
R+22  u8   n0x1C
R+23  u32  v29
```

總長：

```text
3 + 4 + 4 + 1 + 2 + 2 + 2 + 1 + 1 + 1 + 1 + 1 + 4
= 26 bytes
```

整個 movement payload 的 actor body：

```text
u8 N
N × 26-byte actor record
```

這是目前以 C parser 為準的正式 byte-level truth。[C]

### 10.3 目前可以安全命名的欄位

```text
R+00 v28       → semantics [OPEN]
R+01 v19       → semantics [OPEN]
R+02 n16       → Actor/User identity candidate
R+03 v30       → semantics [OPEN]
R+07 v16       → movement/sample state candidate [OPEN]
R+11 v25[0]    → passed into sub_5B3180(actor, byte); state byte candidate [OPEN]
R+12 v35       → spatial component candidate
R+14 v36       → spatial component candidate
R+16 v37       → spatial component candidate
R+18 v23       → controller/state byte candidate [OPEN]
R+19 v38       → controller/state byte candidate [OPEN]
R+20 v14       → controller/state byte candidate [OPEN]
R+21 v15[0]    → controller/state byte/raw-one-byte candidate [OPEN]
R+22 n0x1C      → state/action byte candidate [OPEN]
R+23 v29       → resource/action/sample value candidate [OPEN]
```

其中 `n16` 直接流入：

```text
sub_67DF00(n16)
sub_67D7D0(n16)
```

且後者會落到 `<16` 的玩家 slot range，因此 `n16` 是 actor/player identity candidate；但不能直接命名成 SlotIndex。[C][OPEN]

### 10.4 三個 u16 spatial components

C 直接做：

```text
v20 = v35 / 3.0
v21 = v36 / 3.0
v22 = v37 / 3.0
```

之後把它們作為 player/controller transform sample 的 3D vector 使用。[C]

因此高度確定：

```text
R+12/R+14/R+16 = 3 個固定點位／空間量化分量
```

但 exact axis ordering、world unit、quantization origin 目前仍 `[OPEN]`。

### 10.5 其餘 byte 欄位不能用 local variable type 猜

`v23`、`v38`、`v14`、`v15[0]`、`n0x1C` 都是獨立的 1-byte wire values，之後進入 controller/state/effect path；目前沒有證據可以把它們直接命名成 crouch、jump、fire、stance、weapon 等特定 enum。[C]

尤其：

```text
local variable name
local array size
Hex-Rays guessed type
```

均不是 wire semantic 的證據。

## 11. Actor state application

每筆 actor record 解析後：

```text
n16
  → sub_67DF00(n16)
  → sub_67D7D0(n16)
  → player runtime
```

self/remote actor 判定後，client 會處理 per-slot flags，然後：

```text
v12[0] = v16
v12[1] = v35 / 3.0
v12[2] = v36 / 3.0
v12[3] = v37 / 3.0

sub_5B3180(actor, v25[0])
sub_9BCB00(actor, v12)
sub_5B34B0(actor, v29, n0x1C, v38, v34, n16)
sub_5B71F0(&v20, n16)
```

`sub_9BCB00()` 把新 snapshot/state 寫入 actor interpolation/state structure；因此 `v12` 是至少包含一個非空間 u32 與 3 個空間 float 的 snapshot。[C]

`sub_5B3180()` 直接把 `v25[0]` 寫入 actor `+233`，證明 R+11 是有語意的 state byte，而不是 padding。[C]

`sub_5B34B0()` 接收：

```text
v29, n0x1C, v38, v34, n16
```

並進一步參與 controller/effect processing；exact enum mapping 尚 `[OPEN]`。[C]

`sub_5B71F0()` 會以 `sub_67D7D0(n16)` 找 player slot，並將 `dword_F6DD34[slot]` 經 `sub_568470()` / `sub_9C1B20()` / `sub_62D6C0()` 套入輸入/position-like state；它不是 packet parser 本身，而是 actor update 的後續 state propagation。[C]

## 12. UDP send / peer transport

### 12.1 Generic packet send

`sub_595900(packet)`：

```text
len = sub_591F00(packet) + 8
send local UDP socket from packet + 24
```

因此 `Packet` object 的 internal base 與 physical datagram buffer 並不是同一個 address。[C]

### 12.2 Peer-address send

`sub_595980()` 可將 packet 封裝成 `logical_length + 8` 後，使用傳入的 address pair 送出；`sub_595A10()` 先以 `sub_595BD0()` 取得目前 peer address。[C]

### 12.3 已確認的 UDP periodic packets

`sub_596180()`：

```text
每 >= 1000 ms
→ Packet opcode 17
→ sub_595900()
```

`sub_596670()`：

```text
每約 500 ms
→ Packet opcode 19
→ sub_595A10()/related UDP path
```

其中 19 還帶有 retry/count-like state，最多進入 5 次的 escalation path；不能只稱為普通 heartbeat。[C][OPEN]

## 13. Gameplay event relationship

UDP movement 與 TCP gameplay event 並非兩條完全獨立的語意世界。TCP opcode 166 會進：

```text
sub_58B010
→ sub_58D820
→ sub_749B90
```

`sub_749B90()` 再依 subtype 將事件送入多個 gameplay handlers：

```text
7       → sub_748E40
8/9/18/25 → sub_748EB0
12      → sub_749A30
13      → stage/player reset cleanup
17      → sub_748FF0
24      → time / round-like handling
1       → sub_746360
2/16    → sub_7463E0
3/20    → sub_747980
4       → sub_748860
5       → sub_748A50
6       → sub_748CD0
10      → sub_749230 / sub_749520
11      → sub_7494B0 / sub_749810
14      → sub_749AB0
15      → sub_748420
19      → sub_74D150
21      → sub_747DD0
22      → sub_747AB0
23      → sub_74D410
26      → sub_745F50
27/29   → sub_746060
30      → sub_74D510
31/32   → sub_74D5D0
```

因此 opcode 166 是 subtype-bearing gameplay event envelope，不是單一事件。[C]

## 14. TCP opcode 165：Client→Server gameplay event envelope

目前多個 sender 都直接建立 opcode 165，顯示它是 gameplay event family，而非單一 damage struct。

### 14.1 `sub_55CAB0()` — OnSendPacketDamage

Common shape：

```text
u8 source/player
u8 subtype
(optional special-mode: 3 × u16)
u8 target/player
(optional effect/category byte for selected subtypes)
u16 weapon/resource identity
u32 transformed value A
u32 transformed value B
u8 n4
u8 a8
u8 a9
u32 target-related state dword_F6DD1C[target]
u8 a10
u32 a11
u32 a12
u32 a13
(optional n4==4: resource/action byte + int, or 255)
```

實際 output 會把 `sub_5E72C0()` 產生的兩個 values 量化後用 `sub_592B20()` 寫出；因 `sub_592B20()` 是 4-byte writer，這裡不是 1-byte float field。[C]

### 14.2 `sub_55D090()` — OnSendPacketMineBombDamage

同為 opcode 165，但 subtype 由 caller 傳入，並含：

```text
source
subtype
 target
 optional effect/category
resource u16
2 × transformed u32-like values
several zero/state u32 fields
dword_F6DD1C[target]
additional bytes
```

因此 mine/bomb damage 是同一 opcode family 的另一 branch。[C]

### 14.3 `sub_55D530()` — OnSendPacketMultiDamage

明確寫入 subtype `16`，後面除 source/target/resource 外，還有多個額外 4-byte values，代表 multiple-hit/multi-damage aggregation；這也是 opcode 165 的另一個固定 subtype branch。[C]

### 14.4 其它直接 sender

```text
sub_55C9F0() → opcode 165 subtype 24 / 22
sub_55D440() → opcode 165 subtype 15
```

這再次證實 165 應抽象成：

```text
GameplayEvent165
    = source + subtype + subtype-specific payload
```

而不是 `DamagePacket` 一個 class。[C]

## 15. Damage / weapon state boundary

`sub_5E1CD0()` 會在條件下選擇：

```text
sub_5E06A0()
或
sub_5E0F10()
```

後者遍歷 target/hit candidates、取 `sub_67DFB0(actor)`，再經 weapon/action/resource lookup 計算 damage。它會從 4 個 weapon loadout slots 中比對 current action/resource identity，並進一步呼叫 `sub_603230()` 等 effect/hit generation path。[C]

當 computed damage 達到 threshold 時：

```text
sub_9BC3E0(target, ...)
sub_9BC420(hit_effect_selector, transformed_hit_position)
sub_5E63C0(...)   // death/state transition when applicable
```

之後 local client 再經 `sub_55CAB0()` 等 sender 將 gameplay event 發出去。[C]

因此目前可安全建模成：

```text
input / local simulation
    → hit / weapon calculation
    → local visual/state application
    → gameplay event packet
    → server-side validation / authoritative resolution
```

最後一段的 authoritative server boundary 在目前 client-only evidence 中仍不是「所有情況 100% 證明」，所以 server model 應標為高可信 architectural inference，而非偽裝成直接 C proof。[C][OPEN]

## 16. UDP / TCP / state 三層不能混為一談

目前模型：

```text
Transport
├─ TCP stream
└─ UDP datagram/thread

Protocol envelope
├─ Packet frame
├─ opcode/type
└─ subtype / variable payload

Gameplay state
├─ PlayerState
├─ Character/Equipment
├─ Weapon/Action
├─ Hit/Damage
├─ Room/Mode
└─ Result/Quest
```

尤其：

```text
actor identity != slot index
weapon identity != action identity
packet opcode != packet subtype
runtime object offset != wire field offset
```

這些 distinction 是重寫 Server 時避免系統性錯位的核心。

## 17. Server reconstruction boundary

Network layer：

```text
TCP
├─ Stream reader / frame reassembly
├─ integrity / XOR / checksum
├─ transform/validation
├─ OpcodeRouter
└─ packet codec

UDP
├─ datagram receive
├─ Packet validation / transform
├─ OpcodeRouter
├─ MovementQueue
└─ actor-record codec
```

Gameplay semantic 再交給：

```text
Room_GameRule_Mode.md
Gameplay_Combat.md
Result_Quest_Stats.md
Character_Inventory_Equipment.md
Login_ClientData_Protocol.md
Resource_Pack_Model.md
```

## 18. 目前仍真正 OPEN 的問題

```text
TCP header +0x06 的正式語意
TCP transform/compression exact formula 與 enable conditions
完整 TCP send queue / retry semantics

UDP movement 26-byte record 的：
  R+00 v28 exact meaning
  R+01 v19 exact meaning
  R+02 n16 exact identity namespace
  R+03 v30 exact meaning
  R+07 v16 exact meaning
  R+11 v25[0] formal state enum
  R+12/R+14/R+16 exact axis/unit encoding
  R+18 v23 exact meaning
  R+19 v38 exact meaning
  R+20 v14 exact meaning
  R+21 v15[0] exact meaning
  R+22 n0x1C exact meaning
  R+23 v29 exact namespace/semantics

UDP 8/24 sender/producer call-site
UDP datagram-level external wrapper beyond Packet layer
UDP opcode 17/19 exact gameplay/network-health semantics
UDP timeout 697 counterpart / server role

TCP 165/166 all subtype payloads and exact server validation contracts
TCP 714 exact counterpart / purpose
Exact itemdata category-specific weapon/action fields
Exact maplist tail field names
Exact public weapon-part slot ↔ PARTS06/07 mapping
Full raw itemdata.pat byte-level schema
```

## 19. 最高價值後續追查順序

```text
A. sub_591600 / sub_591900 / sub_593110 / sub_4042A0
   → close TCP/Packet transform

B. exact UDP 8/24 sender producer
   → reverse-construct the 26-byte record

C. all consumers of v28/v19/v30/v16/v23/v38/v14/n0x1C/v29
   → formalize movement fields

D. n16 → sub_67D7D0 → exact actor identity namespace

E. v29 → action/resource identity table

F. 165/166 subtype pairs
   → build complete gameplay event schema

G. 714 receive counterpart
   → close client/server report boundary

H. itemdata.pat category-specific fields
   → close weapon/character/effect definitions
```

## 20. Evidence discipline

```text
[C]     IDA C direct evidence
[RES]   Extracted resource evidence
[WIKI]  Wiki / player-observable historical behavior
[X]     at least two independent evidence classes agree
[OPEN]  unresolved; do not silently replace with 0 or invented enum
```

Parser/serializer implementation has priority over Hex-Rays guessed local types. Resource definitions, runtime state, and network wire layouts must remain distinct until a conversion path is directly established.
