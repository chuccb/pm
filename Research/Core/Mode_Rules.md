# 遊戲模式與勝負機制研究

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年最終 Client。
> 文件角色：只保存各遊戲模式的玩家可見規則、模式差異、版本差異與待驗證 Runtime 行為；具體 selector value 統一見 `Mode_Option_Tables.md`，Room wire 欄位統一見 `Room_Settings_Packets.md`。

## 1. 文件邊界

本文件回答：

```text
這個模式怎麼玩？
什麼條件結束？
什麼條件決定勝負？
有哪些 mode-specific 行為？
哪些規則已由 Client / Resource / Wiki 交叉驗證？
```

不在此重複維護：

```text
selector index / value
Room packet wire schema
ClientData wire schema
單一函式完整反編譯
```

對應主文件：

```text
Mode_Option_Tables.md
Room_Settings_Packets.md
GameRule_Lifecycle.md
Gameplay_166_DeepEvidence.md
```

## 2. 證據原則

```text
[C] PaperMan.exe.c
    → Client 實際流程、state、timer、mode builder、條件判斷

[RES] Extracted
    → mode/map/option/resource 定義

[WIKI] 日本 PaperMan Wiki
    → 玩家可見規則與歷史版本行為

[X] 兩種以上來源一致
    → 可提高信度

[OPEN]
    → 尚未形成足夠閉環
```

Wiki 不取代 Client wire evidence；Resource 不單獨決定 packet 欄位名稱；Hex-Rays 表面型別也不取代 serializer／parser 實際寬度。

## 3. 個人サバイバル

Wiki 的玩家規則指出：

```text
制限時間內以擊殺數判定
達到設定擊殺條件可提前結束
時間到則依結果結算
リスポーン後具有短暫無敵時間
可搭配 Item、Crazy、No Skill 等房間設定
```

Client 已確認此模式有獨立 lobby builder，具體 Kill 與 Time selector value 見 `Mode_Option_Tables.md`。[C][WIKI]

尚待 Runtime 閉合：

```text
kill counter 實際 state 欄位
達標後的 GameRule end trigger
respawn invulnerability timer
timeout result path
reward / quest 更新時機
```

## 4. チームサバイバル

Wiki 的玩家規則指出：

```text
以兩隊累計擊殺數比較
達到設定條件後結束
時間到依兩隊當時結果結算
可搭配 Team Balance / Team Shuffle 等設定
```

目前 Client 已確認它具有獨立 objective selector；**具體 `50/100/200` 等數值只在 `Mode_Option_Tables.md` 維護，不在本文件重複。**

Wiki 另記錄部分歷史異常，例如某些版本曾出現目標擊殺數與實際結束數不同，以及畫面 DRAW 與戰績結果不完全一致。這些應標記為歷史／異常行為，不可覆寫正常 Server rule model。[WIKI]

尚待 Runtime 閉合：

```text
team cumulative score source
team score → player result aggregation
各種 timeout / DRAW 表現
team balance / shuffle 實際 state mutation
```

## 5. チーム戦術モード

Wiki 的玩家規則指出：

```text
以 round 為主要勝負單位
玩家死亡後通常等待 round 結束
依存活人數與其他條件決定 round 結果
round 結束後進入下一 round
```

Client 已確認此模式具有獨立 Round selector；具體數值只見 `Mode_Option_Tables.md`。[C][WIKI]

尚待 Runtime 閉合：

```text
round state
alive player count
round timer
round win count
match win threshold
respawn gate
round draw 行為
```

## 6. 爆破ミッション

Wiki 的玩家規則指出：

```text
攻擊方：設置並引爆炸彈
防守方：阻止目標或在時間內守住
任一方全滅可影響 round 結果
炸彈已設置後，殲滅判定不能單獨覆蓋所有 end condition
時間到時有明確的防守方結算規則
```

Wiki 同時提供設置、解除與爆炸等玩家可見時間資訊；這些目前只作 behavior-level constraint，不直接轉成 Server tick constant。[WIKI]

尚待 Runtime 閉合：

```text
attack / defense team
bomb carrier
bomb object identity
plant progress
planted state
fuse timer
defuse progress
explode event
round end cause
site state
respawn/death handling
```

## 7. スチールモード

Wiki 將此模式描述為以染料／cc 類 objective 推進的獨立 Team mode；Client 也建立獨立 objective/value selector。[C][WIKI]

具體 objective value 只見 `Mode_Option_Tables.md`，不要在本文件維護第二份數值表。

尚待 Runtime 閉合：

```text
objective object
carrier state
return / reset
attack / defense transition
objective accumulation
round / timer
171/172 與 Object selector 的最終關係
```

## 8. パルプ＆ロール

Wiki 的玩家規則指出：

