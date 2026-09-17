# Gameplay／Y_TCP_INF／165–166 整合研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 `Y_TCP_INF_REQ (165)`、`Y_TCP_INF_ACK (166)`、166 subtype 欄位、Gameplay event/state、死亡／K-D、Resource bridge 與 sender/receiver 證據。`Combat_Damage.md` 專注命中與傷害計算；UDP 即時移動仍由其專題主文件維護。

## 1. 最小正確模型

```text
165 Y_TCP_INF_REQ
    = Client → Server gameplay／actor／effect／state event family

166 Y_TCP_INF_ACK
    = Server → Client gameplay／actor／effect／state event family
```

不能簡化成：

```text
165 = DamagePacket
166 = DamageAck
```

165 已直接找到多種 sender：Normal Damage、MultiDamage、Mine/Bomb、BotSuicide、dead-position、effect/state、vector/interaction 等，因此它是 subtype-driven polymorphic family。[C]

## 2. `166` 接收鏈

```text
TCP framing
    ↓
sub_58B010
    ↓ case 166
sub_58D820
    ↓
sub_749B90
    ↓
u8 outer_actor_like
u8 subtype
    ↓
second-level parser
```

`n18`／第二 byte 直接進第二級 switch，因此它是 166 的主要 event discriminator。[C]

## 3. Reader width 基線

```text
sub_592940 → u8
sub_5929C0 → u16
sub_592A00 → u16
sub_592A40 → u32
sub_592AC0 → u32
sub_592B40 → 4-byte read/copy
sub_592730 → variable/string-like reader
```

所有 subtype footprint 以 helper implementation 為準，不依 Hex-Rays 表面 prototype。[C]

## 4. 165 sender family

目前已確認的主要 sender：

| subtype／形態 | Client path | 目前語意 | 信度 |
|---:|---|---|---|
| 2 | `sub_5DF7F0`、`sub_5E6170` | gameplay／action／state event | B |
| 4 | `sub_5E5ED0`、`sub_5E6040` | effect／resource／state event | B |
| 5 | `CViewObj::TempSendDeadPosPacket` | dead-position／event variant | B |
| 6/7 | gameplay／effect callers | event／state | C |
| 8 | `sub_7452D0` | dead-position／state variant | B |
| 9 | `sub_745D60` | small state event | B |
| 10 | `sub_745E80` | small state event | B |
| 13 | `sub_5E6DF0` | vector／interaction report | B |
| 15 | `sub_55D440` | gameplay event | C |
| 16 | `OnSendPacketMultiDamage`／`sub_55D530` | MultiDamage | A |
| 21 | `OnSendPacketBotSuicide`／`sub_5658B0` | BotSuicide | A |
| 其他 | `OnSendPacketDamage`／Mine-Bomb | damage-family variant | A |

這是目前找到的 family inventory，不宣稱 enum 已完整。[C]

## 5. 165 subtype 21：BotSuicide

`sub_5658B0()`：

```text
165
u8 field0
u8 subtype = 21
u16 field2
u16 field3
i16 field4
```

三個 16-bit writer 都是實際 fixed-width serialization，因此：

```text
165 subtype 21 = BotSuicide
field0 = a1
field2 = u16 a2
field3 = u16 a3
field4 = i16 a4
```

其它欄位 public semantic 保持 `[OPEN]`。[C]

## 6. 165 subtype 16：MultiDamage

`GameNetwork::OnSendPacketMultiDamage`：

```c
Packet::possible_ctor_or_dtor_0(v23, 165);
sub_592920(v23, n16);
sub_592920(v23, 16);
sub_592920(v23, n16_1);
```

因此直接閉合：

```text
field1 = subtype 16
    = MultiDamage variant
```

後續還包含 resource/value、多 target components 與 target metadata。[C]

## 7. 165 subtype 4：effect/resource/state

`sub_5E5ED0()`、`sub_5E6040()` 都形成：

```text
165
u8 actor-like
u8 subtype = 4
u8 local-player-like
u8 variant
u8 state/timing-like
u32 value
```

目前只安全命名為 effect/resource/state family。[C][OPEN]

## 8. 165 subtype 5／8：dead-position/state

```text
5 → CViewObj::TempSendDeadPosPacket
8 → sub_7452D0
```

兩者都與 dead-position/transform/state 有關，但不能假定 wire layout 相同。[C][OPEN]

## 9. 165 subtype 9／10

