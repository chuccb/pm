# Gameplay Network Events — Y_TCP_INF_ACK / UDP Gameplay

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA Hex-Rays C export + cross-function data flow + Resource/Research/Wiki cross-check  
> Confidence：直接 Client code = A；Wiki semantic anchor = C unless independently confirmed

本文件承接 `Network_Dispatch.md`，集中記錄 gameplay 階段的 TCP `166 Y_TCP_INF_ACK` 與 UDP dispatcher。重要原則：保留 raw subtype/field，不在證據未閉合前把數值硬命名成 guessed enum。

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

`sub_58B010` 對 `166` 有明確 case；`sub_58D820` 轉呼叫 `sub_749B90`。因此 `sub_749B90` 是 166 receive-side 核心 parser/dispatcher。

---

## 2. 166 packet 第一層 wire fields

`sub_749B90` 在 gameplay gate 成立後立即解析：

```text
field 0: u8 outer_actor_id = n16
field 1: u8 subtype        = n18
```

抽象為：

```text
Y_TCP_INF_ACK (166)
    + actor/player-like id : u8
    + event subtype         : u8
    + subtype-specific body
```

`n16` 多條路徑進入 `sub_67DF00/sub_67DF70/sub_67D7D0`，與 actor/player identity 強相關，但因特殊 subtype 存在，不直接等同 slot index。

---

## 3. 166 raw subtype dispatch

目前直接由 Client dispatcher 確認：

| subtype | handler / path | 已證實內容 |
|---:|---|---|
| 1 | `sub_746360` | u8 player/target id；controller reset/state callback |
| 2 | `sub_7463E0(...,0)` | 大型 player/gameplay event；resource、death-state、round counters、Quest hook |
| 3 | `sub_747980` | resource/impact/effect event；共用 `sub_747460`/`747B90` machinery |
| 4 | `sub_748860` | `u32,u16,u32,+6×u32`；`sub_61BA90` + resource-category branches |
| 5 | `sub_748A50` | `u32,u8,u32,+6×u32`；resource/effect/PVE-state branches |
| 6 | `sub_748CD0` | `u16,u16,u32,+6×u32,u8`；resource category 10/15 branches |
| 7 | `sub_748E40` | ASCII-Z text/event string |
| 8 | `sub_748EB0` | object/controller callback；在 dispatcher context 可能另有 time field |
| 9 | `sub_748EB0` | object/controller callback；可能另有 time field |
| 10 | `sub_749230/749520` | additional u8; explicit `FIRE_BOMB` resource path |
| 11 | `sub_7494B0/749810` | additional u8; compact state/timer reset/update |
| 12 | `sub_749A30` | `u16,u16` |
| 13 | inline lifecycle path | 16-slot state reset + mode/gameplay lifecycle work |
| 14 | `sub_749AB0` | `u32 + 4×u16 + u8`; transform/interpolation state |
| 15 | `sub_748420` | `u8,u16,+3×u8,+2×u32,u8`; resource/state transition |
| 16 | `sub_7463E0(...,1)` | same large parser as subtype 2 with different control flag |
| 17 | `sub_748FF0` | object/controller callback |
| 18 | `sub_748EB0` | callback + possible time field |
| 19 | `sub_74D150` | parser/handler not yet semantically closed |
| 20 | `sub_747980` | same parser core as subtype 3, but subtype value retained |
| 21 | `sub_747DD0` | compact `u8 + u16 + u8 + u8` resource/effect event |
| 22 | `sub_747AB0` | compact state/resource/effect event |
| 23 | `sub_74D410` | parser/handler not yet semantically closed |
| 24 | inline + `sub_7498E0` | `u16,u16,u32,u8`; time-like presentation/update |
| 25 | `sub_748EB0` | callback + possible time field |
| 26 | `sub_745F50` | `u32,u16,u16,u16,+5×u8?,u32`; handler not semantically closed |
| 27 | `sub_746060` | bot/player state/death family; diagnostics include `OnBotDeadCtrl` |
| 29 | `sub_746060` | same family, special route |
| 30 | `sub_74D510` | handler not semantically closed |
| 31 | `sub_74D5D0` | handler not semantically closed |
| 32 | `sub_74D5D0` | handler not semantically closed |

