# 遊戲模式與勝負機制研究

> 研究日期：2026-09-16
> 
> 本文件建立日本 Wiki 的模式規則基線，並逐步用 `PaperMan.exe.c` 與 `Extracted/` 資源確認實際 client state、封包與數值常數。Wiki 原文中的日文名稱保留，不翻譯。

## 證據原則

```text
Wiki
  -> 玩家可見規則

C
  -> Client 實際流程、state、timer、封包、concrete option value

RES
  -> mode/map/option/resource 定義

三者一致
  -> 才提升為高可信 Server reconstruction
```

## 重要新文件

具體的 mode-specific selector value 已獨立整理於：

- [`Mode_Option_Tables.md`](Mode_Option_Tables.md)
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)

其中已直接從 C 封死多組數值，例如：

```text
個人サバイバル       -> 20/30/40/50 Kill
チームサバイバル     -> 50/100/200 Kill
チーム戦術モード     -> 3/5/7/10/12/15 Round
パルプ＆ロール       -> 15/30/45
new占領モード        -> 300/500/700/1000
サッカーモード       -> Time 7/10/15/20 + Goal 5/7/10/15
スチールモード       -> 1000/2000/3000 cc
練習モード           -> 999 Kill
```

這些值不是只由 Wiki 猜出來，而是 client lobby builder 實際用 `sub_4386A0(..., VALUE, ...)` 建立 selector option；generic selector entry 再由 `sub_4387B0()` 從 `+36` 取回 value。

---

## 1. `個人サバイバル`

日本 Wiki 的玩家規則：

- 制限時間內擊殺數最多者勝出。
- 某玩家達成規定 Kill 數時立即結束。
- 達到時間上限時依當時結果結束。
- リスポーン後有 5 秒無敵時間。
- 條件可選 `20/30/40/50 Kill`。
- 時間可選 `10/15/20 分`。
- 可搭配 `アイテム戦`、`クレイジープレイ`、`NO SKILL` 等選項。

來源：[WIKI] `MAP・ルール詳細`。 citeturn761828search1

### C 已新增確認

`CyIndividualSurvivalModeLobbyUI` 直接建立 `20/30/40/50 Kill`，詳見 [`Mode_Option_Tables.md`](Mode_Option_Tables.md)。

### 待 C/RES 驗證

- kill counter 實際 state 欄位。
- 20/30/40/50 的設定如何送至 server，以及是否進入 171/172。
- 10/15/20 分的 timer value mapping。
- 5 秒 respawn invulnerability 的實際 client/server flow。
- 達標後由哪個 GameRule handler 觸發 `GR_END_*`。

## 2. `チームサバイバル`

Wiki 描述：

- 比較兩隊累計擊殺數。
- 達到規定 team kill 數後結束。
- 時間到時依兩隊當時 Kill 數決定結果。
- 條件：`50/100/200 Kill`。
- 時間：`10/20/30 分`。
- 可有 `アイテム戦`、`クレイジープレイ`、`NO SKILL`、`チームバランス`、`チームシャッフル`。

Wiki 也記錄 100 Kill 模式曾出現超過設定值才結束的 bug；這是歷史行為證據，但不能當成正常規則。 citeturn761828search1

### C 已新增確認

`CyTeamSurvivalModeLobbyUI` 直接建立 `50/100/200 Kill`。

### 待 C/RES 驗證

- team kill 累計欄位。
- team score 與個人 score 的區分。
- timeout 與 DRAW／負數統計邏輯。
- `チームバランス`、`チームシャッフル` 實際如何影響 team state。

## 3. `チーム戦術モード`

Wiki 描述：

- 競爭「全滅對方隊伍」的回合勝利數。
- 玩家死亡後直到本 round 結束前不重生。
- Round 結束後全員恢復／進入下一 round。
- 時間到時，剩餘人數較多的一隊取得該 round 勝利。
- 剩餘人數相同時為 draw，該 round 持續／不結算為勝負。
- Round 可選：`3/5/7/10/12/15`。
- 時間可選：`3/4/5 分`。
- Wiki 說明名稱曾由 `チームデスマッチ` 更名。

來源：[WIKI] `MAP・ルール詳細`。 citeturn761828search1

### C 已新增確認

`CyTeamMatchModeLobbyUI` 直接建立 `3/5/7/10/12/15 Round`，而且 selector index 與 value 並不等同。

### 待 C/RES 驗證

```text
round state
alive player count
round timer
round win count
match win threshold
respawn gate
```

