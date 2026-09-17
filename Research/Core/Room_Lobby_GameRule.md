# Room／Lobby／Player／Map／GameRule 整合研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：將 Channel、Lobby、Room、Player Slot／Team、Map、GameRule 與其共同生命週期集中於同一大方向主文件。精確 packet wire 欄位仍由對應 Field Evidence 維護，不在本文件建立第二份欄位真相。

## 1. 整體生命週期

```text
Login
  ↓
Channel / Lobby
  ↓
Room list
  ↓
建立／進入 Room
  ↓
PlayerSlot[16] / Team / Master
  ↓
Room settings
  ↓
Ready
  ↓
Start
  ↓
Match initialization
  ↓
Gameplay / Round
  ↓
Result / End
  ↓
Leave / Room return
```

C 中可直接觀察 `CLobbyLogin`、`CLobbyGameRoom`、`CLobbyTournamentGameRoom`、`CGameRule` 等 Client object layer；這只是 Client object/state layering，不等同於 Server process 或 TCP connection topology。

## 2. Channel → Lobby → Room

PaperMan Wiki 歷史資料指出，2014-06-25 曾進行「チャンネル（待機ロビーとゲームルーム）の紐付けの解消（サーバーチャンネル統合）」。因此 2016 Final 不應直接套用更早期的 Server Channel topology。

目前 evidence-supported Client-side model：

```text
Login UI
  ↓
682 GL_LOGIN_REQ
  ↓
681 GL_LOGIN_ACK
  ↓
server/channel bootstrap
  ↓
Channel / Lobby
  ↓
193/194 channel state family
  ↓
195/196 channel entry family
  ↓
Lobby / Room list
  ↓
GameRoom / TournamentGameRoom
```

`681/682` 精確欄位由 `Login_Adjacent_680_696_Field_Schema.md` 維護；`193–221` 精確欄位由 `Channel_Lobby_193_221_Field_Evidence.md` 維護。

生命週期上另外已確認的重要定位：

```text
199/200 → Item / ClientData bootstrap
201–221 → ClientData / item / collection synchronization
370     → Channel change request
```

195 為 3-byte request、197 為 0-byte request、370 為 1-byte request；精確 field semantic 不在此重複。

## 3. 固定 16-slot Player 模型

`PaperMan.exe.c` 中大量核心函式以：

```c
for (i = 0; i < 16; ++i)
```

掃描玩家資料表。玩家相關資料位於大型固定 stride 結構，例如 `byte_F33120`、`dword_F6DCF4`。

Kick Vote、Ready、Force Out、Change Slot、Match Start 等多個子系統都依賴此 16-slot 模型。

`sub_67D110()` 會利用全域 `::n0x10` 在 16 個 player record 中尋找對應項目，因此：

```text
PlayerId / client player identity
    ≠
SlotIndex
```

Server model 必須分開保存：

```text
PlayerId
SlotIndex
Active / Occupied
Team / Group relation
```

不能因兩者都可能以 byte/int 形式出現就視為同一值。

## 4. Player、Slot 與 Team／Group

一般路徑中：

```text
sub_67D240()
    → local player group/team value

sub_67D520(slot)
    → target player group/team value

sub_67D3F0(slot)
    → 比較兩者是否相等
```

`sub_67D3F0()` 的一般邏輯為：

```c
if (sub_67EB70())
    return true;
return sub_67D520(slot) == sub_67D240();
```

因此 Team Kick 的底層 filtering 確實依賴 player grouping，但仍不能把所有 group-like value 都命名成正式 `TeamId`。

Client 另外還存在：

```text
sub_67D600(a,b)
    → sub_67D440(a) == sub_67D440(b)

sub_67D630(a,b)
    → sub_67D520(a) == sub_67D520(b)
```

顯示至少存在兩種玩家分類／關係值，應保持語意分離。

## 5. Slot active／occupied 狀態

`sub_67D310(slot)` 的一般路徑：

