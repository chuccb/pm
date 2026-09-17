# PaperMan 2016 JP — Login／ClientData／玩家資料協定整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 `680–696` login/account-adjacent protocol 與 `197–221` MyInfo／ClientData 玩家資料同步。Character／Inventory 的 runtime/domain semantic 由 [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md) 維護。

## 1. 一眼看懂

```text
TCP connection success
    ↓
693 / 694
    ↓
682 Login Request
    ↓
681 Login ACK / Server List
    ↓
141/142 secondary connection
    ↓
143/144 UDP bootstrap
    ↓
197/198 MyInfo / ClientData
    ↓
199/200 Item collection
    ↓
201–221 player/item synchronization
```

這份文件只負責 **wire protocol 與 packet-level data-flow**；不要把 Client memory layout 直接當成 wire schema。

## 2. Opcode namespace：680–696

```text
680 GL_LOGIN_BASE
681 GL_LOGIN_ACK
682 GL_LOGIN_REQ
683 GL_SERVERLIST_NOTICE
684 GL_LOGIN_DUPLICATE
685 GL_TUTORIALINDEX_REQ
686 GL_TUTORIALINDEX_ACK
687 GL_TUTORIAL_START
688 GL_TUTORIAL_END
689 GL_TUTORIAL_INDEX_SET_REQ
690 GL_TUTORIAL_INDEX_SET_ACK
691 GL_ITEM_MODIFY_NOTIFIER
692 GG_CP_TERMINATE_APP
693 GL_TCPCONNSUCC
694 GL_ACCOUNTCONNSUCC
695 GS_BUY_ONCEITEM_REQ
696 GS_BUY_ONCEITEM_ACK
```

Registration 只證明 opcode identity，不足以推 body。[C]

## 3. `681 GL_LOGIN_ACK`

Receiver：`CLobbyLogin::sub_43E500`。[C]

### 3.1 成功前綴

```text
u32 status
```

只有 `status == 1` 進成功 bootstrap；接著：

```text
u32 v144
u32 n100
u32 v140
if v140 > 0:
    u32 v120
    u32 v141
    u8  v135
```

其中 `n100` 後續會被 `143 PM_UDPSTART_REQ` 使用，因此存在跨 packet dependency。[C]

### 3.2 Server-list

接著：

```text
u16 record_count
```

每筆：

```text
u16 src
ASCII-Z string
ASCII-Z string
u16
u8
u16
repeat 3:
    u16 sub_count
    if sub_count > 0:
        u8 sub_type
        ASCII-Z string
        u16
        u8
        if sub_type == 3:
            u8
```

這是變長、條件式 wire record，不是固定 struct。[C]

Client raw storage stride = 132 bytes；另有 80-byte `CLobbyServerData` view：

```text
wire record
    → 132-byte raw storage
    → 80-byte UI view
```

不能用 132/80-byte object offset 當 wire offset。[C]

已閉合的 UI-oriented raw fields：

```text
+52  server-name-like data
+63  face/icon source
+122 current users
+124 maximum users
+128 server kind/type lookup
+129 state category
+130 conditional state subtype
```

其它公開名稱保持 `[OPEN]`。[C]

## 4. `682 GL_LOGIN_REQ`

Sender：`CLobbyLogin::sub_43DF00`。[C]

wire：

```text
ASCII-Z USERID
ASCII-Z PASSWORD
u64 datarevision-derived verification composite
u8  hardware-ID source/state
raw 24-byte hardware-ID slot
```

第三個看似 state call 的 `sub_401B50()` 是 Client state update，不是第三個 wire string。[C]

## 5. `680 / 683 / 684 / 690`

目前沒有可靠 concrete body：

```text
680 → registration only / body OPEN
683 → registration only / body OPEN
684 → registration only / body OPEN
690 → registration only / body OPEN
```

不得自行補 payload。[C][OPEN]

## 6. Tutorial / application-control packets

```text
685 GL_TUTORIALINDEX_REQ → 0 bytes
686 GL_TUTORIALINDEX_ACK → u32 tutorial_index
687 GL_TUTORIAL_START    → 0 bytes
688 GL_TUTORIAL_END      → 0 bytes
689 GL_TUTORIAL_INDEX_SET_REQ → u32 tutorial_index
692 GG_CP_TERMINATE_APP → u32 message/resource key
693 GL_TCPCONNSUCC → 0 bytes
694 GL_ACCOUNTCONNSUCC → u16 negotiated packet limit
```

