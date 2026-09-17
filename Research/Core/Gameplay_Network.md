# Gameplay／Y_TCP_INF／Drop-Pickup 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 Gameplay 層的 `165/166 Y_TCP_INF` 與 `960–963` dropped weapon／world-object event。命中、幾何與 damage 計算由 [`Combat_Damage.md`](Combat_Damage.md) 維護；UDP movement 由 [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md) 維護；Result／Quest 由 [`Result_Quest_Stats.md`](Result_Quest_Stats.md) 維護。

## 1. 一眼看懂

```text
165 Y_TCP_INF_REQ
    = Client → Server gameplay / actor / effect / state event family

166 Y_TCP_INF_ACK
    = Server → Client gameplay / actor / effect / state event family

960–963
    = dropped-world-object / weapon pickup stateful event family
```

不要簡化成：

```text
165 = DamagePacket
166 = DamageAck
960–963 = simple pickup request/response
```

正確的 Server 重建方向是：

```text
Client event construction
    ↓
exact wire schema
    ↓
Server validation / resolution
    ↓
Server authoritative event/state
    ↓
Client state application
```

## 2. 165：Client → Server gameplay event family

目前找到的主要 sender：

| subtype／形態 | Client path | 目前語意 | 信度 |
|---:|---|---|---:|
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

### 2.1 subtype 21：BotSuicide

`sub_5658B0()`：

```text
165
u8 field0
u8 subtype = 21
u16 field2
u16 field3
i16 field4
```

三個 16-bit writer 的實際 wire width 已確認。[C]

### 2.2 subtype 16：MultiDamage

`GameNetwork::OnSendPacketMultiDamage`：

```text
Packet opcode = 165
u8/local actor-like
u8 subtype = 16
...
```

因此 subtype 16 = MultiDamage variant 已直接閉合；完整 target/resource fields 仍依 sender path 為準。[C]

### 2.3 subtype 4／5／8／9／10

目前安全模型：

```text
4 → effect/resource/state family
5 → dead-position/state variant
8 → dead-position/state variant
9 → small state event
10 → small state event
```

不同 subtype 不應因相似 caller 名稱而共用 wire layout。[C][OPEN]

### 2.4 subtype 13：vector／interaction report

`sub_5E6DF0()` 建立：

```text
165
u8 actor-like
u8 13
u8 local player
... 4-byte values ...
4-byte vector.x
4-byte vector.y
4-byte vector.z
```

caller `sub_5E3A50()` 在送出前進行 target/state/geometry checks，因此可確認為本地計算後送出的 interaction/vector report，但不能因此宣稱 Client 對最終結果具 authority。[C][OPEN]

## 3. 165 的重要 wire-width 陷阱

`sub_592B20()` 實作：

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

即使 caller 顯示：

```c
sub_592B20(packet, SLOBYTE(value));
```

wire 仍為 4 bytes。[C]

所有 165/166 footprint 都必須以 helper implementation 為準，而不是 Hex-Rays 表面 prototype。

## 4. 166：Server → Client event family

接收鏈：

```text
TCP frame
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
subtype parser
```

`n18`／第二 byte 直接進 subtype switch，因此它是主要 event discriminator。[C]

### 4.1 subtype wire index

| subtype | parser | body 摘要 |
|---:|---|---|
| 1 | `sub_746360` | `u8 target_id` |
| 2 | `sub_7463E0` | `u32 + u8 + u16×3 + u8×3 + u32×2 + u8` |
| 3 | `sub_747980` | `u32 + u8 + u16×3 + u8×2 + u32×2 + u8` |
| 4 | `sub_748860` | `u32 + u16 + u32×7` |
| 5 | `sub_748A50` | `u32 + u8 + u32×6` |
| 6 | `sub_748CD0` | `u16×2 + u32×6 + u8` |
| 7 | `sub_748E40` | variable/string-like |
| 8/9/18/25 | `sub_748EB0` | callback family，部分 context 有附加 `u32` |
| 10 | `sub_749230`／`sub_749520` | `u8 + n13 + state/resource tail` |
| 11 | `sub_7494B0`／`sub_749810` | `u8` |
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

此表只回答 wire／parser inventory，不等同於 public semantic enum。[C]

## 5. 166 subtype 1

`sub_746360()` 讀：

