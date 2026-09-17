# `CGameRule` 與主要遊戲生命週期研究

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：只保存 `CGameRule` 狀態機、生命週期因果、跨物件關係與待閉合節點；`101–192` 的精確 opcode 欄位統一回 `Room_Channel_GameRule_101_192_Field_Evidence.md`。

## 1. 研究目標

恢復：

```text
Lobby / Room
    ↓
Ready
    ↓
Start
    ↓
Match 初始化
    ↓
Gameplay / Round
    ↓
End / Leave
    ↓
返回 Room / Lobby
```

並將各階段連回：

```text
CGameRule
Player Slot / Team
Room
Map
Mode
Round
Network packet
```

## 2. GameRule 封包家族

目前在 Client opcode-name table 中已確認主要 GameRule 操作：

```text
121 GR_MAPCHANGE_REQ
122 GR_MAPCHANGE_ACK
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK
127 GR_READY_REQ
128 GR_READY_ACK
129 GR_START_REQ
130 GR_START_ACK
131 GR_FORCEOUT_REQ
132 GR_FORCEOUT_ACK
133 GR_END_REQ
134 GR_END_ACK
135 GR_CHANGESLOT_REQ
136 GR_CHANGESLOT_ACK
137 GR_STARTTIME_REQ
138 GR_STARTTIME_ACK
189 GR_CHANGEMASTER_REQ
190 GR_CHANGEMASTER_ACK
```

這些名稱只用來描述生命週期節點；實際 payload、欄位寬度與 parser 以：

```text
Room_Channel_GameRule_101_192_Field_Evidence.md
```

為唯一欄位真相。

## 3. Ready 狀態

Ready 的核心因果是：

```text
Room player object
    ↓
本地 Ready precondition
    ↓
127 GR_READY_REQ
    ↓
128 GR_READY_ACK
    ↓
Player room-state mutation
    ↓
Lobby / Room UI refresh
```

C 已證明 `127` 在 sender 前存在本地資格檢查；因此 Server reconstruction 不能把 Ready 視為完全無條件的 client toggle。

`128` 的 wire schema、player identity 欄位與 state byte 請只從 Field Evidence 回讀。

## 4. Start 狀態

目前最重要的狀態鏈：

```text
Ready / Room conditions
    ↓
129 GR_START_REQ
    ↓
130 GR_START_ACK
    ↓
player/game state synchronization
    ↓
CGameRule::NewGameStart
```

`129` 的 payload 並不是單純固定常數；其 sender 會由 Room/Map selector 狀態產生 start parameter。

`130` 則是大型玩家／遊戲狀態同步入口，之後才進入正式 GameRule 初始化。

## 5. `CGameRule::NewGameStart`：Match 初始化根節點

目前已觀察到 `NewGameStart` 會集中重設核心 GameRule state：

```text
+56 = 5000
+48 = 0
+8  = 0
+12 = 0
+20 = 0
+24 = 0
```

並進一步呼叫：

```text
sub_709330
sub_89B200
sub_720820
sub_67E560
```

同時執行 mode/map 相關初始化，並依 player count 等條件調整：

```text
+81
+82
```

重要限制：

```text
+56 = 5000
```

目前只能視為 GameRule 初始化值／time-like state，不能直接命名成「5 秒倒數」。必須與 `137/138`、tick routine、HUD 及 mode-specific code 交叉閉合。

## 6. Round / Gameplay 邊界

`NewGameStart` 後的工作模型為：

```text
GameRule initialized
    ↓
Mode initialization
    ↓
Map / player runtime initialization
    ↓
Gameplay
    ↓
Round-local state
    ↓
Result / End
```

目前 `166 subtype 13` 也會觸發與 `CGameRule::NewGameStart` 對得上的初始化／reset path，因此：

```text
GameRule_Lifecycle
      ↕
Gameplay_166_DeepEvidence
```

兩者應視為跨層關聯，而不是在兩份文件各自重複一套 GameStart 分析。

## 7. Map / Rule / Object selector 的生命週期角色

Room 設定在 GameRule 啟動前已形成一組 selector state：

```text
Map selector
Rule selector
Object / victory-condition selector
Time selector
Item / gimmick flags
Slot / team state
```

其 packet-level 實證集中於：

```text
Room_Settings_Packets.md
Room_Channel_GameRule_101_192_Field_Evidence.md
```

生命週期上可抽象為：

```text
Room configuration
    ↓
validated selector/value state
    ↓
Start precondition
    ↓
129
    ↓
GameRule initialization
```

這裡刻意不重複 selector 的每一個 u8/u16 wire field。

## 8. Change Slot / Master / Force Out

