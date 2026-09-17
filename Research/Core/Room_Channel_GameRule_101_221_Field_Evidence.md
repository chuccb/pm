# PaperMan 2016 JP — Channel／Lobby／Room／GameRule 101–221 封包欄位證據

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件責任：集中 `101–221` 封包的 dispatcher、top-level wire grammar、欄位寬度、parser／serializer 與直接資料流。
> 注意：高階 Room／Lobby／GameRule 生命周期由 [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md) 維護；`198` 的 nested ClientData codec 由 [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) 維護。
>
> 證據規則：raw width 以實際 serializer／parser helper 實作為準；semantic 只有在 downstream data-flow 足夠直接時才提升名稱。未知內容維持 `[OPEN]`。

## 1. 本文件回答什麼

本文件回答：

```text
「101–221 的封包實際如何讀寫？」
「每個 packet 的 top-level grammar 與 byte width 是什麼？」
「parser／serializer 將資料送進哪個 Client state？」
```

不回答：

```text
Room / GameRule 的完整生命週期
Character / Inventory 的 domain model
ClientData nested record 的完整共用 schema
Server 最終 class hierarchy
```

這些內容應回到對應主文件。

## 2. 兩個證據入口

`sub_58D940()` 提供明確 opcode-name table；實際 payload 則必須與 parser／serializer 交叉確認。[C]

```text
101 GT_PING_REQ
102 GT_PING_ACK
105 GL_USERLIST_REQ
106 GL_USERLIST_ACK
107 GL_GAMEROOMINFO_REQ
108 GL_GAMEROOMINFO_ACK
110 GL_ROOMINFOCHANGE_ACK
111 GL_MAKEROOM_REQ
112 GL_MAKEROOM_ACK
113 GL_ENTERROOM_REQ
114 GL_ENTERROOM_ACK
116 GL_ADDUSER_ACK
118 GL_DELETEUSER_ACK
119 GL_CHATTING_REQ
120 GL_CHATTING_ACK
121 GR_MAPCHANGE_REQ
122 GR_MAPCHANGE_ACK
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK
125 GR_CHATTING_REQ
126 GR_CHATTING_ACK
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
139 GG_EXITGAME_REQ
140 GG_EXITGAME_ACK
141 PM_CONNECT_REQ
142 PM_CONNECT_ACK
143 PM_UDPSTART_REQ
144 PM_UDPSTART_ACK
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
167 GR_CHANGEUSER_REQ
168 GR_CHANGEUSER_ACK
169 GR_RULECHANGE_REQ
170 GR_RULECHANGE_ACK
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
175 GR_INTRUSIONCHANGE_REQ
176 GR_INTRUSIONCHANGE_ACK
183 GL_ENDLOADING_REQ
184 GR_ENDLOADING_ACK
187 GG_STARTGAME_REQ
188 GG_STARTGAME_ACK
190 GR_CHANGEMASTER_ACK
191 GR_CALLUSER_REQ
192 GR_CALLUSER_ACK
```

名稱表本身不是 payload proof；每個名稱都必須以實際 parser／serializer 配對。[C]

## 3. 共用 packet helper width

```text
sub_592900  → read 1 byte
sub_592940  → read 1 byte
sub_592980  → read 1 byte
sub_5929C0  → read 2 bytes
sub_592A00  → read 2 bytes
sub_592A40  → read 4 bytes
sub_592AC0  → read 4 bytes
sub_592B20  → write/copy 4 bytes
sub_592B40  → read/copy 4 bytes
sub_592730  → string-like reader
```

Duplicate helpers 即使功能看似相近也應依實作 width 判定；Hex-Rays local type 不得覆蓋 wire width。[C]

## 4. 106 — GL_USERLIST_ACK

`sub_56A250()`：

```text
u16 value_0
if value_0 != 0:
    u8 flags
    u8 count
    repeat count:
        u32 user_or_object_id
        string name/text
        u32 value
        ... local list/object update
```

每筆有效 record 會 resolve internal list/object、保存 id/string、套用 u32 value，並以另一個 u32 更新 `EMBLEM` texture。[C]

目前保留 raw：

```text
header_u16
flags_u8
record_count_u8
record.id_u32
record.text_string
record.value0_u32
record.value1_u32
```

完整 public semantic `[OPEN]`。

## 5. 108 — GL_GAMEROOMINFO_ACK

`sub_568CE0()` 首先讀：

```text
u8 mode_variant
```

若 `mode_variant == 3`，委派 `sub_580A80()`；否則讀取：

