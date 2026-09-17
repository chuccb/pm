# PaperMan 2016 JP — UDP Movement / Control Plane 深入證據

> 研究日期：2026-09-18。
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 本文件是 `Network_Protocol.md` 的唯一 UDP movement/control 深度證據附錄：集中保存跨函式、state、peer/bootstrap、recovery 與 Resource 交叉驗證；Packet／crypto 的 canonical wire truth 仍以 `Network_Protocol.md` 為準。

## 1. 最重要的結論

目前已直接從 `PaperMan.exe.c`／原始 EXE 閉合：

```text
Server → Client
UDP opcode 8 / 24
payload = u8 actor_count + N × 27-byte fixed ActorRecord

Client → UDP peer
UDP opcode 23
payload = 27-byte fixed LocalMovementState
```

兩方向的位置編碼直接形成同一量化家族：

```text
Client serializer:
    u16((world_value * 3.0) + 0.5)

Server→client decoder:
    u16 / 3.0
```

因此目前可安全保留「以 1/3 world-unit 類量化表示」的描述；負值、overflow、world-origin 與完整 rounding policy 不自行補。[C][EXE][X]

---

## 2. UDP transport 基礎

### 2.1 Socket

`CUDPSocket`：

```text
socket(AF_INET, SOCK_DGRAM, 0)
```

constructor 將 port-like member 設為 `27000`，但 `sub_596DA0()` 綁定的是 runtime local-port member：

```text
local bind = 0.0.0.0 : runtime local port
remote endpoint = supplied IP/port
```

所以 `27000` 只能稱為 constructor default，不能直接當作最終 server UDP port。[C]

### 2.2 Receive loop

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom(..., 9600)
    → Packet framing / validation / transform
    → sub_595E80
```

receive loop 每輪有 `_sleep(1)`。[C]

### 2.3 Destination separation

```text
Configured UDP destination
    = CUDPSocket +40 area
    = sub_595A10 / sub_596F00

Per-player learned peer endpoint
    = unk_F6D584 / unk_F6D594
    = sendto(caller sockaddr)
```

因此 Client 同時存在 configured destination 與 per-player peer endpoint 兩種 addressing state。[C]

---

## 3. UDP receive dispatcher

`sub_595E80()` 直接 dispatch：

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

低 opcode 涵蓋 peer maintenance、movement、health/recovery 與 latency/control traffic。[C]

---

## 4. Server → Client movement：opcode 8/24

`sub_596940()` 存在明文：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

只有 gameplay gate `n15 == 13` 時才進 `sub_593750()` queue；之後由 `sub_602E30()` 解析。[C]

### 4.1 Wire structure

```text
u8 actor_count
N × ActorRecord
```

每筆固定 record 為 **27 bytes = 0x1B**：

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

**舊 26-byte 結論已正式撤銷。** 錯誤來自把 Hex-Rays local array／scratch storage 與實際 fixed-width reader consumption 混淆；`v25` 雖為較大的 local array，wire reader 實際只消費一個 byte。[C]

### 4.2 Field model

```text
R+00  u8   field00                          [OPEN]
R+01  u8   field01                          [OPEN]
R+02  u8   actor/player identity candidate  [Strongly Supported]
R+03  u32  field03                          [OPEN]
R+07  u32  field07                          [OPEN]
R+0B  u8   actor state byte                 [Strongly Supported]
R+0C  u16  quantized spatial component 0    [Confirmed spatial]
R+0E  u16  quantized spatial component 1    [Confirmed spatial]
R+10  u16  quantized spatial component 2    [Confirmed spatial]
R+12  u8   controller/state byte            [OPEN]
R+13  u8   controller/state byte            [OPEN]
R+14  u8   controller/state byte            [OPEN]
R+15  u8   controller/state byte            [OPEN]
R+16  u8   StateCode / state-transition selector [Strongly Supported]
R+17  u32  WeaponNum / GunIndex candidate       [Strongly Supported]
```

`R+02` 進 `sub_67DF00()` / `sub_67D7D0()`，並在 `<16` remote-slot domain 內取得 actor/player runtime object；因此高度支持 identity，但 exact public namespace 仍 `[OPEN]`。[C]

`R+0B` 進 `sub_5B3180(actor, byte)` 並寫 actor runtime `+233`，所以不是 padding。[C]

`R+16` 進 generic `sub_5B34B0()` state/action machinery；`16..25` 是其中已確認的 Emotion command/state 子域，但整欄不能命名成 `EmotionId`。[C]

`R+17` 進 `sub_548E80()`；`sub_548C80()` 以 Resource/Action whitelist 驗證它，包含：

```text
0
BOMBPLANT
Pulp_A
Pulp_B
magic_finger
Escape
```

以及 actor weapon/resource identity entries；exact namespace `[OPEN]`。[C]

---

## 5. Spatial encoding：雙向對稱

Server→Client：

```text
float0 = R+0C / 3.0
float1 = R+0E / 3.0
float2 = R+10 / 3.0
```

Client→UDP peer opcode 23：

```text
R+0C = u16((this+16) * 3.0 + 0.5)
R+0E = u16((this+20) * 3.0 + 0.5)
R+10 = u16((this+24) * 3.0 + 0.5)
```

因此是同一 quantized spatial wire family。[C][X]

尚未閉合：

```text
axis ↔ public X/Y/Z naming
negative range
overflow behavior
world-origin convention
exact rounding policy
```

---

## 6. `R+16` / Emotion 子域

`sub_9A8580(n)` 精確判斷：

```text
16 <= n <= 25
```

`sub_7170F0()` 建立：

```text
emotion1  = 16
emotion2  = 17
emotion3  = 18
emotion4  = 19
emotion5  = 20
emotion6  = 21
emotion7  = 22
emotion8  = 23
emotion9  = 24
emotion10 = 25
```

因此：

```text
R+16 ∈ 16..25
    → Confirmed Emotion command/state domain