數值接近、函式編號或共用 helper 都不能單獨當作公開 semantic。

---

## 4. subtype 2 / 16 — multiplexed gameplay/death/result event

`sub_7463E0()`：

```text
subtype 2  → a4 = 0
subtype 16 → a4 = 1
```

共同 payload：

```text
u32 v94
u8  participant_B = n16_2
u16 resource_id   = v90[0]
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

outer `n16` 與 payload `n16_2` 是不同 participant identity。

### 4.1 state-token / Resource semantics

```text
v94 ↔ dword_F2A65C comparison
resource_id → sub_5F5400/sub_5F5450 → resource metadata
v89 → local player object +164
v95 → local player object +172
```

`v94` 暫不命名 timestamp/sequence/result code；`n10/n10_1` 同樣保持 raw。

### 4.2 death/state transition

Remote target branch：

```text
sub_67DF00(n16_2)
    ↓
sub_9BC470(...,1,timeLike,0,0)
```

`sub_9BC470()` 直接修改 runtime/controller：

```text
controller +56 = 1
controller +16 = 0
controller +60 = supplied time-like value
controller +64 = timeGetTime()
clear state arrays/timers
sub_5B7AF0(controller)
```

另存在明確 `CViewObj::OnDeadCtrl` diagnostic path。

因此這個 event family **包含** death/state-transition；不能將全部 subtype 2/16 簡化成單一 `DeathPacket`。

### 4.3 Round-local Kill/Death counters

在 participant identity 與 team/mode 條件成立時：

```text
participant A / outer n16 → +240600 ++
participant B / n16_2      → +240604 ++   only when a4 == 0
```

這組資料由 result/scoreboard presentation 使用，應視為 live round/mode-local result counters。

subtype 16 (`a4=1`) 不做 victim `+240604` increment；因此不能直接把 subtype 16 視為與 subtype 2 完全相同的 kill/death event。

### 4.4 Result-screen fields are a separate layer

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前完整 `PaperMan.exe.c` exact search：

```text
+60150 : 只找到 result/UI reads，沒有找到同等直接 gameplay writer
+60151 : 找到 gameplay death-path direct write
```

所以不要僅因欄位名稱推定 Client 本地會 `MY_KILL++`。

### 4.5 Quest hook

在適用的 player/mode branch：

```text
n2 == gameplay condition
    ↓
sub_92EF00(3,n2,0,resource_id)
    or
sub_92EF00(4,n2,0,resource_id)
```

這是實際 gameplay → Quest progress chain。

`sub_92EF00()` 對 Quest condition ID `quest +2324` 有明確 mappings 1–36；其中 7–10 還依 `n2_1` 分化。不能把 `n2` 單獨命名成 Kill/Assist，必須配合 Quest row / mode / resource/context。

---

## 5. TCP 269 subtype 7 — server-provided player/result state

`case 269 → sub_574B20()`；`n7 == 7` 是大型 player/game-state synchronization branch。

Repeated-record framing：

```text
u8 record_count
repeat record_count:
    u32 record0
    u8  player_id
    ASCII-Z player string
    u8  state byte
    u8  state byte
    u32 K/D field A
    u32 K/D field B
    u32 additional state
    u8  state byte
    u8  state byte
