# Channel → Lobby → Room 生命週期與 2016 Final Client

> 研究日期：2026-09-17
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：只保存 Channel → Lobby → Room 的生命週期、物件邊界與跨封包狀態轉移；精確 wire 欄位統一回 `Channel_Lobby_193_221_Field_Evidence.md`、`GameRule_Lifecycle.md` 與其他對應主文件。

## 1. 版本基線

PaperMan Wiki 的歷史資料記載 2014-06-25 已進行「チャンネル（待機ロビーとゲームルーム）の紐付けの解消（サーバーチャンネル統合）」。因此 2016 Final 不應直接套用更早期的 Server Channel 拓撲。

這不代表 Client object layer 中不存在 Lobby / Room；C 中仍可直接看到：

```text
CLobbyLogin
CLobbyGameRoom
CLobbyTournamentGameRoom
CGameRule
```

所以目前採用的工作模型是：

```text
Login
  ↓
Server / Channel state
  ↓
Lobby state
  ↓
GameRoom / TournamentGameRoom
  ↓
CGameRule
```

這是 Client object/state layering，不等於 Server process 或 TCP connection layering。

## 2. Login → Channel 的生命週期

目前已閉合的高階流程：

```text
Login UI
  ↓
credential validation
  ↓
682 GL_LOGIN_REQ
  ↓
681 GL_LOGIN_ACK
  ↓
server/channel bootstrap data
  ↓
Channel / Lobby layer
```

`681/682` 的完整欄位 schema 不在本文件重複；請使用：

```text
Login_Adjacent_680_696_Field_Schema.md
```

該文件負責 680–696 的欄位與 parser 證據。

## 3. Channel / Lobby 封包邊界

本生命週期只記錄它們在狀態機中的位置；精確欄位、讀寫寬度與 parser 必須回到：

```text
Channel_Lobby_193_221_Field_Evidence.md
```

目前生命週期上可定位：

```text
193/194  Channel list / channel-state family
195/196  Channel entry request / response
197/198  MyInfo bootstrap request / response
199/200  Item/client-data bootstrap family
201–221  ClientData / item / collection synchronization family
370      Channel change request
```

注意：上述「family」是生命週期定位，不代表每個 opcode 的公開 business name 都已完全閉合。

已直接封死的重點例如：

```text
195 → 3-byte request
197 → 0-byte request
370 → 1-byte request
```

其精確欄位名稱仍遵循對應 Field Evidence 主文件。

## 4. Lobby → Room

Wiki 的玩家可見操作流程與 Client object model 形成高階交叉驗證：

```text
進入 Channel
  ↓
Lobby
  ↓
Room list
  ↓
進入／建立 Room
  ↓
Room Master / player slots
  ↓
Ready
  ↓
Start
```

這裡不要把 Wiki 的 UI 名稱直接當成 C 裡未知 byte 的正式 protocol enum；Wiki 用於 behavior-level semantic anchor，C/LST/Resource 才負責 wire closure。

## 5. Ready → Start

GameRule 層的核心生命週期是：

```text
Room
  ↓
127 GR_READY_REQ
  ↓
玩家 Ready state
  ↓
129 GR_START_REQ
  ↓
130 GR_START_ACK / player & game synchronization
  ↓
CGameRule::NewGameStart
```

完整 `127/128/129/130` wire 與 parser 證據統一放在：

```text
GameRule_Lifecycle.md
```

本文件不再複製它們的欄位表，避免日後兩份結論漂移。

## 6. Leave / End

生命週期上必須區分：

```text
GR_LEAVE_REQ  123
GR_LEAVE_ACK  124

GR_END_REQ    133
GR_END_ACK    134
```

目前 C 已證明 123 與 133 都存在無 payload request path，但兩者由不同上層狀態／模式分支觸發，因此 Server state machine 不應只建立一個泛化 `Leave()` 操作。

完整 receiver state transition 請回 `GameRule_Lifecycle.md`。

## 7. 與 Room / GameRule 的責任邊界

```text
Channel_Lobby_Lifecycle.md
    = Channel → Lobby → Room 的高階物件／狀態生命週期

Channel_Lobby_193_221_Field_Evidence.md
    = 193–221 精確 packet/parser/serializer evidence

GameRule_Lifecycle.md
    = Ready / Start / End / Leave / Slot / Master / GameRule state machine

Room_Settings_Packets.md
    = Room UI selector/value → request/ack → state 的專題證據

Server_State_Model.md
    = Server-side state object / ownership / synchronization model
```

這個責任切分是刻意保留的；只有真正不同的研究問題才維持獨立文件。

## 8. Cross-source constraints

```text
Wiki
  → 玩家可見操作、模式規則、歷史版本背景

Extracted
  → ClientData / Resource identity、UI、Map、Avatar 等具體資料

IDA C / LST
  → serializer、parser、caller/callee、state mutation、wire width
```

任何未知欄位都必須先沿 `C/LST → Resource → Wiki` 逐層閉合；未閉合前保持 `field_N`、`value_N` 或 `OPEN`。

## 9. 目前生命週期模型

```text
682 Login Req
      ↓
681 Login Ack / bootstrap
      ↓
Channel selection / entry
      ↓
193/194 channel state
      ↓
195/196 channel entry
      ↓
Lobby
      ↓
GameRoom / TournamentGameRoom
      ↓
Room settings / slots / team
      ↓
127 Ready
      ↓
129 Start
      ↓
130 synchronization
      ↓
CGameRule::NewGameStart
      ↓
Gameplay
      ↓
123 Leave  or  133 End
      ↓
124 / 134
      ↓
Lobby / Channel return
```

這是目前 evidence-supported 的高階模型，不把尚未閉合的 Server topology 或未知欄位當成定論。

## 10. 下一個閉合優先級

```text
P0  196 receiver → Lobby/Channel object update
P0  681 bootstrap → server/channel records
P0  198 → 200 → ClientData / item hydration
P1  Room list → Room entry → CLobbyGameRoom
P1  Room / TournamentRoom slot synchronization
P1  137/138 start-time state
P2  Channel change 370 → 681/196/channel state cross-link
```

所有新增證據應更新對應主文件，不在本文件再次建立一份 packet schema。