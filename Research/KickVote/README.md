# Kick Vote 研究總覽

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Kick Vote 專題入口與研究導覽；完整協定、UI、資格條件與 Master／Room 分層不得在本 README 重複維護。

## 1. 研究範圍

本專題研究：

```text
Vote target
Voter eligibility
Reason selection
Vote request / acknowledgement
Vote state / timer
Vote result
Master / Room kick
```

證據來源固定為：

```text
IDA / Hex-Rays C / LST / ASM
        ↕
Extracted 資源
        ↕
日本 PaperMan Wiki
```

未知欄位保持 `[OPEN]`；不得只依 packet name 或 Hex-Rays 表面型別命名。

## 2. 專題文件分工

| 文件 | 唯一責任 |
|---|---|
| [`Protocol.md`](Protocol.md) | `718–723` 協定、serializer/parser、payload 與封包資料流 |
| [`UI_State.md`](UI_State.md) | Vote UI、候選清單、投票狀態機、計時器與重複投票鎖定 |
| [`Evidence_And_Eligibility.md`](Evidence_And_Eligibility.md) | Wiki／C／Resource 交叉證據與 voter／target eligibility |
| [`Master_Room.md`](Master_Room.md) | `396/397` Master／Room kick 層 |

若需要新增 Kick Vote 證據，先判斷屬於哪一份主文件；沒有新責任就更新既有文件，不要新增平行副本。

## 3. 已閉合的高階流程

```text
選擇 Scope
    ↓
確認 voter / target eligibility
    ↓
選擇 Reason
    ↓
718 啟動投票
    ↓
719 / 720 Server → Client 投票狀態
    ↓
721 投票
    ↓
722 結果
    ↓
723 結束結果／後續狀態
```

`396/397` 為另一層 Master／Room 操作；目前不能因流程相近就直接視為 `718–723` 的別名。

## 4. 目前的重要共識

```text
Team / Full Scope 的候選資格
    != 單純 players.Count

PlayerId
    != SlotIndex

Vote packet field
    != Server eligibility decision

Wiki 的 70 秒
    != Client 中所有其他局部 UI timer
```

這些概念必須在專題內保持分離，避免 Server reconstruction 被 UI implementation 或歷史命名污染。

## 5. Server reconstruction 的邊界

Kick Vote 最終應拆成至少：

```text
VoteScope
VoteEligibility
VoteTargetSet
VoteReason
VoteState
VoteDeadline
VoteResponse
VoteResult
RoomKick / MasterKick
```

但這些是目前的 reconstruction abstraction，不代表原 Client／Server class hierarchy 已完全恢復。

## 6. 目前研究入口

先讀：

```text
Protocol.md
Evidence_And_Eligibility.md
UI_State.md
Master_Room.md
```

再把閉合結果接回：

```text
Research/Core/Player_Slot_Team.md
Research/Core/Server_State_Model.md
```

本 README 只負責導航；任何具體欄位、函式、常數與證據應回到對應主文件維護。

## 7. 維護規則

```text
同一欄位只保留一份主真相
新證據更新既有主文件
新增文件必須有明確新責任
索引同步更新
所有新的 Markdown 說明使用繁體中文
```

完整儲存庫規則以根目錄 `AGENTS.md` 為準。