# PaperMan Server State Model（2016 日本版最終 Client）

> 研究日期：2026-09-16
>
> 本文件不是重新猜一套 server architecture，而是把目前已由 `PaperMan.exe.c`、`Extracted/`、既有 Research 與日本 Wiki 交叉收斂的 Client state，整理成可直接用於 Server reconstruction 的最小 State Model。
>
> 目標版本：**日本版 PaperMan 2016 年結束營運時的最終 Client**。更早版本只作歷史差異對照，不混入本模型。

## 1. 核心原則

Server model 必須區分三件事：

```text
Client runtime field
    !=
wire field
    !=
server semantic name
```

因此未封死的欄位一律使用：

```text
*_value
unknown_*
packed_flags
selector_value
```

而不是依 packet/function 名稱直接命名。

---

## 2. Room 狀態

目前可以安全抽象成：

```text
Room
├─ GameMode
├─ MapSelectorValue
├─ RuleSelectorValue
├─ ObjectSelectorValue
├─ TimeSelectorValue
├─ ItemEnabled
├─ MapGimmickOrRelatedFlag      // currently bit1, semantics not fully closed
├─ TeamBalanceEnabled
├─ TeamShuffleEnabled
├─ DamageRoomState               // independent room state
├─ UserSlots / capacity state
├─ ClanNoSkill / NormalNoSkill   // separate paths
├─ ChatMode
├─ MasterPlayerId                // semantic name still requires final xref closure
└─ LocalRoom / other room flags
```

### 2.1 Selector value 與 UI index 必須分離

Generic selector entry：

```c
return *(*(this + 33) + 40 * index + 36);
```

因此：

```text
OptionIndex != OptionValue
```

Server 不應只保存一個 `RuleIndex`，而應至少保留：

```text
RuleOptionIndex
RuleOptionValue
```

同理適用 Map / Object / Time。

詳細資料流見：

- `Research/Core/Room_Settings_Packets.md`
- `Research/Core/Mode_Option_Tables.md`

---

## 3. Room setting packet boundary

目前已閉合的 Room-setting wire model：

```text
121 GR_MAPCHANGE_REQ
    u8 map_value

122 GR_MAPCHANGE_ACK
    u8 map_value

169 GR_RULECHANGE_REQ
    u8 rule_value

170 GR_RULECHANGE_ACK
    u8 rule_value

171 GR_WINCHANGE_REQ
    u16 object_selector_value

172 GR_WINCHANGE_ACK
    u16 object_selector_value

173 GR_TIMECHANGE_REQ
    u8 time_value

174 GR_TIMECHANGE_ACK
    u8 time_value

175 GR_ITEMCHANGE_REQ
    u8 packed_flags

176 GR_ITEMCHANGE_ACK
    u8 packed_flags
```

目前安全語義：

```text
121/122 -> GAMEROOM_SCROLL_MAP
169/170 -> GAMEROOM_SCROLL_RULE
171/172 -> GAMEROOM_SCROLL_OBJECT
173/174 -> GAMEROOM_SCROLL_TIME
175/176 -> GAMEROOM_ITEM + map/gimmick-related bit
```

### 3.1 `171/172` 不可直接命名 `KillLimit`

Client receive path 直接進入 `GAMEROOM_SCROLL_OBJECT`，並保存到 Room/Player object `+144`。

所以 Server model 應先保存：

```text
ObjectSelectorValue: ushort
```

之後再由：

```text
GameMode + ObjectSelectorValue
    -> concrete Objective / Win Condition
```

解析為 Kill / Round / cc / Point 等 mode-specific meaning。

這樣才能避免同一 packet name 在不同歷史 mode schema 間造成錯誤耦合。

---

## 4. 16 個 Player Slot

Client 有明確固定的 16-slot model。最重要的是：

```text
SlotIndex
!=
PlayerId
!=
Group/Team relation
```

建議 Server model：

```text
PlayerSlot[16]
├─ SlotIndex
├─ Occupied
├─ PlayerId
├─ TeamId / GroupId
├─ ReadyState
├─ ConnectionState
├─ InGameState
├─ CharacterState
├─ LoadoutState
├─ Position / movement state
├─ Combat state
└─ Score
```

### 4.1 Local player mapping

Client 會掃描 slot table，把 global/local player identifier 映射到實際 slot，因此 Server 不應假設：

```text
PlayerId == SlotIndex
```

### 4.2 Team / Group 不應過度合併

Client 至少存在多個 group-like relation helpers，並不是所有 group 欄位都是同一個 TeamId。

因此在 Server implementation 第一階段：

```text
TeamId
GroupId
Relation / Party-like state
```

保持可分離，直到更多 C data flow 關閉。

詳細來源：`Research/Core/Player_Slot_Team.md`。

---

## 5. Player Score State

目前 Client per-player score storage 已閉合：

```text
PlayerSlot.Score
├─ Kill   = dword_F6DCF8[60195 * slot]
└─ Death  = dword_F6DCFC[60195 * slot]
```

Result/high-score comparator：

```text
Kill descending
    -> Death ascending
        -> dword_F33184 ascending
```

第三鍵 `dword_F33184` 的正式語義仍 OPEN。