```text
u8 record_count
repeat:
    u8 player_id
    u8 record_flag/state
    string-like field
    u8 state/control
    u8 flag
    u16 × 3
    u8 flag
    u8 field
    string/raw block around 64–100 bytes
    u8 state
    u8 state
    u8 flag
    u8 flag
```

對有效 player id `< 0xD2`，Client resolve room-player object、重建 appearance state，並經 `sub_53F830()` 套用資料；另會載入 `EMBLEM` texture。[C]

`mode_variant == 2` 另存在 room/global `u32 + string + u8` block，最後經 `sub_5402A0()` 套用。[C]

因此 `108` 是 **bulk room information / player-list state packet**；完整 field semantics `[OPEN]`。

## 6. 110 — GL_ROOMINFOCHANGE_ACK

`sub_569240()` 第一 byte 為：

```text
u8 record_type
```

至少觀察到：

```text
1 → player identity/state + conditional appearance
2 → player identity/state + conditional appearance
3 → player state reset/clear
4 → player state update + 1 control byte
5 → player state update + 1 control byte
6 → player state update + 1 byte-sized state
9 → player state update + controller subobject field
10 → player state update + player +185 byte
12 → packed bits + controller callbacks
14 → player state update + player +109 byte
```

`108` 與 `110` 共用相同 room-player object update machinery；前者偏 bulk snapshot，後者偏 change event。[C]

## 7. 112 — GL_MAKEROOM_ACK

`sub_56A7B0()` 先 reset 16 個 local player records，接著讀取：

```text
u8 status_or_room_flag
u8 room/master player id
u16 value_0
u32 value_1
u8 room/state flag
u8 room string/control flag
```

後續另包含 local participant record 與兩組 `u32 + string` block。Handler 會重建 room/player object、reset room/game state、寫入 server-selected id，並將 `value_1` 存入 `dword_F2A65C`。[C]

因此 `112` 是 room creation/bootstrap state，而非 tiny boolean ACK。

## 8. 114 — GL_ENTERROOM_ACK

`sub_56B360()` 是大型多玩家 room-enter/bootstrap parser。初始內容包括：

```text
u8 control/status
u32 room/server value
u8 flag
u32 room value
u32 room value
u16 × 3
u16[] / u32[] player/member state arrays
u8 player/state fields
string/resource/appearance blocks
```

Client 以 `dword_F6DCF4[60195 * slot]` resolve player slot，填入 `byte_F33120` stride 240780 的 player object，載入 `EMBLEM`/appearance 資源，並套用 weapon/character/controller state。[C]

因此 `114` 是 full room-enter snapshot；exact wire schema 仍 `[OPEN]`。

## 9. 116 — GL_ADDUSER_ACK

`sub_56A4D0()`：

```text
u32 user_id_or_room_object
string user/display name
```

之後呼叫 `sub_588560(id, text, 0)`。u32 的公開 namespace 尚未完全閉合。[C][OPEN]

## 10. 118 — GL_DELETEUSER_ACK

`sub_56A550()` 只讀：

```text
string user/display name
```

再交給 `sub_5886C0()`。沒有額外 u32/u16。[C]

## 11. 120 — GL_CHATTING_ACK

`sub_56E300()`：

```text
u32 value
string source/chat payload
```

會做 string conversion 與 channel/room identity checks；leading u32 semantic `[OPEN]`。[C]

## 12. 122 — GR_MAPCHANGE_ACK

`sub_56E530()` 只讀：

```text
u8 mapchange_value
```

並呼叫 `sub_42FC50(dword_EA10D0, mapchange_value)`。[C]

目前不能直接命名為 `mapId`；較安全名稱是 map-change state/index value。

## 13. 124 — GR_LEAVE_ACK

`sub_5607C0()`：

```text
u8 event_type
```

當 `event_type == 1`，再讀：

```text
u8 player_id
```

resolve 16-slot player entry 後走 leave/removal path。`event_type == 2` 則走 global/current-player leave/reset path。[C]

因此 `124` 是 leave-state event family，不是單一固定 response struct。

## 14. 128 — GR_READY_ACK

`sub_5626D0()`：

```text
u8 state/value
u8 player_id
```

第一 byte 寫入 player room-state path；local player 時亦影響 global ready/game state。public state enum `[OPEN]`。[C]

## 15. 130 — GR_START_ACK

`sub_562870()` 第一 byte：

```text
u8 event_type
```

branch 1 另外包含多個 state fields，並固定讀取：

```text
16 × u32
```

寫入：

```text
dword_F6DD1C[60195 * i]
```

empty entry 還會將 `byte_F6D9EC` 套用 default state。[C]