```

其中：

```text
player_id → dword_F6DCF4[60195*slot]
K/D field A → dword_F6DCF8[60195*slot]
K/D field B → dword_F6DCFC[60195*slot]
```

Result UI 直接使用：

```text
TEAM_RESULT_B_TEXT_KILL  ← F6DCF8
TEAM_RESULT_B_TEXT_DEATH ← F6DCFC
```

`sub_759030()` 也用 F6DCF8/F6DCFC 作 result ranking keys。

因此：

```text
F6DCF8 = server-provided team/result K/D Kill state
F6DCFC = server-provided team/result K/D Death state
```

這與 166 的 `+240600/+240604` live counters 及 `+60150/+60151` local result-screen fields 是三個不同資料層。

另外 subtype 7 repeated record 同時 hydration player name/state/resource/item blocks，因此它不是只有 K/D packet。

---

## 6. TCP 166 subtype 14 vs UDP 8/24

### TCP 166 subtype 14

```text
u32 time_like
u16 sample_0
u16 sample_1
u16 sample_2
u16 sample_3
u8 flag
```

→ `sub_5B3DD0()` → transform sample queue → `IPaperCtrl::sub_9BCBD0()` interpolation。

### UDP 8/24

明文 diagnostic：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF
```

並在 gameplay state `n15==13` 下進 queue，再於 game update 由 `sub_602E30()` consume。

這兩者都是 actor synchronization，但 wire protocol、parser 與 producer/consumer architecture 必須分開。

---

## 7. UDP `S_MOVE_INF` receive / consume architecture

```text
sub_595A60
    ↓ recvfrom
sub_595E80
    ↓ opcode 8 / 24
sub_596940
    ↓
sub_593750
    ↓ thread-safe queue
sub_593510  ← per-tick processing
    ↓
sub_602E30(Packet)
    ↓
actor records
    ↓
player/controller state mutation
```

這是重要 correction：`sub_593510()` 不是 shutdown-only cleanup。

真正 static destruction 另外由 `sub_593410()` 等路徑完成。

### 7.1 Actor record

`sub_602E30()`：

```text
u8 N
repeat N:
    27-byte record
```

27-byte record：

```text
+00 u8
+01 u8
+02 u8 actor/player-id candidate
+03 u32
+07 u32
+0B u8
+0C u16 spatial component candidate
+0E u16 spatial component candidate
+10 u16 spatial component candidate
+12 u8
+13 u8
+14 u8
+15 u8
+16 u8
+17 u32 Resource/Action identifier candidate
```

Decoder footprint：

```text
1 + 27*N
```

這不是整個 UDP datagram length；outer Packet header/transport metadata 必須另行處理。

### 7.2 Position

`field_06..08`：

```text
u16 / 3.0
→ x-like/y-like/z-like float
→ sub_9BCB00
→ controller transform/interpolation
```

因此它們可高可信視為 spatial vector components；coordinate naming/unit 仍保留 raw evidence。

### 7.3 Resource/Action field

最後 `u32 field_0E` 進：

```text
sub_5E2570(...)
sub_548E80(...)
```

`sub_548C80()` 直接比較：

```text
Resource("BOMBPLANT")
Resource("Pulp_A")
Resource("Pulp_B")
Resource("magic_finger")
Resource("Escape")
```

及 actor 內多組 action/resource slots。

因此目前最佳 temporary semantic：

```text
field_0E = Resource/Action identifier candidate
```

不能再泛稱 generic flags。

### 7.4 TCP 714 coupling

`sub_548E80()` 累積符合條件的 field_0E events，達門檻後建立 opcode 714：

```text
u8 local player/network id
u8 byte_EE896D
u8 player +240596
ASCII-Z player +64
u32 field_0E
```

並 `sub_55D960()` send。

這證明 field_0E 會影響另一條 Client→Server report path；但尚無 714 receive counterpart，因此不要把 714 直接命名 anti-cheat。

---

## 8. Other UDP player-state side channel

已確認：

```text
sub_5964E0:
    u8 player_id
    u32 value
    → dword_F6D9E8[slot]

sub_5965D0:
    u8 count
    repeat:
        u8 player_id
        u8 value
    → dword_F6D9E8[slot]
```

`dword_F6D9E8` 的公開 semantic 仍 unresolved；不能因其出現在 movement subsystem 就直接命名 HP/position。

---

## 9. Damage / gameplay result separation

Client→Server damage path：

```text
sub_55CAB0
sub_55D090
sub_55D530
    ↓
opcode 165
```