### 5.1 Team mode 的重要分層

Team Survival 的 Wiki 規則是 team cumulative Kill，但 Client 的 `F6DCF8/F6DCFC` 仍是 per-player storage。

所以 Server 必須採：

```text
PlayerScore
    -> ModeRule aggregation
        -> TeamScore / RoundResult / GameResult
```

而不是把 `Kill` field 改名成 `TeamKills`。

### 5.2 score mutation source 尚未閉合

目前可以確認：

```text
Kill / Death 是 synchronized player state
```

但尚未找到足夠證據證明：

```text
165 Y_TCP_INF_REQ
    -> F6DCF8++ / F6DCFC++
```

因此第一版 Server 應把：

```text
Score mutation source = unresolved server-authoritative event
```

保留為獨立層，不在 protocol parser 中硬接。

詳細來源：`Research/Core/Score_State.md`。

---

## 6. GameRule lifecycle state

目前最可信的 state machine 骨架：

```text
ROOM
  |
  | 127 GR_READY_REQ
  v
READY / player-state synchronization
  |
  | 129 GR_START_REQ + u8 start_parameter
  v
START_REQUESTED
  |
  | 130 GR_START_ACK + player/game synchronization
  v
MATCH_INITIALIZING
  |
  | CGameRule::NewGameStart
  v
IN_GAME / ROUND_RUNTIME
  |
  +--> gameplay events
  +--> round transitions
  +--> timeout / objective completion
  v
MATCH_ENDING
  |
  +--> 133 GR_END_REQ
  +--> 123 GR_LEAVE_REQ
  v
ROOM / POST_MATCH
```

注意：

```text
133 End
!=
123 Leave
```

Client 有明確 branch 選擇兩者，不能在 Server API 層合併成單一 `LeaveGame()`。

詳細資料：`Research/Core/GameRule_Lifecycle.md`。

---

## 7. `NewGameStart` 的 server implication

Client `CGameRule::NewGameStart` 會集中重設大量 state：

```text
+56 = 5000
+48 = 0
+8  = 0
+12 = 0
+20 = 0
+24 = 0
```

並呼叫多個 initialization routine。

其中 `+56 = 5000` 目前不能直接命名為 5 秒倒數；必須等待 `GR_STARTTIME_REQ/ACK`、tick routine、HUD timer 與 caller 完成交叉驗證。

因此 Server model 只定義：

```text
MatchRuntime initialization state
```

不提前把 `5000` 寫成 public protocol constant。

---

## 8. Gameplay / Combat 邊界

目前最重要的 network split：

```text
TCP GameRule / room control
    |
    +-- Ready / Start / End / Room settings

TCP Y_TCP_INF gameplay events
    |
    +-- Damage
    +-- MultiDamage
    +-- Mine/Bomb damage
    +-- Bot suicide

UDP gameplay/network event family
    |
    +-- separate dispatcher / opcode space
```

TCP 與 UDP 必須保持不同 parser / dispatcher，不可以在 Server protocol abstraction 中假設共用 opcode namespace。

### 8.1 `165 Y_TCP_INF_REQ`

165 是 subtype-driven polymorphic packet：

```text
opcode = 165
payload[0] = variant/source-like byte
payload[1] = subtype/event discriminator
remaining = subtype-specific payload
```

至少已確認：

```text
subtype 16 -> MultiDamage variant
subtype 21 -> BotSuicide variant
```

Normal damage、Mine/Bomb damage 也使用 165。

所以 Server implementation 第一版應使用：

```text
YTcpInfRequest
├─ Opcode
├─ Subtype
└─ VariantPayload
```

而不是：

```text
DamagePacket
```

詳細來源：`Research/Core/Y_TCP_INF_Damage.md`、`Research/Core/Y_TCP_INF_Handler_Details.md`。

---

## 9. Damage pipeline

目前 Client damage calculation 已收斂為：

```text
source slot
   ↓
target slot
   ↓
modifier entry resolution
   ↓
damage increase / reduction
   ↓
mode / variant multiplier
   ↓
byte quantization
   ↓
Y_TCP_INF_REQ (165)
```

其中 modifier table 與 object `+548` 等欄位的正式 Resource identity 尚未完全閉合。

因此 Server 不能只保存：

```text
WeaponDamage
```

至少需要：

```text
DamageInput
├─ source
├─ target
├─ base/value
├─ variant/subtype
├─ modifier context
└─ mode/map context
```

詳細來源：`Research/Core/Damage_Calculation.md`。

---

## 10. Objective / Mode layer

Mode-specific rules 不應直接進入通用 Room parser。

目前已直接從 Client lobby builder 確認：

```text
個人サバイバル
    20/30/40/50 Kill

チームサバイバル
    50/100/200 Kill

チーム戦術モード
    3/5/7/10/12/15 Round

爆破ミッション
    3/5/7/10/12/15 Round

スチールモード
    1000/2000/3000 cc

パルプ＆ロール
    15/30/45

new占領モード
    300/500/700/1000 Point

サッカーモード
    Time 7/10/15/20
    Goal 5/7/10/15

練習モード
    999 Kill
```