這些操作都屬於 Room/GameRule state mutation，但不應被合併成一個 generic player operation：

```text
135/136  Change Slot
189/190  Change Master
131/132  Force Out
```

它們都可能改變：

```text
Player
Slot
Team
Room ownership
UI state
```

但各自的 server transition 與 ACK schema 不同；packet-level 證據回 `Room_Channel_GameRule_101_192_Field_Evidence.md`。

## 9. Leave 與 End：兩條不同生命週期出口

目前已直接觀察到：

```text
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK

133 GR_END_REQ
134 GR_END_ACK
```

而 Client 上層 branch 會依 mode/state 選擇 123 或 133。

因此 Server model 應分開：

```text
LeaveRoom()
EndGame()
```

不能只用單一 `Leave()` 取代兩者。

## 10. Start Time / Loading 邊界

另一條重要鏈為：

```text
129 Start
    ↓
137/138 StartTime
    ↓
184 GR_ENDLOADING
    ↓
188 GG_STARTGAME
    ↓
Gameplay
```

這個順序目前仍屬「高價值待驗證生命週期模型」，因 `137/138` 的完整 sender/receiver 與 `184/188` 的所有 branch 尚未全部閉合。

因此：

```text
已確認：封包家族存在、互相屬於 GameRule／Loading／GameStart 層
未確認：所有版本與所有 mode 下的精確時序
```

## 11. Client object / server state 分離

目前必須維持以下層級：

```text
Room
├─ PlayerSlot
├─ Team
├─ Master
├─ RoomSettings
└─ GameRule

GameRule
├─ Match state
├─ Round state
├─ Mode state
├─ Map state
└─ Loading / Start state
```

但這是 reconstruction data model；不能直接當成原始 Server class hierarchy。

同樣地：

```text
Client object offset
≠
wire field offset
≠
server object layout
```

## 12. 與 Result / Gameplay 的跨層關聯

GameRule lifecycle 不負責重新定義 Result packet。

應沿：

```text
GameRule / Mode state
    ↓
Gameplay events
    ↓
round counters
    ↓
Result / Stat synchronization
```

目前對應主文件：

```text
Gameplay_166_DeepEvidence.md
Result_Stat_Protocol_223_245_381_389.md
TCP_269_Subtype7_Field_Detail.md
```

這些文件各自保存自己的 wire/data-flow 真相。

## 13. 三方證據使用方式

```text
Wiki
    → 玩家可見的 Room / Start / Mode 行為與歷史版本背景

Extracted
    → UI / Resource / Map / mode data identity

IDA C / LST
    → packet、state mutation、caller/callee、serializer/parser、實際寬度
```

其中：

```text
Wiki 不取代 wire evidence
Resource 不單獨決定欄位名稱
Hex-Rays local type 不取代 serializer width
```

## 14. 目前生命週期主線

```text
Login / Channel
      ↓
Lobby
      ↓
GameRoom / TournamentGameRoom
      ↓
Room configuration
      ↓
Ready
      ↓
129 Start Request
      ↓
130 Start Synchronization
      ↓
137/138 Start-time layer  [仍待完整閉合]
      ↓
184 Loading layer         [仍待完整閉合]
      ↓
188 GameStart layer       [仍待完整閉合]
      ↓
CGameRule::NewGameStart
      ↓
Gameplay / Round
      ↓
Result / End
      ↓
123 Leave or 133 End
      ↓
124 / 134
      ↓
Room / Lobby return
```

注意：這張圖是目前 Client evidence 支持的工作模型，不代表尚未閉合的 Server timing 或 mode-specific order 已經成為定論。

## 15. 文件責任分界

```text
GameRule_Lifecycle.md
    = 狀態機、生命週期、跨物件因果

Room_Channel_GameRule_101_192_Field_Evidence.md
    = 101–192 精確 packet / parser / serializer / field evidence

Room_Settings_Packets.md
    = Room UI selector/value 與設定封包

Channel_Lobby_Lifecycle.md
    = Channel → Lobby → Room 高階拓撲與進入／離開邊界

Server_State_Model.md
    = Server-side state ownership / synchronization abstraction
```

新增 GameRule 證據時，先判斷它是「欄位事實」還是「生命週期因果」；不要在兩份文件各複製一次。

## 16. 下一輪最高價值閉合點

```text
P0  129 → 130 → 137/138 → 184 → 188 精確時序
P0  CGameRule::NewGameStart caller / tick / end-state
P1  124/134 ACK 完整 state transition
P1  135/136 slot/team 完整 synchronization
P1  189/190 master transfer
P1  133 end → Result/Quest transition
P2  mode-specific GameRule branches
```