R+16 outside 16..25
    → generic actor state/action domain
```

Wiki 的《操作ガイド》亦將 F12 對應 Emotion、F11 可隱藏 Emotion list；這是玩家可見層的獨立 corroboration，但不取代 C-level state boundary。[WIKI][C]

---

## 7. Client → UDP peer movement：opcode 23

`sub_744450()` 建立 opcode 23，後續：

```text
sub_602D70
→ sub_596B90
→ sub_595A10
→ current UDP destination/peer
```

### 7.1 Fixed payload

```text
+00  u8   *sub_417D00()
+01  u8   byte_EE896D
+02  u8   sub_67D010()
+03  u32  dword_EE8CB4
+07  u32  n0x64_0
+0B  u8   sub_720AA0(1,0)
+0C  u16  (this+16)*3 + 0.5
+0E  u16  (this+20)*3 + 0.5
+10  u16  (this+24)*3 + 0.5
+12  u8   sub_744310()
+13  u8   derived/directional state
+14  u8   derived/directional state
+15  u8   this+848
+16  u8   derived movement/action state
+17  u32  sub_5AA5C0(n9)  // WeaponNum / GunIndex
```

總長 **27 bytes**。[C]

### 7.2 `MoveStateFlags`

`sub_744310()` 產生：

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

安全命名：

```text
MoveStateFlags : u8
```

每個 bit 的 public semantic 仍 `[OPEN]`。[C]

### 7.3 Identity/state relations

`sub_417D00()` 回傳 `&byte_EDBF58`；`PM_CONNECT_ACK (142)` handler `sub_5565D0()` 會以 u8 更新該位置，因此 opcode 23 `+00` 是 connection/bootstrap-derived 1-byte value。[C]

`sub_67D010()`：

```text
n2 == 2 → -2
otherwise → local n0x10
```

並由 `sub_67D110()` 映射到 16-entry identity table，因此 +02 屬於 local slot/actor identity domain，exact public namespace `[OPEN]`。[C]

`dword_EE8CB4` 在多處以 32-bit local player identity/value 使用，包含與 incoming player number 的比較；安全命名為 local playerNo/identity candidate，不升格為 confirmed account ID。[C]

`n0x64_0` 是 time/tick-like gameplay value；exact unit `[OPEN]`。[C]

---

## 8. Client/Server movement schema 必須分離

```text
S→C
opcode 8 / 24
u8 N + N × 27-byte fixed ActorRecord
+ optional nested event/effect segment

C→peer
opcode 23
27-byte fixed LocalMovementState
```

兩者欄位寬度／offset 相互對稱，但不能重用同一個 binary struct。[C][X]

---

## 9. Movement-adjacent nested event/effect segment

`sub_5E2570()` 讀第一個 `u8 nested_type`：

```text
type 0 → none
```

### Type 1

```text
u8 type=1
u8 value
u8 value
6 × u16
= 15 bytes
```

### Type 2

```text
u8 type=2
u16 value
u8 value
6 × u16
= 16 bytes
```

### Type 3

```text
u8 type=3
u8 value
6 × u16
= 14 bytes
```

### Type 4

```text
u8 type=4
u32 value
u32 value
6 × float
= 33 bytes
```

Type 1/2/3 → runtime node type 1；type 4 → runtime node type 2。node 透過：

```text
sub_59E490(this+5387, this+5387, ..., &node)
```

進 persistent linked-list / pooled queue，因此不是 parser local temporary。[C]

`sub_5E1D50()` 又將 node encode 回 type 1/2/3/4；Type 1 path 存在 vector difference → normalize → length+10 → position offset 的 geometry correction。[C]

所以 nested segment 已形成：

```text
sub_5E2570 decode
        ↕
