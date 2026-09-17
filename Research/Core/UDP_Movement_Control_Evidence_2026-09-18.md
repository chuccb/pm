# PaperMan 2016 JP — UDP Movement / Control Plane 深入證據

> 研究日期：2026-09-18。
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 本文件是 `Network_Protocol.md` 的深度證據附錄：集中保存本輪新閉合的 UDP movement、peer、control-plane、recovery 與 BulletHole 交叉驗證；不取代其它 Domain 文件的 semantic truth。

## 1. 最重要的結論

目前已直接從 `PaperMan.exe.c` 閉合：

```text
Server → Client
UDP opcode 8 / 24
payload = u8 actor_count + N × 26-byte ActorRecord

Client → current UDP peer
UDP opcode 23
payload = 27 bytes
```

其中兩方向的位置編碼已形成直接 C→C 交叉：

```text
Client serializer:
    u16(round(world_value * 3.0 + 0.5))

Server→client decoder:
    u16 / 3.0
```

所以可高可信建立 1/3 world-unit 的量化家族；但不應超出 C evidence 自行推導負值 overflow、外部座標限制或完整 rounding policy。[C][X]

## 2. UDP transport 基礎

### 2.1 Socket

`CUDPSocket` 使用：

```text
socket(AF_INET, SOCK_DGRAM, 0)
```

constructor 將 port-like member 初始化成 `27000`；但實際 bind 使用的是 runtime `+56`，不是永久常數，因此：

```text
27000 = constructor default
≠ 已證明的最終 local/server port
```

`sub_596DA0()`：

```text
local bind address = INADDR_ANY + local-port member
remote endpoint    = cp + hostshort
```

`sub_596EB0()` / `sub_596F00()` / `sub_596F50()` 為 `sendto` wrappers；`sub_596F90()` / `sub_596FF0()` 為 `recvfrom` wrappers。[C]

### 2.2 Receive thread

```text
CUDPManager::sub_595840
    → loop
    → sub_595A60
    → recvfrom(..., 9600)
    → Packet parse/validation
    → sub_595E80
```

`sub_595840()` 每輪 `_sleep(1)`。[C]

### 2.3 Current peer

`sub_595BD0()` 回傳 manager +2420..2423 的 sockaddr storage。

因此 Server model 應把：

```text
UDP local endpoint
UDP current peer endpoint
```

分成兩個 state。

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

因此低 opcode 不可簡化成單一 movement message；它同時包含 peer state、movement、health/recovery 等控制資料。[C]

## 4. Server → Client movement：opcode 8/24

`sub_596940()` 有明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

只有 `n15 == 13` 才進 `sub_593750()`；之後由 queue 到 `sub_602E30()` 解碼。[C]

### 4.1 Payload

```text
u8 N
N × ActorRecord(26 bytes)
```

### 4.2 ActorRecord

```text
R+00  u8   field00                     [OPEN]
R+01  u8   field01                     [OPEN]
R+02  u8   actor/user identity cand.   [OPEN namespace]
R+03  u32  field03                     [OPEN]
R+07  u32  movement/sample value        [OPEN]
R+0B  u8   ActorStateByte               [confirmed state byte]
R+0C  u16  QuantizedPos0
R+0E  u16  QuantizedPos1
R+10  u16  QuantizedPos2
R+12  u8   state/controller byte        [OPEN]
R+13  u8   state/controller byte        [OPEN]
R+14  u8   state/controller byte        [OPEN]
R+15  u8   state/controller byte        [OPEN]
R+16  u8   StateOrEmotionId
R+17  u32  ActionOrResourceValue        [OPEN namespace]
```

位移：

```text
3 + 4 + 4 + 1 + 6 + 4 + 4 = 26 bytes
```

`R+0B` 不是 padding：`sub_5B3180(actor, R+0B)` 直接把 byte 寫入 actor +233。[C]

## 5. `R+0C/R+0E/R+10`：座標量化閉環

Server→client：

```text
float0 = wire_u16_0 / 3.0
float1 = wire_u16_1 / 3.0
float2 = wire_u16_2 / 3.0
```

Client→peer opcode 23：

```text
wire_u16_0 = u16(round((this+16) * 3.0 + 0.5))
wire_u16_1 = u16(round((this+20) * 3.0 + 0.5))
wire_u16_2 = u16(round((this+24) * 3.0 + 0.5))
```

因此兩方向不是剛好「都用了三」，而是可以直接串成同一個 wire encoding family。[C][X]

目前仍保留：

```text
axis 0/1/2 ↔ 引擎 public X/Y/Z 名稱
negative range
overflow handling
world-origin convention
```

為 OPEN。

## 6. `R+16`：StateOrEmotionId

`sub_9A8580(n)` 精確為：

```c
return n >= 16 && n <= 25;
```

`sub_7170F0()` 建立十個 Emotion entries：

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

`sub_7173E0()` 以這個值查 Emotion table；`sub_7170D0()` 再將 emotion ID 交給 actor path。[C]

因此正式 wire 模型：

