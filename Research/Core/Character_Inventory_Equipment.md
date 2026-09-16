# Character → Inventory → Equipment → Weapon 研究

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client
>
> 本文件開始收斂 Login/Channel 後的 Player profile、Character、Avatar、Inventory、Equipment、Loadout 與 Weapon 邊界。凡尚未由 Client serializer/parser、caller/data-flow 或 Resource loader 封死者，保持 OPEN。

## 1. 目前定位

現有生命週期已收斂至：

```text
GL_LOGIN 682/681
    ↓
Channel / Lobby
    ↓
GameRoom
    ↓
Player state
```

下一層需要回答：

```text
Player profile
    ↓
Character identity
    ↓
Owned items / inventory
    ↓
Equipped avatar / clothing
    ↓
Equipped weapon loadout
    ↓
Weapon runtime state
```

目前 `197 GL_MYINFO_REQ` 已由 Client serializer 證明為 0-byte request，但 response/schema 尚未封閉，因此不能直接宣稱 197 response 就是完整 inventory packet。

## 2. Resource domain：Character 與 Item 是不同層

`Extracted/0.xml` 定義：

```text
character -> Data\\character.dat -> character\\
item      -> Data\\item.dat      -> item\\
```

`Extracted/character` 至少有：

```text
animations/
models/
textures/
datarevision.txt
```

`Extracted/item` 至少有：

```text
avatar/
object/
thumb/
weapon/
datarevision.txt
```

因此目前最安全模型為：

```text
CharacterIdentity
    !=
CharacterRenderAssets

ItemIdentity
    !=
ItemRenderAssets
```

Resource topology 是 [RES:A]；尚不能僅因 directory 名稱推導 server enum。

## 3. Wiki 顯示的 Player-facing Character / Avatar 結構

日本 Wiki 的角色衣裝頁以獨立欄位列示：

```text
Character
Package
Face / Expression
Hairstyle
Set Clothing
Top
Bottom
Shoes
Accessory
```

2016-06/07 的角色衣裝頁仍可看到這種結構。部分頁面還記載：

```text
同一 accessory 部位互斥裝備
部位至少包含：口・胴・目・頭
```

例如 2016-07-01 的露西頁直接以 Character、Package、Face、Hairstyle、Set Clothing、Top、Bottom、Shoes、Accessory 分區。Accessory 又有部位限制。 [WIKI]

因此 server-side Equipment model 不應只保存一個 `AvatarId`；至少需要能表達：

```text
Character
Hairstyle
SetClothing / Clothing
Top
Bottom
Shoes
Accessory slots
```

精確 wire representation 仍 OPEN。

## 4. Package 與 owned item 必須分離

2016 年角色衣裝頁可見 package 是另一種 acquisition unit。例如角色 package 可以同時描述：

```text
Character
Set Clothing
Paper Puzzle
```

且頁面記載角色已購買時不能再次購買相應 package。

因此：

```text
PackageDefinition
    -> grant/acquisition rules

ItemDefinition
    -> concrete character/avatar/item

PlayerInventory
    -> owned records
```

不能把 Package 直接當作一個可裝備 Item。

## 5. Weapon domain

`Extracted/item/weapon` 目前至少包含：

```text
models/
sounds/
sprites/
textures/
```

這只是 Client asset domain 證據，不等於 server weapon schema。

Wiki 玩家層又將武器拆成：

```text
Main
Sub
Melee
Throwing
```

並另外存在期間武器、永久武器、活動／特殊武器等 acquisition/classification。

因此 server loadout 至少需要 category-aware representation，而不是單一 `WeaponId`。

## 6. Weapon ownership / durability / period

日本 Wiki 的「武器耐久値情報」頁最後修改於 2016-03-19。頁面描述：

```text
永久主武器 / 永久副武器
    -> 存在修理耐久值

使用時間 / 戰鬥
    -> 耐久下降

途中退出
    -> 額外耐久 penalty
```

並描述不同武器類型存在基準耐久等級，以及部分特殊武器存在例外。

另有新手教學對比：

```text
期間武器
    -> 到期消失
    -> 不因使用而損壞

永久武器
    -> 不因期間消失
    -> 使用可能降低耐久
    -> 可修理
```

