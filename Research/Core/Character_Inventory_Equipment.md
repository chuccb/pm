# 角色、背包與裝備研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。

本文件是角色、背包與裝備的主文件；與本主題相關的深入證據應逐步整合至此，避免形成兩份平行主線。

## 文件責任

- 保存角色、Inventory、Equipment 的主結論與欄位結構。
- 保存必要的直接證據與交叉驗證結果。
- 深入證據可暫存於 `Character_Inventory_Equipment_DeepEvidence.md`，直到內容完整併入本文件。

## 證據鏈

```text
IDA C / LST
    → serializer / parser
    → caller / callee
    → state field read / write
    → Extracted resource
    → Wiki／歷史行為
    → 交叉驗證
```

任何欄位語意都不得只依 Hex-Rays 變數名稱、型別、名稱相似或數值合理性判定。

## 狀態標記

- `[C]`：反編譯 C 可直接觀察。
- `[RES]`：遊戲資源證據。
- `[WIKI]`：日本 Wiki 歷史資料。
- `[X]`：多來源交叉吻合。
- `[OPEN]`：尚未充分證明。

## 尚待整合

`Character_Inventory_Equipment_DeepEvidence.md` 仍保存本主題的大量深入研究。整理時必須逐段搬移未重複證據，確認沒有遺失函式、位址、欄位或推論鏈後，再刪除重複文件。

## 相關文件

- `MyInfo_198_ClientData_Field_Schema.md`
- `MyInfo_198_Composite_Codec_Evidence.md`
- `Currency_State_Field_Evidence.md`
- `Resource_Pack_Model.md`
