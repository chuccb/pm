# PaperMan 逆向研究

> 研究日期：2026-09-16

本目錄集中保存 PaperMan 日版客戶端的逆向、遊戲機制、封包協定與資源交叉驗證結果。

## 證據分級

- `[WIKI]`：日本 PaperMan Wiki 的玩家可見規則。
- `[C]`：`PaperMan.exe.c` 中可直接觀察到的 Hex-Rays 反編譯結果。
- `[RES]`：從 `Extracted/` 提取出的遊戲資源、XML、封包資源表等。
- `[X]`：多條獨立證據彼此交叉吻合。
- `[OPEN]`：仍未充分證明，不應直接硬編碼。

Hex-Rays 的變數名稱、型別與部分控制流程可能是錯誤恢復結果；研究文件應優先保存原始函式位址、實際讀寫寬度、caller/callee 關係及資料流，再建立語意名稱。

## 研究區

### `KickVote/`

踢人投票系統。包含：

- 玩家可見流程與 Wiki 對照
- 718–723 遊戲規則投票協定
- `Voter` / `VoterMgr` / `CVoteTargetList` / `CVotingStateUI` 等狀態機
- Team Kick / Full Kick、6 種理由、目標列表與倒數
- `PM_KICKUSER_REQ/ACK` 396/397 的 Master／房間層分離

### `Core/`

主要遊戲機制，優先研究：

- 房間生命週期
- Ready / Start / End
- 玩家加入、離開、換位、房主轉移
- 地圖切換
- GameRule 狀態機
- 遊戲模式與回合／時間限制
- 玩家 slot、team、map、round、game state
- 主要遊戲事件與核心封包

### `Resources/`

遊戲資源與 C 程式碼的三方對照，包括：

- `Extracted/ui`
- `Extracted/map`
- `Extracted/item`
- `Extracted/character`
- `ClientDataList.xml`
- `0.xml`
- localization/resource ID

## 研究方法

對每個主要功能，不只搜尋字串，而是沿著完整生命週期追查：

```text
玩家輸入 / 房間操作
    -> 狀態變更
    -> GameRule / Manager
    -> 封包建立
    -> 封包傳送
    -> 接收端 dispatcher
    -> 狀態更新
    -> UI / 資源
    -> Wiki 可見行為
```

遇到間接 virtual call 時，優先追：

```text
vtable slot
    -> concrete implementation
    -> argument provenance
    -> state-field read/write
    -> packet serializer/parser
```

封包欄位寬度以實際 serializer / parser 為最高優先級，不以 Hex-Rays 猜出的參數型別為準。

## 主要研究順序

目前 Kick Vote 的主要協定骨架已大致恢復，因此後續重點轉向整個遊戲的核心機制：

1. `CGameRule` 遊戲生命週期與狀態機
2. `GR_READY_REQ/ACK`、`GR_START_REQ/ACK`、`GR_END_REQ/ACK`
3. `GR_LEAVE_REQ/ACK`、`GR_FORCEOUT_REQ/ACK`
4. `GR_MAPCHANGE_REQ/ACK`
5. 玩家 slot / team / master / user state
6. 地圖、回合、倒數、勝負條件
7. 各主要遊戲模式的 mode-specific state 與事件
8. 戰鬥、傷害、死亡、擊殺、重生等核心事件
9. 資源與協定欄位語意三方交叉驗證

所有尚未證明的結論都應保留 `[OPEN]` 標記，直到能由 `C`、`RES`、`WIKI` 或其他獨立證據封閉。
