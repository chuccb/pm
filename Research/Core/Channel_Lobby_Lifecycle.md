# Channel → Lobby → Room 生命週期與 2016 Final Client 封包研究

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client
>
> 本文件專門收斂 Login 成功後的 Channel / Lobby / Room 邊界。所有尚未由 Client serializer/parser 或 caller/data-flow 封死的欄位，保持 OPEN，不以 packet 名稱猜語意。

## 1. 版本前提：2016 final 不應套用早期 Channel 架構

PaperMan Wiki 的歷史資料記載：2014-06-25 進行「チャンネル（待機ロビーとゲームルーム）の紐付けの解消（サーバーチャンネル統合）」。因此 2016 final 的研究模型應以統合後架構為基線，而不能直接假設早期「待機 Lobby 與 Game Room 分屬不同 server/channel」的舊拓撲。

這不表示 Lobby / Room 在 Client object layer 中不存在；Client 仍有明確的 Lobby、GameRoom、TournamentGameRoom 類別與 UI state。它只表示兩者與 Server Channel 的關係必須依 final Client packet flow 重建。

[W] Wiki：GamePot 宿題頁記載 2014-06-25 的伺服器 Channel 統合。

## 2. 目前已閉合的登入 → Channel 鏈

目前 Client 研究已確認：

```text
Login UI
  ↓
credential validation
  ↓
682 GL_LOGIN_REQ
  ↓
681 GL_LOGIN_ACK
  ↓
bootstrap / server-channel data hydration
  ↓
Channel / Lobby layer
```

### 2.1 `GL_LOGIN_REQ (682)`

Client sender `CLobbyLogin::sub_43DF00()` 會在 credential validation 成功後建立 682。

已從 serializer data-flow 確認它不是單純：

```text
username + password
```

而至少包含：

```text
string field A
string field B
8-byte-ish value derived through sub_592AE0
byte-like field
fixed 0x18-byte binary field
another string field
```

其中 datarevision-derived value 使用 Client 讀入的 `datarevision.txt` 相關 state。

因此 server implementation 不應先假設 682 只有帳密；完整 wire schema 仍需逐 writer 封死。

### 2.2 `GL_LOGIN_ACK (681)`

`CLobbyLogin::sub_43E500()` 先讀取 status byte。

在 `status == 1` 時進入大型 bootstrap parser，會連續讀取 scalar、string、array 與多組 record，並建立後續 server/channel/bootstrap 狀態。

目前已確認這是「登入後資料初始化入口」，而不是單純 login success flag。

精確 record schema 尚 OPEN；下一步應把每一次 `sub_592900/sub_592940/...` read 與最終 object/UI field 一一配對。

## 3. Channel 相關封包目前確認狀態

### `GC_CHANNEL_REQ (193)` / `GC_CHANNEL_ACK (194)`

這一對的 packet registration 已確認存在，但目前尚未完成 top-level sender/parser 的完整 wire body closure。

特別注意：193 這個數字也出現在另一個 nested serializer context 中；該 occurrence 不能直接當作 top-level `GC_CHANNEL_REQ` body 的證據。

因此目前資料模型只保留：

```text
193 GC_CHANNEL_REQ
body: OPEN

194 GC_CHANNEL_ACK
body: OPEN
```

### `GC_ENTERCHANNEL_REQ (195)`

已找到明確 sender `sub_56FF40(a1,a2,...)`。

wire body 已直接閉合為 3 bytes：

```text
195 GC_ENTERCHANNEL_REQ
+0x00 u8 field0
+0x01 u8 field1
+0x02 u8 boolean-like field
```

第三 byte 的產生路徑經 `sub_7338D0` / `sub_735DE0`，具有明顯 boolean-like 行為。

目前不能將前兩 byte 直接命名成 `channel_id` / `server_id`，因為 caller-level provenance 尚未全部封死。

### `GC_ENTERCHANNEL_ACK (196)`

registration 已確認，但目前仍需要：

```text
196 receiver
  ↓
state transition
  ↓
actual lobby/channel object update
```

完整追查。

### `GL_MYINFO_REQ (197)`

`sub_5704B0()` 明確建立並送出 197，沒有 payload：

```text
197 GL_MYINFO_REQ
payload = 0 bytes
```

其 response 尚未完全閉合；必須繼續從 receiver dispatch 及 player-info object 寫入追查，而不能只以 `MYINFO` 名稱推測 response。

### `GL_CHANGECHANNEL_REQ (370)`

`sub_570030(a1)` 在 current channel 與 target channel 不相同時建立 370，body 為單一 byte：

```text
370 GL_CHANGECHANNEL_REQ
+0x00 u8 channel_value
```

因此 channel switch 至少存在一條直接的 one-byte request path。

目前 `channel_value` 不命名為 generic `server_id`；需要繼續與 681 bootstrap 的 channel/server records 及 196 response 對齊。

## 4. Client object layer 的 Lobby / Room 分界