```text
sub_745D60 → 165 + local-player + 9 + object +152 state/value
sub_745E80 → 165 + local-player + 10
```

兩者會進 `sub_602E00()` finalization path；精確 semantic 保持 `[OPEN]`。[C]

## 10. 165 subtype 13：vector／interaction report

`sub_5E6DF0()`：

```text
165
u8 actor-like
u8 13
u8 local player
a3
a4
4-byte value
4-byte value
4-byte vector.x
4-byte vector.y
4-byte vector.z
```

caller `sub_5E3A50()` 在送出前會做 target、state、geometry 檢查，因此至少可確認為本地計算後送出的 interaction/vector report。[C]

不能因此宣稱 Client 對最終結果有 authority。[OPEN]

## 11. `sub_592B20`：wire width 重要陷阱

完整實作：

```c
void *__thiscall sub_592B20(void *this, char a2)
{
    sub_592580(this, &a2, 4u);
    return this;
}
```

因此：

```text
sub_592B20 = 4-byte writer
```

即使 caller 看起來是：

```c
sub_592B20(packet, SLOBYTE(value));
```

wire 仍為 4 bytes。[C]

## 12. `166` subtype 欄位總覽

外層：

```text
u8 actor／subject-like discriminator
u8 subtype
subtype-specific payload
```

目前主要 subtype：

| subtype | parser | payload / 結構摘要 |
|---:|---|---|
| 1 | `sub_746360` | `u8 target_id` |
| 2 | `sub_7463E0` | `u32 + u8 + u16×3 + u8×3 + u32×2 + u8` |
| 3 | `sub_747980` | `u32 + u8 + u16×3 + u8×2 + u32×2 + u8` |
| 4 | `sub_748860` | `u32 + u16 + u32×7` |
| 5 | `sub_748A50` | `u32 + u8 + u32×6` |
| 6 | `sub_748CD0` | `u16×2 + u32×6 + u8` |
| 7 | `sub_748E40` | variable/string-like data |
| 8/9/18/25 | `sub_748EB0` | callback family；部分 context 有附加 `u32` |
| 10 | `sub_749230`／`sub_749520` | `u8 + n13 + state/resource tail` |
| 11 | `sub_7494B0`／`sub_749810` | `u8 n7` |
| 12 | `sub_749A30` | `u16×2` |
| 13 | inline | lifecycle/reset path |
| 14 | `sub_749AB0` | `u32 + u16×4 + u8` |
| 15 | `sub_748420` | `u8 + u16 + u8×3 + u32×2 + u8` |
| 17 | `sub_748FF0` | callback/state family |
| 19/23/30/31/32 | `sub_74D150`／`sub_74D410`／`sub_74D510`／`sub_74D5D0` | parser 尚未完整閉合 |
| 20 | `sub_747980` | 與 subtype 3 共用 parser，context 不同 |
| 21 | `sub_747DD0` | `u8 + u16 + u8×2` |
| 22 | `sub_747AB0` | `u32 + u8 + u16 + u8 + u32×2 + u8` |
| 24 | inline | `u16×2 + u32 + u8` |
| 26 | `sub_745F50` | `u32 + u16×3 + u8×5 + u32` |
| 27/29 | `sub_746060` | `u32 + u16×4 + u8 + u32×2 + u8 + u32×2 + u8` |

這裡只保存 wire／parser 級索引；正式 semantic 仍以各 subtype 證據為準。[C]

## 13. subtype 1

`sub_746360()` 讀：

```text
u8 target_id
```

取得 player object/controller 後，在 remote actor path 進：

```text
sub_5B8EE0(controller)
sub_5B8F70(controller)
```

目前只能確認 Server event → actor controller state/reset callback；公開事件名稱 `[OPEN]`。[C]

## 14. subtype 2／16：Participant Event

Wire body：

