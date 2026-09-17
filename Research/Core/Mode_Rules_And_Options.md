# 遊戲模式、勝負規則、Room Selector 與設定封包整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 ModeId、OptionIndex、OptionValue、Room selector、設定封包、模式規則、版本差異與 Runtime 待閉合項目。

## 1. 一眼看懂

本文件回答兩件彼此相連的事：

```text
Room UI 怎麼產生 selector value、如何送進 packet

以及

不同 Mode 如何解讀這些 value 成為規則
```

核心資料流：

```text
Room UI
  ↓
OptionIndex
  ↓
OptionValue
  ↓
Request / ACK
  ↓
Room state
  ↓
Mode / CGameRule
  ↓
Rule / Time / Objective
  ↓
MatchRuntime
```

因此：

```text
ModeId
    ≠
OptionIndex
    ≠
OptionValue
```

精確 top-level packet bytes 仍由 [`Room_Channel_GameRule_101_221_Field_Evidence.md`](Room_Channel_GameRule_101_221_Field_Evidence.md) 維護；本文件聚焦 selector/value 與其 mode semantics。[C]

## 2. Selector 的共同資料模型

多個 Room scroll control 使用同一種 entry：

```text
entry stride = 40 bytes
entry value  = +36
```

對應 Client：

```c
return *(*(this + 33) + 40 * a2 + 36);
```

因此 Server 必須保留：

```text
OptionIndex  = UI list position
OptionValue  = actual selected / transmitted value
```

不能假設兩者相等。[C]

## 3. Room UI 控制域

Client Room UI 明確包含：

```text
GAMEROOM_START
GAMEROOM_READY
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

Wiki 的 Room information 亦列出 mode、map、victory condition、time、item/no-item、team balance、team shuffle、local rule、knife、crazy、no-skill 等玩家可見設定。[WIKI]

這些 control 不應被視為單一 global option；不同 control 使用不同 selector 或 flag family。[C][WIKI]

## 4. Selector packet 對照

| Opcode | Packet | Wire | Client destination | 目前語意 |
|---:|---|---|---|---|
| 121 | `GR_MAPCHANGE_REQ` | `u8` | Map selector | `map_value` |
| 122 | `GR_MAPCHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_MAP` | `map_value` |
| 127 | `GR_READY_REQ` | 0 | Ready path | ready request |
| 129 | `GR_START_REQ` | `u8` | Start path | map-derived start parameter |
| 169 | `GR_RULECHANGE_REQ` | `u8` | `GAMEROOM_SCROLL_RULE` | `rule_selector_value` |
| 170 | `GR_RULECHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_RULE` | `rule_selector_value` |
| 171 | `GR_WINCHANGE_REQ` | `u16` | `GAMEROOM_SCROLL_OBJECT` | `object_selector_value` |
| 172 | `GR_WINCHANGE_ACK` | `u16` | `GAMEROOM_SCROLL_OBJECT` | `object_selector_value` |
| 173 | `GR_TIMECHANGE_REQ` | `u8` | `GAMEROOM_SCROLL_TIME` | `time_selector_value` |
| 174 | `GR_TIMECHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_TIME` | `time_selector_value` |
| 175 | `GR_ITEMCHANGE_REQ` | `u8` packed | `GAMEROOM_ITEM` + related state | bit0 Item；bit1 map/gimmick-related candidate |
| 176 | `GR_ITEMCHANGE_ACK` | `u8` packed | same | same |
| 177 | `GR_AUTOCHANGE_REQ` | OPEN | OPEN | independent room-state family |
| 178 | `GR_AUTOCHANGE_ACK` | OPEN | OPEN | independent room-state family |

完整 parser／serializer 實作與其它 101–221 packet 不在本文件重複。[C]

## 5. Map selector：121/122

Request：

```text
121 +0x00 u8 map_value
```

ACK：

```text
122 +0x00 u8 map_value
```

`sub_42FC50()` 取得 `GAMEROOM_SCROLL_MAP`，以 `sub_4387B0()` 尋找 `entry value == map_value`，再以 `sub_6B9B10()` 選中 UI item。[C]

Room/player object `+130` 保存：

```text
current_map_selector_value
```

目前不能僅以此命名 `map_id`。[C]

Resource 證據：

```text
Extracted/map/maplist.dat
    ↓
map entry / actual .pmm path
    ↓
GAMEROOM_SCROLL_MAP
    ↓
selector value
    ↓
121/122
```

例如 `maps\\TU_01_tutorial.pmm` 可在 map inventory 中找到。[RES]

因此 Map selector 是目前 Room 設定中最完整的 C／Resource／Wiki 閉環之一。[C][RES][WIKI][X]

## 6. Time selector：173/174

```text
173 GR_TIMECHANGE_REQ → u8 time_value
174 GR_TIMECHANGE_ACK → u8 time_value
```

ACK 經 `sub_430920()` 對應：

```text
Room/Player object +136 = current_time_selector_value
GAMEROOM_SCROLL_TIME
```

Client 用 selector value 反找 list index 並更新 UI。[C]

Server 必須分開：

```text
TimeOptionIndex
TimeOptionValue
Duration
```

即使 Wiki 顯示 `10/20/30 分` 等玩家可見數值，也不能直接把 packet byte 當分鐘數；wire value 與 display duration 不是同一層。[WIKI][OPEN]

## 7. Rule selector：169/170

```text
169 GR_RULECHANGE_REQ → u8 rule_value
170 GR_RULECHANGE_ACK → u8 rule_value
```

ACK：

```text
sub_42FE50()
    ↓
