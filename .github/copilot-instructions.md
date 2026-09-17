# PaperMan 研究與文件規則

本檔案提供 GitHub Copilot／Coding Agent 的工作入口；完整規則以根目錄 `AGENTS.md` 為準，不得與它建立第二套規則。

開始工作前必須閱讀：

```text
AGENTS.md
Research/README.md
Research/DOCUMENT_INDEX.md
```

強制要求：

- 所有 Markdown 一般說明文字只能使用繁體中文。
- 研究目標以日本版 PaperMan 2016 年服務終了時的最終 Client 為基準。
- 新增文件前先搜尋既有主題；能更新既有文件就不要建立新文件。
- `Research/DOCUMENT_INDEX.md` 是唯一研究文件索引；任何新增、刪除、合併、重新命名都必須同步維護。
- 研究結論必須區分 `[C]`、`[RES]`、`[WIKI]`、`[X]`、`[OPEN]`。
- Packet 欄位必須盡可能沿 serializer／parser、caller／callee、實際讀寫寬度、state field、資源與 Wiki 追證，不能靠欄位位置或名稱猜測。
- 未確認欄位不得為了讓 Server 編譯而偷偷填 `0` 或固定常數；需要時必須明確標示為相容性假設。
- 不得建立 `Final2`、`Latest`、`New`、`Copy` 等平行文件。
- 修改 Markdown 後必須執行 `python scripts/check_markdown.py`。

遇到矛盾時，以 `AGENTS.md` 為最高層級規則，並回到原始 Client、IDA C／LST、`Extracted/` 與 Wiki 證據。