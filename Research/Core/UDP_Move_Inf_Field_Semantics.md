# `UDP_Move_Inf` 欄位語意

本文件只保存 `UDP_Move_Inf` 的欄位語意與最小必要證據；完整資料流與跨函式證據鏈集中於 `UDP_Move_Inf_DeepEvidence.md`。

## 文件責任

- 保存已確認的欄位名稱、offset、寬度、編碼與用途。
- 保存必要的直接 C/LST 證據。
- 對尚未確認的語意保留 `[OPEN]`。
- 不重複保存另一份完整生命週期或傳輸分析。

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

## 目前整合狀態

原有欄位研究應與 `UDP_Move_Inf_DeepEvidence.md` 合併時逐項核對。若兩份文件存在不同結論，以較底層的直接讀寫證據為準，並在修正處保留研究演進。

## 相關文件

- `UDP_Move_Inf_DeepEvidence.md`：深入證據鏈與傳輸上下文。
- `Gameplay_Network_Events.md`：遊戲網路事件上下文。