這組 `16 × u32` 是重要跨子系統 anchor：後續 `165` damage sender 會引用 `dword_F6DD1C[target]`。因此不可視為 padding。[C][X]

## 16. 132 — GR_FORCEOUT_ACK

`sub_562EA0()` 讀取 compact player/game-state record：

```text
u8 event/state
u8 player id
u8 state
u8 state
u8 state
u8 state
u16 state
u8 state
u16 state
u8 state
u8 state
u16 state
u8 state
u8 state
u8 state
```

接著直接套用 affected player controller/object；尾端還會 reset local mode/game state。[C]

精確 public field semantics `[OPEN]`。

## 17. 134 — GR_END_ACK

`sub_562EA0()` 與相鄰 lifecycle logic 會重置 per-player room object 與 mode/game state。精確 parser branch 尚待 focused call-graph pass。[C][OPEN]

## 18. 136 — GR_CHANGESLOT_ACK

`sub_56EF40()`：

```text
u8 value
u8 player/slot id
u32 value
u16 value
u16 value
u8 value
u8 value
```

之後 resolve player 並更新 room/gameplay state。精確 slot/team semantic 仍需與 `GR_CHANGESLOT_REQ (135)` sender 以及 Room UI state 配對。[C][OPEN]

## 19. 140 — GG_EXITGAME_ACK

`sub_563430()`：

```text
u8 result/state
u8 player id
```

之後進行 per-player reset、room/game transition 與 mode-specific cleanup。[C]

## 20. 142 — PM_CONNECT_ACK

`sub_5565D0()`：

```text
string ip_or_host
u16 port
u8 flag
u32 value
```

其中前三個欄位已可安全描述為：

```text
host/address = string
port = u16
flag = u8
```

最後 u32 經 `sub_534F20(value, word_1D0D1F8)` 消費；semantic 暫保 raw。[C][OPEN]

## 21. 144 — PM_UDPSTART_ACK

`sub_555D50()` exact prefix：

```text
u8 status/mode
u8 flag
u32 dword_1D0D23C
string block (40-byte local buffer)
u32 value0
u32 value1
u32 raw4
f32/raw32 value3
u32 value4 → dword_F2A684
u8 udp_flag
```

`udp_flag != 0` 時另外讀：

```text
u8 × 4
8 × u32
```

這是 UDP startup/configuration ACK，不是 generic boolean ACK；完整 transport semantic 尚待 `143` request 與 downstream UDP initialization 閉合。[C][OPEN]

## 22. 168/170/172/174/176 — compact GameRule ACK family

目前以 direct reader width 為真相：

```text
168 GR_CHANGEUSER_ACK → 2 bytes
170 GR_RULECHANGE_ACK → u8
172 GR_WINCHANGE_ACK → u16/value
174 GR_INTRUSIONCHANGE_ACK → u8
176 GR_* ACK → u8
```

完整 semantic 必須與 request-side values、Room UI state 一起追，不從 opcode name 猜測。[C][OPEN]

## 23. 184 — GR_ENDLOADING_ACK

`sub_563B00()`：

```text
u8 loading_event_type
```

branches：

```text
0 → u8 player/state + timing callback
1 → gameplay loading complete callback
2 → u8 player/state；非 local 時進 player update
3 → timing callback
4 → gameplay loading callback
5 → u8 state + sub_406AB0
```

因此 `184` 是 multi-branch loading lifecycle event。[C]

## 24. 188 — GG_STARTGAME_ACK

`sub_563D60()`：

```text
u8 start_event_type
```

branch 1：

```text
u8 count
repeat count:
    u8 player id
```

每名 player 經 `sub_548830()`／`sub_406E50()` reset/init。branch 2 則 reset current/global game state 並進入 game lifecycle reset。[C]

## 25. 190 — GR_CHANGEMASTER_ACK

`sub_56FBF0()` 首先讀：

```text
u8 new_master_or_player_id
```

再更新 room master/player state 與 UI/global state。完整 semantic 需與 request sender 閉合。[C][OPEN]

## 26. 192 — GR_CALLUSER_ACK

`sub_56FE10()`：

```text
u8 value
```

依 current game state 分支；目前不得直接命名 user id 或 result code。[C][OPEN]

## 27. 193–221：第二段 packet family

以下 packet 不與 `101–192` 重複保存，而是在同一份 Field Evidence 中依 opcode 順序接續。

### 27.1 194 — channel state/result

Receiver：`sub_56FE90()`。

```text
u8 × 5
```

五個 byte 原樣寫入：

```text
byte_BEFF76[0..4]
```

並驅動 `dword_E9FDE0` 相關 channel state transition。[C]

