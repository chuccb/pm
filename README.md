# PaperMan Client — 證據驅動逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。

本儲存庫保存 PaperMan 最終版 Client 的逆向研究資料、完整遊戲資源、IDA 反編譯結果，以及依據 Client、`Extracted/` 與日本 Wiki 交叉驗證後形成的研究文件。

## 研究入口

- [研究總覽](Research/README.md)
- [完整文件索引](Research/DOCUMENT_INDEX.md)
- [核心遊戲機制](Research/Core/README.md)
- [Kick Vote](Research/KickVote/README.md)
- [文件與研究規範](AGENTS.md)

## 證據來源

研究結論以以下來源互相驗證，而不是只依賴單一來源：

- `PaperMan.exe`：原始 Client。
- `PaperMan.exe.c`：IDA / Hex-Rays 反編譯輸出。
- `PaperMan.exe.lst.zip`：IDA LST 輸出。
- `Extracted/`：完整遊戲資源與資料檔。
- 日本 PaperMan Wiki：歷史玩家可見行為與版本資料。

## 文件原則

所有 Markdown 的說明文字、標題、表格與註解一律使用**繁體中文**。程式碼、封包名稱、函式名稱、變數名稱、檔案路徑、API 名稱、正式產品名稱及必要的原文內容可維持原樣。

研究文件必須清楚區分「直接證據」、「交叉推導」與「尚未確認」。禁止把推測當成已確認協定，也禁止以方便實作為由替未知欄位任意填入數值。

文件新增、修改或合併後，必須同步維護 `Research/DOCUMENT_INDEX.md`；不要為同一概念建立第二份平行真相。
