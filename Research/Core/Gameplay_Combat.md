# Gameplay／Combat／Y_TCP_INF／Drop-Pickup 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中「命中／傷害前置 → 165 Client→Server → 166 Server→Client → 960–963 掉落武器／拾取」這條完整 Gameplay 證據鏈。UDP movement 仍由 [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md) 維護；Result／Quest 由 [`Result_Quest_Stats.md`](Result_Quest_Stats.md) 維護。

## 1. 一眼看懂

```text
本地 Aim / Hit Detection
    ↓
Combat / Damage preprocessing
    ↓
165 Y_TCP_INF_REQ
    ↓
Server validation / resolution
    ↓
166 Y_TCP_INF_ACK
    ↓
Client actor / effect / state mutation
    ↓
Result / Quest
```

平行的 world-object 路徑：

```text
961/962/963/960
    = dropped-world-object / weapon pickup state machine
```

不要先把：

```text
165 = DamagePacket
166 = DamageAck
963 = simple pickup ACK
```

視為固定資料型別。它們都是 polymorphic／stateful event family。[C]

## 2. Combat → 165 的最短證據鏈

```text
2D hit-map / 3D geometry
    ↓
HitDetectionResult
    ↓
Runtime hit state (+1244)
    ↓
DamageInput
    ↓
sub_5E72C0 modifier
    ↓
variant multiplier / quantization
    ↓
Y_TCP_INF_REQ (165)
```

Client 確實進行本地命中與傷害前置計算，但目前沒有足夠證據證明 Client 擁有最終 damage authority。[C][OPEN]

## 3. Hit Detection：`sub_5EB290()`

核心函式：

```c
double __thiscall sub_5EB290(
    void *this,
    float a2,
    float a3,
    _WORD *hitType,
    float *rawResult)
```

主要流程：

```c
v7 = sub_5EAB60(this + 4, 256, 512, dword_1D0D724, a2, a3);
if (v7 == 0)
    return 0.0;

*hitType = HIBYTE(v7);
*rawResult = v7;
v6 = *rawResult / 100.0;

if (*hitType != 0)
    return v6 * 1.5;
return v6;
```

因此 `sub_5EAB60()` 的 16-bit return 同時攜帶：

```text
低位元組 → numeric component
高位元組 → hit-result category
```

category 非 0 時 normalized result × 1.5。[C]

## 4. `sub_5EAB60()`：256×512 Detection Map

資料來源：

```text
dword_1D0D724
```

以：

```text
256 × 512
x ∈ [0,255]
y ∈ [0,511]
```

掃描局部半徑內非零 entry，保留最近結果；若：

```text
nearest distance > radius²
```

則回傳 0。[C]

因此這不是單純 boolean raycast，而是：

```text
16-bit-valued detection map
+
nearest hit selection
```

輸入 `a2/a3` 經 255/511 比例換算，目前只能叫 normalized 2D hit-detection coordinates，不直接命名成 screen pixel／UV。[C][OPEN]

`dword_1D0D724` 的 initialization／allocation／loader／Extracted origin 尚未閉合，暫不命名成 `HitboxTexture`。[OPEN]

## 5. Hit category：runtime field `+1244`

`sub_5E63C0()` 依 `+1244` 分支：

```text
0 / 4  → hit
1      → hit_headshot
2      → hit_heartbreak
3      → hit_critical
0x15   → target_impact_bullet1
0x16   → target_impact_bullet2
```

目前高信度：

```text
+1244 = hit-result category / hit-effect selector
```

不能只命名 `HitRegion`，因為它同時包含 headshot、critical、heartbreak 等不同分類。[C]

## 6. 2D Hit Map 與 3D Geometry 必須分離

另一路徑在 `165 subtype 13` 前會做：

```text
target existence/state
range / distance
frustum
AABB / geometry
forward-direction dot
```

因此至少有兩種不同證據：

```text
2D hit-map detection
3D world-space geometry / direction checks
```

不可壓成單一 `HitDistance`／`HitMultiplier`。[C][OPEN]

## 7. Damage modifier：`sub_5E72C0()`

以下 165 sender 都會呼叫：

```text
OnSendPacketDamage
OnSendPacketMultiDamage
OnSendPacketMineBombDamage
```

並先：

```c
sub_5E72C0(source, target, raw_value);
```

所以它是 165 family 共用的低階 damage transform。[C]

source／target 最多各掃描 3 個 entries，透過 `sub_67D7D0(identifier)` 映射實際 player slot。[C]

目前 category mapping：

```text
0,1,2       → 2
3,4,5       → 3
6           → 4
7,8         → 6
9           → 1
10,11       → 5
12          → 7
13,14,25    → 8
19,20,21    → 10
24          → 12
26          → 9
other       → -1
```

