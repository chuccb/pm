# 角色、背包與裝備研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。

本文件是角色、背包與裝備的主文件。與此主題高度相關的深入證據應併入本文件；只有在證據用途確實不同時才保留獨立文件。

## 研究範圍

本主題涵蓋 Character、Inventory、Equipment，以及三者在 Client 狀態、資源與網路同步中的關係。

## 原有研究內容

以下保留本主題原有研究結論；後續整合 `Character_Inventory_Equipment_DeepEvidence.md` 時，不得刪除其中尚未納入的證據、函式位址、欄位與推導。

## 證據要求

任何欄位語意都必須盡可能追到：

```text
IDA C / LST
    → serializer / parser
    → caller / callee
    → state field read / write
    → Extracted resource
    → Wiki／歷史行為
    → 交叉驗證
```

不得把名稱相似、數值合理或 Hex-Rays 猜測直接當成已確認語意。

## 狀態標記

- `[C]`：反編譯 C 可直接觀察。
- `[RES]`：遊戲資源直接提供的證據。
- `[WIKI]`：日本 Wiki 的歷史玩家可見資料。
- `[X]`：多來源交叉吻合。
- `[OPEN]`：尚未充分證明。

## 尚待整合

`Character_Inventory_Equipment_DeepEvidence.md` 目前仍含有本主題的深入研究。它暫時保留，直到逐段搬入本文件並確認沒有證據遺失，再刪除重複文件。

## 相關文件

- `MyInfo_198_ClientData_Field_Schema.md`
- `MyInfo_198_Composite_Codec_Evidence.md`
- `Currency_State_Field_Evidence.md`
- `Resource_Pack_Model.md`