sub_5E1D50 encode
```

但 public gameplay event names 仍 `[OPEN]`。

---

## 10. Peer endpoint / handshake family

16-entry player identity → endpoint table：

```text
unk_F6D584 + 240780*slot = learned endpoint blob, 16 bytes
unk_F6D594 + 240780*slot = source/local sockaddr, 16 bytes
dword_F6DCF4[slot] = identity mapping
```

### Opcode 4 → 5

Inbound 4：

```text
u8 count
count × (u8 identity + 16-byte endpoint)
```

更新 `F6D584`、標記 `byte_F6D5B0[slot]`，並對 active non-local peer fan-out opcode 5 三次：

```text
u8 local identity
u32 n0x3E8_3
```

同時記錄 `dword_F6D5A8[slot] = timeGetTime()`，local state=`4`。[C]

### Opcode 5 → 6

Inbound 5：

```text
u8 identity
u32 value
```

first-arrival path：

```text
byte_F6D5A4[slot] = 1
byte_F6D5A5[slot] = 1
unk_F6D594[slot] = current source sockaddr
```

建立 opcode 6：

```text
u8 local identity
u32 n0x3E8_3
```

並對 stored endpoint 發三次；incoming `u32` 在 visible handler 中未被用於 response construction。[C]

### Opcode 6

同樣解析 `u8 identity + u32 value`；若未 ready，建立 A4/A5 state 與 source endpoint；visible handler 沒有 outbound packet。[C]

### Opcode 10 / 12 → 13

10：`u8 identity + 16-byte endpoint`；12：`u8 count + N×(u8 identity + 16-byte endpoint)`。

兩者更新 `F6D584`，再建立 opcode 13：

```text
u8 local identity
u32 n0x3E8_3
```

10 是 targeted path，12 是 bulk path；兩者都可對 active peer 三次 fan-out。[C]

### Opcode 13 → 14

13：`u8 identity + u32 value`。first arrival 時保存 source sockaddr、A4/A5，建立 opcode 14：

```text
u8 local identity + u32 n0x3E8_3
```

14：`u8 identity + u32 value`；visible handler 主要完成 terminal/source state capture，不再建立新的 packet。[C]

### Timing-like field

`n0x3E8_3` 來自：

```text
timeGetTime() - dword_F2563C
```

因此安全名稱為 elapsed/timing-like handshake value；尚不能叫 RTT、nonce、sequence 或 absolute timestamp。[C]

### Readiness timeouts

```text
sub_5941D0 → 3000 ms
sub_594DA0 → 5000 ms
```

兩個門檻證明 peer table 具有兩階段時間生命週期，但正式 state labels `[OPEN]`。[C]

---

## 11. Ping / latency side channel

### UDP 22

```text
u8 mode/record flag
if flag == 1:
    u8 count
    count × (u8 identity + u32 ping-like value)
```

寫入 `dword_F6D9E8[slot]`。[C]

### UDP 154

```text
u8 count
count × (u8 identity + u8 ping-like value)
```

同樣寫入 `dword_F6D9E8[slot]`。[C]

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

因此 per-player latency classification 是 confirmed Client-side behavior；opcode 154 的 raw one-byte unit 仍 `[OPEN]`。

---

## 12. UDP bootstrap / recovery / health

TCP bootstrap：
```
141 PM_CONNECT_REQ
142 PM_CONNECT_ACK
143 PM_UDPSTART_REQ
144 PM_UDPSTART_ACK
```

`sub_5565D0()` 處理 142 時建立/更新 UDP endpoint-related setup；`sub_555C60()` 建立 143。完整 144 body 仍未完全閉合，因此只保留已證實的 registration / transition，不自行補欄位。[C]

UDP opcode 18：

```text
sub_596300
    → sub_556530
    → TCP opcode 141 = PM_CONNECT_REQ
    → empty payload