日本 Wiki 的玩家規則與其中多組值相互吻合；例如個人、團隊生存、團隊戰術、Steel、Pulp & Roll、new占領、Soccer 的最終頁面均有相應設定。Wiki 同時記錄部分異常／歷史差異，因此這些行為不可全部等同為「正常 Server contract」。

來源：`Research/Core/Mode_Rules.md`、`Research/Core/Mode_Option_Tables.md`、日本 Wiki `MAP・ルール詳細`。

---

## 11. 2016 final Wiki 的重要 Server constraints

日本 Wiki `MAP・ルール詳細` 的最終內容提供多個可用於驗證 Server/UI state 的外部 constraint：

```text
Room information
├─ mode
├─ map
├─ win condition
├─ time limit
├─ item/no-item
├─ team balance
├─ team shuffle
├─ local rule
├─ knife battle
├─ crazy play
└─ no-skill
```

而進度顯示依 mode 分成：

```text
elapsed-time display
    個人 / Team Survival / Steel / Pulp & Roll / Soccer

round-progress display
    Team Tactical / Bomb / Occupy / PVE
```

這意味 Server → Client 的 room/game state 必須允許：

```text
ElapsedTime
RoundIndex
```

同時存在，而不能用單一 `Progress` field 取代。

Wiki 另明確指出：

```text
Knife Battle
    -> current Room UI description restricts this option to Soccer

Practice
    -> special lobby filtering behavior
```

這表示 option capability 也屬於 mode-specific validation，而不是所有 room flags 都是全球可用。

---

## 12. Recommended reconstruction objects

第一階段可用以下模型，所有 unresolved 欄位刻意保留：

```text
GameServer
├─ Session[]
├─ Room[]
└─ MatchRuntime[]

Session
├─ Connection
├─ PlayerId
└─ CurrentRoomId

Room
├─ GameMode
├─ MapSelectorValue
├─ RuleSelectorValue
├─ ObjectSelectorValue
├─ TimeSelectorValue
├─ PackedRoomFlags
├─ MasterPlayerId
└─ PlayerSlot[16]

PlayerSlot
├─ SlotIndex
├─ PlayerId
├─ Occupied
├─ TeamId
├─ GroupId
├─ Ready
├─ InGameState
├─ Character
├─ Loadout
├─ PositionState
├─ CombatState
└─ Score

Score
├─ Kill
├─ Death
└─ UnknownTieBreak

MatchRuntime
├─ Phase
├─ RoundIndex
├─ RoundWinCount[team/group]
├─ ElapsedTime
├─ TimeLimit
├─ ObjectiveValue
├─ ObjectiveState
├─ SpawnState
├─ Bomb/Pulp/Occupy/Soccer state as mode-specific extension
└─ Result
```

這不是宣稱 Client 已完全恢復所有 server object，而是目前證據可支持的最小 implementation boundary。

---

## 13. 已閉合 / 半閉合 / OPEN

| Area | Status | Current conclusion |
|---|---|---|
| 16 player slots | A/B | fixed 16-slot runtime model |
| PlayerId vs SlotIndex | A/B | must remain separate |
| K/D storage | A | `F6DCF8/F6DCFC` |
| K/D comparator | A | Kill ↓, Death ↑, third key ↓ |
| Room selector index/value | A | separate, value at generic entry +36 |
| 121/122 map | A/B | map selector value |
| 169/170 rule | A/B | rule selector value |
| 171/172 object | A/B | 16-bit object selector value |
| 173/174 time | A/B | time selector value |
| 175/176 flags | A/B | bit0 Item; bit1 map/gimmick-related unresolved |
| Ready/Start lifecycle | A/B | 127 → 128 → 129 → 130 |
| NewGameStart | A | match initialization root |
| 165 subtype architecture | A/B | polymorphic gameplay event request |
| Damage modifiers | B | calculation pipeline recovered, resource identity incomplete |
| Score mutation source | OPEN | synchronization proven, increment source not proven |
| `GR_STARTTIME 137/138` semantics | OPEN | registration only so far |
| 124/134 full transition | OPEN | receiver identified, state machine incomplete |
| 136 full slot semantics | OPEN | large layout sync, field semantics incomplete |
| 171/172 concrete mode meaning | OPEN | object selector closed, mode mapping not yet closed |
| 175/176 bit1 semantic | OPEN | map/gimmick-related data flow only |
| Bomb / round / respawn server contract | OPEN | Wiki constraints exist, C runtime closure incomplete |

---

## 14. Next highest-value closure chain

```text
GR_STARTTIME 137/138
    ↓
NewGameStart +56 / tick routine
    ↓
countdown / start transition

171/172 ObjectSelectorValue
    ↓
mode-specific lobby builder
    ↓
concrete objective / win condition

175/176 bit1
    ↓
sub_728D90
    ↓
GAMEROOM_GIMMICK
    ↓
map/resource semantics

165/166
    ↓
combat / state synchronization
    ↓
score mutation source
    ↓
round / objective result
    ↓
124/134
```

這四條鏈應優先於新增更多泛化文件；每閉合一條，就回寫對應既有 Research，而不是另外建立重複摘要。