sub_426930(...)
    ↓
Room/Player object +130
    ↓
GAMEROOM_SCROLL_RULE
    ↓
entry value match
    ↓
UI selection
```

`GAMEROOM_USERSLOTS` 等 Room state 也可能在同一路徑更新。[C]

Client 內部也存在 value → index 的反向查找，因此不能丟掉 Index/Value 的區分。[C]

## 8. Object selector：171/172

Registration：

```text
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
```

wire：

```text
u16
```

`sub_430720()` 明確操作：

```text
GAMEROOM_SCROLL_OBJECT
Room/Player object +144
```

因此目前安全語意是：

```text
171/172 = 16-bit Object selector value
```

不能因 packet name `WINCHANGE` 就直接命名 `kill_limit`、`round_limit` 或 `win_type`。[C]

Wiki 的 mode-specific values（Kill／Round／Point／CC）是 rule domain 證據；它們與此 16-bit selector value 是否一一對應，仍需 caller + resource + mode builder 閉合。[WIKI][OPEN]

## 9. Item packed flags：175/176

Request：

```text
175 +0x00 u8 packed_flags
```

ACK：

```text
176 +0x00 u8 packed_flags
```

建包前：

```text
bit 0 = GAMEROOM_ITEM state
bit 1 = map-dependent / gimmick-related result candidate
```

ACK decode：

```text
bit 0 → Item on/off
bit 1 → map-dependent / gimmick-related flag
```

bit 0 有 Wiki `アイテム/ノーアイテム戦` 與 C path 的獨立吻合。[C][WIKI][X]

bit 1 目前仍不可直接命名 `Crazy`、`Knife` 等。[C][OPEN]

`GAMEROOM_DAMAGEROOM` 有獨立控制 path：

```text
sub_430FA0 → sub_56F950
sub_430FD0 → GAMEROOM_DAMAGEROOM +76
```

因此它不能與 175/176 的 packed item byte 共用 enum。[C]

## 10. No Skill / Team Balance / Team Shuffle

Client 同時存在：

```text
GAMEROOM_TEAMBALANCE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_USERSLOTS
```

No Skill 還有 context split：

```text
current player/object +188 == 2
    → GAMEROOM_CLAN_NOSKILL
else
    → GAMEROOM_NORMAL_NOSKILL
```

因此 No Skill 至少在 Client UI/state 層不是單一 global boolean。[C][WIKI]

完整 wire opcode/value mapping 尚待對應 sender/receiver 閉合。[OPEN]

## 11. Start selector：129

Start path 在通過 precondition 後：

```text
sub_437060()
    ↓
GAMEROOM_SCROLL_MAP
    ↓
