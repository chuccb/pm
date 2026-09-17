# 遊戲模式、勝負規則與 Selector Values 整合研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中各遊戲模式的玩家可見規則、Client mode builder、selector index/value、版本差異與 Runtime 待閉合項目。Room 通用 wire schema 仍由 Room 相關主文件維護。

## 先看這裡：這份文件回答什麼

如果問題是「這個模式有哪些規則值、OptionIndex 與 OptionValue 是什麼、模式規則如何映射到 Runtime」，看這份文件。

如果問題是「Room setting packet 怎麼編碼」，看：

```text
Room_Settings_Packets.md
Room_Channel_GameRule_101_192_Field_Evidence.md
Channel_Lobby_193_221_Field_Evidence.md
```

如果問題是「遊戲進行中某個事件如何改 state」，看：

```text
Gameplay_Network.md
Combat_Damage.md
UDP_Move_Inf_DeepEvidence.md
```

最短理解路徑：

```text
Mode
  ↓
OptionIndex
  ↓
OptionValue
  ↓
Room state
  ↓
CGameRule / ModeRuntime
  ↓
Win / Round / Objective condition
```

## 1. 核心模型：Mode、OptionIndex、OptionValue 必須分離

Room selector entry 一般為：

```text
entry stride = 40 bytes
entry value  = +36
```

因此：

```text
ModeId
    ≠
OptionIndex
    ≠
OptionValue
```

Mode-specific lobby builder 會直接建立 concrete option value，再交給 generic selector；Server reconstruction 不應只保存 UI index，也不能把 selector value 自動當成 mode enum。[C]

## 2. Team Match／チーム戦術モード

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

Wiki 的 `チーム戦術モード` 與 Client values 一致。[C][WIKI][X]

玩家規則層：以 round 為主要勝負單位，依存活人數與相關條件決定 round 結果，再進下一 round。Runtime 尚待完整閉合：

```text
alive player count
round timer
round win count
match win threshold
respawn gate
draw behavior
```

## 3. Individual Survival／個人サバイバル

C：`CyGameModes::CyIndividualSurvivalModeLobbyUI::sub_750220()`。

```text
Kill values:
20 / 30 / 40 / 50
```

| Index | Display | Value |
|---:|---|---:|
| 0 | `20 Kill` | 20 |
| 1 | `30 Kill` | 30 |
| 2 | `40 Kill` | 40 |
| 3 | `50 Kill` | 50 |

Wiki 與 Client 完全一致。[C][WIKI][X]

玩家規則：時間內依擊殺數判定，達到設定條件可提前結束，時間到則結算；可搭配 Item、Crazy、No Skill 等房間設定。[WIKI]

Runtime 尚待：

```text
kill counter source
kill threshold end trigger
respawn invulnerability
 timeout result path
reward / quest timing
```

## 4. Team Survival／チームサバイバル

C：`CyGameModes::CyTeamSurvivalModeLobbyUI::sub_751510()`。

```text
Kill values:
50 / 100 / 200
```

Wiki 現行規則一致。[C][WIKI][X]

玩家規則：兩隊累計擊殺數比較，達標或時間到後結算。[WIKI]

重要歷史反證：2010-02-07 日本 `ver.Gp` Wiki 記載同名模式曾使用：

```text
染料ポイント 1000 / 2000 / 3000cc
時間 10 / 20 / 30 分
```

而目前研究的 Final Client／Wiki 為 Kill-based `50/100/200`。所以：

```text
ModeName != immutable RuleSchema
```

Server reconstruction 必須至少區分：

```text
ClientBuild / ProtocolRevision
Mode
RuleFamily
RuleValue
```

## 5. Pulp & Roll／パルプ＆ロール

C：`CyGameModes::CyPulpnRollModeLobbyUI::sub_753000()`。

```text
Time values:
15 / 30 / 45
```

| Index | Resource key | Value |
|---:|---:|---:|
| 0 | `0x24` | 15 |
| 1 | `0x2D` | 30 |
| 2 | `0x395` | 45 |

Wiki 與 15/30/45 分一致。[C][WIKI][X]

玩家規則：奪取 Pulp 並運回指定區域；A/B/C 據點、持有／掉落、攻守輪替、計時與 point 累積等屬 mode-specific state。[WIKI]

Runtime 待閉合：

```text
pulp object ID
carrier/drop/pickup
A/B/C objective state
phase transition
point producer
暴走狀態
round/match end
```

## 6. Steel／スチールモード

C：`CyGameModes::CyStealModeLobbyUI::sub_751D20()`。

```text
Objective values:
1000 / 2000 / 3000 cc
```

