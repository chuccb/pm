# Room／GameRule／Mode／Selector 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 Channel／Lobby／Room／PlayerSlot、Team／Group、Map、Room settings、ModeId、OptionIndex／OptionValue、GameRule lifecycle、Mode-specific rules 與 MatchRuntime。`101–221` 的逐 byte packet evidence 由 [`Room_Channel_GameRule_101_221_Field_Evidence.md`](Room_Channel_GameRule_101_221_Field_Evidence.md) 維護。

## 1. 一眼看懂

```text
Channel / Lobby
    ↓
Room
    ↓
PlayerSlot[16] / Team / Master
    ↓
Room selector
    ├─ Map
    ├─ Rule
    ├─ Object
    ├─ Time
    └─ packed flags
    ↓
ModeId + OptionValue
    ↓
CGameRule
    ↓
MatchRuntime
    ↓
Gameplay / Result
```

最重要的 namespace separation：

```text
PlayerId       ≠ SlotIndex
ModeId         ≠ OptionIndex ≠ OptionValue
Client offset  ≠ wire offset ≠ server object layout
```

## 2. Channel → Lobby → Room

Client object layer 可直接看到：

```text
CLobbyLogin
CLobbyGameRoom
CLobbyTournamentGameRoom
CGameRule
```

這是 Client-side object/state layering，不等同於 Server process 或 TCP connection topology。[C]

目前最可靠的 Client-side lifecycle：

```text
Login
  ↓
Channel / Lobby
  ↓
Room list
  ↓
建立／進入 Room
  ↓
GameRoom / TournamentGameRoom
  ↓
PlayerSlot[16]
  ↓
Room settings
```

2014-06-25 Wiki 有「チャンネル（待機ロビーとゲームルーム）の紐付けの解消（サーバーチャンネル統合）」歷史資料，因此 2016 Final 不應直接套用更早期的 Server Channel topology。[WIKI]

## 3. 固定 16-slot Player 模型

大量 Client 函式固定掃描：

```c
for (i = 0; i < 16; ++i)
```

相關 player storage 包含：

```text
byte_F33120
byte_F6D9E4
byte_F6DD11
F6DCF4 / F6DCF8 / F6DCFC
```

因此 Server model 應明確分離：

```text
PlayerId
SlotIndex
Occupied / Active
Team / Group relation
```

`sub_67D110()`、`sub_67D310()` 等資料流進一步顯示 PlayerId／identity 與 slot 不可直接視為同值。[C]

### 3.1 Team／Group

主要 helper：

```text
sub_67D240 → local group/team-like value
sub_67D520 → target group/team-like value
sub_67D3F0 → comparison
sub_67D600 → relation A equality
sub_67D630 → relation B equality
```

至少存在兩種 relation-like value；尚不足以把所有值統一命名成正式 TeamId。[C][OPEN]

### 3.2 Active / Occupied

`sub_67D310(slot)` 一般路徑：

```text
slot >= 16             → 0
byte_F6D9E4[slot] != 0 → 0
byte_F6DD11[slot] != 0 → 0
local player           → 2
otherwise              → 1
```

因此：

```text
0 → 非一般 active participant
1 → active participant，非 local
2 → active participant，local
```

這不能簡化為 `Room.PlayerCount`。[C]

## 4. Room settings：Selector 是 Index 與 Value 的兩層模型

多個 scroll control 使用 40-byte entry：

```text
entry stride = 40 bytes
entry value  = +36
```

因此：

```text
OptionIndex  = UI list position
OptionValue  = actual selected/transmitted value
```

不可假設兩者相等。[C]

Room UI 至少包含：

```text
GAMEROOM_SCROLL_MAP
GAMEROOM_SCROLL_RULE
GAMEROOM_SCROLL_OBJECT
GAMEROOM_SCROLL_TIME
GAMEROOM_ITEM
GAMEROOM_GIMMICK
GAMEROOM_TEAMBALANCE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_DAMAGEROOM
GAMEROOM_USERSLOTS
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_CHATMODE
GAMEROOM_MASTERROOM
GAMEROOM_LOCALROOM
```