用途可確認為 channel/state transition input；五個 byte 的 public names `[OPEN]`。

### 27.2 196 — channel-entry response

Receiver：`sub_570100()`。

第一欄：

```text
u8 state/result
```

`state == 1`：

```text
u8 v28
ASCII-Z string cp
u16 hostshort
u8 trailing
```

`cp + hostshort` 送入 `sub_596E60()` 建立後續 network/channel object，因此 `hostshort` 可高信度視為 port-like。[C]

其它 state 不消費相同 endpoint grammar，而進 state cleanup / UI/error path。[C]

### 27.3 197 — GL_MYINFO_REQ

`sub_5704B0()`：

```text
opcode = 197
payload = 0 bytes
```

完整資料由 `198` 提供。[C]

### 27.4 198 — GL_MYINFO_ACK

Top-level grammar：

```text
u8 status
if status != 0:
    u32 first_scalar
    ProfileBlock
    AppearanceRecords
    LoadoutRecords
    ItemSlotValidation
    SkillSlotValidation
    u16 standalone_0
    u32 standalone_1
    u8 list_count
    repeat:
        u8 list_value
```

本文件只保留 top-level boundary；nested schema 與 hydration 由：

```text
MyInfo_198_ClientData_Field_Schema.md
ClientData_Shared_Decoder_Field_Evidence.md
```

維護。[C][RES]

### 27.5 199 — GL_MYITEM_REQ

`sub_570A00()`：

```text
opcode = 199
payload = 0 bytes
```

送出後進 loading/information 類 UI state。[C]

### 27.6 200 — GL_MYITEM_ACK

`sub_570AB0()` 首先讀：

```text
u8 status/result
```

成功時委派 `sub_524B70()`，即 Shared Decoder 的 Family C；之後還會呼叫：

```text
sub_41BF20(byte_BF0724)
byte_EE8C05 = 1
```

因此 `200` 是 item/client-data subsystem initialization point。[C]

### 27.7 201 / 202 — 17-byte logical collection record

兩者首先讀：

```text
u32 count
```

每筆：

```text
u32 field0
u32 field1
u8 field2
u32 field3
u32 field4
```

故 logical wire record：

```text
4 + 4 + 1 + 4 + 4 = 17 bytes
```

Client internal object 可配置 `0x14` bytes，但不得反推 wire record 為 20 bytes。[C]

`201` 經 `sub_95A3B0()` 插入 `sub_95A4A0()` collection；`202` 同樣讀 record 後呼叫 `sub_95A800(this, field1, field0)`。另外兩個 u32 未進入該 call，semantic `[OPEN]`。[C]

### 27.8 203 — Family-A direct delegation

`sub_571D50()` 直接：

```c
return sub_524660(..., a1);
```

所以 `203 = Family-A codec`。[C]

完整 Family-A wire grammar 由 Shared Decoder 維護。

### 27.9 204 — variable item/data change request

`sub_571100()`：

```text
u8 count
repeat:
    u32 key/id
    u8 category
    u16 value
    if category ∈ {12,13,17}:
        u16 secondary_value
```

optional u16 確定存在於 wire，因 caller 只對三種 category 呼叫 writer。[C]

204 與 206 共用 category/value validation machinery。[C]

### 27.10 205 — item/state synchronization + economy tail

`sub_571910()`：

```text
u8 count
repeat:
    u8 present
    if present:
        u32 id
        u32 field1
        u32 field2
        u32 field3
        u8 field4
        u16 field5
```

record 會進入：

```text
sub_534450(resourceIdentity, id, field5)
sub_524F70(..., id, field3, field1, field2, field4, field5)
```

後段還有七個 `u32`，其中已知部分為：

```text
u32 trailing_0
u32 PG
u32 trailing_2
u32 CASH
u32 trailing_4
u32 trailing_5
u32 CP
```

其它 tail fields 由 `Currency_State_Field_Evidence.md` 維護。[C]

### 27.11 206 — four-field change request

`sub_571620()`：

```text
u32 a2
u32 a3
u8 category
u32 value
```

四個欄位依序使用 4/4/1/4-byte writer；最後 value 與 204 共用 category/value validation machinery。[C]

### 27.12 207 / 208 — collection removal/update family

`208` 的 `sub_572AD0(char a1)` 雖表面是 char，實際使用 `sub_592A20`，故：

```text
208 field0 = u32
```

不能按 prototype 寫成 u8。[C]

`207`：

```text
u8 status/present
if non-status branch:
    u32
    u32
    u8
    u32
    u32
```

後面另有六個 `u32`，已閉合的 economy 部分：