```text
StateOrEmotionId ∈ 16..25
    → definite Emotion ID domain

otherwise
    → generic state/action path
```

不能把整個欄位叫成 `EmotionId`。[C][X]

Wiki 亦描述：

```text
F11 = emotion list hide
F12 = emotion
```

與 client 內 16..25 的 Emotion subsystem 相互吻合。

Wiki：
https://wikiwiki.jp/paperman/操作ガイド

## 7. Client → current peer movement：opcode 23

`sub_744450()`：

```text
Packet opcode 23
→ sub_602D70
→ sub_596B90
→ sub_595A10
→ current UDP peer
```

在正常 PM_UDPSTART gameplay context 下，current peer 為 server endpoint，因此 Server reconstruction 應接收 opcode 23 作為 client-generated movement/state input。[C]

### 7.1 精確 payload

```text
+00 u32  session/account-like = *sub_417D00()
+04 u8   byte_EE896D
+05 u8   Actor/User identity candidate = sub_67D010()
+06 u16  dword_EE8CB4
+08 u32  tick/frame/time-like = n0x64_0
+0C u8   MoveStateFlags
+0D u16  QuantizedPos0
+0F u16  QuantizedPos1
+11 u16  QuantizedPos2
+13 u8   angle/state byte A
+14 u8   angle/state byte B
+15 u8   actor-state byte = *(this+848)
+16 u8   StateOrActionByte
+17 u32  ActionOrResourceValue candidate = sub_5AA5C0(n9)
```

總長：

```text
27 bytes
```

### 7.2 MoveStateFlags

`sub_744310()` 精確生成：

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

所以安全命名為：

```text
MoveStateFlags : u8
```

各 bit 的 public semantic 仍 OPEN。

### 7.3 StateOrActionByte

`n12` 基礎值來自 `n9[0]`；特殊情況：

```text
n5_1 == 4 → 12
n5_1 == 5 → 13
(this+104) != 0 → set bit7
```

若 local actor 存在且 actor+284 != 0，則 override 成 `sub_717430()`；該函式若有 actor 回傳 actor+286，否則 28。[C]

所以 Server 不應把 +16 自行枚舉成未證實的 `WeaponId` / `EmotionId`。

## 8. Client/Server movement struct 必須分離

```text
S→C:
  opcode 8/24
  u8 N + N×26-byte ActorRecord

C→peer:
  opcode 23
  27-byte LocalMovementState
```

兩者共享 identity/state/position/action 家族，但 wire layout 不同；不能重用同一個 binary struct。[C][X]

## 9. Actor state application

`sub_602E30()` 每筆 record 最終形成：

```text
R+0B
  → sub_5B3180(actor, byte)
  → actor +233

R+0C..R+10
  → /3.0
  → transform snapshot
  → sub_9BCB00

R+16
  → sub_5B34B0 state/action path

R+17
  → sub_5B34B0 resource/action path
```

`sub_5B34B0()` 的分流：

```text
StateOrEmotionId 16..25
    → Emotion/animation subsystem

otherwise
    → generic state/action + item/weapon/resource lookup
```

## 10. Peer control / recovery

### 10.1 UDP opcode 18 → TCP PM_CONNECT_REQ

UDP receive `sub_596300()` 收到 opcode 18 後，在正常 gate 下呼叫 `sub_556530()`。

`sub_556530()` 明確建立：

```text
TCP opcode 141 = PM_CONNECT_REQ
payload = empty
```

並透過 `sub_555090(&dword_1321D00, ...)` 發送。[C]

因此已閉合：

```text
UDP opcode 18
    → TCP PM_CONNECT_REQ (141, empty)
```

### 10.2 Explicit symbol family 153–164

Protocol registration 明確給出：

```text
153 UDP_ALL_PING_REQ
154 UDP_ALL_PING_ACK
155 Y_UDP_C_HOLE_INF
156 Y_UDP_S_HOLE_INF
157 UDP_TCP_DEAD_REQ
158 UDP_TCP_DEAD_ACK
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
161 UDP_TCP_LIVE_REQ
162 UDP_TCP_LIVE_ACK
163 TCP_UDP_LIVE_REQ
164 TCP_UDP_LIVE_ACK
```

但 symbol registration 不代表所有 opcode 都經同一 receive dispatcher；本 client 的 UDP `sub_595E80()` 目前直接看到的是 154、158。[C]

### 10.3 UDP_ALL_PING_ACK 154

`sub_5965D0()`：

```text
u8 count
repeat count:
    u8 player/peer identity
    u32 value
```

再以 `dword_F6DCF4` 的 16-player table 找 slot，把 value 寫到 `dword_F6D9E8[slot]`。[C]

所以 154 不是空 payload ping ACK，而是 per-peer/per-player state/value update。

### 10.4 UDP 6 / 13 / 14：peer endpoint/state path

`sub_5940E0()`、`sub_594A10()`、`sub_594CA0()` 都以第一個 u8 找 16-player peer entry；相關資料寫到 `F6D594` 等 per-player storage，且部分 branch 建立 opcode 6/13/14 對指定 endpoint `sendto`。[C]