entry value
```

至少在 `n124 == 125` path 中，Client 可能從 map selector list 隨機選擇一個 value，再送入：

```text
129 GR_START_REQ
```

因此 129 的 byte 是 map-derived start parameter，而非可直接命名的 generic `start_flag`。[C][OPEN]

## 12. Autochange：177/178

```text
177 GR_AUTOCHANGE_REQ
178 GR_AUTOCHANGE_ACK
```

目前只確認它是獨立 Room-state family；完整 sender → receiver → state/resource chain 尚未閉合。[C][OPEN]

## 13. Mode factory／Client mode namespace

目前 Client mode factory／lobby class：

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

這是 Client mode namespace，不可直接當成：

```text
GR_RULECHANGE value
GR_TIMECHANGE value
GR_WINCHANGE value
CGameRule helper type predicate
```

## 14. Final Client mode rules

### 14.1 Team Match／チーム戦術モード

C：`CyGameModes::CyTeamMatchModeLobbyUI::sub_74F8B0()`。

```text
Round values:
3 / 5 / 7 / 10 / 12 / 15
```

| Index | Display | Value |
|---:|---|---:|
| 0 | `3 Round` | 3 |
| 1 | `5 Round` | 5 |
| 2 | `7 Round` | 7 |
| 3 | `10 Round` | 10 |
| 4 | `12 Round` | 12 |
| 5 | `15 Round` | 15 |

Client values 與 Wiki `チーム戦術モード` 一致。[C][WIKI][X]

Runtime 尚待：alive count、round timer、round win count、match threshold、respawn gate、draw behavior。[OPEN]

### 14.2 Individual Survival／個人サバイバル

C：`CyGameModes::CyIndividualSurvivalModeLobbyUI::sub_750220()`。

```text
Kill values: 20 / 30 / 40 / 50
```

| Index | Display | Value |
|---:|---|---:|
| 0 | `20 Kill` | 20 |
| 1 | `30 Kill` | 30 |
| 2 | `40 Kill` | 40 |
| 3 | `50 Kill` | 50 |

Client 與 Wiki 一致。[C][WIKI][X]

Runtime 尚待 kill counter、threshold end trigger、respawn timing、timeout result、reward/quest timing。[OPEN]

### 14.3 Team Survival／チームサバイバル

```text
Kill values: 50 / 100 / 200
```

Client 與現行 Wiki 一致。[C][WIKI][X]

歷史反證：2010-02-07 日本 `ver.Gp` 曾使用：

```text
染料ポイント 1000 / 2000 / 3000cc
時間 10 / 20 / 30 分
```

所以：

```text
ModeName != immutable RuleSchema
```

Server 必須區分：

```text
ClientBuild / ProtocolRevision
Mode
RuleFamily
RuleValue
```

### 14.4 Pulp & Roll／パルプ＆ロール

```text
Time values: 15 / 30 / 45
```

Resource keys：`0x24 / 0x2D / 0x395`。[C]

Wiki 與 Client 一致。[C][WIKI][X]

Runtime 尚待 pulp object、carrier/drop/pickup、A/B/C objective、phase、point producer、暴走、match end。[OPEN]

### 14.5 Steel／スチールモード

```text
Objective values: 1000 / 2000 / 3000 cc
```

`sub_751D20()` 明確建立這組 selector values。[C]

不能直接由 `GR_WINCHANGE` 名稱推成 kill limit；Wiki behavior 與 Runtime objective 尚待完整閉合。[WIKI][OPEN]

### 14.6 Occupy Renewal／new占領モード

```text
Point values: 300 / 500 / 700 / 1000
Resource keys: 0x53B / 0x53C / 0x53D / 0x53E
```

Client 與 Wiki values 一致；resource key 對原始日文 literal 仍 `[OPEN]`。[C][RES][WIKI][X]

### 14.7 Occupy／占領

```text
Round values: 1 / 2 / 3
```

與 Team Match 的 Round family 分開。[C]

### 14.8 Practice／練習モード

```text
999 Kill
```

Tutorial 亦存在 `999 Kill`。

Wiki 指出 Practice 的 `999 kill` 不依一般 Kill target 正常結束，因此 Server 不應只有：

```text
if Kill >= RuleValue:
    MatchEnd()
```

而應由 mode-specific `IsMatchOver()` 決定。[C][WIKI]

### 14.9 Soccer／サッカーモード

Time：

```text
7 / 10 / 15 / 20
```

Goal：

```text
5 / 7 / 10 / 15
```

Client 明確分成兩套 builder，因此必須保留：

```text
TimeOption
GoalOption
```

不可併成單一 option family。[C][WIKI][X]

## 15. Mode / Rule / Objective 的 Server 模型

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
    └─ packed flags
    ↓
ModeRuntime
    ├─ Phase
    ├─ RoundIndex
    ├─ ElapsedTime
    ├─ ObjectiveValue
    ├─ ObjectiveState
    └─ MatchEndState
```

`ModeId`、selector value、display value、wire value 與 Runtime condition 必須保持分層。[C][OPEN]

## 16. Server reconstruction boundary

Room setting 的安全資料流：

```text
UI selector state
    ↓
OptionValue validation
    ↓
Room state
    ↓
Start precondition
    ↓
CGameRule / ModeRuntime
    ↓
win / round / time / objective condition
```

不要在 Server 中直接寫成：

```text
byte rule
byte time
ushort win
```

應保留 semantic object：

```text
MapOption
RuleOption
ObjectOption
TimeOption
PackedRoomFlags
```

並在 codec 層映射到 121/122、169/170、171/172、173/174、175/176 等 packet。[C]

## 17. 三方交叉驗證

### Map

```text
[C] GAMEROOM_SCROLL_MAP + entry +36 + object +130 + 121/122
[RES] maplist.dat / .pmm resources
[WIKI] Room / map selection behavior
```

三方互相支持，但仍分開保留各自責任。[X]

### Time / Rule

```text
[C] selector value + 173/174 or 169/170
[WIKI] player-visible options
[RES] selector/resource system
```

### Objective / Item

```text
[C] 171/172 object selector、175/176 packed flags
[WIKI] mode-specific objective / item settings
[RES] concrete resource mapping
```

其中尚未閉合的對應仍保留 `[OPEN]`。

## 18. 目前 OPEN 與最高價值追查

```text
P0  mode builder → selector → packet → CGameRule 完整映射
P0  mode-specific IsMatchOver / round transition
P0  171/172 object selector value → public rule/object semantics
P1  169/170 rule value → exact mode/rule semantics
P1  173/174 value → exact duration mapping
P1  175 bit1 → exact public label
P1  177/178 full sender/receiver semantics
P1  team balance / team shuffle / no-skill wire mapping
P1  bomb plant/defuse/fuse state
P1  pulp carrier/objective state
P1  steel objective producer
P1  occupy capture/point producer
P1  soccer ball/goal state
P2  historical rule divergence across builds
```

所有未確認值保持 `[OPEN]`，不得為 Server 實作方便而填 `0`、固定常數或 guessed enum。
