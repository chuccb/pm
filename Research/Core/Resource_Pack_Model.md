# PaperMan Resource Pack / Loader 邊界研究

> 研究日期：2026-09-17
> Target：日本版 PaperMan 2016 年最終 Client
>
> 本文件記錄目前能由 `Extracted/`、IDA C/LST、runtime caller、packet dispatcher、Wiki 直接支持的 Resource pack / loader 邊界。資源檔案的「格式語意」與「玩家可見語意」必須分開處理；沒有足夠交叉證據時維持 `[OPEN]`。

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

**[RES]** 直接來自 `Extracted/0.xml`。

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

不能僅因為資料夾叫 `item` 就宣稱其中某個檔案必定是「玩家 inventory database」；它首先證明的是 client resource domain / pack domain。

而本輪對 `ui/lang` 與 `ui/cfg` 的研究進一步證明：**Client 還有一層獨立於 `character/item/map` pack domain 的 text/config database subsystem。**

## 3. Character Resource domain

`Extracted/character` 目前至少存在：

```text
animations/
models/
textures/
datarevision.txt
```

因此 Client 的 Character 資源域至少把 animation、model、texture、revision 放在同一個 `character` pack domain 下。

**[RES]** directory topology + `0.xml` pack mapping。

Server reconstruction 應分離：

```text
CharacterIdentity
    !=
CharacterRenderAsset
```

Server 保存玩家／角色語義 ID 與 state；Client 再透過 resource domain 取得模型、材質、動畫。

## 4. Item Resource domain 的內部分層

`Extracted/item` 至少分成：

```text
avatar/
object/
thumb/
weapon/
datarevision.txt
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

因此：

```text
ItemIdentity
ItemCategory
ItemState
```

應先保持一般化，再由 category 映射至 avatar / weapon / object 等 Client resource domain。

**[RES]** directory topology。

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

因此：

```text
MapList / map-selection metadata
    !=
actual map asset
```

目前既有 GameRule 研究已經得到：

```text
GAMEROOM_SCROLL_MAP
    -> map selector value
    -> 121/122
    -> 129 start parameter
```

而 `Extracted/map` 又存在 `maplist.dat` + `maps/` 兩層，所以不能直接把 selector byte 當作檔案名稱、array index 或 physics map object。

**[RES]** map domain topology + existing Room/GameRule C evidence。

## 6. `datarevision.txt` 的交叉證據

目前根層、character、item、map 的 `datarevision.txt` 均可讀出：

```text
811034967
```

因此這些 domain 在目前 Extracted 版本中共享同一 revision value。

既有 Login 研究另已確認 `GL_LOGIN_REQ (682)` 的 serializer 使用與 datarevision 相關的 state，因此：

```text
Client resource revision
    -> login bootstrap compatibility input
```

是很強的 cross-domain 線索。

但不能把 `811034967` 命名成 server protocol version；它首先被證明是 client data revision value。

**[RES]** revision files；**[C]** Login serializer data-flow。

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

因此 Client 另有一層 `ClientDataList` 索引概念，並非所有資料都經 `character/item/map` 三個 PackFile domain。

**[RES]** `ClientDataList.xml`。

## 8. `ui/lang/msgtableres.lang`：它不是普通 key/value 語言檔

### 8.1 檔案身份

目前 `Extracted/ui/lang` 的語言資源中直接存在：

```text
msgtableres.lang
```

檔案開頭明確寫：

```text
// This file was automatically generated. (CyLangPackTool generated include file)
// - 2014/11/26 : 15.54.51 -
```

後面是一個**按固定順序排列的純文字 message list**，例如：

```text
フリーチャンネル %02d
メッセージ
差出人
%d PG
%d PG - 期間
%d CASH
%sさんは%d番爆弾の設置を開始しました。
%d番爆弾が爆発!!!
個人サバイバル
ゲームルーム作成中…
ルームが存在しません。
アイテム購入成功
キャラクター購入成功
```

這證明它的內容不是一般配置參數，而是玩家可見的 localized message / format-string catalog。

**[RES]** 檔案內容本身。

### 8.2 Client 如何載入

IDA 中可見 language loader 會組造：

```text
lang\\<locale-selected-name>.lang
```

若該 locale 路徑沒有成功，則 fallback 到：

```text
lang\\MsgTableRes.lang
```

這條路徑與 Client 的 message table singleton 初始化相連。fileciteturn353file4L957-L998

### 8.3 真正的 key 是「ordinal message ID」

這是目前最重要的結論。

runtime lookup `sub_408080(this, a2)` 並不是做字串 key lookup；它先以：

```text
record_count = (end - begin) / 28
```

檢查 `a2`，然後直接訪問：

```text
record = begin + 28 * a2
return record.string
```

所以 `a2` 是**訊息表的 ordinal ID / index**。fileciteturn354file2L468-L505

因此在 Server reconstruction / Client compatibility 中應把它理解成：

```text
MessageId (ordinal)
    -> localized format string
