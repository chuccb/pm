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

來源：[WIKI] `MAP・ルール詳細`。

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

現行 Wiki 還記錄：若時間到時兩隊 Kill 數相同，畫面顯示 DRAW，但該模式不存在真正的平局勝績，實際會使雙方都被記為敗北；另外曾有 100 Kill 模式需到 101 Kill 才結束的通信相關 bug。這兩點都應視為歷史/異常行為，不可覆寫正常規則模型。

### C 已新增確認

`CyTeamSurvivalModeLobbyUI` 直接建立 `50/100/200 Kill`。

### 待 C/RES 驗證

- team kill 累計欄位。
- team score 與個人 score 的區分。
- timeout、DRAW 顯示與實際 result/recording 的差異。
- `チームバランス`、`チームシャッフル` 實際如何影響 team state。
- 超過目標 Kill 的異常是否能在 Client state / packet trace 找到對應原因。

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

來源：[WIKI] `MAP・ルール詳細`。

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

Wiki 描述：

- 攻擊方與防守方交替。
- 攻擊方目標是放置並引爆炸彈；防守方目標是在時間內守住目標。
- 任一方將對手全滅可取得該 round 勝利；但如果炸彈已經放置，防守方不能只靠殲滅對手直接結束，必須處理已放置炸彈。
- Round 時間到時，無論炸彈狀態如何，防守方直接獲勝，因此該模式沒有真正的 round draw。
- Wiki 的現行說明給出 concrete interaction times：設置約 5 秒、解除約 7 秒、設置後爆炸約 50 秒。
- 條件可選 `3/5/7/10/12/15 Round`。
- 時間可選 `3/4/5 分`。
- 可搭配 `アイテム戦`、`クレイジープレイ`、`NO SKILL`、`チームバランス`、`チームシャッフル`。

這些屬於玩家可見規則基線；目前仍沒有把 5/7/50 秒直接當成 server tick constant，因為仍需對應 C timer、bomb object state 與 packet。

### 待 C/RES 驗證

```text
attack/defense team assignment
bomb carrier
bomb object identity
bomb planted flag
plant start/progress/end
fuse timer
explode event
defuse start/progress/end
round end cause
round win state
respawn/death handling
site A/B/etc.
```

## 5. `スチールモード`

Wiki 將其列為獨立的 team mode，目前規則段落中的 objective 為染料（cc）。現行數值為 `1000/2000/3000 cc`。

### C 已新增確認

`CyStealModeLobbyUI` 直接建立 `1000/2000/3000 cc`。這證明該 mode 存在獨立 objective/value selector，不應與一般 Kill target 共用 global enum。

Wiki 當前說明也指出該模式屬於「Cold」型規則，而非簡單的第一隊拿到某個固定 flag 即結束；具體 carrier / return / aggregation 仍應以 C runtime 為準。

### 待 C/RES 驗證

```text
steal objective
carrier state
parallel carriers
return/reset
attack/defense transition
round / timer
point accumulation
171/172 實際承載的 object selector semantics
```

## 6. `パルプ＆ロール`

Wiki 描述：

- 攻擊方奪取對手的 `パルプ` 並帶回本隊魔法箱。
- 防守方在 `1分30秒` 內阻止；成功奪取 1 個或成功守住後攻守交換。
- `A/B/C` 三個據點各有 1 個パルプ。
- 搶到パルプ後會切換成專用近戰武器且不能換武器。
- 運送者被擊倒時パルプ會掉落，攻擊方可再拾取；防守方還可在特定條件下破壞落地的パルプ。
- 防守成功會按時間累積 point，Wiki 記錄每 10 秒增加 1 point、最多 8 point，另外 1:30 守住後還會觸發額外 point/特殊狀態。
- 達成一定條件後有 30 秒 `暴走モード`；此狀態會改變武器、移動、無敵與 scoring 行為，Wiki 明確說明 Kill/Death 不計入但該狀態下取得擊殺仍會即時給經驗與 PG。
- 勝利條件包括達到設定 point，或時間結束時 points 較多。
- `15/30/45 分` 是 lobby 的 time selector values。

