# PaperMan 逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 研究基準日：2026-09-17。
> 研究文件角色：`Research/` 的總入口，不承載單一封包或單一函式的完整細節。

本目錄保存 PaperMan 日版最終 Client 的逆向研究、遊戲機制、封包協定、資源分析與三方交叉驗證結果。

## 最短閱讀路徑

```text
第一次進入研究
    ↓
Research/README.md
    ↓
DOCUMENT_INDEX.md
    ↓
用「我要查什麼」找到第一入口
    ↓
主文件
    ↓
必要時才深入 Field Evidence / Schema / Detail
```

不要為了找一個 Packet 或 State 同時打開所有 Markdown。`DOCUMENT_INDEX.md` 的「最快定位」表就是為了先縮小上下文。

## 先讀這三份

```text
AGENTS.md
    ↓
Research/README.md
    ↓
Research/DOCUMENT_INDEX.md
```

`AGENTS.md` 是維護規則；本文件是研究總覽；`DOCUMENT_INDEX.md` 是全部研究 Markdown 的唯一索引與問題定位入口。

## 研究材料

```text
PaperMan.exe / PaperMan.exe.c / PaperMan.exe.lst.zip
                         ↕
                    Extracted/
                         ↕
             日本 PaperMan Wiki
```

其中：

- `PaperMan.exe.c`：IDA／Hex-Rays 反編譯輸出。
- `PaperMan.exe.lst.zip`：IDA LST 與更低階的反組譯資訊。
- `Extracted/`：完整遊戲資源與資料檔。
- 日本 PaperMan Wiki：歷史玩家可見的規則、內容與版本資料。

任何研究結論都必須保留其來源與版本上下文。

## 版本原則

研究的 primary target 固定是：

```text
日本版 PaperMan
2016-12-26 服務終了時的最終 Client
```

同名封包、模式、資源或規則在不同年份、地區或 Client 中不保證相同。

較早資料可以用於：

```text
版本演進
旁證
反證
歷史差異
```

但不得未標記地覆蓋 2016 final Client 的直接證據。

## 證據標記

| 標記 | 定義 |
|---|---|
| `[C]` | `PaperMan.exe.c` 中可以直接觀察的反編譯證據 |
| `[RES]` | `Extracted/` 中的資源或資料檔證據 |
| `[WIKI]` | 日本 PaperMan Wiki 的歷史玩家可見資料 |
| `[X]` | 兩種以上獨立來源互相吻合 |
| `[OPEN]` | 尚未充分證明，不可當作已確認協定 |

`[C]` 不等於「Hex-Rays 猜測一定正確」。函式名稱、變數名稱、型別與部分控制流程仍需用實際讀寫、caller／callee、資料流與其他來源驗證。

## 三方交叉驗證方法

每個重要功能盡可能沿著以下鏈路追查：

```text
玩家操作／事件
    ↓
Client state
    ↓
packet serializer
    ↓
network transport / dispatcher
    ↓
packet parser
    ↓
GameRule / Room / Player state
    ↓
UI / Resource
    ↕
Wiki 行為
```

封包欄位的寬度與位置，以實際 serializer／parser 的讀寫為最高優先級；不要因欄位名稱、相鄰位置或常見協定習慣而自行命名。

遇到 virtual call 時，優先追：

```text
vtable slot
→ concrete implementation
→ caller / callee
→ argument provenance
→ state-field read / write
→ serializer / parser
```

## 研究文件如何分工

`Research/DOCUMENT_INDEX.md` 是文件間的真正導航；`Research/Core/README.md` 則提供 Core 內部更細的問題定位。

```text
Research/DOCUMENT_INDEX.md
    = 「我該去哪份文件？」

Core/README.md
    = 「這個主題各文件怎麼分工？」

各主文件
    = 「目前已知什麼？」

Field Evidence / Schema / Detail
    = 「具體欄位、函式、讀寫與證據是什麼？」

C / LST / Extracted / Wiki
    = 「這個結論為什麼成立？」
```

大方向如下：

```text
網路與 Dispatcher
    ↓
Login / ClientData
    ↓
Channel / Lobby / Room
    ↓
Player / Slot / Team
    ↓
GameRule / Mode
    ↓
Gameplay / Combat / Movement
    ↓
Result / Quest / Resource
```

文件名稱中的角色也有固定語意：

- `Protocol`：封包或資料流整體協定。
- `Schema`：欄位、型別、寬度與資料結構。
- `Field_Evidence`／`Field_Semantics`：欄位來源與語意證據。
- `DeepEvidence`：跨函式、跨資源、跨來源的完整證據鏈。
- `Detail`：單一封包或窄功能的深入拆解。
- `Lifecycle`：生命週期與狀態轉移。
- `State`：狀態資料與狀態機。
- `README`：入口與導航，不堆放大量細節。

## 新研究的標準流程

```text
1. 先閱讀 AGENTS.md
2. 閱讀本文件與 DOCUMENT_INDEX.md
3. 用索引的「最快定位」找到第一入口
4. 搜尋既有文件與相同 Opcode／函式／資源
5. 找到主文件後直接擴充，不建立平行副本
6. 從 C / LST 追 serializer、parser、caller、callee 與 state field
7. 對照 Extracted 資源
8. 對照 Wiki 與版本資料
9. 區分已確認、交叉推導與 OPEN
10. 更新主文件、主題 README、DOCUMENT_INDEX
11. 執行 python scripts/check_markdown.py
```

## 未確認事項

研究可以長期累積，因此未知資訊必須保留在 `[OPEN]`，不可因 Server 實作需要而偷偷改成 `0`、固定常數或看似合理的欄位。

若實作階段真的需要預設值，文件必須明確寫成：

```text
相容性假設，不是逆向確認
```

## 維護邊界

本文件不重複保存各專題的完整內容；詳細研究請從 [`DOCUMENT_INDEX.md`](DOCUMENT_INDEX.md) 或其「最快定位」表進入。

所有文件格式、命名、語言、證據與更新規則以根目錄 [`AGENTS.md`](../AGENTS.md) 為準。