165 可能依 subtype/resource/mode 有不同 tail。尤其 `sub_592B20()` 本身寫 4 bytes，不能因 caller 的 `char` appearance 將其標成 u8。

Server→Client gameplay/result：

```text
166 subtype 2/16
269 subtype 7
```

分別負責不同 state layer；不能把 165/166/269 合成一個 damage/result struct。

---

## 10. Wiki cross-check

PaperMan Wiki 的 Quest 系統頁明確列出：

```text
Kill count
Special shot
Multi-shot
Assist
Play time
Wins
Play count
Item/EXP/PG collection
PVE
Single mode
```

並描述不同條件在比賽中、比賽結束或退離 channel 時更新；Wiki 頁面本身最後修改日期為 2016-02-19。citeturn999004view0

Wiki 主頁記錄 PaperMan 於 2016-12-26 12:00 結束服務，可作本研究 target 的歷史時間錨點。citeturn200054search0

Kill-log Wiki 又區分 air combo、headshot、heartbreak、critical、normal kill，以及多種 assist/objective log。這些資料目前作為 behavior-level semantic anchor，不直接取代 Client wire evidence。citeturn918916search1

---

## 11. Current server reconstruction layers

目前至少應分開：

```text
PlayerIdentity / Slot / Team

Client→Server
    DamageReport (165)
    Action/Resource report (e.g. 714)

Server→Client
    TCP 166 multiplexed gameplay events
    TCP 269 player-state/result hydration
    UDP real-time gameplay state

Runtime state
    Transform / interpolation
    Alive/dead transition
    Health/controller state
    Resource/action state
    Mode/round state
    Quest progress
    Assist state

Result state
    166 live round counters (+240600/+240604)
    269 server-provided team/result K/D (F6DCF8/F6DCFC)
    local result-screen MY_K/D (+60150/+60151)
```

這些概念可以最終在 Server model 中互相同步，但目前不能因為 UI 最終都顯示 Kill/Death 就合併 wire representation。

---

## 12. Evidence discipline / unresolved policy

只有以下證據足夠時才升級欄位正式 semantic：

```text
A. Client 直接明文使用 / Resource lookup / named UI string
B. 多個 Client callsites 一致使用
C. Client + Extracted Resource + Wiki 行為一致
D. ASM/LST 修正 Hex-Rays width/type 後仍一致
```

否則保留：

```text
field_XX
RawXX
value_N
candidate
unresolved
```

尤其不能把以下尚未閉合項目硬填成 0 或 guessed enum：

```text
166 19/23/30/31/32
166 26/27/29 大部分 scalar semantics
166 subtype 13 lifecycle exact meaning
UDP 8/24 remaining byte fields
UDP outer packet length/header
packet sequence/encryption/checksum
714 server counterpart
+60150 writer
F3319C Assist writer
```

---

## 13. Main remaining proof targets

```text
1. +60150 完整 writer/result hydration source
2. F3319C Assist writer + Assist state producer
3. 269 subtype 7 repeated-record exact offsets after stringZ
4. 269 subtype 7 four resource/item blocks ↔ Extracted IDs
5. 166 subtype 2/16 v94/v89/v95/n10/n10_1/v86 exact semantics
6. 166 subtype 3/4/5/6/10/15/21/22 every scalar
7. 166 subtype 13 ↔ GameRule 133/134/137/138 ↔ respawn/end lifecycle
8. UDP S_MOVE_INF field_00/01/03/04/05/09/0A/0B/0C/0D/0E via ASM/LST
9. TCP 714 receive/server counterpart
10. Packet outer header, sequence, crypto/checksum
11. Extracted resource IDs for FIRE_BOMB/BOMBPLANT/Pulp/magic_finger/Escape
12. Final Wiki ↔ Resource ↔ Client three-way verification for every gameplay condition
```

本文件維持 raw evidence 與 semantic hypothesis 分離，避免後續 Server implementation 被未驗證命名污染。
