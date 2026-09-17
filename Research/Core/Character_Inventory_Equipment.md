# 角色、背包與裝備研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。

本文件是角色、背包與裝備的主文件。與此主題高度相關的深入證據應併入本文件；只有在證據用途確實不同時才保留獨立文件。

## 原有研究內容與證據

本文件的前一版已被本次整理暫時收斂；完整歷史內容仍保存在 Git 歷史中的原始 Blob，後續整合時必須逐段恢復並合併，不得以摘要取代。

## 文件角色

本文件負責保存角色、背包、裝備的主結論與欄位結構。跨函式、跨資源的深入證據可先保留於 `Character_Inventory_Equipment_DeepEvidence.md`，但不得形成兩套互相矛盾的主結論。

## 證據要求

```text
IDA C / LST
    → serializer / parser
    → caller / callee
    → state field read / write
    → Extracted resource
    → Wiki／歷史行為
    → 交叉驗證
```

- `[C]`：反編譯 C 可直接觀察。
- `[RES]`：遊戲資源證據。
- `[WIKI]`：日本 Wiki 歷史資料。
- `[X]`：多來源交叉吻合。
- `[OPEN]`：尚未充分證明。

## 相關文件

- `Character_Inventory_Equipment_DeepEvidence.md`
- `MyInfo_198_ClientData_Field_Schema.md`
- `MyInfo_198_Composite_Codec_Evidence.md`
- `Currency_State_Field_Evidence.md`
- `Resource_Pack_Model.md`