Wiki 的 Room information 同樣存在 mode、map、victory condition、time、item/no-item、team balance、team shuffle、local rule、knife、crazy、no-skill 等玩家可見設定。[WIKI]

## 5. Map selector：121/122/129

`121/122`：

```text
121 GR_MAPCHANGE_REQ → u8 map_value
122 GR_MAPCHANGE_ACK → u8 map_value
```

ACK 經 `sub_42FC50()` 取得 `GAMEROOM_SCROLL_MAP`，以 `sub_4387B0()` 找 `entry value == map_value`，再 `sub_6B9B10()` 更新 UI/state。[C]

Room/player object：

```text
+130 = current_map_selector_value
```

不能僅因此命名 `map_id`。[C]

Resource chain：

```text
Extracted/map/maplist.dat
    ↓
GAMEROOM_SCROLL_MAP
    ↓
entry value
    ↓
121/122
```

`maps\\TU_01_tutorial.pmm` 等實際 map asset 可在 Extracted map domain 中找到。[RES]

Start path `sub_437060()` 也會從 `GAMEROOM_SCROLL_MAP` 取 value，再形成 `129 GR_START_REQ` 的 byte；因此 129 不是單純 generic start flag。[C][OPEN]

## 6. Rule／Object／Time selector packets

### 6.1 Rule：169/170

```text
169 GR_RULECHANGE_REQ → u8 rule_value
170 GR_RULECHANGE_ACK → u8 rule_value
```

`sub_42FE50()`：

```text
rule_value
  ↓
sub_426930
  ↓
GAMEROOM_SCROLL_RULE / room state
  ↓
entry value match
  ↓
UI selection
```

因此 wire value 與 UI index 必須分開。[C]

### 6.2 Object：171/172

```text
171 GR_WINCHANGE_REQ → u16
172 GR_WINCHANGE_ACK → u16
```

`sub_430720()` 實際操作：

```text
GAMEROOM_SCROLL_OBJECT
Room/Player object +144
```

所以目前只能叫：

```text
object_selector_value
```

不可因 `GR_WINCHANGE` 名稱自行命名 `kill_limit`／`round_limit`／`win_type`。[C][OPEN]

### 6.3 Time：173/174

```text
173 GR_TIMECHANGE_REQ → u8 time_value
174 GR_TIMECHANGE_ACK → u8 time_value
```

`sub_430920()`：

```text
Room/Player object +136 = current_time_selector_value
GAMEROOM_SCROLL_TIME
```

Server 應分開：

```text
TimeOptionIndex
TimeOptionValue
Duration
```

Wiki 顯示的「分鐘」是玩家層語意，不能直接覆蓋 wire value。[C][WIKI][OPEN]

### 6.4 Item：175/176 packed flags

```text
175 GR_ITEMCHANGE_REQ → u8 packed_flags
176 GR_ITEMCHANGE_ACK → u8 packed_flags
```

已閉合：

```text
bit 0 = GAMEROOM_ITEM on/off
bit 1 = map-dependent / gimmick-related flag candidate
bits 2..7 = OPEN
```

bit0 與 Wiki 的 `アイテム/ノーアイテム戦` 互相驗證。[C][WIKI][X]

`GAMEROOM_DAMAGEROOM` 有獨立 path，不得和 175/176 packed byte 共用 enum。[C]

### 6.5 No Skill / Team Balance / Team Shuffle

No Skill 在 Client 至少分：

```text
current object +188 == 2
    → GAMEROOM_CLAN_NOSKILL
else
    → GAMEROOM_NORMAL_NOSKILL
```

所以不是單一 global boolean。[C]

Team balance／shuffle 與 userslots 同屬 Room state machine，但 exact wire mapping 仍 OPEN。

### 6.6 Autochange

```text
177 GR_AUTOCHANGE_REQ
178 GR_AUTOCHANGE_ACK
```

