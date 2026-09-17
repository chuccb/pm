# PaperMan Server State Model（2016 日本版最終 Client）

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年結束營運時的最終 Client。
> 文件角色：只保存跨 Packet／跨子系統的 Server reconstruction 抽象模型，不重新複製單一封包欄位或單一功能的詳細證據。

## 先看這裡：這份文件回答什麼

如果問題是「Server 應該保存哪些狀態、這些狀態怎麼分層、不同 Packet 最後修改哪一層」，看這份文件。

如果問題是「某個 Packet 到底有哪些 bytes」，不要在這裡找：

```text
Packet wire layout
    → 對應 Protocol / Schema / Field Evidence

單一功能 C / LST 證據
    → 對應該功能的研究文件

跨域 Server graph
    → 本文件
```

最短理解路徑：

```text
Session
  ↓
Room
  ↓
PlayerSlot[16]
  ↓
MatchRuntime
  ↓
Gameplay / Result
  ↓
Profile / Inventory / Economy
```

## 1. 模型原則

嚴格區分：

```text
Client runtime field
    ≠
wire field
    ≠
server semantic field
```

未知欄位保持：

```text
unknown_*
*_value
selector_value
packed_flags
```

只有跨來源證據真正閉合後才升級 public semantic。

## 2. Server 核心邊界

```text
GameServer
├─ Session[]
├─ Room[]
└─ MatchRuntime[]
```

```text
Session      = connection / identity / current room
Room         = room configuration + player slots
MatchRuntime = in-game mode / round / objective / result
```

三者不可壓成單一 `Player` 或 connection state。

## 3. Session

```text
Session
├─ Connection
├─ PlayerId
├─ CurrentRoomId
└─ ConnectionState
```

必須保存：

```text
PlayerId ≠ SlotIndex
```

詳細證據：[`Network_Protocol.md`](Network_Protocol.md)、[`Room_GameRule_Mode.md`](Room_GameRule_Mode.md)。

## 4. Room

```text
Room
├─ GameMode
├─ MapSelector
├─ RuleSelector
├─ ObjectSelector
├─ TimeSelector
├─ PackedRoomFlags
├─ MasterPlayerId
├─ PlayerSlot[16]
└─ RoomPhase
```

每個 selector 都保留：

```text
OptionIndex
OptionValue
```

詳細研究：[`Room_GameRule_Mode.md`](Room_GameRule_Mode.md)。

## 5. PlayerSlot[16]

Client 存在固定 16-slot player model；Server 第一階段也使用固定容量抽象：

```text
PlayerSlot
├─ SlotIndex
├─ Occupied
├─ PlayerId
├─ TeamId
├─ GroupId
├─ ReadyState
├─ ConnectionState
├─ InGameState
├─ CharacterState
├─ LoadoutState
├─ PositionState
├─ CombatState
└─ ScoreState
```

`TeamId`／`GroupId` 暫不合併成單一 relation 欄位。

## 6. Room → Match lifecycle

```text
CHANNEL / LOBBY
      ↓
ROOM
      ↓
READY
      ↓
START_REQUESTED
      ↓
MATCH_INITIALIZING
      ↓
IN_GAME / ROUND_RUNTIME
      ↓
MATCH_ENDING
      ↓
POST_MATCH / ROOM
```

由 [`Room_GameRule_Mode.md`](Room_GameRule_Mode.md)、[`Gameplay_Network.md`](Gameplay_Network.md)、[`Result_Quest_Stats.md`](Result_Quest_Stats.md) 共同支撐。

## 7. MatchRuntime

```text
MatchRuntime
├─ Phase
├─ GameMode
├─ MapValue
├─ RuleValue
├─ ObjectValue
├─ TimeValue
├─ ElapsedTime
├─ RoundIndex
├─ RoundState
├─ ObjectiveState
├─ SpawnState
├─ TeamState
├─ PlayerRuntime[16]
└─ ResultState
```

`RoundIndex` 與 `ElapsedTime` 必須分開；不同 mode 同時存在回合型與時間型進度。[OPEN]

## 8. Score / Result 分層

至少分成三個 Client data layer：

```text
Live round / mode-local
    +240600 / +240604

Server-provided player/result synchronization
    F6DCF8 / F6DCFC

Local result-screen My K/D
    +60150 / +60151
```

不能建立一個 global `KillDeath` 欄位讓所有 packet 共用。[C]