```

已閉合 `UDP 18 → TCP 141`。[C]

### 30-second health path

`sub_5934B0()`：

```text
stored timestamp == 0 → healthy
elapsed <= 30000 ms   → healthy
elapsed > 30000 ms    → clear + unhealthy
```

`sub_593510()` 在 `n15 == 13` 且 timeout failure 時建立：

```text
TCP opcode 697
u16 payload = 1
```

Protocol registration：`697 = GG_CHEATER_REPORT_REQ`。

Direct Client fact 是 30 秒 transport/UDP health timeout → 697；不能把 timeout 本身當成 cheating proof，server counterpart `[OPEN]`。[C]

---

## 13. Periodic control packets

Opcode 17：

```text
sub_596180
→ >=1000 ms
→ opcode 17
```

`sub_596240()` 也建立 opcode 17，並帶 string payload。[C]

Opcode 19：

```text
sub_596670
→ 約每 500 ms
→ opcode 19
→ current/peer UDP path
```

另有 retry/count-like state，超過 5 次進 escalation；因此只命名為 periodic control/recovery packet，不直接叫 generic heartbeat。[C][OPEN]

---

## 14. BulletHole cross-validation

`Extracted/BulletHole/` 有：

```text
type000.dds
type001.dds
...
```

`pmFile::possible_ctor_or_dtor_57()` 從 `BulletHole\\type000.dds` 開始掃描，最多約 1000 個 type texture 並讀 dimensions。[C][RES]

Protocol symbol registration 又有：

```text
155 Y_UDP_C_HOLE_INF
156 Y_UDP_S_HOLE_INF
```

但本 Client 的 `sub_595E80()` direct switch 未看到 155/156，因此目前只能建立：

```text
BulletHole resource family exists
↕
protocol names 155/156 exist
```

不能自行補 exact payload、direction 或 producer。[C][RES][OPEN]

---

## 15. Evidence / Confidence

| Conclusion | Confidence | Evidence |
|---|---|---|
| UDP 8/24 = `Y_UDP_S_MOVE_INF` | Confirmed | dispatcher + diagnostic string |
| 8/24 fixed actor record = 27 bytes | Confirmed | exact parser widths + 23 producer symmetry |
| 23 fixed payload = 27 bytes | Confirmed | `sub_744450` writers |
| movement spatial fields are u16 ↔ /3.0 | Confirmed | decoder + encoder |
| movement R+16 has Emotion subdomain 16..25 | Confirmed | state predicate + 10-entry emotion table |
| R+17 is Resource/Action identity candidate | Strongly Supported | whitelist + downstream validation |
| opcode 4/5/6/10/12/13/14 form peer maintenance family | Confirmed at Client behavior level | endpoint table + parser/serializer flows |
| 3s / 5s readiness checks exist | Confirmed | direct clock comparisons |
| opcode 18 → TCP 141 | Confirmed | direct call + empty serializer |
| opcode 697 follows 30s timeout path | Confirmed | timeout + packet construction |
| opcode 154 feeds common ping-quality state | Confirmed | parser + shared table + UI consumer |
| opcode 155/156 correlate with BulletHole resource family | Strongly Supported | symbol registration + resource family |
| 8/24 server-side producer | Unknown | absent from Client binary |
| opcode 23 formal public name | Unknown | symbol closure missing |
| R+16 has internal StateCode mapping | Confirmed | sub_5B76A0 switch |
| R+17 maps into CGunDataCtrl index domain | Strongly Supported | sub_5B35F0 + sub_5F5400/sub_5F5450 |
| exact movement field semantics beyond closed relations | Mostly OPEN | insufficient independent evidence |
| peer timing field exact semantics | Unknown | remote value not consumed by response construction |

---

## 16. Remaining highest-value questions

```text
A. Movement R+00/R+01/R+03/R+07/R+12/R+13/R+14/R+15 exact semantic
B. Movement R+02 exact identity namespace
C. Movement R+16 complete non-Emotion state/action enum
D. Movement R+17 exact weapon / CGunData public namespace
E. sub_5E2570 type 1/2/3/4 exact public event mapping
F. UDP 8/24 server-side serializer
G. UDP 23 formal protocol name
H. UDP 155/156 producer/consumer + BulletHole wire fields
I. UDP 17/19 exact periodic semantics
J. UDP 154 one-byte unit
K. 3s/5s peer state-machine formal labels
L. opcode 697 server counterpart
```

## 17. Canonical ownership

```text
Network_Protocol.md
    = Packet frame / integrity / compression / AES-CFB / UDP movement canonical wire truth

UDP_Movement_Control_Evidence_2026-09-18.md
    = movement / peer-control / recovery / BulletHole deep evidence appendix

Network_Dispatcher_Inventory.md
    = complete TCP opcode → handler map + dispatcher-oriented UDP evidence
```

同一 packet schema 只允許一份 canonical 定義；本附錄補充 function-level evidence，不維護第二套 schema。