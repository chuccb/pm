# `UDP_Move_Inf` 欄位語意

> 本文件記錄 `UDP_Move_Inf` 的欄位語意與直接證據；完整傳輸與深入資料流分析應集中於 `UDP_Move_Inf_DeepEvidence.md`，避免兩份文件各自維護完整結論。

## 文件角色

本文件只保存欄位層級結論、欄位表與必要的最小證據。跨函式資料流、caller/callee、生命週期與大量反編譯推導優先放在 `UDP_Move_Inf_DeepEvidence.md`。

## 證據規則

欄位名稱、寬度、offset、編碼與用途不得只依變數名稱推測；優先使用實際封裝與解析函式的讀寫寬度，再用狀態欄位與資源交叉確認。

## 目前狀態

原有深入分析文件仍是本主題的證據庫。若新證據改變欄位語意，應先修改主結論，再同步更新深入證據，而不是建立第三份新表。

## 相關文件

- `UDP_Move_Inf_DeepEvidence.md`：深入證據鏈與完整資料流。
- `Gameplay_Network_Events.md`：遊戲網路事件上下文。