完整證據由 [`Result_Quest_Stats.md`](Result_Quest_Stats.md) 維護；其中包含 `269 subtype 7` producer/consumer evidence。[C]

## 9. Profile / Economy / Inventory

```text
PlayerProfile
├─ CharacterAppearanceState
├─ ItemCollection
│    └─ OwnedItem
│         ├─ Identity
│         ├─ ItemAssociatedValues
│         └─ DurabilityState
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
├─ SwitchWeaponSlot
├─ ItemSlotToClient[9]
└─ ProfileEconomy
     ├─ PG
     ├─ CASH
     └─ CP
```

詳細 domain model：[`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md)。

`198/200/203/218/220/221` wire codec：[`ClientData_Protocol.md`](ClientData_Protocol.md)。

## 10. Network boundary

Server 至少維持：

```text
TCP GameRule / Room control
TCP Y_TCP_INF gameplay/event
TCP dropped-world-object / pickup events
UDP real-time gameplay
```

它們的 opcode namespace、frame、serializer/parser、queue 與 state application 不可因最後都修改 `PlayerSlot` 就合併。[C]

Transport：[`Network_Protocol.md`](Network_Protocol.md)
Room packet：[`Room_Channel_GameRule_101_221_Field_Evidence.md`](Room_Channel_GameRule_101_221_Field_Evidence.md)
Gameplay：[`Gameplay_Network.md`](Gameplay_Network.md)
UDP movement：[`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)

## 11. Y_TCP_INF Server abstraction

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
```

不要先建立：

```text
DamagePacket
KillPacket
```

因 165/166 是 polymorphic gameplay family。[C]

詳細證據：[`Gameplay_Network.md`](Gameplay_Network.md)。

## 12. Dropped-world-object abstraction

```text
DroppedWorldObject
├─ InstanceId
├─ ResourceOrActionId
├─ Transform / raw spatial state
└─ UnknownState
```

`InstanceId != ResourceOrActionId`。[C]

具體 960–963 wire/state 由 [`Gameplay_Network.md`](Gameplay_Network.md) 維護。

## 13. Combat state boundary

Combat Server abstraction 保持：

```text
DamageInput
├─ Source
├─ Target
├─ RawValue
├─ HitResult
├─ ModifierContext
└─ VariantContext
```

但：

```text
HitDetectionResult
    ≠ DamageInput
    ≠ authoritative DamageResult
```

Client 目前可確認存在：

```text
local hit detection
→ damage/event construction
→ 165 request
```

是否所有 mode 的最終 damage 都由同一 authority path 決定，仍 `[OPEN]`。[C]

詳細證據：[`Gameplay_Network.md`](Gameplay_Network.md) 的 Combat 章節。

## 14. Room setting → MatchRuntime

```text
UI selector
    ↓
OptionValue validation
    ↓
Room state
    ↓
Start precondition
    ↓
CGameRule / ModeRuntime
```

Mode-specific：

```text
Win condition
Round condition
Time condition
Objective
Spawn rule
Team aggregation
```

由 [`Room_GameRule_Mode.md`](Room_GameRule_Mode.md) 解譯，不由 generic Room parser 自行決定。

## 15. Evidence → Server contract

當新證據出現：

```text
1. 更新對應 wire/domain 主文件
2. 若跨多子系統成立，再更新本文件抽象
3. 不在本文件建立第二份 Packet / Field truth
```

最低條件：

```text
serializer/parser 已閉合
+
caller/consumer data-flow 一致
+
必要時 Resource/Wiki 交叉驗證
```

## 16. 目前禁止的 Server 過早簡化

```text
PlayerId == SlotIndex
OptionIndex == OptionValue
Kill == TeamKills
165 == DamagePacket
166 == DamageAck
RoundIndex == ElapsedTime
Client object offset == wire offset
DroppedObjectInstanceId == ResourceOrActionId
HitDetectionResult == DamageResult
```

## 17. 下一個跨層閉合目標

```text
Session
  ↓
Room
  ↓
PlayerSlot[16]
  ↓
GameRule / MatchRuntime
  ↓
Gameplay / Combat / UDP
  ↓
Live state
  ↓
Result / Quest
  ↓
Profile / Inventory / Economy
```

下一階段只在有新證據時細化這張 graph；packet bytes、field semantics 與單一函式證據仍回到其各自主文件。
