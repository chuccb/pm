# `UDP_Move_Inf` 欄位語意

本文件只保存 `UDP_Move_Inf` 的欄位語意與最小必要證據；完整資料流與跨函式證據鏈集中於 `UDP_Move_Inf_DeepEvidence.md`。

## 文件責任

保存已確認的欄位名稱、offset、寬度、編碼與用途，以及必要的直接證據。不重複建立第二份完整傳輸或生命週期研究。

## 證據優先順序

```text
實際 serializer / parser
→ 實際讀寫寬度與 offset
→ caller / callee 與資料流
→ state field
→ Extracted 資源
→ Wiki／歷史行為
→ 交叉驗證
```

尚未充分證明的欄位維持 `[OPEN]`，不得因實作便利而填入猜測值。

## 相關文件

- `UDP_Move_Inf_DeepEvidence.md`：完整深入證據鏈。
- `Gameplay_Network_Events.md`：遊戲網路事件上下文。
