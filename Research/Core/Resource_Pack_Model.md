# PaperMan Resource Pack / Loader 邊界研究

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client
>
> 本文件只記錄目前能由 `Extracted/` 與 Client 研究直接支持的 Resource pack / loader 邊界。資源的遊戲語意仍需與 C/LST/ASM caller、runtime object 及 Wiki 繼續交叉驗證。

## 1. `Extracted/0.xml` 是高價值的 pack-to-folder 索引

`Extracted/0.xml` 不是普通 gameplay XML；它直接列出 Client 使用的 PackFile 定義：

```xml
<PackFile key="character" filename="Data\\character.dat" folderpath="character\\" />
<PackFile key="item"      filename="Data\\item.dat"      folderpath="item\\" />
<PackFile key="map"       filename="Data\\map.dat"       folderpath="map\\" />
<PackFile key="pepachi"   filename="Data\\pepachi.dat"   folderpath="pepachi\\" />
<PackFile key="pmClient"  filename="Data\\pmClient.dat"  folderpath="" />
```

除此之外還有大量獨立 sound pack：

```text
sounds
sounds01 ... sounds92（部分編號存在；並非完全連續）
```

每個 sound pack 都指定自己的 `filename` 與解包後 `folderpath`。

**[RES:A]** 直接來自 `Extracted/0.xml`。

## 2. Resource domain 與 runtime domain 不應直接畫等號

目前最安全的抽象是：

```text
Pack key
    -> physical .dat pack
    -> extracted folder/domain
    -> loader/parser
    -> runtime object/cache
    -> actual usage
```

例如：

```text
character
    -> Data\\character.dat
    -> Extracted/character/*

item
    -> Data\\item.dat
    -> Extracted/item/*

map
    -> Data\\map.dat
    -> Extracted/map/*
```

不能僅因為資料夾叫 `item` 就宣稱其中某個檔案必定是「玩家 inventory database」；它首先證明的是 **client resource domain / pack domain**。

## 3. Character Resource domain

`Extracted/character` 目前至少存在：

```text
animations/
models/
textures/
datarevision.txt
```

因此 Client 的 Character 資源域至少把：

```text
animation
model
texture
revision
```

放在同一個 `character` pack domain 下。

**[RES:A]** directory topology + `0.xml` pack mapping。

這對 Server reconstruction 的含義是：

```text
CharacterIdentity
    !=
CharacterRenderAsset
```

Server 需要保存的是 player/character 的語義 ID / state；Client 再使用 character resource domain 決定模型、材質與動畫。兩者不可因檔案名稱直接合併。

## 4. Item Resource domain 的內部分層

`Extracted/item` 至少分成：

```text
avatar/
object/
thumb/
weapon/
datarevision.txt
```

這是一個重要結構證據：Client item domain 並不是單一「weapon」類型，而至少存在：

```text
Avatar asset domain
Object asset domain
Thumbnail/UI representation domain
Weapon asset domain
```

`weapon` 又至少分成：

```text
models/
sounds/
sprites/
textures/
```

`object` 至少分成：

```text
animations/
models/
sounds/
textures/
```

**[RES:A]** directory topology。

因此目前 Server data model 不應寫成：

```text
Item = Weapon
```

而應保留較一般化的：

```text
ItemIdentity
ItemCategory
ItemState
```

再由 category 映射至 avatar / weapon / object 等 Client resource domain。

## 5. Map Resource domain

`Extracted/map` 目前可直接確認至少包含：

```text
datarevision.txt
gamematerial.dat
gameobject.dat
gamesfx.dat
gamesshader.dat
maplist.dat
maps/
minimaps/
models/
portraits/
sfx/
sounds/
textures/
```

特別值得注意的是：

```text
maplist.dat
```

與實際：

```text
maps/
```

同時存在。

因此：

```text
MapList / map-selection metadata
    !=
actual map asset
```

這與目前 `121/122/129` 的 Client data-flow 非常重要：

```text
GAMEROOM_SCROLL_MAP
    -> map selector value
    -> 121/122
    -> 129 start parameter
```

而 `Extracted/map` 又存在 `maplist.dat` + `maps/` 兩層，故不能直接把 selector byte 當作檔案名稱、array index 或 physics map object；需要繼續追 loader conversion。

