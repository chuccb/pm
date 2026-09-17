# `166` 封包欄位索引

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 文件角色：`166` 的欄位總表與快速索引。
>
> 完整 parser、state mutation、Resource、K/D 與 subtype 證據統一放在 [`Gameplay_166_DeepEvidence.md`](Gameplay_166_DeepEvidence.md)。本文件不再維護第二份完整語意真相。

## 1. 外層結構

```text
166
├─ u8 actor／subject-like discriminator
├─ u8 subtype
└─ subtype-specific payload
```

接收鏈：

```text
sub_58B010
    → sub_58D820
    → sub_749B90
```

## 2. Subtype 欄位快速表

| subtype | 共用 Parser／Handler | 目前已知結構 | 詳細證據 |
|---:|---|---|---|
| 1 | `sub_746360` | `u8 target_id` | `Gameplay_166_DeepEvidence.md` |
| 2 | `sub_7463E0` | `u32 + u8 + u16×3 + u8×3 + u32×2 + u8` | `Gameplay_166_DeepEvidence.md` |
| 3 | `sub_747980` | `u32 + u8 + u16×3 + u8×2 + u32×2 + u8` | `Gameplay_166_DeepEvidence.md` |
| 4 | `sub_748860` | `u32 + u16 + u32×7` | `Gameplay_166_DeepEvidence.md` |
| 5 | `sub_748A50` | `u32 + u8 + u32×6` | `Gameplay_166_DeepEvidence.md` |
| 6 | `sub_748CD0` | `u16×2 + u32×6 + u8` | `Gameplay_166_DeepEvidence.md` |
| 7 | `sub_748E40` | NUL 結束字串 | `Gameplay_166_DeepEvidence.md` |
| 8/9/18/25 | `sub_748EB0` | 主要為 callback；部分 context 有附加 `u32` | `Gameplay_166_DeepEvidence.md` |
| 10 | `sub_749230`／`sub_749520` | `u8 participant + n13 + state/resource tail` | `Gameplay_166_DeepEvidence.md` |
| 11 | `sub_7494B0`／`sub_749810` | `u8 n7` | `Gameplay_166_DeepEvidence.md` |
| 12 | `sub_749A30` | `u16×2` | `Gameplay_166_DeepEvidence.md` |
| 13 | inline | lifecycle/reset path；實際 body 需依 parser context | `Gameplay_166_DeepEvidence.md` |
| 14 | `sub_749AB0` | `u32 + u16×4 + u8` | `Gameplay_166_DeepEvidence.md` |
| 15 | `sub_748420` | `u8 + u16 + u8×3 + u32×2 + u8` | `Gameplay_166_DeepEvidence.md` |
| 17 | `sub_748FF0` | callback/state family | `Gameplay_166_DeepEvidence.md` |
| 19/23/30/31/32 | `sub_74D150`／`sub_74D410`／`sub_74D510`／`sub_74D5D0` | parser 尚未完整閉合 | `Gameplay_166_DeepEvidence.md` |
| 20 | `sub_747980` | 與 subtype 3 共用 parser，context 不同 | `Gameplay_166_DeepEvidence.md` |
| 21 | `sub_747DD0` | `u8 + u16 + u8×2` | `Gameplay_166_DeepEvidence.md` |
| 22 | `sub_747AB0` | `u32 + u8 + u16 + u8 + u32×2 + u8` | `Gameplay_166_DeepEvidence.md` |
| 24 | inline | `u16×2 + u32 + u8` | `Gameplay_166_DeepEvidence.md` |
| 26 | `sub_745F50` | `u32 + u16×3 + u8×5 + u32` | `Gameplay_166_DeepEvidence.md` |
| 27/29 | `sub_746060` | `u32 + u16×4 + u8 + u32×2 + u8 + u32×2 + u8` | `Gameplay_166_DeepEvidence.md` |

上述表只作欄位索引；公開 semantic 若未由主文件證據閉合，保持 raw／candidate。

## 3. 欄位命名規則

```text
RawXX
fieldXX
value_N
```

只有 `Gameplay_166_DeepEvidence.md` 內的證據真正閉合後，才在本表升級名稱。不能先因名稱相似就建立猜測式 public enum。

## 4. 常用交叉索引

```text
166 subtype 2/16
    → Gameplay_166_DeepEvidence.md
    → 269 subtype 7
    → +240600/+240604
    → +60150/+60151

166 subtype 14
    → UDP_Move_Inf_DeepEvidence.md

166 subtype 13
    → GameRule_Lifecycle.md

166 subtype 3/20/21/22
    → Resource metadata
    → effect/state bridge
```

## 5. 文件維護規則

若新證據只改變欄位寬度或順序，更新本表並同步主文件。

若新證據改變語意、state mutation 或 lifecycle，先更新 `Gameplay_166_DeepEvidence.md`，再回填本表。

不得在本文件重新複製完整 parser 分析。