| Index | Display | Value |
|---:|---|---:|
| 0 | `1000 cc` | 1000 |
| 1 | `2000 cc` | 2000 |
| 2 | `3000 cc` | 3000 |

這再次證明 `GR_WINCHANGE` 之類名稱不能被直接解讀成 global kill limit。[C]

Wiki 對 Steel 的具體 objective 行為仍需與 Client runtime 持續閉合。[WIKI][OPEN]

## 7. Occupy Renewal／new占領モード

C：`CyGameModes::CyOccupyRenewalModeLobbyUI::sub_755420()`。

```text
Point values:
300 / 500 / 700 / 1000
```

Wiki 同樣列出這四個 Point value。[C][WIKI][X]

Resource label keys：

```text
0x53B / 0x53C / 0x53D / 0x53E
```

目前 resource-backed 已確認，但 key → 原始日文 literal 仍 OPEN。[C][RES][OPEN]

## 8. Occupy／占領

C：`CyGameModes::CyOccupyModeLobbyUI::sub_753BA0()`。

```text
Round values:
1 / 2 / 3
```

這與 Team Match 的 `3/5/7/10/12/15` 是不同 option family；不能建立 global round enum 並視為相同條件。[C]

## 9. Practice／練習モード

C：`CyGameModes::CyPracticeModeLobbyUI::sub_752540()`。

```text
999 Kill
```

Tutorial mode 同樣存在 `999 Kill` option。

Wiki 明確說 Practice 的 `999 kill` 不會依一般 Kill target 正常結束，因此 Server 不應只有：

```text
if Kill >= RuleValue:
    MatchEnd()
```

而要交給 mode-specific `IsMatchOver()` policy。[C][WIKI]

## 10. Soccer／サッカーモード

Client `CyTeamSoccerModeLobbyUI` 明確分成兩套 option builder。

### 10.1 Time

`sub_754750()`：

```text
7 / 10 / 15 / 20
```

Resource keys：

```text
0x4C6 / 0x21 / 0x24 / 0x28
```

Wiki 同樣為 7/10/15/20 分。[C][WIKI][X]

### 10.2 Goal

`sub_754B20()`：

```text
5 / 7 / 10 / 15
```

Resource keys：

```text
0x4F3 / 0x4F4 / 0x4F5 / 0x4FA
```

Runtime/HUD 又直接使用：

```text
GOAL_POINT_5
GOAL_POINT_7
GOAL_POINT_10
GOAL_POINT_15
```

Wiki 同樣列出 5/7/10/15 Goal。[C][WIKI][X]

因此 Soccer 必須維持：

```text
TimeOption
GoalOption
```

而不是單一 option family。

## 11. Mode factory／Client mode namespace

目前 Client mode factory／lobby class 包含：

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

這些是 Client mode namespace；不能直接拿來當：

```text
GR_RULECHANGE value
GR_TIMECHANGE value
GR_WINCHANGE value
```

## 12. Room capability 與 mode-specific rules

Room UI 可見控制包含：

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
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
```

某些能力／規則只在特定 mode 有效。例如 Knife Battle、No Skill、Gimmick 等不能當成所有 Room 的 global capability。[WIKI][C][OPEN]

## 13. 版本隔離

同名模式在不同 Client build／歷史版本可以使用完全不同的 rule family。因此 Server domain model 建議：

```text
ClientBuild / ProtocolRevision
├─ ModeId
├─ RuleFamily
├─ RuleValue
├─ TimeOption
└─ CapabilitySet
```

不能：

```text
ModeName → 永久固定 rule/value
```

## 14. Server reconstruction

模式層應沿：

```text
Room setting
    ↓
Client mode / CGameRule
    ↓
ModeRuntime
    ├─ Phase
    ├─ RoundIndex
    ├─ ElapsedTime
    ├─ ObjectiveValue
    ├─ ObjectiveState
    └─ MatchEndState
    ↓
score / objective
    ↓
Result / Reward / Quest
```

具體 selector value 不能取代 mode rule；mode rule 也不能反向覆蓋 wire value。兩者要靠 C、Extracted、Wiki 三方證據閉合。

## 15. 未閉合與最高價值追查

```text
P0  各 mode builder → Room selector → 169/171/173/175 等 packet → CGameRule
P0  mode-specific IsMatchOver() / round transition
P1  bomb object / plant / defuse / fuse state
P1  pulp carrier / objective state
P1  steel objective producer
P1  occupy capture state / point producer
P1  soccer ball / goal state
P1  capability validation（Knife / No Skill / Gimmick）
P2  歷史版本與 2016 Final client 的 rule divergence
```
