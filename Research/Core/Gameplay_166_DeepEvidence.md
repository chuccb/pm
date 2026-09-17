# `166` Gameplay 深入證據

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是 `166` Gameplay／結果／死亡／移動事件的深入證據主文件。`Packet_166_Field_Map.md` 只負責快速欄位索引；本文件負責完整 parser、reader width、state mutation、Resource、K/D 與跨函式證據。原本分散的 `Gameplay_166_KD_Field_Evidence.md` 與 `Packet_166_Field_Detail_3_15.md` 已整合至本文件，不再維護第二份完整 semantic 真相。

## 1. `166` 是多型 Gameplay Event Family

已確認接收鏈：

```text
TCP ClientSocket
  → sub_58B010
  → opcode 166
  → sub_58D820
  → sub_749B90
  → field0 u8 actor/player-like id
  → field1 u8 subtype
  → subtype-specific parser
```

`sub_749B90` 開頭依序讀取 `u8 n16` 與 `u8 n18`，其中 `n18` 直接進第二級 switch。因此 166 是多種 gameplay event 共用的 multiplexed family，不是一個固定結構的死亡封包。[C]

## 2. Reader Width 基線

目前直接對應的 reader helper：

```text
sub_592940 = u8
sub_5929C0 = u16
sub_592A00 = u16
sub_592A40 = u32
sub_592AC0 = u32
sub_592B40 = 4-byte copy／reader family
sub_592730 = variable／opaque data reader
```

所有後續 subtype footprint 都依實際 helper 呼叫判定，不依 Hex-Rays 表面 prototype。[C]

## 3. subtype 1

`sub_746360()` 讀：

```text
u8 target_id
```

然後：

```text
sub_67DF00(target_id)
→ player object/controller
→ remote actor 時 sub_5B8EE0(controller)
→ sub_5B8F70(controller)
```

目前可確認是 Server event → actor controller state/reset callback；公開事件名稱仍 `[OPEN]`。[C]

## 4. subtype 2／16：Participant Event

### 4.1 Wire payload

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

Body footprint：

```text
4 + 1 + 2 + 1 + 1 + 1 + 4 + 4 + 1 = 19 bytes
```

外層另有：

```text
u8 participant_A
u8 subtype
```

因此 logical body（含外層 discriminator）為：

```text
2 + 19 = 21 bytes
```

### 4.2 Participant direction

```text
outer n16     = participant_A
payload n16_2 = participant_B
```

兩者分別經 `sub_67D7D0()` 映射到 local player/slot object。[C]

### 4.3 Resource anchor

`resource_id` 進入：

```text
sub_5F5400(resourceTable, resource_id)
sub_5F5450(resourceTable, resource_id)
sub_5EF5B0
sub_5EFE00
sub_5EF5F0
```

因此不是 decorative field，而是 gameplay event 的重要 Resource identity。[C]

### 4.4 `n2` downstream mapping

```text
n2 == 1 → sub_61FC20(..., 6, resource_id)
n2 == 2 → sub_61FC20(..., 4, resource_id)
n2 == 3 → sub_61FC20(..., 7, resource_id)
n2 == 4 → sub_61FC20(..., 5, resource_id)
default  → sub_61FC20(..., 1, resource_id)
```

這個 mapping 是 effect/presentation type，不等於 wire subtype。[C]

### 4.5 `v89`／`v95`

```text
v89 → local player object +164
v95 → local player object +172
```

公開語意仍 `[OPEN]`。[C]

### 4.6 Death／state transition

Participant B 的 remote branch 可進：

```text
sub_9BC470(controller, 1, timeLike, 0, 0)
```

之後直接修改：

```text
controller +56 = 1
controller +16 = 0
controller +60 = timeLike
controller +64 = timeGetTime()
```

並清理 controller state/timer arrays。[C]

因此 subtype 2/16 **包含** death/state-transition branch，但整個 subtype family 不能被命名成單一 DeathPacket。[C]