目前 Client C 中至少存在：

```text
CLobbyLogin
CLobbyGameRoom
CLobbyTournamentGameRoom
```

以及 GameRule layer。

因此應採用：

```text
Server Channel state
        ↓
Lobby state
        ↓
GameRoom / TournamentGameRoom state
        ↓
CGameRule state
```

作為目前 reconstruction 的工作模型。

但是這是 Client object layering，不等於 server process / TCP connection layering；後者必須由 packet transport 與 socket lifecycle 另外證明。

## 5. Wiki 與 Client 對 Lobby / Room 的交叉驗證

Wiki 的操作教學記載：進入 channel/server 後會看到 lobby；Lobby 中可以查看對戰 room list，選擇 room 後進入待機 room；待機 room 顯示 room master、ready 與 start 等狀態。

Wiki 另記載一般模式需要玩家準備完成後由 Room Master 開始，而練習模式存在較特殊的最少人數條件。

這些玩家可見規則與 Client 已找到的：

```text
127 GR_READY_REQ
129 GR_START_REQ
130 GR_START_ACK
135 GR_CHANGESLOT_REQ
```

在概念層一致，但不能反過來用 Wiki 規則直接替 C 中未知 byte 命名。

## 6. 目前最可信的 Channel / Lobby / Room 模型

```text
GL_LOGIN_REQ 682
      ↓
GL_LOGIN_ACK 681
      ↓
bootstrap server/channel records
      ↓
Channel selection / entry
      ├── GC_CHANNEL_REQ 193   [body OPEN]
      ├── GC_CHANNEL_ACK 194   [body OPEN]
      ├── GC_ENTERCHANNEL_REQ 195
      │      + 3 bytes
      ├── GC_ENTERCHANNEL_ACK 196 [state OPEN]
      ├── GL_MYINFO_REQ 197
      │      + 0 bytes
      └── GL_CHANGECHANNEL_REQ 370
             + 1 byte
      ↓
Lobby
      ↓
GameRoom / TournamentGameRoom
      ↓
Room settings / player slots
      ↓
127 Ready
      ↓
129 Start
      ↓
130 Start sync
      ↓
CGameRule::NewGameStart
```

## 7. 尚未允許命名的欄位

目前特別保留：

```text
195 +0x00 = field0 / OPEN
195 +0x01 = field1 / OPEN
195 +0x02 = boolean-like / semantic OPEN
370 +0x00 = channel_value / semantic OPEN
193 body = OPEN
194 body = OPEN
196 state transition = OPEN
681 bootstrap records = OPEN
```

不能因為：

```text
packet 名稱
UI label
常見 server protocol 慣例
```

就直接改成：

```text
server_id
channel_id
channel_type
region
user_count
```

除非後續取得 caller provenance、parser destination 或 Resource 對照。

## 8. 下一步優先級

### P0：196 `GC_ENTERCHANNEL_ACK`

要找出：

```text
receiver
→ status / fields
→ lobby object
→ channel object
→ player list / room list refresh
```

這會直接封閉 195 的兩個未知 byte。

### P0：197 `GL_MYINFO_REQ`

追：

```text
197 sender
→ receiver
→ player profile object writes
→ character / level / currency / equipment bootstrap
```

這是 Login → Character / Inventory / Equipment 的天然入口。

### P0：681 bootstrap

將大型 parser 分段標記為：

```text
record start offset
field width
field destination
loop count provenance
resource/string cross-reference
```

目標是把「登入成功後 server 回傳資料」變成可實作的 schema，而不是只知道它很大。

### P1：193/194

找到 top-level sender / receiver；確認是否是：

```text
channel list request
channel list response
```

或其他 GC-level operation。未封死前保持 OPEN。

### P1：Room entry

沿：

```text
Lobby room list
→ room create / join operation
→ CLobbyGameRoom construction
→ player slot population
→ room setting sync
```

繼續接到既有 `GameRule_Lifecycle.md`。

## 9. 證據等級

- 193/194：目前為 Client registration-level evidence，wire body OPEN。
- 195：Client serializer direct evidence；3-byte body 已閉合。
- 196：registration-level + receiver path 待完整 closure。
- 197：Client serializer direct evidence；0-byte body 已閉合。
- 370：Client serializer direct evidence；1-byte body 已閉合。
- 681/682：Client direct evidence；大型 schema 仍待逐欄位 closure。
- Wiki Channel/Lobby historical architecture：Wiki evidence；用於版本背景，不直接取代 Client protocol evidence。

## 10. Reconstruction 原則

此文件只記錄目前證據能支持的程度。

在 server reconstruction 中，未知欄位應保持：

```text
unknown / optional / default candidate
```

只有在 Client C + LST/ASM + Resource + caller/callee data-flow 都無法再提供證據時，才考慮以 0 或 hardcoded fallback 實作，並明確標示為 fallback，而不是 protocol fact。