以上是高價值 Wiki evidence，但目前不要把 `1:30`、10 秒、30 秒與各 point 數字直接硬編入 server，因為需要 C timer/objective state/packet cross-check。

### C 已新增確認

`CyPulpnRollModeLobbyUI` 建立 concrete values `15/30/45`，Wiki 顯示同樣的 `15/30/45 分`。

### 待 C/RES 驗證

```text
pulp object ID
carrier/player state
pickup/drop/destroy packet
A/B/C objective state
attack/defense phase
1:30 timer
point accrual
rage/暴走 gauge
暴走 30s timer
kill/death suppression
reward side effect
round/match end
```

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

這是一個非常適合用來確認「mode-specific branch」的模式，因為它與一般 FFA 的 player count、respawn、reward、end condition 都有明顯差異。

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

Wiki 對 `new占領モード` 與 `サッカーモード` 的上述玩家可見數值可獨立交叉確認。

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

## 11. Wiki 可觀察的 Room metadata／特殊規則

2026-09-16 再次核對日本 Wiki `MAP・ルール詳細` 後，補充以下可直接觀察、但不能擴張成通用 protocol 規則的 evidence：

### 11.1 Lobby Room information 依 mode 顯示不同的進度欄位

Wiki 說明 Room information 會顯示：房間狀態、模式、地圖、勝利條件、制限時間、以及進行度等資訊；其中：

```text
個人サバイバル
チームサバイバル
スチールモード
パルプ＆ロール
サッカーモード
    -> 顯示「開始後經過時間」

チーム戦術モード
爆破ミッション
占領モード
PVE
    -> 顯示「目前進行 round 數」
```

另外 Wiki 明確記錄：**平局 round 不會讓這個 round 顯示值增加**；而且註記以前曾會增加，代表此行為具有歷史版本差異。

這是重要的 Server/UI constraint：不能假設所有 mode 共用單一 `Progress = elapsedSeconds` 或單一 `RoundIndex`。

### 11.2 Soccer 的 Knife 戰是 mode-specific feature

Wiki 現行描述指出，Room information 中的「ナイフ戦」目前只有 `サッカーモード` 能啟用。

因此 Server model 不應把 knife-room flag 視為所有 mode 都合法的 global option；至少要有：

```text
Mode capability / option availability
    -> KnifeBattle allowed?
```

再由 room validation 決定能否接受設定。

### 11.3 Practice mode 在 Lobby filter 中是特殊案例

Wiki 的 mode filter 清單包含多個正式模式，但明確說：

```text
練習モード
    -> 只能在 `MODE（全体）` 中參照
```

因此「所有 mode 都可被相同 lobby filter enum 直接選取」也是錯誤抽象；至少 Practice 在 UI filter 層有例外。

### 11.4 Source / Historical note

本節僅記錄 Wiki 可見行為，沒有把它們反推成 packet opcode。來源為：

```text
https://wikiwiki.jp/paperman/MAP%E3%83%BB%E3%83%AB%E3%83%BC%E3%83%AB%E8%A9%B3%E7%B4%B0
```

其中部分條目明確帶有歷史修正註記，因此後續仍必須用對應 Client build / Resource / 實測判定版本範圍。

## 12. 版本差異：同名 mode 不代表固定規則 schema

目前已由兩個 Wiki 時間點看到直接 evidence：

```text
2010-02-07 ver.Gp
    チームサバイバル
    -> 1000/2000/3000cc 染料條件

2015-10-23 現行 Wiki
    チームサバイバル
    -> 50/100/200 Kill 條件
```

因此：

```text
ModeName
    != immutable RuleSchema
```

Server reconstruction 必須把版本／build context 與 mode/rule 分開保存。這也解釋了為什麼 `GR_WINCHANGE (171/172)` 不應只靠 packet 名稱或 current Wiki 命名。

## 13. 目前最重要的下一階段

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