```text
u32 v94
u8  participant_B
u16 resource_id
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

共 19 bytes；連同外層兩個 discriminator 為 21 bytes。[C]

```text
outer n16     = participant_A
payload n16_2 = participant_B
```

兩者都經 `sub_67D7D0()` 映射至 player/slot。[C]

`resource_id` 進入：

```text
sub_5F5400
sub_5F5450
sub_5EF5B0
sub_5EFE00
sub_5EF5F0
```

因此是 gameplay event 的重要 Resource identity。[C]

`n2` downstream effect mapping：

```text
1 → type 6
2 → type 4
3 → type 7
4 → type 5
default → type 1
```

`v89`、`v95` 分別寫入 local player object `+164`、`+172`，公開 semantic OPEN。[C]

Remote branch 可進：

```text
sub_9BC470(controller, 1, timeLike, 0, 0)
```

並修改：

```text
controller +56 = 1
controller +16 = 0
controller +60 = timeLike
controller +64 = timeGetTime()
```

因此 subtype 2/16 包含 death/state-transition branch，但整個 family 不是單一 DeathPacket。[C]

### 14.1 Live K/D

正常 `a4 == 0` 路徑：

```text
participant A → +240600 ++
participant B → +240604 ++
```

`a4 == 1` 時不增加 victim `+240604`。[C]

目前高信度：

```text
+240600 = live round/mode-local Kill counter
+240604 = live round/mode-local Death counter
```

## 15. subtype 3／20：impact/status family

`sub_747980()`：

```text
u32 gate_v21
u8  target_or_other_player
u16 resource_id
u8  state_type
u8  state_a
u8  state_b
u32 aux_a6
u32 aux_n26
u8  aux_n0x1E
```

Body 19 bytes，且：

```text
gate_v21 == dword_F2A65C
```

才進 `sub_747460()`。Remote actor path 另進 `sub_747B90()`。[C]

`sub_747460()` 最後會直接：

```c
*(target_object + 16) = a6;
```

因此 `a6` 是 Server → Client 直接寫入 target runtime object 的 value-like state；目前僅稱 `target_runtime_value`，不能在 object layout 未閉合前直接命名為 HP。[C][OPEN]

其後還會透過：

```text
sub_5F5450(resourceId)
sub_74CB20(category)
```

把 Resource lookup／category 接到 effect/state application。[C]

## 16. subtype 4／5／6

### subtype 4

```text
u32 control_or_time
u16 control
u32 resource_id
u32 p0..p5
```

Body 34 bytes；p0..p5 為 4-byte reader family。[C]

### subtype 5

```text
u32 value_0
u8 control
u32 resource_id
after six × u32 effects
```

Body 29 bytes；Resource category 10 有特殊 branch。[C][OPEN]

### subtype 6

```text
u16 value_0
u16 resource_id
u32 value_2..value_7
u8 tail
```

Body 33 bytes；Resource category 10/15 有特殊 handling。[C][OPEN]

## 17. subtype 7／8／9／10／11／12

### 7

`sub_748E40()` 經 `sub_592730()` 處理 variable/string-like data，不能假定固定 wire length。[C][OPEN]

### 8／9／18／25

`sub_748EB0()` 主要交給 vtable callback；完整 body grammar 需沿 indirect callback 追。[C][OPEN]

### 10

包含：

```text
u8 secondary_player_id
u8 n13
u8 n0x1E
u32 resource_or_action_id
u32 n26
u32 value
```

Resource fallback 可直接對到 `FIRE_BOMB`，因此目前為 FIRE_BOMB-related family；n13 enum OPEN。[C]

### 11

`n7 == 1` → `sub_7494B0`，其它 → `sub_749810`；後者清理 indexed player state，部分值寫入 `timeGetTime()`。[C][OPEN]

### 12

```text
u16 value_A
u16 value_B
```

4-byte body，進 `sub_67CD20()`。[C][OPEN]

## 18. subtype 13／14／15／17

### 13

會：

```text
byte_F6DD11[16 slots] = 0
sub_95EC00(slot) × 16
sub_718000
sub_7603A0
sub_67B5C0(...)
sub_62D570
sub_720A10
```

`sub_67B5C0` 已與 `CGameRule::NewGameStart` 對上，因此是 Server-driven Game/round reset/start path。[C]

仍不能直接命名成 Respawn、RoundEnd 或 RoundStart。[OPEN]

### 14

```text
u32 sample_or_time
u16 sample_a
u16 sample_b
u16 sample_c
u16 sample_d
u8 flag
```

13-byte body；`sub_5B3DD0()` 保存 transform samples，`IPaperCtrl::sub_9BCBD0()` 做插值。[C][OPEN]

### 15

```text
u8 target_player_id
u16 resource_id
u8 state_39
u8 state_30
u8 state_35
u32 target_controller_state
u32 auxiliary
u8 n0x1E
```

15-byte body；直接：

```text
target_controller +16 = target_controller_state
```

並做 Resource state/effect handling。[C][OPEN]

### 17

`sub_748FF0()` 會刷新多個 gameplay callbacks/state helpers；目前保持 callback/state event family。[C][OPEN]

## 19. subtype 19／20／21／22／23／24／26／27／29／30／31／32

### 19／23／30／31／32

目前 handler：

```text
19 → sub_74D150
23 → sub_74D410
30 → sub_74D510
31/32 → sub_74D5D0
```

完整 parser 尚未閉合，不依函式名稱猜語意。[C][OPEN]

### 20

與 subtype 3 共用 parser，但 context 不同。[C]

### 21

```text
u8 participant
u16 resource_id
u8 effect_a
effect_b
```

5-byte body，為 compact resource/action event candidate。[C][OPEN]

### 22

```text
u32 state_token
u8 participant_B
u16 resource_id
u8 n20
u32 value_0
u32 value_1
u8 tail_flag
```

16-byte body；需要 `state_token == dword_F2A65C` 後進 effect machinery。[C][OPEN]

### 24

```text
u16 field_A
u16 field_B
u32 elapsed_like
u8 flag
```

9-byte body；`elapsed_like` 以 `/1000/60` 與 `%60` 顯示為分鐘／秒，因此屬 server-driven timing/state presentation family，但 `1000` 是 Client presentation divisor，不等於已確認的 wire unit。[C][OPEN]

### 26

```text
u32
u16×3
u8×5
u32
```

17-byte body，進 `sub_604AC0()`；semantic OPEN。[C]

### 27／29

```text
u32
u16×4
u8
u32×2
u8
u32×2
u8
```

34-byte body；存在 `CViewObj::OnBotDeadCtrl` 與 `n27 == 27` special branch，至少屬 bot/player AI death/state family；semantic OPEN。[C]

## 20. `166` 主要 Resource／state 架構

大量 subtype 都遵循：

```text
166
 ↓