`689` 是典型：Hex-Rays prototype 可呈現 char，但實際 writer 為 4 bytes。[C]

`694` negotiated limit 受 `0x2580 = 9600` 上限約束，之後轉入 `682`。[C]

## 7. `691 GL_ITEM_MODIFY_NOTIFIER`

```text
u32 count
u32 flags
repeat count:
    if flags & 0x01:
        u32 key/resource_id
        u32 value
    else if flags & 0x10:
        u32 key/resource_id
        u32 value
```

是 `if / else if`，不是兩個 flag 同時處理。[C]

## 8. `695 / 696` purchase protocol

`695` 是 polymorphic request；descriptor class 決定 payload grammar。已見：

```text
class family A:
    u32 resource/item key
    ASCII-Z secondary string
    u8 type/duration
    u8 period/count

other families:
    u32 resource/item key
    u8 type/duration
    u8 period/count

special family:
    u32 transformed key
    u32 period/count/value
```

已知固定 descriptor identity：

```text
E975A1
E975A2
E975A3
E975A4
E975A7
```

仍不應把 descriptor identity 猜成 public item enum。[C][OPEN]

`696`：

```text
u8  ack_mode
u32 item/resource descriptor
```

後續 grammar 依 `ack_mode` 與 descriptor family 分支；可包含 u32、u8、u16、string、nested ClientData 等。[C][OPEN]

## 9. Login / connection 主鏈

目前最可靠：

```text
693
 → 143
 → 694
 → 682
 → 681
 → server-list
 → 141/142
 → 143/144 UDP bootstrap
```

實際事件先後仍應以 Client object/data-flow 為準，不靠 opcode 編號猜測。[C][OPEN]

## 10. `197–221` ClientData namespace

```text
197 GL_MYINFO_REQ
198 GL_MYINFO_ACK
199 GL_MYITEM_REQ
200 GL_MYITEM_ACK
201/202 collection synchronization
203 Family-A
204 item/data change request
205 item/state + economy synchronization
206 item/data change request
207/208 collection update/removal family
209 removal/update request
210–216 small control/state family
218 Family-B delta synchronization
219 compact control/state
220/221 Family-A repeated synchronization
```

## 11. ClientData wire family

### Family A

```text
u8  type
u16 primary
if type != 3:
    3 × u16
if primary != 0:
    8 × u32
```

大小：3 / 9 / 35 / 41 bytes，最多 4 records。

主要：`203/220/221`。[C]

### Family B

```text
u8 index
12 × u16
```

= 25 bytes。

`218` top-level：

```text
u8 current_or_aggregate_state
u8 changed_count <= 20
repeat:
    Family-B record
```

218 是 selective/delta synchronization，不是 Family A。[C]

### Family C

`200`：

```text
u32 collection cursor/base
repeat:
    u32 field0
    u32 resource_id
    u32 field2
    u32 field3
    u32 field4
    u8  extra_flag
    u16 extra_value
```

單筆 = 23 bytes。最多處理 100 logical entries 或 ClientData 5120 bound。[C]

`resource_id` 直接經 resource validation；invalid item 走 error 6。[C]

### Family D

`198` appearance component：

```text
u8 count <= 20
repeat:
    u8 field0
    12 × u16
```

單筆 = 25 bytes。[C]

## 12. `198 GL_MYINFO_ACK` composite bootstrap

`197` request：

```text
payload = 0 bytes
```

`198` 成功路徑：

```text
u8 status
if status != 0:
    u32 first_scalar
    ProfileBlock
    Family-D appearance records
    Family-A loadout/config records
    ItemSlotValidation
    SkillSlotValidation
    u16 standalone_0
    u32 standalone_1
    u8 list_count
    repeat:
        u8 list_value
```

Profile block `sub_523BF0()`：

```text
NUL-terminated strings
multiple u32/u8
raw 48-byte block
```

存在 serializer `sub_523E10()`。[C]

Skill validation block：

```text
7 × u32 = 28 bytes
```

失敗為 `INVALID_SKILL_SLOT` error 9。[C]

Item-slot validation：

```text
sub_527550 → 9 × u32
```

