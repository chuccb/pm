# 角色、背包與裝備研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 
> 本文件是角色、背包與裝備主文件；與本主題相關的直接證據、欄位細節與深入交叉分析集中於此。新增研究應優先更新本文件，而不是另建平行摘要。

## 研究範圍

本主題涵蓋：

- Character 與角色狀態。
- Inventory 與持有物品。
- Equipment 與裝備欄位。
- Character、Inventory、Equipment 三者在 Client state、資源與網路同步中的關係。

## 目前研究狀態

目前已存在一份同主題的深入證據文件 `Character_Inventory_Equipment_DeepEvidence.md`。後續應將其可泛用的證據鏈整合至本文件；若某些段落只是對同一結論的重述，應以本文件中的單一結論為準。

## 整合規則

任何欄位結論必須區分：

```text
直接由 C / LST 觀察
→ 資源對照
→ Wiki／歷史行為對照
→ 交叉驗證
→ 尚未確認
```

不得因欄位名稱、資源名稱或數值排列看似合理，就直接建立伺服器語意。

## 相關文件

- `Character_Inventory_Equipment_DeepEvidence.md`：既有深入證據；後續應逐步併入本主文件，避免長期維持兩份平行結論。
- `MyInfo_198_ClientData_Field_Schema.md`：玩家 ClientData 與相關欄位。
- `Currency_State_Field_Evidence.md`：玩家貨幣與狀態欄位。
- `Resource_Pack_Model.md`：資源資料模型與資源對照。