這是 UDP peer control plane 的重要證據：

```text
16 player entries
+ endpoint/address state
+ timestamp/state flags
```

## 11. Periodic packets

### 11.1 opcode 17

`sub_596180()`：

```text
>= 1000 ms
→ opcode 17
→ sub_595900
```

`sub_596240()` 亦建立 opcode 17，另寫入 string。[C]

Exact public semantic 仍 OPEN。

### 11.2 opcode 19

`sub_596670()`：

```text
約每 500 ms
→ opcode 19
→ sub_595A10/current peer
```

且有 retry/count-like state；超過 5 次進 escalation，不能只叫 generic heartbeat。[C][OPEN]

## 12. BulletHole cross-validation

### 12.1 Resource

GitHub `Extracted/BulletHole/` 包含：

```text
type000.dds
type001.dds
...
type2xx.dds
```

而 `pmFile::possible_ctor_or_dtor_57()` 從：

```text
BulletHole\\type000.dds
```

開始，最多掃描 1000 個 type texture，讀取 texture dimensions。[C][RES]

### 12.2 Protocol

Protocol registration 存在：

```text
155 Y_UDP_C_HOLE_INF
156 Y_UDP_S_HOLE_INF
```

### 12.3 Wiki

Wiki 的武器條目觀察到不同武器可以共享相同弾痕；例如 Paperman Of Comic 明確說弾痕與 Magic Book 相同：

https://wikiwiki.jp/paperman/Paperman%20Of%20Comic%E8%A9%B3%E7%B4%B0

因此目前可以高可信建立 domain-level relation：

```text
Y_UDP hole protocol
    ↔ bullet-hole runtime resource family
    ↔ observable weapon bullet-hole behavior
```

但 exact：

```text
155/156 payload schema
weapon/action → typeXXX mapping
```

仍 OPEN；不可因資源名稱直接創造 wire enum。[C][RES][WIKI][OPEN]

## 13. Wiki 對 movement/state 的旁證

Wiki `銃の撃ち方いろいろ` 明確描述：

```text
standing
crouching
jumping
moving
grenade blow-up
falling
being shot
```

這些狀態會影響 crosshair state；其中 moving/jumping 等會進入較大的 crosshair 狀態。

https://wikiwiki.jp/paperman/%E9%8A%83%E3%81%AE%E6%92%83%E3%81%A1%E6%96%B9%E3%81%84%E3%82%8D%E3%81%84%E3%82%8D

這只證明 PaperMan 有豐富的 movement/combat state machine，不能反向把某一個 wire bit 命名成 crouch/jump/fire；所以仍維持 `[OPEN]`。

## 14. 目前對 Server reconstruction 的直接影響

推薦的協定 abstraction：

```text
UdpEndpointState
    LocalEndpoint
    CurrentPeerEndpoint

UdpPacketCodec
    FrameCodec
    TransformCodec

ServerMovementPacket8_24
    ActorCount
    ActorRecord[26]

ClientMovementPacket23
    SessionLike
    ActorIdentityLike
    TickLike
    MoveStateFlags
    QuantizedPosition[3]
    AngleState[2]
    ActorStateByte
    StateOrActionByte
    ActionOrResourceValue

UdpControlPlane
    AllPing
    PeerEndpointState
    DeadLiveRecovery
    HoleInformation
```

不要把所有資料塞成一個 `PlayerMovementPacket`。

尤其：

```text
opcode 8/24 ≠ opcode 23
R+16 可能是 Emotion，但只有 16..25 時成立
R+17 ≠ 已證實 WeaponId
n16 ≠ 已證實 SlotIndex
27000 ≠ 已證實遠端 server port
```

## 15. 本輪後仍 OPEN

```text
UDP 8/24：
  field00/01/03/07
  exact identity namespace
  R+12/R+14/R+16 public axis naming
  R+18..21 exact state/angle semantics
  R+23 resource/action namespace

UDP 23：
  +00/+04/+06/+08 exact public semantics
  angle/state bytes exact mode mapping
  +15 exact actor-state enum
  +16 generic state/action full enum
  +17 resource/action namespace
  all producer cadence/conditions

UDP control：
  153 sender
  155/156 exact serializer + BulletHole type mapping
  157/159/161/163 counterpart state machines
  158/160/162/164 exact payloads
  17/19 exact network/gameplay semantics
  UDP timeout → TCP 697 counterpart

TCP/Packet：
  header +0x06
  transform formula
  full send queue/retry behavior
```

## 16. Evidence discipline

```text
[C]      IDA C direct evidence
[RES]    Extracted resource evidence
[WIKI]   PaperMan Wiki / observable behavior
[X]      >=2 independent evidence classes agree
[OPEN]   unresolved; do not invent enum, 0, or hardcoded semantic
```

本文件只把已由 parser/serializer、runtime consumer、resource、Wiki 交叉支持的結論提升；其餘保持 OPEN。