## 5. `+240600/+240604` 即時 Round K/D-like state

在正常 `a4 == 0` 路徑：

```text
participant A → player +240600 ++
participant B → player +240604 ++
```

`a4 == 1` 時不執行 victim `+240604` increment。[C]

這兩個欄位在 player stride `240780` 內，並由 `RoundStat` UI 直接消費。因此目前高信度模型：

```text
+240600 = live round/mode-local Kill counter
+240604 = live round/mode-local Death counter
```

## 6. subtype 3／20：shared impact/status wire form

`sub_747980()` 讀：

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

Body footprint：19 bytes。

接受條件：

```text
gate_v21 == dword_F2A65C
```

再進：

```text
sub_747460(..., resource_id, state_type, aux_a6, aux_n26, aux_n0x1E, subtype)
```

Remote outer actor 另外進：

```text
sub_747B90(resource_id, target, state_a, state_b, outer_actor)
```

目前高可信：Resource/impact/gameplay effect family。[C]

## 7. subtype 4：Resource／effect record

`sub_748860()`：

```text
u32 control_or_time
u16 control
u32 resource_id
u32 p0
u32 p1
u32 p2
u32 p3
u32 p4
u32 p5
```

Body footprint：34 bytes。

六個 `p0..p5` 全部由 `sub_592B40()` 等 4-byte helper 取得，並送入 `sub_61BA90()`。[C]

Resource category 1–7 還會走額外 effect/presentation path。正式公開名稱仍 `[OPEN]`。

## 8. subtype 5

`sub_748A50()`：

```text
u32 value_0
u8  control
u32 resource_id
u32 effect_0
u32 effect_1
u32 effect_2
u32 effect_3
u32 effect_4
u32 effect_5
```

Body footprint：29 bytes。

Resource category 10 會進主要特殊 branch；local/remote 有不同 downstream helper。[C][OPEN]

## 9. subtype 6

`sub_748CD0()`：

```text
u16 value_0
u16 resource_id
u32 value_2
u32 value_3
u32 value_4
u32 value_5
u32 value_6
u32 value_7
u8  tail
```

Body footprint：33 bytes。

Resource category 10/15 有特殊 state/effect handling。[C][OPEN]

## 10. subtype 7

`sub_748E40()`：

```text
variable／opaque string-like data
```

透過 `sub_592730()` 寫入最多 256-byte local buffer，再交給 `sub_61FCB0()`。不可從本函式自行宣稱固定 wire length；應追 `sub_592730()`。[C][OPEN]

## 11. subtype 8／9／18／25

`sub_748EB0()` 主要把 actor、subtype 與 Packet 交給 vtable callback；不能從函式本體假定 body 为空。

部分 context 後續還會讀 `u32` time-like field，因此完整 wire grammar 必須從 indirect callback 追。[C][OPEN]

## 12. subtype 10：FIRE_BOMB family

Dispatcher 先讀：

```text
u8 secondary_player_id
u8 n13
```

後續 parser：

```text
u8  n0x1E
u32 resource_or_action_id
u32 n26
u32 value
```

可直接確認 Resource fallback：

```text
FIRE_BOMB
```

因此目前是 FIRE_BOMB-related gameplay effect family；`n13=9/10/13` 的公開 enum 仍 `[OPEN]`。[C]

## 13. subtype 11

Dispatcher 讀：

```text
u8 n7
```

`n7 == 1` → `sub_7494B0`；其它 → `sub_749810`。

`sub_749810()` 會清理 indexed player state，並在特定 `n7` 值寫入 `timeGetTime()`。[C]

目前語意：player timer/state reset family；公開 enum `[OPEN]`。

## 14. subtype 12

```text
u16 value_A
u16 value_B
```

Body footprint：4 bytes。

下游：

```text
sub_67CD20(n9_0, value_A, value_B, 2 - !sub_67F2F0())
```

目前為 two-u16 state/control event。[C][OPEN]