```text
slot >= 16                 → return 0
byte_F6D9E4[slot] != 0     → return 0
byte_F6DD11[slot] != 0     → return 0
player id == local id      → return 2
otherwise                  → return 1
```

因此在沒有特殊 `sub_67E940()` override 時：

```text
0 → 不視為一般 active participant
1 → active participant，非 local
2 → active participant，且為 local
```

`sub_67D680()` 與 `sub_67D6F0()` 另外提供「全部有效玩家是否完成特定狀態」的 global check，因此某些操作不應只用 room count 判定。

## 6. Lobby → Room → Ready → Start

玩家可見操作與 Client object model 目前形成：

```text
進入 Channel
  ↓
Lobby
  ↓
Room list
  ↓
建立／進入 Room
  ↓
Room Master / PlayerSlot[16]
  ↓
Room settings
  ↓
127 GR_READY_REQ
  ↓
128 GR_READY_ACK
  ↓
129 GR_START_REQ
  ↓
130 GR_START_ACK
  ↓
CGameRule::NewGameStart
```

`127` 在 Client sender 前有 local precondition，因此 Ready 不是無條件 client toggle。

`129` 的參數又與 `GAMEROOM_SCROLL_MAP` selector value 有資料流關係，不能只把它當 generic start flag。

## 7. Room selector 模型

Room UI 至少直接操作：

```text
GAMEROOM_START
GAMEROOM_READY
GAMEROOM_SCROLL_MAP
GAMEROOM_SCROLL_RULE
GAMEROOM_SCROLL_OBJECT
GAMEROOM_SCROLL_TIME
GAMEROOM_ITEM
GAMEROOM_GIMMICK
GAMEROOM_TEAMBALANCE
GAMEROOM_DAMAGEROOM
GAMEROOM_USERSLOTS
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_CHATMODE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_MASTERROOM
GAMEROOM_LOCALROOM
```

多個 scroll control 共用 40-byte entry：

```text
entry stride = 40 bytes
entry value  = +36
```

所以 Server／研究模型必須區分：

```text
OptionIndex
OptionValue
```

不可假設 `OptionIndex == OptionValue`。

## 8. Map selector

核心 Client／Resource chain：

```text
Extracted/map/maplist.dat
        ↓
GAMEROOM_SCROLL_MAP
        ↓
40-byte UI entry
        ↓
entry value @ +36
        ↓
121 GR_MAPCHANGE_REQ / 122 GR_MAPCHANGE_ACK
        ↓
Room / Map state
```

Start 路徑另有：

```text
Start precondition
    ↓
sub_437060()
    ↓
GAMEROOM_SCROLL_MAP
    ↓
selected / derived OptionValue
    ↓
129 GR_START_REQ
```

因此目前只能安全稱為 `map_value` / `OptionValue`；尚不能只依名稱把它定成 `map_id`。`rand()` 出現在 `sub_437060()` 也不足以直接命名成 `random_map`。

地圖尚待閉合：

```text
sub_4387B0()
    → entry value 的正式 namespace

sub_6B9B10()
    → 122 後完整 Room/GameRule mutation

sub_439600()
    → 特殊地圖列表／選擇型態

130 / NewGameStart
    → selector 如何進入真正 map loading
```

## 9. CGameRule 主生命週期

主要 GameRule family：

```text
121/122  Map change
123/124  Leave
127/128  Ready
129/130  Start
131/132  Force Out
133/134  End
135/136  Change Slot
137/138  Start Time
189/190  Change Master
```

這些名稱只描述生命週期節點；精確 payload 以 `Room_Channel_GameRule_101_192_Field_Evidence.md` 為唯一欄位主文件。

核心狀態鏈：

```text
Room conditions
    ↓
Ready
    ↓
129 Start Request
    ↓
130 Start Synchronization
    ↓
137/138 Start-time layer       [待完整閉合]
    ↓
184 End-loading layer          [待完整閉合]
    ↓
188 Game-start layer           [待完整閉合]
    ↓
CGameRule::NewGameStart
    ↓
Gameplay / Round
    ↓
Result / End
```

