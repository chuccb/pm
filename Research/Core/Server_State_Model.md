# PaperMan Server State Model（2016 日本版最終 Client）

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年結束營運時的最終 Client。
> 文件角色：只保存跨 Packet／跨子系統的 Server reconstruction 抽象模型，不重新複製單一封包欄位或單一功能文件的詳細證據。

## 1. 模型原則

Server reconstruction 必須嚴格區分：

```text
Client runtime field
    ≠
wire field
    ≠
server semantic field
```

因此未知欄位保持：

```text
unknown_*
*_value
selector_value
packed_flags
```

只有跨來源證據真正閉合後才升級 public semantic。

## 2. Server 的核心邊界

目前最小可行抽象：

```text
GameServer
├─ Session[]
├─ Room[]
└─ MatchRuntime[]
```

三者責任不同：

```text
Session
    = connection / identity / current room

Room
    = lobby/game-room configuration + player slots

MatchRuntime
    = in-game mode / round / objective / result state
```

不能把三者壓成單一 `Player` 或單一 connection state。

## 3. Session

最小模型：

```text
Session
├─ Connection
├─ PlayerId
├─ CurrentRoomId
└─ ConnectionState
```

Client evidence 明確要求 Server 另外保存：

```text
PlayerId ≠ SlotIndex
```

相關跨層證據入口：

```text
Room_Lobby_GameRule.md
Network_Protocol.md
Gameplay_Network.md
```

## 4. Room

最小模型：

```text
Room
├─ GameMode
├─ MapSelectorValue
├─ RuleSelectorValue
├─ ObjectSelectorValue
├─ TimeSelectorValue
├─ PackedRoomFlags
├─ MasterPlayerId
├─ PlayerSlot[16]
└─ RoomPhase
```

selector 必須保留兩層：

```text
OptionIndex
OptionValue
```

不能只保存 UI index。

完整 evidence：

```text
Room_Lobby_GameRule.md
Room_Settings_Packets.md
Room_Channel_GameRule_101_192_Field_Evidence.md
```

## 5. PlayerSlot[16]

Client 存在固定 16-slot player model，因此 Server 第一階段也應採固定容量抽象：

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

`TeamId`、`GroupId` 與其它 relation-like state 目前不要過早合併成單一欄位。

詳細研究入口：

```text
Room_Lobby_GameRule.md
```

## 6. Room → Match 的生命週期

跨文件目前最可信的狀態骨架：

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

跨層 graph 由：

```text
Room_Lobby_GameRule.md
Gameplay_Network.md
Result_Quest_Stats.md
```

共同支撐。

## 7. MatchRuntime

最小抽象：

```text
MatchRuntime
├─ Phase
├─ GameMode
├─ MapValue
├─ TimeLimit
├─ ElapsedTime
├─ RoundIndex
├─ RoundState
├─ ObjectiveState
├─ SpawnState
├─ TeamState
├─ PlayerRuntime[16]
└─ ResultState
```

`RoundIndex` 與 `ElapsedTime` 必須是可分離欄位：不同模式的 Client UI 與 GameRule 行為同時存在時間型與回合型進度。

## 8. Score / Result 分層

至少分開三個 Client data layer：

```text
Live round / mode-local
    +240600 / +240604

Server-provided player/result synchronization
    F6DCF8 / F6DCFC

Local result-screen My K/D
    +60150 / +60151
```

因此 Server model 不應建立單一 `KillDeath` 欄位並讓所有 packet 直接共用。

詳細 evidence：

```text
Gameplay_Network.md
TCP_269_Subtype7_Field_Detail.md
Result_Quest_Stats.md
```

## 9. Economy / Profile state

帳戶經濟資料是獨立於 Live combat state 的一層：

```text
ProfileEconomy
├─ PG
├─ CASH
└─ CP
```

目前 Client 已直接閉合：

```text
EE8D18 → PG
ArgList → CASH
EE8D1C → CP / COUPON UI
```