**[RES:A]** map domain topology + existing `Map_And_Room.md` client evidence。

## 6. `datarevision.txt` 的交叉證據

目前根層、character、item、map 的 `datarevision.txt` 均可讀出：

```text
811034967
```

因此至少可以確認：這些 domain 在目前 Extracted 版本中共享相同的 revision value。

此外既有 Login 研究已確認 `GL_LOGIN_REQ (682)` 的 serializer 使用與 datarevision 相關的 state，因此：

```text
Client resource revision
    -> login bootstrap compatibility input
```

是目前很強的 cross-domain 線索。

但目前還不能把 `811034967` 命名成 server protocol version / build number；它首先是 client data revision value。

**[RES:A]** revision files；**[C]** Login serializer data-flow。

## 7. `ClientDataList.xml` 的意義

`Extracted/ClientDataList.xml` 直接列出：

```xml
<DataList key="BulletHole" />
<DataList key="effect" />
<DataList key="ui" />
<DataList key="ui_temp" />
<DataList key="0.xml" />
<DataList key="convars.pat" />
<DataList key="data.pat" />
<DataList key="datarevision.txt" />
<DataList key="ClientDataList.xml" />
```

因此 Client 另有一層「client data list」索引概念，並非所有資料都經 `character/item/map` 三個 PackFile domain。

這意味：

```text
PackFile domain
    !=
全部 Client-side data source
```

`ui`、`effect`、`data.pat`、`convars.pat` 等也可能參與 runtime behavior / rendering / configuration，後續 Resource research 不應只掃 `character/item/map`。

**[RES:A]** `ClientDataList.xml`。

## 8. Wiki 與 Resource domain 的互相驗證

日本 Wiki 的玩家可見分類包含：

```text
Character
Character clothing / avatar
Weapons
Main / Sub / Melee / Grenade
Paper Puzzle / Skill
```

例如角色頁將 Character 與 package、face/expression、hairstyle、set clothing、top、bottom、shoes、accessory 分開列示；武器則按 main、sub、melee、throwing 等分類。

因此 Wiki 的玩家概念分類與 `Extracted/item` 中存在 `avatar` / `weapon` / `object` 等獨立 resource domains 是相互兼容的。

但這只能證明分類層的吻合，**尚不足以證明每個 Wiki item ID 對應哪個 binary asset ID**。

**[WIKI:C]** 玩家可見分類；**[RES:C]** resource topology。

## 9. 對 Server reconstruction 的直接約束

目前較穩健的 server model 應分離：

```text
Player
├─ CharacterState
├─ InventoryState
├─ EquipmentState
└─ LoadoutState
```

以及 Client resource resolution：

```text
CharacterIdentity
    -> character resource domain

ItemIdentity + category
    -> item/avatar/weapon/object resource domain

EquippedWeaponIdentity
    -> weapon resource domain
```

這只是 model boundary，不代表上述 packet 已全部恢復。

尤其目前 197 `GL_MYINFO_REQ` 的 response 尚未封死，因此不能把 Character / Inventory / Equipment 欄位硬塞進 197 的 schema。

## 10. 目前最大的 OPEN

下一步仍然必須由 Client data-flow 逐層確認：

```text
197 GL_MYINFO_REQ
   ↓
receiver / response
   ↓
player profile object
   ↓
CharacterState
   ↓
Inventory records
   ↓
Equipment / Loadout
   ↓
Weapon identity / durability / expiry / ammo-related state
```

同時需要繼續搜尋：

```text
item loader / parser
character loader / parser
weapon loader / parser
UI inventory builder
MyCharacter screen
Present / Gift screen
```

直到可以形成：

```text
Wiki item
 ↕
Resource identity
 ↕
Client runtime object
 ↕
Packet field
 ↕
Server state
```

## 11. 不應提前下的結論

目前證據不足以下列結論：

```text
item.dat = database inventory schema
character.dat = player-owned character list
maplist.dat value = universal map_id
811034967 = network protocol version
197 response = complete inventory packet
weapon directory name = exact server ItemType enum
```

這些全部保留 OPEN。