actor／participant discriminator
 ↓
subtype
 ↓
resource／state scalar
 ↓
Resource lookup
 ↓
state/effect bridge
 ↓
player/controller mutation
 ↓
UI／sound／Quest／secondary state
```

因此 Server reconstruction 的合理抽象是：

```text
GameplayEventEnvelope
```

而不是 `DamageAck`。[C]

## 21. K/D 與 Result 的三層邊界

```text
+240600/+240604
    = live round/mode-local K/D-like state

F6DCF8/F6DCFC
    = Server-provided result K/D

+60150/+60151
    = local result-screen My K/D
```

`166` 目前沒有直接找到 `++F6DCF8` 或 `++F6DCFC`，因此不能假定：

```text
166 kill event → F6DCF8++
```

完整 Result／Quest 關係統一見 `Result_Quest_Stats.md`。[C]

## 22. Gameplay network 與 Combat 的邊界

```text
Combat_Damage.md
    = Hit Detection、3D geometry、Damage modifier、165 建包前計算

Gameplay_Network.md
    = 165/166 event family、subtype、Resource/state application

UDP_Move_Inf_DeepEvidence.md
    = UDP movement／actor record

DropWeapon_Protocol.md
    = weapon drop/pickup event
```

因此同一個 damage event 可以被多個主文件引用，但不能複製整套 schema。[C]

## 23. Server reconstruction

最低抽象：

```text
YTcpInfReq
├─ Opcode = 165
├─ ActorOrSource
├─ EventSubtype
└─ VariantPayload

YTcpInfAck
├─ Opcode = 166
├─ ActorOrSubject
├─ EventSubtype
└─ VariantPayload
```

Server 不應先寫死：

```text
DamagePacket
KillPacket
```

應依實際 parser／sender grammar 分 variant DTO／codec。[C]

## 24. Evidence／未確認

```text
所有 165 subtype 的完整 enum
166 subtype 8/9/18/25 callback body grammar
166 subtype 19/23/30/31/32 完整 parser
sub_592B20 所有 caller 的 exact pairing
166 ↔ 269 K/D replacement/aggregation
165/166 所有 Resource ID 的 concrete mapping
Client / Server authority contract
```

任何未知欄位保持 `[OPEN]`，不得以方便 Server 編譯為由填 `0` 或 guessed enum。

## 25. 最高價值後續追查

```text
A. 完整建立 165 sender → subtype → field → state graph
B. 完整建立 166 subtype → state/resource graph
C. `166 n18=3/20` → target runtime value → 269 result state
D. `166 subtype 13/14` ↔ GameRule / UDP ordering
E. 165/166 Resource ID → Extracted concrete data
F. 所有 `sub_592B20` caller → reader pairing
G. `sub_58D7D0` / `sub_602E00` → Network_Protocol.md
```
