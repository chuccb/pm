# PaperMan Client — 證據驅動逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。

本儲存庫保存 PaperMan 最終版 Client 的逆向研究資料、完整遊戲資源、IDA 反編譯結果，以及從 Client、`Extracted/` 與日本 PaperMan Wiki 交叉驗證得到的研究結果。

## 研究入口

閱讀順序固定為：

1. [研究與維護規則](AGENTS.md)
2. [研究總覽](Research/README.md)
3. [完整文件索引](Research/DOCUMENT_INDEX.md)
4. [核心遊戲機制](Research/Core/README.md)
5. [Kick Vote](Research/KickVote/README.md)

GitHub Copilot／Coding Agent 另有 [Copilot 研究規則](.github/copilot-instructions.md)，內容不得與 `AGENTS.md` 分叉。

## 證據來源

研究結論不以單一來源為準：

- `PaperMan.exe`：原始 Client。
- `PaperMan.exe.c`：IDA / Hex-Rays 反編譯輸出。
- `PaperMan.exe.lst.zip`：IDA LST 輸出。
- `Extracted/`：完整遊戲資源與資料檔。
- 日本 PaperMan Wiki：歷史玩家可見行為與版本資料。

## 文件原則

所有 Markdown 的一般說明文字、標題、表格與註解一律使用繁體中文。程式碼、封包名稱、函式名稱、變數名稱、檔案路徑、API、外部識別字與必要的原文證據可維持原樣。

同一概念只能有一份主要真相。新增文件前必須先搜尋既有研究；能更新舊文件就不要建立副本。所有研究 Markdown 都必須出現在 `Research/DOCUMENT_INDEX.md`。

研究證據必須區分 `[C]`、`[RES]`、`[WIKI]`、`[X]` 與 `[OPEN]`。Packet 欄位要盡可能從 serializer／parser、caller／callee、實際讀寫寬度、state field、資源與 Wiki 交叉確認；未知欄位不得為了讓 Server 編譯而偷偷填入 `0` 或固定值。

文件修改後執行：

```text
python scripts/check_markdown.py
```