```

而不是：

```text
"SOME_NAME" -> string
```

### 8.4 `.lang` 與 `CyMsgTableID` 名稱層是兩件事

IDA 中另有 `sub_6849D0()`，會把 runtime message records 輸出成：

```text
enum CyMsgTableID
{
    <symbol>, // <string>
    ...
    IDMT_TOTALCOUNT
};
```

而 `sub_684770()` 則會把相同 message records 輸出成一行一個 string 的 `.lang`。fileciteturn352file2L406-L442 fileciteturn352file3L467-L520

所以應該建立三層概念：

```text
CyMsgTableID symbol
        ↓ compile-time name layer
ordinal message ID
        ↓ runtime lookup
localized string in msgtableres.lang
```

目前 Extracted repository 中沒有看到對應完整的 `CyMsgTableID` 原始 enum/header，因此**不能反過來從 `.lang` 猜出 symbol name**。

### 8.5 runtime record stride `28` 不是 `.lang` 的 wire format

`28` 是 runtime message table record 的 stride；`sub_408080()` 以 `begin + 28 * index` 取 record，並依 small-string / heap-string capacity 決定字串位置。fileciteturn354file2L468-L494

因此：

```text
28-byte runtime record
    !=
一行 .lang 的檔案大小
    !=
network packet field size
```

這個界線在後續 LLM 逆向時非常重要。

### 8.6 Message ID 可以直接參與 gameplay/UI 邏輯

Client 大量呼叫：

```text
sub_408140()
    -> sub_408080(message_id)
    -> sub_407F90(format, ...)
```

例如目前 C 中可直接看到 `795`、`796`、`801`、`813`、`820`、`827`、`828` 等 message ID 被拿來建立玩家可見文字。fileciteturn353file2L451-L510

因此 `msgtableres.lang` 可以拿來反查：

```text
numeric constant in C
    -> actual Japanese text
    -> observable UI/gameplay semantic
```

這對目前大量 `[OPEN]` 的 event、error、room、combat、quest 研究非常有價值。

### 8.7 禁止混淆的另一個 table

`dword_EE3D88` 是另一個文字驗證／禁止字詞相關 table；Client 會用 `sub_52B4F0()` 對 nickname / string 做檢查。它不是 `msgtableres.lang` message table。

因此：

```text
MessageTable
    !=
