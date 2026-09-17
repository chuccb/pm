# Kick Vote 研究入口

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

Kick Vote 已將 UI、target/voter eligibility、718–723 協定、139 lifecycle、131/132 Force Out 與 396/397 Master/Room 關係整合到單一主文件：

```text
Research/KickVote/Research.md
```

## 閱讀方式

直接閱讀 [`Research.md`](Research.md)。

內容依大方向分為：

```text
UI / Scope / Reason / Target
        ↓
Eligibility / Voter state
        ↓
718–723 protocol
        ↓
139 lifecycle signal
        ↓
131/132 Force Out
        ↓
396/397 Master / Room
        ↓
Server reconstruction
```

完整證據仍以：

```text
PaperMan.exe.c / LST
Extracted/
日本 PaperMan Wiki
```

三方交叉確認為準；未知項目保留 `[OPEN]`，不因 Server 實作需要而自行填入 `0`、固定值或 guessed enum。

整個儲存庫的維護規則以 [`AGENTS.md`](../../AGENTS.md) 為最高層級規則，研究文件索引以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為唯一入口。