目前只確認為獨立 Room-state family，完整 sender/receiver/state chain OPEN。[C][OPEN]

## 7. Ready → Start → GameRule

目前 Client lifecycle：

```text
Room
  ↓
127 GR_READY_REQ
  ↓
128 GR_READY_ACK
  ↓
129 GR_START_REQ
  ↓
130 GR_START_ACK
  ↓
137/138 Start-time layer
  ↓
184 End-loading layer
  ↓
188 Game-start layer
  ↓
CGameRule::NewGameStart
  ↓
Gameplay / Round
```

這是目前工作模型；137/138、184、188 的精確 timing relationship 仍需持續閉合。[C][OPEN]

## 8. NewGameStart

`CGameRule::NewGameStart` 會集中重設：

```text
+56 = 5000
+48 = 0
+8  = 0
+12 = 0
+20 = 0
+24 = 0
```

並呼叫：

```text
sub_709330
sub_89B200
sub_720820
sub_67E560
```

以及依 player distribution 更新：

```text
+81
+82
```

`+56 = 5000` 目前只叫 initialization time-like value；不能直接說是 5 秒倒數。[C][OPEN]

NewGameStart 不是單看總玩家數，會按 grouping/participant distribution 做條件判定。[C]

## 9. Change Slot／Master／Force Out／Leave／End

以下是獨立 lifecycle events：

```text
135/136 → Change Slot
189/190 → Change Master
131/132 → Force Out
123/124 → Leave
133/134 → End
```

雖可能共同修改 Player／Slot／Team／Room state，但不能合併成一個 generic operation。

尤其：

```text
LeaveRoom()
    ≠
EndGame()
```

Server transition 必須分開。

## 10. Client Mode namespace

目前 factory／lobby classes：

```text
0  CyTeamMatchModeLobbyUI
1  CyIndividualSurvivalModeLobbyUI
2  CyDefuseBombModeLobbyUI
3  CyTeamSurvivalModeLobbyUI
4  CyStealModeLobbyUI
5  CyPracticeModeLobbyUI
6  CyTutorialModeLobbyUI
7  CyChattingRoomModeLobbyUI
8  CyPulpnRollModeLobbyUI
9  CyGunShootingModeLobbyUI
10 CyOccupyModeLobbyUI
11 CyAIMultiModeLobbyUI
12 CyTeamSoccerModeLobbyUI
13 CyOccupyRenewalModeLobbyUI
15 CyWeaponTestModeLobbyUI
```

這只是 Client mode namespace，不可直接當 packet selector value。[C]

## 11. Final Client 的 mode rule values

### Team Match

```text
Round = 3 / 5 / 7 / 10 / 12 / 15
```

Client builder：`CyTeamMatchModeLobbyUI::sub_74F8B0()`。[C]
Wiki 與 Client 一致。[WIKI][X]

### Individual Survival

```text
Kill = 20 / 30 / 40 / 50
```

Client：`CyIndividualSurvivalModeLobbyUI::sub_750220()`。[C][WIKI][X]

### Team Survival

```text
Kill = 50 / 100 / 200
```

Client 與現行 Wiki 一致。[C][WIKI][X]

重要歷史反證：2010-02-07 日本 `ver.Gp` 曾使用：

```text
染料ポイント 1000 / 2000 / 3000cc
時間 10 / 20 / 30 分
```

所以：

```text
ModeName != immutable RuleSchema
```

### Pulp & Roll

```text
Time = 15 / 30 / 45
Resource keys = 0x24 / 0x2D / 0x395
```

Client 與 Wiki 一致。[C][WIKI][X]

Runtime 尚待 pulp object、carrier、A/B/C objective、phase、point producer、暴走、match end。[OPEN]

### Steel

```text
Objective = 1000 / 2000 / 3000 cc
```

Client：`CyStealModeLobbyUI::sub_751D20()`。[C]
Wiki／Runtime objective 尚待完整閉合。[WIKI][OPEN]