因此 reconstruction model 應把：

```text
WeaponIdentity
Ownership
Duration / Expiry
Durability
EquippedState
```

視為獨立概念。

但目前仍不能把 Wiki 所述百分比直接當成 packet 中的 byte/ushort/unit；wire field 尚 OPEN。

## 7. Weapon categories 與 local rules 的分離

Wiki 的 local rule 顯示房間可以限制：

```text
Knife only
Sub weapon only
Sniper only
```

並依規則限制 Main/Sub/Melee/Throwing 的可用範圍。

因此：

```text
EquipmentState
    ↓
Loadout
    ↓
Mode / LocalRule validation
```

比「裝備成功即等於任何模式都可使用」更符合目前可見的 client/gameplay model。

但這裡仍要由 C 中 mode validation 與 weapon-state checks 進一步封閉。

## 8. 初步 Server object model

```text
PlayerProfile
├─ PlayerId
├─ Level
├─ Currency / PG state
├─ Experience
├─ CharacterState
├─ InventoryState
└─ EquipmentState

CharacterState
├─ CharacterId
├─ HairstyleId
├─ SetClothingId
├─ TopId
├─ BottomId
├─ ShoesId
└─ AccessoryBySlot

InventoryState
├─ OwnedCharacterRecords
├─ OwnedItemRecords
├─ OwnedWeaponRecords
└─ PackageGrantHistory / acquisition state

EquipmentState
├─ ActiveCharacterId
├─ AvatarEquipment
└─ WeaponLoadout

WeaponRecord
├─ ItemId
├─ Category
├─ Ownership
├─ Duration / Expiry
├─ Durability
└─ EquippedState
```

上述是 reconstruction domain model，不是 Client wire schema。

## 9. 197 `GL_MYINFO_REQ`：下一個 C-level 核心節點

目前已證明：

```text
197 GL_MYINFO_REQ
payload = 0 bytes
```

真正需要封閉的是：

```text
197
 ↓
server response
 ↓
receiver
 ↓
PlayerProfile writes
 ↓
CharacterState writes
 ↓
Inventory records
 ↓
Equipment / Loadout
 ↓
Weapon state
```

應逐一記錄：

```text
packet field offset
read width
destination object / global
loop count
string length/data
conditional branches
resource lookup
UI update
follow-up request/response
```

只有這樣才有資格把 response 命名成 `MYINFO_ACK` 或拆成多個實際 server messages。

## 10. 目前 Unresolved

```text
[OPEN] 197 response opcode
[OPEN] 197 response complete schema
[OPEN] PlayerProfile wire fields
[OPEN] CharacterId wire field
[OPEN] Inventory record layout
[OPEN] Equipment record layout
[OPEN] Weapon item identity mapping
[OPEN] Durability wire unit
[OPEN] Duration/expiry wire representation
[OPEN] Accessory slot encoding
[OPEN] Package grant record encoding
[OPEN] Character resource ID ↔ server CharacterId conversion
[OPEN] Item resource ID ↔ inventory ItemId conversion
```

## 11. 下一輪優先追查

P0：

```text
197 receive-side response
```

P0：

```text
Client MyCharacter / Present UI
    -> item lookup
    -> equipment selection
    -> actual send packet
```

P0：

```text
weapon runtime object
    -> item identity
    -> durability / period
    -> weapon slot
    -> combat runtime
```

P1：

```text
character loader
item loader
weapon loader
UI resource lookup
```

P1：

```text
Package
    -> grants
    -> inventory ownership
    -> equipment availability
```

## 12. Evidence policy

```text
[RES:A]
Extracted pack mapping / directory topology

[WIKI]
Player-facing character / equipment / weapon behavior

[C]
197 sender與既有 Client data-flow

[OPEN]
尚未封死的 protocol / runtime semantics
```

Wiki 可以約束 Player-facing behavior，但不能直接替代 Client parser。
Resource directory 可以證明 domain topology，但不能直接替代 ItemId / CharacterId schema。

最終仍必須完成：

```text
Wiki
 ↕
Resource
 ↕
Client C/LST/ASM
 ↕
Runtime object
 ↕
Packet
 ↕
Server state
```