目前直接可確認的 special candidates：

```text
source category 8 → increase

target category 9 → reduction
```

其它 category 保持 raw。[C][OPEN]

## 8. Damage 百分比公式

若：

```text
R = raw damage
P = source increase percentage
Q = target reduction percentage
```

Client：

```text
A = R * (1 + P/100)
B = A * (1 - Q/100)
```

即 target reduction 作用在已完成 source increase 的結果上。[C]

data flow：

```text
source identifier
    ↓ sub_67D7D0
source slot
    ↓
dword_F5653C[slot][0..2]
    ↓
category
    ↓
Resource object +548
    ↓
percentage modifier
```

target side 同理。[C]

## 9. Damage variant multiplier / quantization

目前 C path 可見：

```text
一般路徑          → 1.0
某些 client state → 2.0
n20 == 3          → 1.2
```

完整前置鏈：

```text
raw input
 → source increase
 → target reduction
 → variant/client-state multiplier
 → caller-side low-byte truncation
 → serializer
 → 165
```

`n20` 只稱 event/damage subtype-like byte，不直接命名 `DamageType`。[C][OPEN]

## 10. `sub_592B20()` 是 wire-width 陷阱

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

即使 caller 表面傳 `SLOBYTE(value)`，wire 仍為 4 bytes。[C]

## 11. 165 sender family

目前主要 sender：

```text
2   → sub_5DF7F0 / sub_5E6170
4   → sub_5E5ED0 / sub_5E6040
5   → CViewObj::TempSendDeadPosPacket
6/7 → gameplay/effect callers
8   → sub_7452D0
9   → sub_745D60
10  → sub_745E80
13  → sub_5E6DF0
15  → sub_55D440
16  → OnSendPacketMultiDamage / sub_55D530
21  → OnSendPacketBotSuicide / sub_5658B0
other → OnSendPacketDamage / Mine-Bomb
```

這是目前找到的 family inventory，不宣稱 enum 完整。[C]

### 11.1 subtype 16 — MultiDamage

`GameNetwork::OnSendPacketMultiDamage` 建立：

```text
Opcode = 165
... actor/source
subtype = 16
... target/resource/value fields
```

因此 subtype 16 = MultiDamage variant 已閉合。[C]

### 11.2 subtype 21 — BotSuicide

```text
165
u8  field0
u8  subtype = 21
u16 field2
u16 field3
i16 field4
```

目前已閉合 wire width；其它 semantic OPEN。[C][OPEN]

### 11.3 subtype 13 — vector / interaction report

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

caller 在送出前做 target/state/geometry checks，因此是本地計算後送出的 interaction/vector report。[C][OPEN]

## 12. 166 receive family

接收鏈：

```text
TCP frame
 → sub_58B010
 → case 166
 → sub_58D820
 → sub_749B90
 → u8 outer_actor_like
 → u8 subtype
 → subtype parser
```

## 13. 166 subtype inventory

| subtype | parser | body 摘要 |
|---:|---|---|
| 1 | `sub_746360` | `u8 target_id` |
| 2 | `sub_7463E0` | `u32 + u8 + u16×3 + u8×3 + u32×2 + u8` |
| 3 | `sub_747980` | `u32 + u8 + u16×3 + u8×2 + u32×2 + u8` |
| 4 | `sub_748860` | `u32 + u16 + u32×7` |
| 5 | `sub_748A50` | `u32 + u8 + u32×6` |
| 6 | `sub_748CD0` | `u16×2 + u32×6 + u8` |
| 7 | `sub_748E40` | variable/string-like |
| 8/9/18/25 | `sub_748EB0` | callback/vtable family |
| 10 | `sub_749230` / `sub_749520` | secondary player + resource/action tail |
| 11 | `sub_7494B0` / `sub_749810` | state/reset family |
| 12 | `sub_749A30` | `u16×2` |
| 13 | inline | lifecycle/reset/start path |
| 14 | `sub_749AB0` | `u32 + u16×4 + u8` |
| 15 | `sub_748420` | `u8 + u16 + u8×3 + u32×2 + u8` |
| 17 | `sub_748FF0` | callback/state family |
| 19/23/30/31/32 | `sub_74D150` / `74D410` / `74D510` / `74D5D0` | parser OPEN |
| 20 | `sub_747980` | same parser as 3, different context |
| 21 | `sub_747DD0` | `u8 + u16 + u8×2` |
| 22 | `sub_747AB0` | 16-byte effect/impact |
| 24 | inline | `u16×2 + u32 + u8` |
| 26 | `sub_745F50` | 17-byte parser |
| 27/29 | `sub_746060` | 34-byte bot/player AI death/state candidate |