## 15. subtype 13

Inline lifecycle/reset path：

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

不可直接改名成 Respawn、RoundEnd 或 RoundStart，直到與 GameRule 133/134/137/138、269 state 完整串接。[OPEN]

## 16. subtype 14：transform sample

精確 body：

```text
u32 sample_or_time
u16 sample_a
u16 sample_b
u16 sample_c
u16 sample_d
u8  flag
```

Body footprint：13 bytes。

`sub_5B3DD0()` 保存 transform samples，後續 `IPaperCtrl::sub_9BCBD0()` 做插值。[C]

四個 u16 的 signedness／軸向公開語意需由 ASM/LST 進一步確認；目前只稱 spatial/transform sample components。[C][OPEN]

## 17. subtype 15

`sub_748420()`：

```text
u8  target_player_id
u16 resource_id
u8  state_39
u8  state_30
u8  state_35
u32 target_controller_state
u32 auxiliary
u8  n0x1E
```

Body footprint：15 bytes。

直接 mutation：

```text
target_controller +16 = target_controller_state
```

並以 `resource_id` 做 Resource state/effect handling。[C][OPEN]

## 18. subtype 17

`sub_748FF0()` 與 callback family 類似，會刷新：

```text
sub_7093A0
sub_9F94C0
sub_62DCF0
sub_62E9E0
sub_62C180
sub_5A06B0
```

目前保持為 callback/state event family。[C][OPEN]

## 19. subtype 19／23／30／31／32

目前 handler 定位：

```text
19 → sub_74D150
23 → sub_74D410
30 → sub_74D510
31 → sub_74D5D0
32 → sub_74D5D0
```

完整 parser 尚未閉合；目前禁止從函式名稱或相鄰 subtype 猜公開 semantic。[C][OPEN]

## 20. subtype 21

Payload：

```text
u8 participant
u16 resource_id
u8 effect_a
u8 effect_b
```

Body footprint：5 bytes。

`sub_747B90()` 會使用 Resource、effect values 與 target actor；目前高可信：compact resource/action event。[C][OPEN]

## 21. subtype 22

`sub_747AB0()`：

```text
u32 state_token
u8  participant_B
u16 resource_id
u8  n20
u32 value_0
u32 value_1
u8  tail_flag
```

Body footprint：16 bytes。

需要：

```text
state_token == dword_F2A65C
```

再進 `sub_747460()`；與 subtype 3/20 共用 effect/impact machinery，但 downstream path 不完全相同。[C][OPEN]

## 22. subtype 24

Inline body：

```text
u16 field_A
u16 field_B
u32 elapsed_like
u8  flag
```

Body footprint：9 bytes。

其中 `elapsed_like` 會以：

```text
minutes = value / 1000 / 60
seconds = value / 1000 % 60
```

進 `sub_7498E0()`，因此為 server-driven gameplay time presentation/update family。[C][OPEN]

`1000` 是 Client presentation calculation divisor，不應單獨宣布為協定單位定義。

## 23. subtype 26

`sub_745F50()` parser：

```text
u32
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

Body footprint：17 bytes。

後續進 `sub_604AC0()`。正式 semantic `[OPEN]`。[C]

## 24. subtype 27／29

`sub_746060()` parser：

```text
u32
u16
u16
u16
u16
u8
u32
u32
u8
u32
u8
u32
```

Body footprint：34 bytes。

具有 `CViewObj::OnBotDeadCtrl` 診斷與 `n27 == 27` 特殊 branch，因此至少屬 bot/player AI death/state family；欄位語意仍 `[OPEN]`。[C]

## 25. subtype 20

`sub_747980()` 與 subtype 3 共用 parser，但 `n3=20` 會影響 `sub_747460()` downstream branch。

因此：

```text
wire structure ≈ subtype 3
semantic context != necessarily subtype 3
```

不能只因共用 parser 就宣稱兩者完全相同。[C]

## 26. 166 Event → Resource → State 的共同架構

大量 subtype 皆呈現同一結構：

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
UI／sound／quest／secondary packet
```