profanity / invalid-name table
```

## 9. `ui/cfg/*.pat` 的完整清單

目前 `Extracted/ui/cfg` 中的 `.pat` **剛好是六個**：

```text
Quest.pat
RecommandItem.pat
itemdata.pat
maplist.pat
partsability.pat
weaponparts.pat
```

`Map.dat`、`pm_lobbydata.dat` 是其它 config/data；它們不屬於本輪「全部 `.pat`」六檔範圍。

另外：

```text
data.pat
convars.pat
```

存在於更廣義 ClientData 資料層，但不在 `ui/cfg/`，不可把它們誤算成這六檔。

六個 `.pat` 的共同特徵是：

```text
cfg\\<file>.pat
    ↓
pmFile loader
    ↓
CRLF-separated text
    ↓
comma-separated columns
    ↓
fixed-size runtime record / index
```

目前看到的 `sub_931720`、`sub_95C9A0`、`sub_9F5C00` 都是直接掃到 comma / CRLF 的欄位切割器，而不是完整 CSV parser；不能假定有一般 CSV 的 quoted-field / escaping semantics。

共同原則仍然是：

```text
.pat file row
    !=
runtime record
    !=
network packet
```

## 10. `Quest.pat`：Quest subsystem 的大型靜態資料表

Client 的 loader 是 `sub_931790()`，明確開啟：

```text
cfg\\Quest.pat
```

它把第一行解析成總筆數，跳過表頭區，然後以：

```text
0x3090 = 12432 bytes / runtime record
```

建立每筆資料。fileciteturn355file2L883-L928

每列欄位是 comma-separated，會被寫入大量固定 runtime offsets；其中已可直接確認：

```text
+0      int key
+4      bool-like flag
+8      int
+4108   int
+5136   int
+5140   wide string
+6164..6180  5 ints
+6184..6200  5 ints
+6204   wide string
+7228..7240  4 ints
+7244   wide string
+8268   wide string
+9292..9304  4 ints
+9308..9316  3 ints
+9320..9328  3 ints
+9332..9340  3 ints
+9344   int
+9348   int
+9352   int
+9356   wide string
+10380  wide string
+11404  wide string
+12428  bool-like flag
```

原始 C 逐欄 parse 的證據見 `sub_931790()`。fileciteturn355file2L947-L1128

### 10.1 key namespace

Loader 之後直接依：

```text
key / 10000
```

分流：

```text
== 1       -> sub_927870
== 2/3/4   -> sub_92A870 + sub_9216B0
```

這證明 `key / 10000` 是 Quest subsystem 內部的重要 namespace/class discriminator。fileciteturn355file2L1106-L1121

但它**還不能單獨證明**是「Quest 類型 1/2/3/4」的玩家可見 enum，因此正式研究名稱仍應寫成：

```text
QuestKeyNamespace = key / 10000
```

精確公開語意 `[OPEN]`。

### 10.2 與現有 Quest/Event packet 研究的關係

目前 `Result_Quest_Stats.md` 已經還原 `sub_92EF00()` 的 Quest/Event mutation graph；`Quest.pat` 則提供了「定義資料」一側。

因此下一階段可用：

```text
Quest.pat key
    ↕
sub_92EF00(id, subtype, amount, filter)
    ↕
message ID / quest UI string
    ↕
Wiki quest/event description
```

來封閉目前很多 `[OPEN]` 的 public semantic。

目前不能把：

```text
sub_92EF00(35,...)
```

直接命名為「Quest 35」；既有 C evidence 已證明第二參數等也有獨立語義，ID namespace 必須分別處理。

## 11. `itemdata.pat`：Item Definition / UI effect / durability defaults 的核心資料庫

Client 的 loader `sub_52E1C0()` 明確開啟：

```text
cfg\\ItemData.pat
```

並從檔案取得：

```text
version-like first value
record count
```

然後建立：

```text
0x710 = 1808 bytes / runtime row
```

的固定記憶體記錄。fileciteturn355file0L117-L136

已直接確認的重要欄位：

```text
+0       int key
+4       int
+8       int
+12      int
+16      variable blob
+528     blob length
+532     byte
+533     byte
+534..536 3 bytes
+540,+544,+548  3 x 4-byte values
+552..636      22 x 4-byte values
+640,+641      bytes
+644       int
+648       variable 16-bit data area
+1160      count for variable area
+1164,+1165 bytes
+1168..1184   5-byte region
+1188..1192   5-byte region
+1196      int
+1200,+1202 runtime-initialized to 0
+1204      4-byte static value
+1208,+1209 version-conditional values
+1212..1240 several 4-byte values
+1248,+1252 4-byte values
+1272      byte
+1273      bool-like derived state
+1276      runtime-initialized -1
+1280      runtime state
+1284..1795 runtime 0x200-byte buffer
+1796,+1800,+1804 runtime state/defaults
```

其中 `+1273` 並非檔案直接欄位，而是 loader 計算 `+584..+608` 若干值中是否存在正值後得到的衍生 bool。fileciteturn355file0L217-L267

### 11.1 durability 的交叉驗證

既有 Character/Inventory 研究已從 runtime helper 確認：

```text
sub_534450(resourceIdentity, int16)
    -> runtime +1200 / +1202
```

而 `itemdata.pat` loader 本身又把：

```text
+1200 = 0
+1202 = 0
+1204 = file-derived value
```

因此：

```text
+1200/+1202
    = mutable runtime durability state

+1204
    = static/base durability-related value
```

已達 `[X]` 等級；但 exact unit / wire conversion 仍是 `[OPEN]`。

### 11.2 Item resource 與 itemdata.pat 的關係

`itemdata.pat` 的 row key 還會進入 lookup；而特定 key range 會觸發額外 runtime index / UI weapon effect initialization。fileciteturn355file0L315-L369

因此它是：

```text
ItemDefinition / ItemConfig
    -> runtime item tables
    -> UI / effect metadata
    -> weapon/item behaviour helpers
```

不是：

```text
PlayerInventory
```

### 11.3 Server 邊界

因此 Server 應分離：

```text
ItemDefinition
    !=
PlayerOwnedItem
```

而 `itemdata.pat` 更接近 Definition / static configuration 一側。

## 12. `weaponparts.pat`：武器零件組合／關聯表

Client 的 loader `sub_95CA10()` 明確開啟：

```text
cfg\\weaponparts.pat
```

它建立：

```text
0x170 = 368 bytes / runtime row
```

的記錄。每列的已知結構為：

```text
+0        int key
+4..+40   10 x int
+44..+80  10 x int
+84..+120 10 x int
+124..+160 10 x int
+164..+200 10 x int
+204..+240 10 x int
+244..+280 10 x int
+284..+316 9 x int
+320      int
```

也就是精確的：

```text
1 key
+ 10 / 10 / 10 / 10 / 10 / 10 / 10 / 9 integer references
+ 1 trailing integer
```

loader / row materialization 證據見 `sub_95CA10()`。fileciteturn355file3L1247-L1371

### 12.1 八組 integer reference arrays 有實際 runtime 消費者

`sub_958140()` 明確把參數 `1..8` 映射到：

```text
1 -> +4..+40
2 -> +44..+80
3 -> +84..+120
4 -> +124..+160
5 -> +164..+200
6 -> +204..+240
7 -> +244..+280
8 -> +284..+316
```

並逐一測試候選 ID 是否存在其中。這不是死資料；後續 `sub_956BB0`、`sub_957070`、`sub_957140`、`sub_957200`、`sub_9574E0`、`sub_957C20` 等都把這些欄位當成 runtime part/component 關聯來消費。fileciteturn357file2L1326-L1396

因此高信心結論是：

```text
weaponparts.pat
    -> weapon/part relation definitions
    -> runtime component selection / matching
```

### 12.2 與 network packet 的直接交叉確認

Client packet registration 直接存在：

```text
207  GS_BUY_WEAPONPARTS_ACK
912  GL_WEAPONPARTS_EQUIP_CHANGE_REQ
913  GL_WEAPONPARTS_EQUIP_CHANGE_ACK
```

對應 C evidence：

```text
207 -> packet registration
912 -> Packet::ctor(912) + fields
913 -> response registration / receiver
```

`912` request 的 serializer 至少直接寫入：

```text
sub_592920(v8, 0)
sub_592AA0(v8, a5)
sub_592AA0(v8, thisa)
sub_555090(&dword_1321D00, v8)
```

證明武器零件裝備變更是正式 network operation，而不是純 client UI 狀態。fileciteturn359file0L1-L14 fileciteturn359file1L16-L29 fileciteturn359file2L31-L44 fileciteturn362file1L174-L187

但是目前還**不能**把八組欄位直接命名成 `Scope/Barrel/Muzzle/...` 等公開 slot 名稱。這需要 `.lang` / UI config / item resource / Wiki 再做一輪一對一證明。

## 13. `partsability.pat`：零件 ability / parameter table，但公開欄位名稱仍未完全封閉

Client 的 `partsability.pat` loader 建立：

```text
0x106C = 4204 bytes / runtime row
```

並以第一欄 key 建 lookup。

目前可以確定它不是單純字串資源；每列包含一組固定的數值欄位，核心欄位區域落在：

```text
+0      int key
+4..+48    多個 float-like numeric parameters
+52..+96   多個 additional numeric parameters
+100,+104 integer parameters
```

更重要的是，`sub_956240(key)` 會從這個 table 取回對應 record 的 `+16` 值；而 `sub_958140()` 等 consumer 又依照與 `weaponparts.pat` 相同的八組 part/reference 結構進行 component matching。這說明兩個檔案是同一個武器零件 runtime subsystem 的不同資料層：

```text
weaponparts.pat
    -> 哪些 part / component 關聯

partsability.pat
    -> part 對應的 numeric ability/config parameters
```

**[C]** loader + consumer；**[X]** 與 weapon-part runtime graph；**[OPEN]** 每個 numeric column 的公開玩家語意與 exact formula。

不能直接把 `+16` 命名成 Damage / Accuracy / Recoil 等，直到找到對應 calculation caller + Wiki/resource evidence。

## 14. `maplist.pat`：地圖 catalog / runtime map parameters

Client 的 loader `sub_723B10()` 明確開啟：

```text
cfg\\maplist.pat
```

第一行被讀成：

```text
float-like version value
```

第二個值作為 record count；每列 materialize 成：

```text
0x344 = 836 bytes / runtime record
```

fileciteturn355file1L409-L471

已直接確認欄位布局：

```text
+0      int
+4      int
+8..+135      128-byte block
+136..+263    128-byte block
+264..+391    128-byte block
+392..+519    128-byte block
+520..+647    128-byte block
+648..+775    128-byte block
+776/+780     pair
+784/+788     pair
+792/+796     pair
+800/+804     pair
+808/+812     pair
+816          int
+820          int
+824          optional field if version >= 1.02
+828          optional field if version >= 1.03
+832          int
```

fileciteturn355file1L472-L537

### 14.1 它不是實際地圖 asset

loader 後續還會建立：

```text
qp_engine::CMapData
CEntityManager
其他 map runtime subsystems
```

因此 `maplist.pat` 是 **catalog/config + map-runtime parameters**，不是 `maps/` 裡面的實際場景資產。fileciteturn355file1L552-L613

### 14.2 與 121/122 GameRule map selector 的關係

目前只能確定它與 map subsystem 同域，而且與 `Extracted/map/maplist.dat` 都存在於 Client map pipeline。

不能直接假定：

```text
maplist.pat row key
    ==
121/122 map value
    ==
maplist.dat index
    ==
actual map resource folder name
```

這四者必須由 caller conversion 一一閉環。

## 15. `RecommandItem.pat`：推薦物品參數資料，而非 inventory

Client 的 loader `sub_9F5C80()` 明確開啟：

```text
cfg\\RecommandItem.pat
```

它建立：

```text
0x30 = 48 bytes / runtime record
```

第一行為 record count，第二行另有一個 integer metadata/value；資料列則是固定數量的 integer columns：

```text
+0
+4
+8
+12
+16
+20
+24
+28
+32
+36
+40
+44
```

即 12 個 integer fields。fileciteturn357file0L71-L164

### 15.1 runtime 名稱已提供很強語意證據

後續 `sub_9F6B30()` 的 log 明確出現：

```text
CRecommandItemParamCtrl::SetAllConceptTypeItem
```

並把選出的 row 欄位 +3..+11 拷貝到 concept-type item runtime table。fileciteturn357file1L714-L744

所以目前高信心結論是：

```text
RecommandItem.pat
    -> recommended-item parameter definitions
    -> concept-type recommendation runtime state
```

而不是：

```text
PlayerInventory
```

`key == 2498` 雖然在 loader 中有 special branch，但不能僅依這個值猜 public semantic。

## 16. 六個 `.pat` 的統一資料模型

目前整體已可穩定整理成：

```text
ui/cfg/
│
├─ Quest.pat
│    └─ Quest subsystem definitions / indexed quest data
│
├─ itemdata.pat
│    └─ Item definition / item runtime metadata / UI-effect inputs
│
├─ maplist.pat
│    └─ Map catalog + map-runtime parameters
│
├─ weaponparts.pat
│    └─ Weapon-part relation / component groups
│
├─ partsability.pat
│    └─ Part ability / numeric parameter definitions
│
└─ RecommandItem.pat
     └─ Recommended-item / concept-type recommendation parameters
```

而：

```text
ui/lang/msgtableres.lang
    └─ localized player-facing message catalog
       indexed by ordinal MessageId
```

兩者的責任完全不同：

```text
message resource
    -> 把 numeric message ID 轉成玩家看得到的文字

.pat config databases
    -> 把 static ID/key 轉成 gameplay/UI/resource runtime parameters
```

因此不可把 `.lang` 與 `.pat` 當成同一種 config format。

## 17. 與 Wiki 的正確交叉驗證方式

目前 Wiki 能提供的是玩家可見語意，例如：

```text
Weapons
Characters
Avatar / clothing
Modes
Quest
Shop / Package
Durability
UI-visible actions / room behavior
```

而 `.pat` 提供的是：

```text
static ID
field grouping
numeric parameter
lookup relation
version gating
runtime consumer
```

最有價值的交叉方式不是「檔名像不像」，而是：

```text
Wiki visible concept
        ↕
message ID / UI text
        ↕
.pat key or numeric row
        ↕
IDA runtime consumer
        ↕
packet / state mutation
```

例如武器零件目前已經有：

```text
weaponparts.pat
    ↕
part runtime matching
    ↕
207 / 912 / 913 network operations
```

而 message table 又可以提供 UI-visible Japanese strings 作為最後一層語意驗證。

Quest 同樣可以形成：

```text
Quest.pat
    ↕
Quest runtime object
    ↕
sub_92EF00 event mutation
    ↕
msgtableres.lang / Quest UI
    ↕
Wiki Quest / Event behavior
```

這種閉環才足以把 `[OPEN]` 升成 `[X]`。

## 18. 對 Server reconstruction 的最重要邊界

目前 resource subsystem 應至少拆成：

```text
StaticDefinition
├─ ItemDefinition
├─ QuestDefinition
├─ MapDefinition / MapConfig
├─ WeaponPartDefinition
├─ PartAbilityDefinition
└─ RecommendationDefinition

LocalizedText
└─ MessageId -> LocalizedFormatString

RuntimeState
├─ PlayerInventory
├─ CharacterState
├─ EquipmentState
├─ WeaponPartEquipState
├─ QuestProgress / EventState
└─ Match / Gameplay State
```

其中：

```text
.pat row
    !=
Player-owned state
```

但某些 `.pat` 欄位會直接決定 runtime calculation / UI / equip validation，因此 Server compatibility model 必須能查到對應 static definition。

## 19. `[OPEN]` 與禁止猜測清單

目前仍不能僅依 resource filename 或 numeric offset 下列結論：

```text
itemdata.pat field +X = 某個公開 ItemType enum
weaponparts.pat group 1..8 = 某八種固定零件槽名稱
partsability.pat +16 = Damage / Accuracy / Recoil 等具體 stat
Quest.pat key/10000 = 玩家看到的 QuestType enum
maplist.pat key = universal map_id
maplist.pat row = actual map asset
RecommandItem.pat concept type = 某個公開 Shop category
msgtableres.lang 第 N 行 = 某個英文/C++ symbol name
811034967 = network protocol version
```

只有在出現：

```text
[C] runtime calculation / caller
+ [RES] exact resource row / string
+ [WIKI] player-visible behavior
```

至少兩層獨立證據一致時，才應升級成 `[X]` 或具體公開 semantic。

## 20. 目前最值得繼續封閉的四條鏈

### A. Message ID closure

```text
numeric ID in C
    -> msgtableres.lang exact line
    -> caller context
    -> Japanese UI meaning
```

這可以批量降低 C 中大量 `sub_408080(v, 0xNNN)` 的黑盒程度。

### B. Weapon-part closure

```text
weaponparts.pat group
    -> part/item resource ID
    -> UI string / icon
    -> Wiki weapon-part concept
    -> 912/913 payload field
```

這是目前最有希望直接解出正式 weapon-part slot semantics 的鏈。

### C. Quest closure

```text
Quest.pat key / row
    -> Quest runtime offset
    -> sub_92EF00 / 243 / 245 / 381..389
    -> message string
    -> Wiki Quest/Event
```

### D. Map closure

```text
maplist.pat key / row
    -> map resource ID
    -> GAMEROOM_SCROLL_MAP
    -> 121/122
    -> 129
    -> actual map resource folder
    -> Wiki map/mode
```

這四條鏈都不應靠猜測補洞。

## 21. 最終目前的 Resource 認知模型

現在可以把 PaperMan 的 client-side static resource subsystem 穩定理解成：

```text
                         ┌─ character.dat ── character assets
Pack / Asset layer ──────┼─ item.dat ─────── item/avatar/weapon/object assets
                         └─ map.dat ──────── map assets

                         ┌─ msgtableres.lang ── MessageId -> localized text
UI / Config layer ───────┼─ Quest.pat
                         ├─ itemdata.pat
                         ├─ maplist.pat
                         ├─ weaponparts.pat
                         ├─ partsability.pat
                         └─ RecommandItem.pat

                                   ↓
                           runtime definition/index
                                   ↓
                    Client UI / gameplay / validation
                                   ↓
                       packet / state / result behavior
                                   ↓
                         Server reconstruction
```

最重要的邊界是：

```text
resource definition
    !=
runtime player state
    !=
network wire schema
```

但三者存在大量明確 cross-reference。逆向工作真正要做的是把：

```text
ID / key
→ static definition
→ runtime consumer
→ player-visible message
→ packet/state mutation
```

完整閉環，而不是單獨猜其中任一層。