## 10. `CGameRule::NewGameStart`

目前已觀察到集中重設：

```text
+56 = 5000
+48 = 0
+8  = 0
+12 = 0
+20 = 0
+24 = 0
```

並呼叫：

```text
sub_709330
sub_89B200
sub_720820
sub_67E560
```

同時進行 mode/map 初始化，並依 player distribution／count 更新：

```text
+81
+82
```

`+56 = 5000` 目前只能稱為 GameRule initialization time-like value；不能單獨命名成「5 秒倒數」。需再與 `137/138`、tick、HUD、mode-specific code 閉環。

`NewGameStart` 會掃描 PlayerSlot 並依 grouping 分成兩群：

```text
if (n2 < 2 || n2_1 < 2)
    +82 = 1
    +81 = 1
```

因此 Start 相關 server model 不能只看「玩家總數」。

## 11. Change Slot／Master／Force Out

這三類都會修改 Room/Player state，但不能合併成單一 generic operation：

```text
135/136 → Change Slot
189/190 → Change Master
131/132 → Force Out
```

它們都可能影響：

```text
Player
Slot
Team
Room ownership
UI state
```

但 server transition 與 ACK schema 不同，應保持獨立事件模型。

## 12. Leave 與 End

Client 明確存在兩條不同出口：

```text
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK

133 GR_END_REQ
134 GR_END_ACK
```

因此 Server reconstruction 應區分：

```text
LeaveRoom()
EndGame()
```

不能把兩者壓成單一 `Leave()`。

## 13. 三方交叉驗證規則

主要來源分工：

```text
IDA C / LST
    → serializer / parser / caller / callee / state mutation / wire width

Extracted
    → Resource、Map、UI、Character 等 concrete identity

日本 PaperMan Wiki
    → 玩家可見規則、操作、歷史版本背景
```

遇到衝突時：

```text
不要選「看起來合理」的答案
    ↓
回到更底層 serializer / parser / data-flow
    ↓
確認版本範圍
    ↓
仍無法閉合 → [OPEN]
```

## 14. Server reconstruction 邊界

目前最小 Server abstraction：

```text
Room
├─ RoomSettings
├─ PlayerSlot[16]
├─ Team / Group
├─ MasterPlayerId
└─ RoomPhase

MatchRuntime
├─ GameMode
├─ MapValue
├─ RoundState
├─ PlayerRuntime[16]
└─ ResultState
```

但這只是 reconstruction model，不代表原始 Server class hierarchy。

同時維持：

```text
Client object offset
    ≠ wire field offset
    ≠ server object layout
```

## 15. 目前最高價值閉合點

```text
P0  196 → Lobby/Channel object update
P0  681 → Channel/server record closure
P0  129 → 130 → 137/138 → 184 → 188 precise timing
P0  CGameRule::NewGameStart caller / tick / end-state
P1  PlayerSlot / Team helper closure
P1  124 / 134 complete state transition
P1  135 / 136 slot/team synchronization
P1  189 / 190 master transfer
P1  133 → Result / Quest transition
P1  Map selector → actual map loading
```

## 16. 相關主文件

```text
Network_Protocol.md
    = 網路、TCP/UDP、frame、codec、dispatcher

Login_Adjacent_680_696_Field_Schema.md
    = 680–696 wire schema

MyInfo_198_ClientData_Field_Schema.md
ClientData_Shared_Decoder_Field_Evidence.md
    = 198 與共用 ClientData wire family

Room_Channel_GameRule_101_192_Field_Evidence.md
Channel_Lobby_193_221_Field_Evidence.md
Room_Settings_Packets.md
    = 精確 packet / field evidence

Gameplay_166_DeepEvidence.md
Y_TCP_INF_Damage.md
UDP_Move_Inf_DeepEvidence.md
    = Gameplay / network event evidence

KickVote/Research.md
    = Kick Vote 完整研究

Server_State_Model.md
    = 跨子系統 Server abstraction
```