因此後續 Server reconstruction 的抽象單位應是 `GameplayEventEnvelope`，而不是單一 `DamageAck`。[C]

## 27. K/D 三層資料邊界

目前必須分開：

```text
+240600/+240604
    = live round/mode-local K/D-like counters

F6DCF8/F6DCFC
    = Server-provided result/team K/D

+60150/+60151
    = local result-screen My K/D
```

其中 `F6DCF8/F6DCFC` 由 `TCP 269 subtype 7` repeated player records 直接灌入；目前沒有找到 166 handler 直接 `++F6DCF8` 或 `++F6DCFC`。[C]

因此不能假定：

```text
166 kill event → F6DCF8++
```

## 28. Player Identity：PlayerId != SlotIndex

所有 166／score/death path 都顯示 PlayerId、SlotIndex、Team/Group 與 RuntimeObject 必須分離。`sub_67D7D0()` 負責把 compact identity 映射到 local player/slot state。[C]

Server model 至少保持：

```text
PlayerId
SlotIndex
Team/Group
RuntimeObject
ConnectionState
```

## 29. TCP transport boundary

部分 165 sender 走：

```text
sub_58D7D0(byte_13242F8, packet)
```

部分 runtime/state path 走：

```text
sub_602E00(packet)
```

目前不能假定兩者等價。仍需追：

```text
packet finalization
→ length/header
→ queue/send
→ encryption/checksum
→ socket
```

因此 logical payload 與 final TCP frame 必須分開記錄。[C][OPEN]

## 30. Evidence Matrix

| 項目 | 狀態 |
|---|---|
| 165 = `Y_TCP_INF_REQ` | CLOSED |
| 166 = `Y_TCP_INF_ACK` | CLOSED |
| 165 為 polymorphic family | CLOSED |
| 165 subtype 16 = MultiDamage | CLOSED |
| 165 subtype 21 = BotSuicide | CLOSED |
| 166 second byte = event discriminator | CLOSED |
| 166 subtype 2/16 包含 death/state transition | HIGH |
| 166 subtype 13 = Game/round reset path | HIGH |
| 166 subtype 14 = transform sample | HIGH |
| 166 subtype 24 = timing/state path | HIGH |
| +240600/+240604 = live round K/D-like | HIGH |
| F6DCF8/F6DCFC = Server-provided result K/D | CLOSED |
| 166 直接修改 F6DCF8/F6DCFC | NOT FOUND |
| 所有 `sub_592B20` caller 的 wire width | OPEN |
| `sub_58D7D0` / `sub_602E00` 完整 transport boundary | OPEN |
| 所有 subtype public semantic | OPEN |

## 31. Server reconstruction 禁止事項

不要寫：

```text
165 = DamagePacket
166 = DamageAck
166 → Score.Kill++
```

應保持：

```text
YTcpInfReq
    Opcode = 165
    EventSubtype = subtype-specific
    Payload = exact serializer-defined grammar

YTcpInfAck
    Opcode = 166
    ActorOrSubject = first discriminator
    EventSubtype = second discriminator
    Payload = subtype-specific
```

未知欄位、writer width、state mutation、resource lookup、caller/callee 都應保留到證據閉合。[C][RES][WIKI][X]

## 32. 下一輪最高優先級

```text
A. 完整追 sub_592B20
B. 完整追 sub_58D7D0 / sub_602E00
C. 建立全部 165 subtype caller→state graph
D. 完整閉合 166 n18=3/20
E. 追 166 ↔ 269 K/D aggregation / replacement
F. 用 LST/ASM 驗證可疑 serializer prototype
G. 把 Y_TCP_INF Resource IDs 對到 Extracted 資源
H. 比對 166 subtype 14 與 UDP 8/24 對 actor controller 的寫入先後
```

在證據未閉合前，不為未知欄位填入猜測值。
