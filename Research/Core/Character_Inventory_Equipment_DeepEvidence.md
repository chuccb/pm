# Character / Inventory / Equipment / Weapon — Deep Evidence

> 研究日期：2026-09-16
> Target：日本版 PaperMan 日本版 2016 年結束營運時的最終 Client
>
> 本文件不是替代 `Character_Inventory_Equipment.md`，而是記錄本輪新增、可追溯到 IDA C 的細粒度證據。尚未封死的語義維持 OPEN。

## 1. `CClientData` 的實際分層

`CClientData::possible_ctor_or_dtor()` 直接建立多層資料區，而不是單一 Inventory array：

```text
20 × 13-word records
5120 × 7-DWORD records (28 bytes / record)
4 × 22-word blocks
`tItemSlotToClient`
1024 × 23-DWORD auxiliary records
```

因此 Server reconstruction 不應把 Character / owned item / equipment loadout 壓成單一 collection。

證據：IDA `CClientData::possible_ctor_or_dtor` 對上述區域逐一初始化；20-record 與 5120-record 為固定容量，4-slot block 與 `tItemSlotToClient` 亦在同一 constructor 建立。

## 2. Item Record Collection：5120 × 28-byte

`sub_524B70(this,a2,a3)` 是大型 Item Record 解析器：

```text
read start/count
clamp internal count to [0,5020]
for up to 100 entries
    hard capacity check < 5120
    read record field +0
    read resource/item identity field +4
    validate identity through resource manager
    read additional record fields
    optionally read another byte when a3 != 0
    read associated 28-byte auxiliary state
```

每個 record 以 7 DWORD、28 bytes 為固定 stride。

後續函式又能：

```text
find by identity
exists by identity
update record field
remove record
compact records by memmove
```

所以這不是 UI-only list，而是可查找、同步、修改、刪除的 runtime item collection。

證據：`sub_524B70`, `sub_526E20`, `sub_526DD0`, `sub_526E80`, `sub_528D80`。

## 3. `GL_MYITEM_REQ/ACK` 與 Item Collection 的直接鏈

```text
199 GL_MYITEM_REQ
    payload = 0 bytes

200 GL_MYITEM_ACK
    status byte
    if status != 0:
        sub_524B70(..., a3=1)
```

Lobby bootstrap state 也直接表現為：

```text
MYINFO stage
    -> send 199
    -> receive 200
    -> proceed to ROOMINFO / next lobby state
```

因此 200 是目前最直接的 Player Item bootstrap response 證據，而不是單純 ACK flag。

## 4. 20-record composite：不是簡單 CharacterId

`sub_524010()` 解析最多 20 筆 composite records，每筆：

```text
field[157]
field[158..169]
```

共 12 個主要 data values 參與後續比較；`sub_525450()` 會逐 field 比對同 index record。

不同 accessor 又會把 field 映射到多個 Resource-ID namespace，例如：

```text
10,000,000
10,100,000
...
10,900,000
19,900,000
```

`sub_526730()` / `sub_5269F0()` 會把這些 derived identities 交給 resource manager resolve / validate。

因此目前最安全的語義是：

```text
Multi-component resource identity / composite appearance-like state
```

而不是直接把 20 筆中的各欄命名成 Hair / Face / Top / Shoes 等。那些名稱仍需 Resource + UI + caller 完整封閉。

## 5. `tItemSlotToClient`

`tItemSlotToClient` 是實際存在的 C++ type。

其 constructor 清零 field 0..9；其兩個直接 method 表明有 9 個 addressable mapping slots：

```text
sub_5291A0(index) -> clear mapping[index]
sub_5291D0(index,value) -> set mapping[index]
```

這證實 Item-slot mapping 是獨立 runtime object，而不是單純從 Item ID 即時推算。

## 6. Weapon loadout：四個可同步 record 的精確 UI mapping

這是本輪最重要的閉環之一。

四個 serializable slot records 使用：

```text
record +144206
record +144208
record +144210
record +144212
```

在 `sub_4C7C00()` 中，這四欄分別被直接綁定到 UI slot：

```text
+144206 -> PRIMARYSLOT
+144208 -> SECONDARYSLOT
+144210 -> MELEESLOT
+144212 -> THROWSLOT
```

而且每一個都會建立 3 個 selectable entries：

```text
Primary    : value + 12,100,000 -> index 0..2
Secondary  : value + 12,200,000 -> index 0..2
Melee      : value + 12,300,000 -> index 0..2
Throw      : byte_BD3580[value]  -> index 0..2
```

這是 UI literal 與 state field 的直接 data-flow 證據，因此四個 record 的 slot-level semantic 已可達到高可信度：

```text
Primary
Secondary
Melee
Throw
```

## 7. `SWITCHWEAPONSLOT` 是獨立 state，不是第五個 serialized slot

同一 `sub_4C7C00()` 中：

```text
SWITCHWEAPONSLOT
    -> state +144338
```

它只建立單一 selected entry，且同樣使用 `+12,100,000` namespace。

因此應避免這個錯誤模型：

```text
4 blocks == Main/Sub/Melee/Throw/???
```

目前更符合證據的是：

```text
Four serialized loadout records
    Primary
    Secondary
    Melee
    Throw

Separate local/loadout selection state
    SwitchWeaponSlot
```

至於 SwitchWeaponSlot 究竟是 current active weapon category、primary/secondary toggle、或其它 UI selection state，仍需 caller/runtime gameplay chain 才能最後封死。

## 8. `GI_CHANGEWP_REQ/ACK` 的資料形狀

```text
220 GI_CHANGEWP_REQ
221 GI_CHANGEWP_ACK
```

`sub_573340()` 會：

