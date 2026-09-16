# 遊戲模式與勝負機制研究

> 研究日期：2026-09-16
> 
> 本文件目前先建立日本 Wiki 的模式規則基線；下一階段會逐一用 `PaperMan.exe.c` 與 `Extracted/` 資源確認實際 client state、封包與數值常數。Wiki 原文中的日文名稱保留，不翻譯。

## 證據原則

本文件不把 Wiki 描述直接當成 Server 實作證據。

```text
Wiki
  -> 玩家可見規則

C
  -> Client 實際流程、state、timer、封包

RES
  -> mode/map/option/resource 定義

三者一致
  -> 才能把規則提升為高可信重建結果
```

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

### 待 C/RES 驗證

- kill counter 實際 state 欄位。
- 20/30/40/50 的設定如何送至 server。
- 10/15/20 分的 timer 單位與倒數來源。
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

### 待 C/RES 驗證

這個模式是後續最值得追的模式之一，因為它需要至少：

```text
round state
alive player count
round timer
round win count
match win threshold
respawn gate
```

要完整追出 Server 行為，必須在 `CGameRule` 中找到上述 state 的更新點，而不是只照 Wiki 寫固定規則。

## 4. `爆破ミッション`

Wiki 將此模式描述為攻擊／防守雙方競爭目標的爆破／防衛。 citeturn761828search1

目前本文件不把簡短 Wiki 描述擴充成未經證實的完整 Bomb protocol。

### 待 C/RES 驗證

優先追查：

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

後續重點：

```text
steal objective
carrier state
return/reset
attack/defense transition
round / timer
```

## 6. `パルプ＆ロール`

這是較特殊的攻防／奪取模式。Wiki 描述：

- 攻擊方奪取對手的 `パルプ` 並帶回本隊魔法箱。
- 防守方必須在 `1分30秒` 內阻止。
- 成功奪取 1 個或成功守住後攻守交換。
- 每 round 分前後半，雙方各執行一次攻擊與防守。
- 存在 A/B/C 三個據點。
- A、B 被占領後才可占領 C。
- C 開放時重生點改變。

這些內容屬於 Wiki 玩家規則基線；真正 timer／objective packet 仍需 C/RES 驗證。 citeturn761828search1

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

## 8. 模式選擇本身已與房間資源連接

C-side 已發現房間 UI 使用：

```text
GAMEROOM_SCROLL_MAP
GAMEROOM_SCROLL_RULE
GAMEROOM_USERSLOTS
GAMEMODE
PERIOD
```

其中 `GAMEMODE`、`PERIOD` 已被其他 UI/room code 透過 `sub_439600()` 讀取；`GAMEROOM_SCROLL_MAP` 則直接參與 map value 的取得與封包。這說明「模式／規則／時間／地圖」是房間 state 的獨立資料項，而不是單純顯示文字。

## 9. 目前最重要的模式逆向方向

接下來要做的不是再抄 Wiki，而是建立下列對照表：

```text
Wiki rule
   <-> mode identifier
   <-> room resource / rule value
   <-> CGameRule concrete class
   <-> state fields
   <-> timers
   <-> objective events
   <-> end condition
   <-> result packet
```

優先順序：

```text
個人サバイバル
チームサバイバル
チーム戦術モード
爆破ミッション
スチールモード
練習モード
```

這樣才能逐步建立真正可執行的 PaperMan Server 遊戲規則，而不是只做 Wiki-level 的資料整理。