### Occupy Renewal

```text
Point = 300 / 500 / 700 / 1000
Resource keys = 0x53B / 0x53C / 0x53D / 0x53E
```

Client／Wiki values 一致；resource key 的日文 literal OPEN。[C][RES][WIKI][X]

### Occupy

```text
Round = 1 / 2 / 3
```

與 Team Match 的 Round family 分開。[C]

### Practice / Tutorial

```text
999 Kill
```

Practice 不依一般 `Kill >= RuleValue` 正常結束，因此 Server 需要 mode-specific `IsMatchOver()` policy。[C][WIKI]

### Soccer

Time：

```text
7 / 10 / 15 / 20
```

Goal：

```text
5 / 7 / 10 / 15
```

Client 使用兩套 option builder，因此：

```text
TimeOption ≠ GoalOption
```

[C][WIKI][X]

## 12. ModeRuntime 模型

```text
ClientBuild / ProtocolRevision
    ↓
ModeId
    ↓
Room selectors
    ├─ Map.OptionIndex / OptionValue
    ├─ Rule.OptionIndex / OptionValue
    ├─ Object.OptionIndex / OptionValue
    ├─ Time.OptionIndex / OptionValue
    └─ PackedFlags
    ↓
ModeRuntime
    ├─ Phase
    ├─ RoundIndex
    ├─ ElapsedTime
    ├─ ObjectiveValue
    ├─ ObjectiveState
    └─ MatchEndState
```

不同 mode 的 win condition、round condition、time condition、objective、spawn rule、team aggregation 必須由 mode-specific rule 負責，不塞進 generic Room parser。[C][OPEN]

## 13. Server reconstruction

Room：

```text
Room
├─ RoomSettings
├─ PlayerSlot[16]
├─ Team / Group
├─ MasterPlayerId
└─ RoomPhase
```

Match：

```text
MatchRuntime
├─ GameMode
├─ MapValue
├─ RuleValue
├─ ObjectValue
├─ TimeValue
├─ RoundState
├─ ObjectiveState
├─ PlayerRuntime[16]
└─ ResultState
```

Packet codec 再分：

```text
121/122 → map
169/170 → rule
171/172 → object
173/174 → time
175/176 → packed flags
```

不要直接建模成：

```text
byte rule
byte time
ushort win
```

也不要把 `ModeId` 當成所有 rule selector 的唯一 namespace。[C]

## 14. 三方交叉驗證

### Map

```text
[C] selector + 121/122 + object state
[RES] maplist.dat + map assets
[WIKI] Room/map behavior
```

### Mode rules

```text
[C] mode builder concrete values
[WIKI] 玩家可見 rule values
[RES] selector/resource labels where available
```

三方一致時才提升為高可信 Client-compatible rule；不同版本資料不得無標記覆蓋 Final Client。[C][RES][WIKI][X]

## 15. 目前 OPEN 與最高價值追查

```text
P0  129 → 130 → 137/138 → 184 → 188 → NewGameStart precise timing graph
P0  171/172 object value → public objective/rule semantics
P0  mode-specific IsMatchOver / round transition
P1  169/170 rule value → exact mode/rule semantics
P1  173/174 time value → exact duration mapping
P1  175 bit1 → exact public label
P1  177/178 sender/receiver/state semantics
P1  Team balance / shuffle / No Skill wire mapping
P1  Bomb / Pulp / Steel / Occupy / Soccer runtime objective state
P2  historical rule divergence across builds
```

所有未確認值保持 raw／`[OPEN]`；不得為 Server 實作方便而填 `0`、固定常數或 guessed enum。

## 16. 相關文件

```text
Room_Channel_GameRule_101_221_Field_Evidence.md
    = 101–221 exact packet wire evidence

Gameplay_Network.md
    = 165/166 + 960–963 gameplay

Result_Quest_Stats.md
    = result / score / quest

Server_State_Model.md
    = cross-domain server abstraction
```