```text
scan slot 0..3
find changed slots through sub_525680()
write changed_count
for each changed slot
    serialize associated composite slot data
send
```

因此 220 不是單一 WeaponId packet，而是 **variable-length delta synchronization**。

`sub_524A50()` 負責單一 slot serializer；`sub_524880()` 負責同形狀 parser。

`sub_5735F0()` 先讀 changed-count，再把多個 slot records 解析到 temporary `CClientData`，最後透過 `sub_523370()` 套回 global state。

## 9. Slot record wire structure：目前可確認部分

每個 slot record 都至少包含：

```text
u8  slot/type
u16 primary component
u16 component #2
u16 component #3
u16 component #4
optional 8 × wider values
```

注意：這不是最終欄位命名；某些欄位只在條件成立時出現，因此必須按 parser branch 解碼。

`slot/type == 3` 時，三個額外 u16 不會依正常 branch 讀取；這是 wire-level conditional branch，不能在 Server 端做成固定 4 × u16。

## 10. Weapon-slot resource validation

`sub_527DB0()` 對 slot record 中 4 個 component values 分別走不同 resource namespace / validity path：

```text
component 1 -> &stru_B8A19C.action + value
component 2 -> value + 12,200,000
component 3 -> value + 12,300,000
component 4 -> byte_BD3580[value]
```

Invalid 時會產生不同 error class：

```text
21
22
23
24
```

而更高階 error logger 還明確存在：

```text
E_CRI_ERR_INVALID_WEAPON_SLOT
E_CRI_ERR_INVALID_AVATA_SLOT
E_CRI_ERR_INVALID_ITEM_SLOT
E_CRI_ERR_INVALID_SKILL_SLOT
E_CRI_ERR_INVALID_VOICE_SLOT
```

因此 Item / Avatar / Weapon / Skill / Voice slot 是不同 validation domains。

## 11. `220` full-sync / delta-sync 的雙重形態

同一 packet 220 不只有 delta path。

至少兩個 caller 會：

```text
write count = 4
for slot 0..3
    sub_524A50(slot)
send opcode 220
```

因此 reconstruction protocol 必須同時允許：

```text
count = changed slots
```

與：

```text
count = 4
full four-slot snapshot
```

不要把 220 實作成永遠四筆或永遠一筆。

## 12. Character creation packet

`GM_CREATECHAR_REQ = 214` 有直接 serializer：

```text
u8
u16
u8
u16
```

即 payload 6 bytes。

目前沒有足夠證據把四欄直接命名為 CharacterId / Gender / Name / Slot 等；保留 OPEN。

`GM_CREATECHAR_ACK = 215` 的 receiver 仍需和 UI / profile state 進一步完整追蹤。

## 13. `GP_CHPLAYC_REQ/ACK` 特別注意

Registration 明確存在：

```text
222 GP_CHPLAYC_REQ
223 GP_CHPLAYC_ACK
```

但 `223` 的實際 receiver 是 `sub_556730()`，其行為只有：

```text
read one 32-bit value
sub_92EF00(21,23, delta,0)
store into dword_EE8D34
```

因此目前：

```text
Packet name = GP_CHPLAYC_ACK
Actual receiver semantics = OPEN
```

不得因名稱直接下結論說這是 Character switching success response。

更需要追的是 `sub_556730` 寫入的 `dword_EE8D34` 後續所有 xref，以及真正 opcode 222 sender 的 data provenance。

## 14. Resource topology cross-check

GitHub `Extracted/` 對應：

```text
Extracted/character/
    animations/
    models/
    textures/

Extracted/item/
    avatar/
    object/
    thumb/
    weapon/

Extracted/item/weapon/
    models/
    sounds/
    sprites/
    textures/
```

因此 Resource 層本身再次支持：

```text
Character render/resource domain
!=
Item domain

Item/Avatar domain
!=
Item/Weapon render domain
```

這只能證明 resource topology，不能單獨證明 wire ID。

## 15. 目前已封閉與仍 OPEN

### High confidence / directly evidenced

```text
[C:A]
CClientData has separate 20-record / 5120-item / 4-slot / mapping structures

[C:A]
200 response populates 5120-record item collection

[C:A]
220/221 are composite weapon-loadout synchronization

[C:A]
220 supports changed-count delta and full four-slot snapshot caller paths

[C:A]
+144206 = PRIMARYSLOT
+144208 = SECONDARYSLOT
+144210 = MELEESLOT
+144212 = THROWSLOT

[C:A]
+144338 = SWITCHWEAPONSLOT separate state

[C:A]
Weapon/Avatar/Item/Skill/Voice slot validation domains are distinct
```

### OPEN

```text
197 response exact opcode/schema
Character ID wire meaning
20-record field-by-field semantic labels
5120-item 28-byte field-by-field semantic labels
214 field semantics
215 parser / side effects
222 sender and field layout
223 true business meaning
Durability / expiry exact wire fields
Resource ID -> server ID conversion
Primary/Secondary 3-entry exact variant semantics
SwitchWeaponSlot exact gameplay semantics
```

## 16. Next trace priority

```text
P0
sub_556730 -> all xrefs of dword_EE8D34

P0
opcode 222 sender discovery

P0
215 parser -> character/profile runtime state

P0
sub_522580 + sub_522CE0 + sub_523370 combined component model

P0
Primary/Secondary/Melee/Throw entries -> actual weapon runtime object

P1
Extracted/item/weapon naming/IDs -> loader -> resource manager

P1
durability/period fields -> inventory record -> UI -> gameplay
```

## 17. Evidence discipline

本文件只把 Client 直接可見的 data-flow 提升為高可信證據；任何 Player-facing 名稱都必須標示其來源。Wiki / Resource topology 可以支持 domain interpretation，但不能取代 packet parser。