表格只描述 wire/parser inventory，不是 public enum。[C]

## 14. 166 subtype 1 / 2 / 16

### subtype 1

```text
u8 target_id
```

取得 player controller 後走 reset/state callback；public event name OPEN。[C]

### subtype 2 / 16

body：

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

19-byte body + outer 2 bytes = 21 logical bytes。[C]

```text
outer n16     = participant_A
payload n16_2 = participant_B
```

兩者經 `sub_67D7D0()` 映射 player/slot。[C]

`resource_id` 進 `sub_5F5400` / `sub_5F5450` / `sub_5EF5B0` / `sub_5EFE00` / `sub_5EF5F0`。[C]

`n2` mapping：

```text
1 → 6
2 → 4
3 → 7
4 → 5
default → 1
```

`v89/v95` 寫入 local player `+164/+172`。[C]

Remote path 可呼叫：

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

因此 family 包含 death/state transition branch，但不是單一 DeathPacket。[C]

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

## 15. 166 subtype 3 / 20

body = 19 bytes：

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

只有：

```text
gate_v21 == dword_F2A65C
```

才進 `sub_747460()`；其中：

```c
*(target_object + 16) = a6;
```

因此 `a6` 只能叫 target runtime value，不能直接叫 HP。[C][OPEN]

## 16. 166 subtype 4 / 5 / 6

```text
4 → u32 + u16 + resource u32 + 6×u32 = 34-byte body
5 → u32 + u8 + resource u32 + 6×u32 = 29-byte body
6 → u16×2 + 6×u32 + u8 = 33-byte body
```

都有 Resource/effect handling；public semantics 部分 OPEN。[C]

## 17. 166 subtype 7–17

```text
7      → variable/string-like
8/9/18/25 → callback/vtable family
10     → secondary player + resource/action; fallback FIRE_BOMB
11     → state/reset/timer family
12     → u16×2
13     → GameRule/NewGameStart-like reset/start path
14     → 13-byte transform sample；保存後做 interpolation
15     → target/controller/resource state；直接寫 controller +16
17     → callback/state refresh
```

其中 subtype 14：

```text
u32 sample_or_time
u16 sample_a
u16 sample_b
u16 sample_c
u16 sample_d
u8 flag
```

`sub_5B3DD0` 保存 transform sample，`IPaperCtrl::sub_9BCBD0` 插值。[C][OPEN]

subtype 13 中 `sub_67B5C0` 已與 `CGameRule::NewGameStart` 對上，但不能直接叫 Respawn／RoundStart／RoundEnd。[C][OPEN]

## 18. 166 subtype 19–32

```text
19 → sub_74D150
20 → sub_747980
21 → u8 + u16 + u8×2
22 → 16-byte effect/impact
23 → sub_74D410
24 → 9-byte timing-like
26 → 17-byte parser
27/29 → 34-byte bot/player AI death/state candidate
30 → sub_74D510
31/32 → sub_74D5D0
```

subtype 24 的 `elapsed_like` 雖被 `/1000/60` 與 `%60` 顯示，但這只是 Client presentation divisor，不等於 wire unit。[C][OPEN]

## 19. Combat → 165 → 166 的 authority 邊界

目前最安全的 intermediate model：

```text
Client local detection
    → Client event construction
    → 165 Client → Server
    → Server validates/resolves
    → 166 Server → Client state
```

這不是「所有 damage 都必然如此」的最終證明；authority contract 仍 `[OPEN]`。[C]

166 並沒有直接看到 `F6DCF8++` / `F6DCFC++`，因此不可假定 166 kill event 直接增加 result K/D。[C]

## 20. 960–963 Dropped Weapon／World Object

這組仍屬 Gameplay 層，但使用獨立 world-object state。[C]

### 20.1 Packet family

```text
960 Server → Client  GameNetwork::OnGGWeaponPickUpDestroyNotify
961 Server → Client  dropped-world-object update
962 Client → Server  GameNetwork::OnSendGGDropWeaponGetAndDropReq
963 Server → Client  GameNetwork::OnGGDropWeaponGetAndDropAck
```

Dispatcher／sender：

```text
960 → sub_566B30
961 → sub_566BF0
963 → sub_5672E0
962 → sub_566F50 → sub_555090(send)
```

### 20.2 960 destroy notification

```text
u8 count
repeat:
    u16 dropped_object_id
```

ID 非零時：

```text
sub_95F8F0(dropManager, id, 0)
→ sub_962DF0
```

高信度：

```text
u16 = DroppedObjectInstanceId
```

不是 Resource template ID。[C]

### 20.3 961 world-object update