失敗為 error 10。[C]

### 12.1 `198` hydration

198 接收後進：

```text
INFORMATION
  └─ MYINFO
       └─ AVATAR
```

可見 downstream：

```text
sub_522CE0
sub_525680
sub_551E80
sub_6A9950(..., L"AVATAR", ...)
```

因此：

```text
198 ≠ authentication-only ACK
198 = login 後 ClientData / MyInfo bootstrap carrier
```

### 12.2 198 OPEN

```text
first_scalar
standalone_0
standalone_1
list_value[]
ProfileBlock 各 scalar public semantics
Family-D field[0..11] public mapping
```

均保持 `[OPEN]`，直到找到唯一 consumer / producer / Resource evidence。[C][RES][OPEN]

## 13. `199 / 200` item collection

```text
199 → 0-byte request
200 → status + Family-C collection
```

`200` 成功後會初始化 item collection state。[C]

Client runtime inventory 5120 records 與 wire Family-C 不應混為同一 struct；domain semantic 回 [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md)。

## 14. `201 / 202`

兩者主要 record：

```text
u32 field0
u32 field1
u8 field2
u32 field3
u32 field4
```

= 17-byte logical record。[C]

`201` 插入 collection；`202` 也處理 collection update，但部分 u32 semantics OPEN。[C][OPEN]

## 15. `204 / 206`

### 204

```text
u8 count
repeat:
    u32 key/id
    u8 category
    u16 value
    if category ∈ {12,13,17}:
        u16 secondary_value
```

optional u16 確認存在於 wire。[C]

### 206

```text
u32 value0
u32 value1
u8 category
u32 value2
```

與 204 共用 category/value validation machinery。[C]

## 16. `205 / 207 / 208 / 209`

### 205

Repeated item/state records 後有 7 × u32：

```text
trailing_0
PG
trailing_2
CASH
trailing_4
trailing_5
CP
```

其中 PG/CASH/CP 直接寫入：

```text
EE8D18 = PG
ArgList = CASH
EE8D1C = CP
```

其餘 tail fields OPEN。[C]

### 207

最後 6 × u32 中：

```text
trailing_0
trailing_1
trailing_2
CASH
PG
CP
```

仍有部分 tail semantics OPEN。[C]

### 208

雖 prototype 顯示 char，writer 是 4-byte，因此：

```text
208 field0 = u32
```

[C]

### 209

flag 後依條件最多讀 3 × u32；用途為 collection record 定位／移除候選，business semantics OPEN。[C][OPEN]

## 17. `210–216 / 218 / 219 / 220 / 221`

```text
210 → string request
211 → u8
212 → string
213 → u8
214 → u8 + u16 + u8 + u16
215 → u8
216 → u8
219 → u8
```

`218` = Family-B delta。

`220/221`：

```text
u8 count
repeat:
    Family-A record
```

完整 public semantics 仍維持 raw／`[OPEN]`。[C]

## 18. Economy boundary

```text
Account economy
    ├─ PG
    ├─ CASH
    └─ CP
```

Client 已閉合：

```text
EE8D18 → PG
ArgList → CASH\ nEE8D1C → CP / COUPON
```

但這是 runtime state，不代表每個 economy wire field 都已知道名稱。

## 19. Server reconstruction

帳戶／玩家資料的最低 wire/domain 分層：

```text
LoginCodec
    ↓
ServerListCodec
    ↓
MyInfoCodec
    ├─ ProfileBlock
    ├─ AppearanceFamily
    ├─ LoadoutFamily
    ├─ ItemSlotValidation
    └─ SkillSlotValidation
    ↓
MyItemCodec
    └─ ItemCollection
```

其中：

```text
wire record
    ≠
Client memory object
    ≠
PlayerProfile domain model
```

## 20. 目前 OPEN 與最高價值追查

```text
681 server-list 全部 public fields
682 verification composite / hardware-ID exact semantics
695/696 所有 descriptor-class grammar
198 first_scalar / ProfileBlock / tail
Family A/B/C/D public field semantics
201/202 collection fields
204/206 category semantics
205/207 remaining economy tail
209 conditional u32 semantics
210–216/219 public labels
```

所有未知欄位保持 `[OPEN]`，不得用 `0`、固定常數或 guessed enum 假裝已閉合。