```text
攻擊方奪取パルプ並運回指定區域
A/B/C 據點各有對應 objective
持有者被擊倒後 objective 可掉落
部分狀態會限制武器切換
存在攻守輪替、計時與 point 累積
另有特殊暴走狀態與相應行為差異
```

具體 `15/30/45` 等 selector value 只見 `Mode_Option_Tables.md`。[C][WIKI]

尚待 Runtime 閉合：

```text
pulp object ID
carrier / drop / pickup state
A/B/C objective state
phase transition
timer / point producer
暴走狀態與計時
Kill / Death / reward 是否抑制或改道
round / match end
```

## 9. 練習モード

Wiki 的玩家規則指出：

```text
戰績不計入
死亡後可立即或特殊條件重生
部分一般模式規則在此不適用
武器耐久度具有特殊處理
結束後 reward 具有特殊結果
```

Client 明確存在 Practice mode builder；特殊 `999 Kill` value 只在 `Mode_Option_Tables.md` 維護。[C][WIKI]

`999 Kill` 不能直接套用通用：

```text
if Kill >= RuleValue then MatchEnd
```

因為 Practice 的 `IsMatchOver()` 本身屬於 mode-specific policy。[WIKI][C]

## 10. new占領モード

Wiki 將其描述為 Point／據點進度型模式，存在獨立的目標值與進度規則。[WIKI]

具體 Point selector value 只見 `Mode_Option_Tables.md`。[C][WIKI]

尚待 Runtime 閉合：

```text
point source
capture state
team ownership
objective transition
round / timeout
score aggregation
match-end condition
```

## 11. サッカーモード

Wiki 將 Soccer 視為獨立 mode，並具有至少兩組不同設定：

```text
Time
Goal
```

Client `CyTeamSoccerModeLobbyUI` 也確實使用不同 builder 建立兩組 selector，因此不能把它們視為同一個 option family。[C][WIKI]

具體 Time／Goal value 只見 `Mode_Option_Tables.md`。

此外 Wiki 目前將部分 Knife Battle 選項限制在特定 mode；這屬於 **Mode capability**，不是所有 Room 都可無條件接受的 global flag。[WIKI]

尚待 Runtime 閉合：

```text
ball / objective state
score
goal condition
timeout
knife capability validation
weapon restriction
respawn / round handling
```

## 12. CyGameModes 與 Mode Code 必須分離

Client 中存在獨立的 mode factory / lobby class namespace，例如：

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

這些值描述 Client mode namespace，不等同：

```text
GR_RULECHANGE value
GR_TIMECHANGE value
GR_WINCHANGE value
```

Server model 必須分開保存 `Mode` 與各 selector value。

## 13. 跨模式的 Room/UI 約束

目前 Room UI 已確認存在：

```text
GAMEROOM_SCROLL_MAP
GAMEROOM_SCROLL_RULE
GAMEROOM_SCROLL_OBJECT
GAMEROOM_SCROLL_TIME
GAMEROOM_ITEM
GAMEROOM_GIMMICK
GAMEROOM_TEAMBALANCE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_USERSLOTS
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_DAMAGEROOM
```

selector entry 的通用資料結構將 `Index` 與 `Value` 分開；具體 option value 請勿在本文件再抄一次。[C]

Room 設定與 packet data-flow 統一見 `Room_Settings_Packets.md`。

## 14. 版本差異：同名模式不代表固定規則

目前已確認 Wiki 歷史資料存在同名模式的不同規則，例如：

```text
2010-02-07 ver.Gp
    チームサバイバル
    → 1000/2000/3000cc 染料條件

較後期 Wiki / Client
    チームサバイバル
    → Kill-based rule
```

這表示：

```text
ModeName
    ≠ immutable RuleSchema
```

因此 Server reconstruction 至少要把：

```text
ClientBuild / ProtocolVersion
Mode
RuleFamily
RuleValue
```

分開處理。

## 15. 玩家可見進度與 Runtime state

Wiki 的 Room information / mode 說明顯示，不同模式可能使用不同進度表示：

```text
Elapsed Time
Round Progress
Objective / Point Progress
```

不能在 Server model 中強行統一成單一 `Progress` 欄位。

目前較安全的抽象是：

```text
ModeRuntime
├─ Phase
├─ RoundIndex
├─ ElapsedTime
├─ ObjectiveValue
├─ ObjectiveState
└─ MatchEndState
```

具體來源與封包同步仍由各主題文件負責。

## 16. 下一階段

Mode 層下一步應從「玩家可見規則」深入到 Client Runtime：

```text
Room setting
    ↓
CGameRule / concrete mode
    ↓
spawn / player state
    ↓
damage / death
    ↓
score / objective
    ↓
round / timeout
    ↓
match end
    ↓
result / reward / quest
```

每一個具體 mode 都應以：

```text
C
↕
Extracted
↕
Wiki
```

逐條閉合；尚未閉合的數值或 enum 維持 `[OPEN]`。