## 4. `爆破ミッション`

Wiki 將此模式描述為攻擊／防守雙方競爭目標的爆破／防衛。 citeturn761828search1

目前不把簡短 Wiki 描述擴充成未經證實的完整 Bomb protocol。

### 待 C/RES 驗證

```text
攻守 team
bomb carrier
bomb planted
plant timer
defuse timer
round end
round win
round draw
site A/B/etc.
```

## 5. `スチールモード`

Wiki 將其列為獨立的 team mode，但目前需要結合其專屬頁面與 C GameRule handler 才能完整恢復。 citeturn761828search1

### C 已新增確認

`CyStealModeLobbyUI` 直接建立 `1000/2000/3000 cc`。這證明該 mode 存在獨立 objective/value selector，不應與一般 Kill target 共用 global enum。

### 待 C/RES 驗證

```text
steal objective
carrier state
return/reset
attack/defense transition
round / timer
171/172 實際承載的 object selector semantics
```

## 6. `パルプ＆ロール`

Wiki 描述：

- 攻擊方奪取對手的 `パルプ` 並帶回本隊魔法箱。
- 防守方必須在 `1分30秒` 內阻止。
- 成功奪取 1 個或成功守住後攻守交換。
- 每 round 分前後半，雙方各執行一次攻擊與防守。
- 存在 A/B/C 三個據點。
- A、B 被占領後才可占領 C。
- C 開放時重生點改變。

這些內容屬於 Wiki 玩家規則基線；真正 timer／objective packet 仍需 C/RES 驗證。 citeturn761828search1

### C 已新增確認

`CyPulpnRollModeLobbyUI` 建立 concrete values `15/30/45`，Wiki 顯示同樣的 `15/30/45 分`。

## 7. `練習モード`

Wiki 描述：

- 戰績不計入。
- 形式上接近 `個人サバイバル`。
- 死亡後在死亡位置重生，沒有一般重生等待時間。
- 可選很多其他模式的地圖。
- 可 1 人開始。
- 武器耐久度不下降。
- 結束後固定 `0PG / 0Exp`。
- `999 kill` 只是設定值，達成也不會使練習模式正常結束。

這是一個非常適合用來確認「mode-specific branch」的模式，因為它與一般 FFA 的 player count、respawn、reward、end condition 都有明顯差異。 citeturn761828search1

### C 已新增確認

`CyPracticeModeLobbyUI` 直接建立 `999 Kill`，而 `CyTutorialModeLobbyUI` 也有同一特殊 value。

## 8. `new占領モード` 與 `サッカーモード`

這兩個 mode 的具體 selector values 現在也已由 C 收斂：

```text
new占領モード
    300/500/700/1000 Point

サッカーモード
    Time = 7/10/15/20
    Goal = 5/7/10/15
```

其中 soccer 特別值得注意：同一 `CyTeamSoccerModeLobbyUI` 存在兩個不同 builder，分別建立 Time 與 Goal selector；因此不能把同一 class 裡所有 option value 視為同一設定。

Wiki 對 `new占領モード` 與 `サッカーモード` 的上述玩家可見數值可獨立交叉確認。citeturn606128search0

## 9. 模式選擇與 Room state

C-side Room UI 已發現：

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

generic selector entry 的 value 在 `+36`；因此 mode-specific option builder 與 Room packet layer 可以用同一個 selector value model 串起來。

詳細 wire formats 與目前 destination mapping 見 [`Room_Settings_Packets.md`](Room_Settings_Packets.md)。

## 10. Mode code 不能與 selector value 混用

Client 中存在獨立的 `CyGameModes` mapping，例如：

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

這些是 mode factory／lobby class 的 namespace，不得與 `GR_RULECHANGE`、`GR_TIMECHANGE`、`GR_WINCHANGE` 的 selector values 直接共用。

## 11. 目前最重要的下一階段

目前 Room selector layer 已經比單純 Wiki-level 的整理完整很多；下一階段應轉到真正的 gameplay runtime：

```text
Room setting
   ↓
CGameRule concrete mode
   ↓
spawn
   ↓
player state
   ↓
damage / death
   ↓
kill / score / objective
   ↓
round / timeout
   ↓
match end
   ↓
result / GR_END / higher-layer packet
```

優先：

```text
個人サバイバル
チームサバイバル
チーム戦術モード
爆破ミッション
スチールモード
練習モード
```

只有把這條 lifecycle 從 C/RES/Wiki 三方閉合，才適合進入真正可執行的 Server implementation。