```text
u8 target_id
```

取得 player object/controller 後，在 remote actor path 進：

```text
sub_5B8EE0(controller)
sub_5B8F70(controller)
```

目前只確認 Server event → actor controller reset/state callback；public event name `[OPEN]`。[C]

## 6. 166 subtype 2／16：participant + Resource/state event

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

body = 19 bytes；加 outer two discriminator = 21 logical bytes。[C]

```text
outer n16     = participant_A
payload n16_2 = participant_B
```

兩者經 `sub_67D7D0()` 映射 player/slot。[C]

`resource_id` 進入：

```text
sub_5F5400
sub_5F5450
sub_5EF5B0
sub_5EFE00
sub_5EF5F0
```

`n2` downstream effect mapping：

```text
1 → type 6
2 → type 4
3 → type 7
4 → type 5
default → type 1
```

`v89`、`v95` 寫入 local player object `+164`、`+172`，名稱仍 `[OPEN]`。[C]

Remote branch 可進：

```text
sub_9BC470(controller, 1, timeLike, 0, 0)
```

並寫：

```text
controller +56 = 1
controller +16 = 0
controller +60 = timeLike
controller +64 = timeGetTime()
```

因此這個 family 包含 death/state-transition branch，但仍不是單一 `DeathPacket`。[C]

### 6.1 Live K/D layer

正常 `a4 == 0`：

```text
participant A → +240600 ++
participant B → +240604 ++
```

`a4 == 1` 時 victim `+240604` 不增加。[C]

目前高信度：

```text
+240600 = live round/mode-local Kill counter
+240604 = live round/mode-local Death counter
```

## 7. 166 subtype 3／20：impact/status family

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

body = 19 bytes。[C]

只有：

```text
gate_v21 == dword_F2A65C
```

才進 `sub_747460()`；remote actor path 另進 `sub_747B90()`。[C]

`sub_747460()`：

```c
*(target_object + 16) = a6;
```

故 `a6` 是直接寫入 target runtime object 的 value-like state；目前不可直接命名為 HP。[C][OPEN]

同時 Resource lookup／category：

```text
sub_5F5450(resourceId)
sub_74CB20(category)
```

## 8. 166 subtype 4／5／6

### subtype 4

```text
u32 control_or_time
u16 control
u32 resource_id
u32 p0..p5
```

body = 34 bytes。[C]

### subtype 5

```text
u32 value_0
u8 control
u32 resource_id
6 × u32 effect values
```

body = 29 bytes；Resource category 10 有特殊 branch。[C][OPEN]

### subtype 6

```text
u16 value_0
u16 resource_id
6 × u32 values
u8 tail
```

body = 33 bytes；Resource category 10/15 有特殊 handling。[C][OPEN]

## 9. 166 subtype 7／8／9／10／11／12

```text
7  → variable/string-like via sub_592730
8/9/18/25 → callback/vtable family
10 → secondary player + state/resource/action values；fallback 可對到 FIRE_BOMB
11 → state/reset branch；部分路徑使用 timeGetTime()
12 → u16×2 control/state
```

其中 subtype 10 的 n13 enum、8/9/18/25 callback body、11/12 exact semantic 均 `[OPEN]`。[C]

## 10. 166 subtype 13／14／15／17

### subtype 13

會執行：

```text
byte_F6DD11[16 slots] = 0
sub_95EC00(slot) × 16
sub_718000
sub_7603A0
sub_67B5C0(...)
sub_62D570
sub_720A10
```

`sub_67B5C0` 已與 `CGameRule::NewGameStart` 對上，因此可確認是 Server-driven Game/round reset/start path，但不能直接命名 Respawn／RoundEnd／RoundStart。[C][OPEN]

### subtype 14

```text
u32 sample_or_time
u16 sample_a
u16 sample_b
u16 sample_c
u16 sample_d
u8 flag
```

13-byte body；`sub_5B3DD0()` 保存 transform samples，`IPaperCtrl::sub_9BCBD0()` 做插值。[C][OPEN]

### subtype 15

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

### subtype 17

`sub_748FF0()` 刷新 gameplay callbacks/state helpers；保持 callback/state event family。[C][OPEN]

## 11. 166 subtype 19–32：目前維持 raw