205/207 等 ClientData／collection synchronization 也會同步其中部分值。

詳細欄位證據：

```text
Currency_State_Field_Evidence.md
Character_Inventory_Equipment.md
MyInfo_198_ClientData_Field_Schema.md
```

## 10. Character / Inventory / Loadout 分層

Server 不應把角色、物品與武器視為同一張 flat inventory table：

```text
CharacterState
    ↓
Appearance / Avatar state

InventoryState
    ↓
OwnedItem[...]

LoadoutState
    ↓
Primary / Secondary / Melee / Throw
```

角色複合資源、物品集合與武器裝備都有不同 Client data structure。

詳細資料：

```text
Character_Inventory_Equipment.md
MyInfo_198_ClientData_Field_Schema.md
ClientData_Shared_Decoder_Field_Evidence.md
```

## 11. Network boundary

Server 至少維持三個獨立 network families：

```text
TCP GameRule / Room control
TCP Y_TCP_INF gameplay/event
UDP real-time gameplay
```

它們的：

```text
opcode namespace
framing
serializer/parser
queueing
state application
```

不可因最終都修改 `PlayerSlot` 就共用同一 packet abstraction。

詳細資料：

```text
Room_Channel_GameRule_101_192_Field_Evidence.md
Gameplay_Network.md
Network_Protocol.md
UDP_Move_Inf_DeepEvidence.md
```

## 12. Y_TCP_INF 的 Server 抽象

第一階段只需要：

```text
YTcpInfRequest
├─ Opcode = 165
├─ Subtype
└─ VariantPayload
```

不要預先建立：

```text
DamagePacket
KillPacket
```

因 Client 已確認 165 是 polymorphic family，至少包含：

```text
MultiDamage
BotSuicide
Normal damage
Mine/Bomb damage
```

完整 165/166 事件、parser、sender 與 state evidence 由：

```text
Gameplay_Network.md
```

維護。

## 13. Room settings → MatchRuntime

基本資料流：

```text
UI selector state
    ↓
OptionValue validation
    ↓
Room state
    ↓
Start precondition
    ↓
MatchRuntime initialization
```

尤其：

```text
MapSelectorValue
RuleSelectorValue
ObjectSelectorValue
TimeSelectorValue
PackedRoomFlags
```

都不應直接等同於最終 mode semantic；應交給 `ModeRule` / `GameRule` 層解譯。

## 14. Mode-specific state

不同 mode 的：

```text
Win condition
Round condition
Time condition
Objective
Spawn rule
Team aggregation
```

必須是 mode-specific rule 的責任，而不是塞入通用 Room parser。

對應研究：

```text
Mode_Rules_And_Options.md
Room_Lobby_GameRule.md
Gameplay_Network.md
```

## 15. Evidence → Server contract 的升級規則

當新的 Client / Resource / Wiki 證據出現時：

```text
1. 更新對應 packet / field 主文件
2. 若跨多個子系統成立，再更新本文件抽象
3. 不在本文件新增第二份欄位真相
```

可升級為 Server contract 的最低條件：

```text
Client parser / serializer 已閉合
        +
caller / consumer data-flow 一致
        +
必要時 Resource / Wiki 交叉驗證
```

## 16. 目前禁止的 Server 過早簡化

```text
PlayerId == SlotIndex
RoomSelectorIndex == SelectorValue
Kill == TeamKills
165 == DamagePacket
166 == DamageAck
RoundIndex == ElapsedTime
Client object offset == wire offset
```

任何以上等式若沒有新的直接證據，都不應進入正式 Server protocol contract。

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
Y_TCP_INF / UDP gameplay
  ↓
Live state
  ↓
Result / Quest / Profile synchronization
```

下一階段應優先把這張 graph 與具體 packet sender/receiver、Resource identity、Wiki behavior 一一接上；本文件只維護 graph，不重新複製下層證據。