```text
u8 count
repeat:
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

處理：

```text
sub_95E7D0(dropManager, 0, src, 0)
sub_5F5BE0(resourceTable, id)
sub_5BB9F0(resource)
```

目前高信度：

```text
961 = Server → Client dropped-world-object appearance/state record
```

first u16 的 instance/resource namespace、各 secondary value、0x20-byte block、座標 unit 仍 `[OPEN]`。[C]

### 20.4 962 GetAndDrop request

實際 writer width：

```text
sub_592920 → 1 byte
sub_5929E0 → 2 bytes
sub_592B20 → 4 bytes
```

目前 raw sequence：

```text
field_00 : 2 bytes
field_02 : 2 bytes
field_04 : 1 byte
field_05 : 2 bytes
field_07 : 2 bytes
field_09 : 4 bytes
```

`a2` 與 action/resource selection 有 direct data flow；`v21` 參與 local weapon/action slot lookup。最後 `v26` 為 quantitative action/weapon state candidate，尚未證明是 durability。[C][OPEN]

### 20.5 963 GetAndDrop ACK

開頭：

```text
u8 status
```

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

當 resource/action id != 0：

```text
u16 value_4
u16 value_5
u16 value_6
u32 float-like/raw scalar
0x20-byte raw block
```

namespace separation：

```text
DroppedObjectInstanceId
    = v26
    → sub_95F600 / sub_95F8F0

ResourceOrActionId
    = n2789
    → sub_534D20 / sub_5F5BE0
```

`sub_95F600()` 比較：

```text
*(dropObject + 22) == v26
```

因此已確認：

```text
DroppedObjectInstanceId != ResourceOrActionId
```

ACK application：

```text
963
 → sub_960250
 → resource/action + world-object state
 → sub_95F920
 → player weapon/action state
 → sub_95F8F0
 → remove/resolve picked object
```

### 20.6 Drop object / player state bridge

`sub_95F600()` 可見 object state：

```text
+20
+38
+40
+44
+48..+76
+128
+132
+136
```

`sub_95F920()` local-player branch 更新：

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

因此 963 確實會改變 player weapon/action state；ammo、PG、temporary item level/effect、selection exact mapping 仍 OPEN。[C]

Wiki 的 drop／weapon pickup 描述僅作玩家可見 gameplay role 旁證，不直接命名 wire field。[WIKI]

## 21. K/D 與 Result 邊界

```text
+240600/+240604
    = live round/mode-local K/D-like state

F6DCF8/F6DCFC
    = Server-provided result K/D

+60150/+60151
    = local result-screen My K/D
```

`Result_Quest_Stats.md` 維護完整 Result／Quest aggregation；本文件只保留 gameplay 端的 live K/D evidence。[C]

## 22. Resource／state bridge

165/166 與 960–963 都大量進入 Resource helper：

```text
sub_5F5400
sub_5F5450
sub_5EF590
sub_5EF5B0
sub_5EFE00
sub_5F0FB0
sub_5F5BE0
```

但 Resource ID → Extracted concrete record 仍須逐項閉合，不能由 helper 名稱推 public semantic。[C][RES][OPEN]

## 23. Server reconstruction

建議第一階段只使用 polymorphic envelopes：

```text
GameplayEvent
├─ Direction
├─ Opcode
├─ ActorOrSubject
├─ Subtype
└─ VariantPayload

DroppedWorldObjectEvent
├─ Opcode = 960..963
├─ InstanceId
├─ ResourceOrActionId
└─ VariantPayload

DamageInput
├─ Source
├─ Target
├─ RawValue
├─ HitResult
├─ ModifierContext
└─ VariantContext
```

不要直接創造：

```text
DamagePacket
DamageAck
KillPacket
WeaponPickupPacket
```

除非後續證據真的形成獨立且穩定的 semantic schema。[C][OPEN]

## 24. 目前 OPEN 與最高價值追查

```text
165 所有 sender / subtype / field 完整 graph
166 callback families 8/9/18/25
166 parser 19/23/30/31/32
166 ↔ 269 K/D replacement / aggregation
165/166 Resource ID → Extracted concrete records
Client / Server authority contract

dword_1D0D724 initialization → loader → Extracted source
sub_5EAB60 exact coordinate producer
+1244 完整 producer/consumer closure
sub_55CAB0 hit → 165 exact mapping

960–963 secondary field semantics
961 instance-ID assignment / resource namespace
962 packed field ASM/LST verification
963 optional block discriminator / exact state mutation
960–963 Resource ID → Extracted concrete mapping
```

所有未知欄位維持 `[OPEN]`；不得因 Server 實作方便而填 `0`、固定常數或 guessed enum。