```text
19 → sub_74D150
20 → sub_747980（與 3 共用 parser，context 不同）
21 → sub_747DD0：u8 + u16 + u8×2
22 → sub_747AB0：16-byte effect/impact family
23 → sub_74D410
24 → u16×2 + u32 + u8（9 bytes）
26 → sub_745F50：17-byte parser
27/29 → sub_746060：34-byte bot/player AI death/state family candidate
30 → sub_74D510
31/32 → sub_74D5D0
```

subtype 22 需 `state_token == dword_F2A65C` 後進 effect machinery；subtype 24 的 `elapsed_like` 會被 `/1000/60`、`%60` 顯示，但這只是 presentation divisor，不能直接當作 wire unit。[C][OPEN]

## 12. 166 的共同架構與 Result 邊界

大量 subtype 都符合：

```text
166
 ↓
actor/participant discriminator
 ↓
subtype
 ↓
resource/state scalar
 ↓
Resource lookup
 ↓
state/effect bridge
 ↓
player/controller mutation
 ↓
UI / sound / Quest / secondary state
```

因此 Server 應使用中性的：

```text
GameplayEventEnvelope
```

而不是 `DamageAck`。[C]

K/D 三層保持：

```text
+240600/+240604 = live round/mode-local
F6DCF8/F6DCFC   = Server-provided result K/D
+60150/+60151   = local result-screen My K/D
```

完整 Result／Quest 關係由 [`Result_Quest_Stats.md`](Result_Quest_Stats.md) 統一維護；本文件只維護 `165/166` gameplay-side evidence。[C]

## 13. `960–963` Dropped Weapon／World Object Protocol

這組是與 Y_TCP_INF 平行、但仍屬 Gameplay 層的 stateful world-object event family。[C]

### 13.1 Packet family

```text
960 → sub_566B30
961 → sub_566BF0
963 → sub_5672E0
```

Client request：

```text
sub_566F50
    → Packet opcode 962
    → sub_555090(send)
```

方向與名稱：

```text
960 Server → Client  GameNetwork::OnGGWeaponPickUpDestroyNotify
961 Server → Client  dropped weapon/world-object update
962 Client → Server  GameNetwork::OnSendGGDropWeaponGetAndDropReq
963 Server → Client  GameNetwork::OnGGDropWeaponGetAndDropAck
```

### 13.2 Packet 960：destroy notification

```text
u8 count
repeat:
    u16 dropped_object_id
```

當 ID 為 0 時 loop 可提前結束。非零 ID 送入：

```text
sub_95F8F0(dropManager, dropped_object_id, 0)
→ sub_962DF0
```

因此高信度：

```text
u16 = dropped-world-object instance ID
```

不是 Resource template ID。[C]

### 13.3 Packet 961：world-object update

`sub_566BF0()`：

```text
u8 count
repeat count:
    u16 object_or_weapon_id
    u8 control
    u32 value_0
    u16 value_1
    u16 value_2
    u16 value_3
    u16 value_4
    u16 value_5
    u32 value_2_32
    u32 value_3_32
    0x20-byte raw block
```

Handler 建立 world-object representation、處理 position、Resource lookup，並進：

```text
sub_95E7D0(dropManager, 0, src, 0)
sub_5F5BE0(resourceTable, id)
sub_5BB9F0(resource)
```

因此高信度：

```text
961 = Server → Client dropped-world-object appearance/state record
```

以下維持 `[OPEN]`：

```text
first u16 的 instance/resource namespace
control byte
secondary u16/u32
0x20-byte raw block
coordinate packing / unit
```

### 13.4 Packet 962：GetAndDrop request

實際 helper width：

```text
sub_592920 → 1 byte
sub_5929E0 → 2 bytes
sub_592B20 → 4 bytes
```

目前最佳 raw sequence：

```text
field_00 : 2 bytes = a1
field_02 : 2 bytes = a2 / action-table-related value
field_04 : 1 byte  = v21 = *a5
field_05 : 2 bytes = packed a3-related value
field_07 : 2 bytes = a4
field_09 : 4 bytes = float-like v26
```

`field_05` 必須再以 ASM/LST 驗證，因 caller temporary 有 packed representation。[C][OPEN]

`a2` 明確與 action/resource selection 相連：

```text
&stru_B8A19C.action + a2
→ sub_535020
→ sub_533FF0
```