```text
trailing_0
trailing_1
trailing_2
CASH
PG
CP
```

record 會進相同 `sub_95A4A0()` collection subsystem。[C]

### 27.13 209 — removal/update request

`sub_572B80()`：

```text
u8 flag
```

依 flag／conditions 最多消費三個 `u32`，用於定位／移除 Client-side collection record，並可能對 28-byte internal record table 做位移。[C]

具體 business semantic `[OPEN]`；不要直接命名為 `item_id` 或 `slot`。

### 27.14 210–216 — small control/state family

```text
210 → string request
211 → u8
212 → string
213 → u8
214 → u8 + u16 + u8 + u16
215 → u8
216 → u8
```

210/212 是 NUL-terminated string，其餘依 fixed-width helper。[C]

高階 public labels `[OPEN]`。

### 27.15 218 — Family-B delta synchronization

`sub_572FC0()`：

```text
u8 current_or_aggregate_state
u8 changed_count   // <=20
repeat changed_count:
    Family-B record
```

Family-B 單筆：

```text
u8 index
12 × u16
= 25 bytes
```

它沒有 Family-A optional `8 × u32` block。`changed_count == 0` 且 aggregate state 未改變時，Client 走本地更新 path。[C]

完整 Family-B schema 見 Shared Decoder。

### 27.16 219 — compact state/control

`sub_573230()`：

```text
u8 value
```

目前僅確認 width 與 direct state update 用途；public meaning `[OPEN]`。[C]

### 27.17 220 / 221 — Family-A repeated synchronization

兩者均使用 Family-A repeated records：

```text
u8 count
repeat:
    Family-A record
```

Family-A：

```text
u8 type
u16 primary
if type != 3:
    3 × u16
if primary != 0:
    8 × u32
```

完整 resource validation 與 weapon/config bridge 由 Shared Decoder 維護。[C]

## 28. 跨 packet 關係

### 130 → 165

```text
GR_START_ACK (130)
    → 16 × u32 F6DD1C[player]
    → 165 damage sender 引用 F6DD1C[target]
```

這是 direct cross-packet state dependency，Server reconstruction 必須保留。[C][X]

### 108 ↔ 110 ↔ 114

```text
108 bulk room snapshot
110 room-info change event
114 room-enter snapshot
    ↓
shared per-player room object
    ↓
identity / emblem / character / weapon / state
```

### 142 ↔ 144

```text
142 PM_CONNECT_ACK
    → host + port + transport/config value

144 PM_UDPSTART_ACK
    → UDP startup/config/session parameters
```

### 121–136

```text
map / leave / ready / start / forceout / end / slot-change
```

形成核心 room/game lifecycle family，應建模為 state transitions 而不是彼此孤立的 request/response structs。

## 29. 與其他文件的責任切分

```text
101–221 top-level packet grammar
    → 本文件

Room / Lobby / GameRule 高階 lifecycle
    → Room_Lobby_GameRule.md

198 composite order / MyInfo / Avatar hydration
    → MyInfo_198_ClientData_Field_Schema.md

ClientData Family A/B/C/D
    → ClientData_Shared_Decoder_Field_Evidence.md

Character / Inventory / Equipment runtime model
    → Character_Inventory_Equipment.md

PG / CASH / CP
    → Currency_State_Field_Evidence.md

TCP/UDP transport / frame / transform / dispatcher
    → Network_Protocol.md
```

原則：**top-level packet 與 nested codec 是不同層；共用 ClientData runtime state 不代表 wire layout 相同。**

## 30. 目前 OPEN 與 proof targets

```text
101–106 未完全閉合的 request/ACK pair semantics
108/110/114 player-record shared structure
112/114 完整 room bootstrap fields
116/118/120 identity/chat fields
121–136 每一 request ↔ ACK 完整對映
130 的 16 × u32 F6DD1C semantic
134 exact parser branch
136 slot/team exact semantics
142/144 transport config end-to-end
168–176 request-side paired semantics
190/192 public state meaning
194 五個 state byte 名稱
196 status enum / endpoint trailing byte
198 first_scalar / standalone fields / byte-list semantics
201/202 五欄 collection semantics
204 category/value public mapping
205/207 剩餘 economy tail fields
209 三個 u32 的條件式語意
210–216 public labels
218 12 × u16 mapping
219 public meaning
220/221 Family-A public semantic
```

除非找到新的 `PaperMan.exe.c`／LST／ASM、`Extracted/` 或日本 Wiki 證據，以上項目保持 `[OPEN]`；不得為 Server 實作方便而填 `0`、固定常數或 guessed enum。