`v21 = *a5` 會參與 local weapon/action slot lookup；最後 `v26` 是 quantitative action/weapon state candidate，但**尚未證明為 durability**。[C][OPEN]

### 13.5 Packet 963：GetAndDrop ACK

開頭：

```text
u8 status
```

`status != 0` early return；零為 success。[C]

success body：

```text
u8  player/network id
u32 state/value
u16 dropped_object_id
u8  control
u16 resource/action id
u16 value_1
u16 value_2
u16 value_3
```

當 `resource/action id != 0`：

```text
u16 value_4
u16 value_5
u16 value_6
u32 float-like/raw scalar
0x20-byte raw block
```

最重要的 namespace separation：

```text
DroppedObjectInstanceId
    = v26
    → sub_95F600(dropManager, v26, ...)
    → sub_95F8F0(dropManager, v26, 0)

ResourceOrActionId
    = n2789
    → sub_534D20(actionTable, n2789)
    → sub_5F5BE0(resourceTable, n2789)
```

`sub_95F600()` 比較：

```text
*(dropObject + 22) == v26
```

所以已確認：

```text
DroppedObjectInstanceId != ResourceOrActionId
```

ACK application：

```text
963
 ↓
sub_960250
 ↓
resource/action + world-object state
 ↓
sub_95F920
 ↓
player weapon/action state
 ↓
sub_95F8F0
 ↓
remove/resolve picked object
```

因此 963 是 state-changing ACK。[C]

### 13.6 Drop object / player state bridge

`sub_95F600()` 會掃描 active drop objects；可見 object state：

```text
+20
+38
+40
+44
+48..+76 (8 DWORD state values)
+128
+132
+136
```

`sub_95F920()` local-player branch 會更新：

```text
+238740
+238964
+144208
+144210
+144220..+144248
+239576
```

並呼叫：

```text
sub_956BB0
sub_95B9B0
sub_5F66A0
sub_5F67A0
sub_5F3A90
sub_5FF2C0
```

因此 963 可以確認改變 player weapon/action state；ammo、PG、temporary item level/effect、selection 的 exact mapping 仍 `[OPEN]`。[C]

### 13.7 Wiki 定位

Wiki 的 drop／weapon pickup 描述只能作為玩家可見 gameplay role 的外部旁證；不能單獨用來命名 960–963 的 wire fields。[WIKI]

## 14. Gameplay 與其它層的固定邊界

```text
Network_Protocol.md
    = transport / frame / integrity / codec / dispatcher

Gameplay_Network.md
    = 165/166 + 960–963 gameplay event families

Combat_Damage.md
    = hit / geometry / damage modifier / 165 建包前計算

UDP_Move_Inf_DeepEvidence.md
    = UDP 8/24 movement / actor record

Result_Quest_Stats.md
    = result / score / quest aggregation
```

同一事件可以跨文件引用，但不能複製整套 wire/semantic truth。

## 15. Server reconstruction

```text
YTcpInfRequest
├─ Opcode = 165
├─ ActorOrSource
├─ Subtype
└─ VariantPayload

YTcpInfAck
├─ Opcode = 166
├─ ActorOrSubject
├─ Subtype
└─ VariantPayload

DroppedWorldObjectEvent
├─ Opcode = 960..963
├─ InstanceId
├─ ResourceOrActionId
└─ VariantPayload
```

Server 不應先寫死：

```text
DamagePacket
KillPacket
WeaponPickupPacket
```

而應依 parser／sender grammar 建立 variant codec／DTO。

## 16. 目前 OPEN 與最高價值追查

```text
165 所有 subtype 完整 enum / field semantics
sub_592B20 所有 caller → exact reader/writer pairing
166 subtype 8/9/18/25 callback body grammar
166 subtype 19/23/30/31/32 parser
166 ↔ 269 K/D replacement / aggregation
165/166 Resource ID → Extracted concrete mapping
Client / Server authority contract
166 subtype 14 ↔ UDP/GameRule ordering

960–963 secondary field semantics
961 instance-ID assignment / Resource namespace
962 packed field ASM/LST verification
963 optional block discriminator / exact state mutation
960–963 Resource ID → Extracted concrete mapping
```

所有未知欄位保持 `[OPEN]`；不得因 Server 實作方便而填 `0`、固定常數或 guessed enum。
