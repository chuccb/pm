# PaperMan Resource Pack / Loader 邊界研究

> 研究日期：2026-09-17
> Target：日本版 PaperMan 2016 年最終 Client
>
> 本文件是目前 Resource / `ui/cfg` / `ui/lang` 的單一 truth。所有命名都以 `PaperMan.exe.c` 的 loader/consumer、實際 Extracted 資源內容、PaperMan Wiki 三方交叉驗證；只有單一來源支持的語意維持 `[OPEN]`。

## 1. Resource subsystem 的基本邊界

目前最安全的資料流是：

```text
Pack / file
    -> physical resource
    -> decoder / loader
    -> runtime object / table
    -> actual caller / UI / gameplay
```

必須分開：

```text
resource row
    != runtime record
    != player-owned state
    != network packet
```

因此 `itemdata.pat` 不等於 inventory、`Quest.pat` 不等於 QuestProgress、`maplist.pat` 不等於實際 map asset。

## 2. `Extracted/0.xml` 與 ClientDataList

`Extracted/0.xml` 直接定義主要 PackFile：

```xml
<PackFile key="character" filename="Data\\character.dat" folderpath="character\\" />
<PackFile key="item"      filename="Data\\item.dat"      folderpath="item\\" />
<PackFile key="map"       filename="Data\\map.dat"       folderpath="map\\" />
<PackFile key="pepachi"   filename="Data\\pepachi.dat"   folderpath="pepachi\\" />
<PackFile key="pmClient"  filename="Data\\pmClient.dat"  folderpath="" />
```

另有 `sounds`, `sounds01...sounds92` 等獨立 sound pack。

`Extracted/ClientDataList.xml` 又直接列出：

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

因此 `character/item/map` PackFile 與 `ui/cfg`、`ui/lang` 所在的 ClientData layer 必須分開理解。

## 3. Revision

目前 root、`character`、`item`、`map` 的 `datarevision.txt` 都是：

```text
811034967
```

`GL_LOGIN_REQ (682)` 的 C data-flow 又使用與 datarevision 相關的 state，因此：

```text
client resource revision
    -> login compatibility input
```

是強交叉線索；但 `811034967` 不能直接改名成 server protocol version。

## 4. `ui/lang/msgtableres.lang`

### 4.1 實際檔案內容

檔案開頭明確是：

```text
// This file was automatically generated. (CyLangPackTool generated include file)
// - 2014/11/26 : 15.54.51 -
```

其後是一行一個日文 localized message / format string，例如：

```text
フリーチャンネル %02d
メッセージ
差出人
%d PG
%d CASH
%sさんは%d番爆弾の設置を開始しました。
%d番爆弾が爆発!!!
個人サバイバル
ゲームルーム作成中…
ルームが存在しません。
アイテム購入成功
アイテム購入失敗
```

[RES] 實際檔案內容。

### 4.2 Runtime lookup 是 ordinal，不是 string key

`sub_408080(this, messageId)` 會以：

```text
record_count = (end - begin) / 28
record = begin + 28 * messageId
```

直接取得 runtime record。

因此：

```text
messageId (ordinal)
    -> runtime 28-byte message record
    -> localized string
```

`28` 是 runtime record stride，不是 `.lang` 一行的檔案大小，也不是 packet wire width。

[C] `sub_408080` / runtime table consumer。

### 4.3 `CyMsgTableID` 是另一層名稱

`sub_684770()` 會把同一 message table 輸出成 `.lang`；`sub_6849D0()` 則會輸出：

```c
enum CyMsgTableID
{
    ...
    IDMT_TOTALCOUNT
};
```

所以應維持三層：

```text
CyMsgTableID symbol
        ↓
ordinal message ID
        ↓
localized string
```

不能從 `.lang` 單獨反推出完整的 enum symbol name。

[C] `sub_684770`, `sub_6849D0`。

### 4.4 Message ID 對研究的價值

Client 大量使用 `sub_408140() -> sub_408080(messageId) -> sub_407F90(...)`。因此 C 裡的 numeric message ID 可以反查成玩家可見文字，再與 Wiki / UI 行為對照。

例如目前已看到 `795/796/801/813/820/827/828` 等 ID 被用於玩家可見文字。

`dword_EE3D88` 則是另一個 nickname / invalid-word validation table，不是 MessageTable。

## 5. `.pat` decoder

所有 `ui/cfg/*.pat` 都經過 Client 的 `pmFile` resource loading chain；目前由 `PaperMan.exe.c` 可還原出從檔尾向前的 byte transform：

```text
for i = length-1 .. 0:
    byte[i] = ROR8(byte[i] XOR state, i)
    state = ((state XOR 0xFA5387AD) & 0x0F3A94AA)
             XOR ((i | state) + 1217682890)
```

其中 `state` 以 32-bit 運算維持。

`pmFile::possible_ctor_or_dtor_39` 讀檔後呼叫 `sub_7118A0 -> sub_7117D0`，loader 才開始掃描 CRLF / comma 欄位。

因此這些 `.pat` 不是「天生可讀的 CSV」；應理解成：

```text
encoded resource bytes
    -> client decoder
    -> plaintext text / table stream
    -> fixed runtime structures
```

### 5.1 Parser 邊界

`sub_931720`、`sub_95C9A0`、`sub_9F5C00` 類似直接掃描 comma / CRLF 的 field splitter；沒有證據表明它們支援一般 CSV 的 quoted field / escaping。

## 6. `ui/cfg` 的完整六檔

目前 `Extracted/ui/cfg` 中的 `.pat` **剛好六個**：

```text
Quest.pat
RecommandItem.pat
itemdata.pat
maplist.pat
partsability.pat
weaponparts.pat
```

`Map.dat`、`pm_lobbydata.dat` 不屬於 `.pat`；`data.pat`、`convars.pat` 位於更廣義的 ClientData layer，也不要混進這六檔。

---

## 7. `Quest.pat`

### 7.1 Loader / runtime layout

C loader：`sub_931790()`，直接開啟：

```text
cfg\\Quest.pat
```

第一行是 record count，第二行是 header，資料 row 被 materialize 成：

```text
0x3090 = 12432 bytes / runtime record
```

[C] `sub_931790`。

### 7.2 已確認的 runtime offsets

```text
+000  int
+004  bool-like / integer flag
+008  int
+4108 int
+5136 int
+5140 wide string
+6164..6180  5 x int
+6184..6200  5 x int
+6204 wide string / condition data
+7228..7240  4 x int
+7244 wide string / condition data
+8268 wide string / condition data
+9292,+9296,+9300,+9304  4 x int
+9308..9316  3 x int
+9320..9328  3 x int
+9332..9340  3 x int
+9344 int
+9348 int
+9352 int
+9356 wide string
+10380 wide string
+11404 wide string
+12428 bool-like
```

原始 loader 是逐欄 `atol` / `mbstowcs_s` 寫入上述位置，因此這些不是 Hex-Rays 猜出的 class fields，而是 parser 真正寫入的位置。

### 7.3 實際 header 與 public Quest 語意

解碼後 header 已確認包含以下語意欄位：

```text
Index
QuestRepeat
QuestLevel
QuestName
QuestTermDescription
QuestDescription
LimitDate
CharacterType
UserLevel
ChanelList
TermItem1..5
UseAvatarItem1..5
UseWeapon
UseWeaponItem1..4
GameMode
MapNumber
PeriodType
QuestTerm
QuestTermData
QuestDropProbability
ClearItem1..3
ClearItemOption1..3
ClearItemLimit1..3
HonorMedalPosition
numberthumbnailFront
numberthumbnailBack
HonorMedalColor
StartDate
EndDate
Hidden
```

這些名稱以實際檔案 header 為主，再由 loader 逐欄 parse 驗證；但不是每個名稱都已經能與 public UI offset 做 1:1 完整閉環，因此個別 offset 在研究中仍可保留 `[OPEN]` 的「更深層資料類型」。

### 7.4 Wiki 三方驗證

Wiki 的 Quest system 明確記載：

```text
2012-10-31 實裝
每日共通 3 個 daily quest
玩家另可選最多 3 個 free quest
```

free quest 的受注條件包含：

```text
階級
称号
チャンネル
キャラクター
アバター
武器（特別クエスト）
```

進行條件還可以包含：

```text
モード
マップ
武器
```

Wiki 並進一步說明指定 channel / character / avatar / mode / map / weapon 時，只有符合條件的試合才會計入進度。citeturn517885view1

這與 `Quest.pat` 的 `CharacterType / ChanelList / UseAvatarItem / UseWeapon / GameMode / MapNumber` 類資料域高度一致，因此 Quest definition ↔ eligibility rule 已達 `[X]`。

但仍不能把任何一個 numeric value 直接命名成 public enum，除非 C + resource + Wiki 都閉合。

### 7.5 Quest runtime 不是 Definition table

`sub_933CE0` / `sub_933EC0` 明確區分：

```text
QUEST / QUESTCLEARLIST
QUESTCHALLENGE
```

各自有獨立 runtime object / list。

因此：

```text
Quest.pat
    = QuestDefinition / static definition

Quest runtime
    = progress / clear / challenge state
```

### 7.6 Honor Medal 額外閉環

`+9344` 被 `sub_927780` / `sub_927870` 以 63 為分組尺度排序、定位；`sub_925890` 又用：

```text
honor_f%d.dds
honor_b%d.dds
```

建立 Honor Medal 前後景圖路徑。

`+9348` / `+9352` 直接參與 front/back honor texture index。

`+9356` 不是任意文字：`sub_933220(+9356)` 會把 `/` 分隔的四個數值解析成 4 個 float；每個值若 >1 會除以 255，之後直接用於 Medal render pipeline。因此它是高度可信的四分量 visual/color-like data。

[C] `sub_927780`, `sub_927870`, `sub_925890`, `sub_933220`。

### 7.7 Quest period / eligibility 邏輯

`sub_9252D0` 直接以 `+9296` 做 1..21 的分支，再拿 `+9300` 與目前帳號的長期統計 / time-like state 比較；另外 `+7244` condition data 也被多處用於條件判定。

因此 `+9296` 至少是 QuestDefinition 中的**period / condition-class discriminator**，而不是普通文字或任意 ID；其 public enum name 仍應維持 `[OPEN]` 直到完整 enum 閉環。

## 8. `partsability.pat`

### 8.1 真實 header

解碼後 header 已確認：

```text
Item Index
Dot IG
Dot TG
gun_model_frame
gun3_model_frame
recoil
effective_range
limit_range
effective_damage
limit_damage
shot_delay
fov_level_min
fov_level_max
bullet_hole
ballCaseSize
add_damage
damage_repeat
move_speed
shoot_Wide
miJump
miSit
miStand
miWalk
miRun
shots_per_fire
first_shot_wide
first_shot_angle
tanpi_pap_type
tanpi_mot_type
sniperbackimgidx
sniperviewimgidx
```

### 8.2 C runtime mapping

loader 建立：

```text
0x106C = 4204 bytes / runtime row
```

`sub_958530(a1, n24, a3)` 是精確的欄位 accessor：

```text
n24=01 -> +004
n24=02 -> +008
n24=03 -> +012
...
n24=23 -> +092
n24=24 -> +096
```

也就是前 24 個 ability/config 欄位與 runtime offset 完全一一對應。

`sub_95BC90` 會對 n24=1..30 計算值，但只把 1..24 存入 aggregation object 的 24 個數值欄位；當 `j==5` 時另複製：

```text
+100
+104
+108
+1132
+2156
+3180
```

其中 `+108/+1132/+2156/+3180` 是額外 string/blob data。

[C] `sub_958530`, `sub_958360`, `sub_95BC90`。

### 8.3 八個 part 的聚合方式

`sub_958360`：

```text
weaponparts resolved IDs (最多 8)
        ↓
對每個 selected part lookup partsability
        ↓
對 n24=1..24 各自累加
        ↓
得到目前裝備組合的 aggregate ability
```

`sub_958460` 在 version 17 特殊路徑下，當 base weapon 不在八個 part 中時還會把 base value 加入。

### 8.4 Wiki 驗證

Wiki 的武器零件系統明確把公開效果分成：

```text
攻撃
精度
連射速度
射程
反動
移動
初弾命中
```

且同名零件可以因武器類型與實際武器不同而有不同效果；DOT 亦為獨立項。Wiki 的零件表直接存在 `Ⅰ..Ⅴ` 與 `DOT`，並列出不同武器的效果變化。citeturn732847search0turn732847search1turn642310search0

因此：

```text
partsability header
    ↔
weapon-part public stat domain
    ↔
sub_958530 n24 aggregation
```

已達 `[X]`。

注意：`recoil/effective_range/...` 這些是**欄位名稱**；它們不是 `sub_958530` 的 public enum value。`n24=1..24` 只是 table-column index。

## 9. `weaponparts.pat`

### 9.1 真實 header / runtime layout

解碼後 header 是：

```text
Gun Item No
Parts 1 No 1..10
Parts 2 No 1..10
Parts 3 No 1..10
Parts 4 No 1..10
Parts 5 No 1..10
Dot 1..10
Parts 6 No 1..10
Parts 7 No 1..10
```

loader 建立：

```text
0x170 = 368 bytes / runtime row
```

對應：

```text
+000      Gun Item No
+004..+040   Parts group 1, ten references
+044..+080   Parts group 2, ten references
+084..+120   Parts group 3, ten references
+124..+160   Parts group 4, ten references
+164..+200   Parts group 5, ten references
+204..+240   Dot, ten references
+244..+280   Parts group 6, ten references
+284..+316   Parts group 7, nine references used by the row parser
+320      trailing integer
```

`sub_958140` 會把 public/runtime group index 1..8 映射到上述八組位置；`sub_9591F0` 則逐組呼叫 `sub_9592C0`，解析成八個 resolved Part IDs。

### 9.2 Runtime slot 名稱的直接 C 證據

Client binary 中存在真正的 UI resource keys：

```text
PARTS01
PARTS02
PARTS03
PARTS04
PARTS05
DOTSIGHT
PARTS06
PARTS07
```

UI/model code 會逐一尋找這些 keys 並依裝備狀態顯示 / 套用它們。因此八個 runtime group 不是抽象虛構 slot。

[C] UI `sub_4180E0(... L"PARTS01" ... L"DOTSIGHT" ... L"PARTS07")` consumers。

### 9.3 與 Wiki 的關係

Wiki 公開展示的是：

```text
Ⅰ
Ⅱ
Ⅲ
Ⅳ
Ⅴ
DOT
```

以及具體零件名稱，例如 barrel / trigger / front sight / grip / stock / dot sight。citeturn732847search0

可直接成立：

```text
runtime PARTS01..07 / DOTSIGHT
    ↔
同一個 weapon-part subsystem
```

但目前尚未找到單一 binary call 能把 `PARTS06/PARTS07` 逐字等同於 Wiki 的Ⅰ..Ⅴ其中哪一個 public Roman slot，因此不要把八個 runtime group 強行壓成六個 public category。保留兩層表示：

```text
RuntimePartGroup = PARTS01..PARTS07 / DOTSIGHT
PublicPartSlot = Ⅰ..Ⅴ / DOT
```

兩者的精確 mapping `[OPEN]`。

## 10. `maplist.pat`

### 10.1 Loader / runtime layout

`sub_723B10()` 明確開啟：

```text
cfg\\maplist.pat
```

資料第一個值是 version-like value；第二個值是 record count；runtime row：

```text
0x344 = 836 bytes
```

欄位：

```text
+000 u32
+004 u32
+008..+135   128-byte block
+136..+263   128-byte block
+264..+391   128-byte block
+392..+519   128-byte block
+520..+647   128-byte block
+648..+775   128-byte block
+776/+780 pair
+784/+788 pair
+792/+796 pair
+800/+804 pair
+808/+812 pair
+816 u32
+820 u32
+824 u32 (version >= 1.02)
+828 u32 (version >= 1.03)
+832 u32
```

實際解碼內容的第一筆已看見：

```text
maps\\TU_01_tutorial.pmm
Tutorial
portraits\\Port_PP_01_dialog.dds
```

因此至少有直接的 map asset path、display/name-like string、portrait path 等資料。

### 10.2 Runtime consumer

`sub_729000(name)` 逐 row 使用 `wcscmp(name, row+136)`，找到後回傳該 row 的 `+4`。

此外：

```text
sub_728EE0 -> +816
sub_728F10 -> +820
sub_728D90 -> +824 != 0 check
sub_728DE0 -> +828 byte write
```

而其他 map/game calculations 直接消費 `+816/+820`。

因此 `maplist.pat` 是：

```text
Map catalog
+ resource binding
+ map/game parameters
+ feature/version flags
```

而不是單純名字列表。

### 10.3 與 room map selector 的邊界

目前 room path 另有：

```text
GAMEROOM_SCROLL_MAP
    -> selector value
    -> packet 121/122
    -> packet 129 start parameter
```

因此目前不能直接宣稱：

```text
121/122 map byte
    == maplist.pat row key
    == maplist.dat index
    == maps/*.pmm filename
```

這四者仍應各自建模，直到找到完整 conversion caller。

## 11. `RecommandItem.pat`

### 11.1 真實格式

第一個 metadata/count 資訊目前已實際讀到：

```text
1030
20
```

header：

```text
Index
Character Type
Concept Type
Item01
Item02
Item03
Item04
Item05
Item06
Item07
Item08
Item09
```

runtime row：

```text
0x30 = 48 bytes
```

欄位：

```text
+00 Index
+04 Character Type
+08 Concept Type
+0C Item01
+10 Item02
+14 Item03
+18 Item04
+1C Item05
+20 Item06
+24 Item07
+28 Item08
+2C Item09
```

### 11.2 Consumer

C 中存在：

```text
CRecommandItemParamCtrl::SetAllConceptTypeItem
```

並把 row 的 item groups 複製到 concept-type recommendation runtime table；其他 consumer 依 character/category 條件選擇推薦項。

因此：

```text
RecommandItem.pat
    = recommendation definition / selection data
```

不是 inventory，也不是 ownership state。

## 12. `itemdata.pat`

### 12.1 目前最強的已確認部分

Git blob SHA：

```text
2fbde8d4c8a9ca334655c312b2d9ed5d3ac8f2ac
```

實際檔案大小約 21.1 MB；目前 connector 未能把完整 binary blob 無截斷地交給分析環境，因此**本檔 raw bytes 尚未達到逐 byte 完整審閱**。這個限制不能被掩飾。

但是 C loader / consumers 已經足以把 runtime model 還原得很完整。

### 12.2 Loader / runtime record

`sub_52E1C0()` 明確開啟：

```text
cfg\\ItemData.pat
```

從檔頭讀 version-like value + record count，建立：

```text
1808 bytes / runtime row
```

目前直接從 parser 確認：

```text
+000,+004,+008,+00C       4 x int
+010                       variable blob
+210                       blob length
+214/+215                  bytes
+216..                     small metadata
+21C/+220/+224             3 x 4-byte value-like fields
+228..+27C                 22 x 4-byte values
+280/+281                  bytes
+284                       int
+288                       variable UTF-16 area
+488                       variable-area count
+48C/+48D                  bytes
+490..+498                 two small regions
+49C                       int
+4B0/+4B2                  mutable runtime durability
+4B4                       static/base durability source
+4B8/+4B9                  version-dependent bytes
+4BC..+4D8                 several 4-byte metadata values
+4E0/+4E4                  4-byte metadata
+4F8                       byte
+4F9                       derived bool-like state
+4FC                       runtime state
+500..+6FB                 runtime 0x200-byte buffer
+6FC/+700/+704             runtime state/defaults
```

（以上為十六進位 offset；例如 `+4B0=1200`、`+4B2=1202`、`+4B4=1204`。）

### 12.3 Item effect/value group

最重要的 consumer group 是：

```text
+22C .. +248  = 7 x 4-byte value-like fields
+264 .. +27C  = 7 x 4-byte IDs
```

對應的 C getters：

```text
sub_534070 -> value slot
sub_5340F0 -> value slot
sub_534170 -> value slot
sub_5354B0 -> 在 7 個 ID 中尋找指定 ID
```

這證明它們是有語意的 item/category-dependent definition data，而不是 padding；但不能把七欄全域硬命名成 Damage/Accuracy/etc.，因為 getter 會依 item category 2/9/10/11/15/16 等走不同 indexing rule。

### 12.4 Durability 已達 `[X]`

`sub_534450(itemId, int16)` 直接寫：

```text
runtime +1200
runtime +1202
```

而 `sub_534B60` 對 category 21/22 類 item 取得：

```text
+1204
```

作為 static/base value。

`sub_534530` / `sub_534660` / `sub_534890` 又以 current/base 或 action-specific value 計算百分比。

Wiki 同時記載一般永久武器有 durability、戰鬥會消耗、修理可恢復；因此：

```text
+1200/+1202 = mutable durability runtime state
+1204        = static/base durability value
```

已是 `[X]`，但 exact unit / packet conversion 仍 `[OPEN]`。

### 12.5 其他已知 consumer

```text
sub_533FF0 -> +533 category byte
sub_534030 -> +16 item text/blob
sub_534290 -> +552 scalar
sub_5342F0 -> +1164 count/flag field
sub_534C10 -> +1165 packed byte
sub_534CE0 -> derived +1273 bool-like state
sub_535680 -> parses #... hex into +1276
sub_5359B0 -> returns 4-byte block at +1212 + index and ID at +1248 + index
```

其中 `sub_535680` 明確把 `#...` 後的十六進位字串轉為數值，這也是 static resource metadata，而不是 ownership。

### 12.6 Server boundary

因此 server model 必須保持：

```text
ItemDefinition (static, from itemdata.pat)
        !=
OwnedItem (player state)
        !=
WeaponLoadout / EquipmentState
```

`itemdata.pat` 可以提供 definition-side defaults/effects/durability metadata；player current durability、ownership、slot state 另由 runtime/network domain 保存。

## 13. 六個 `.pat` 的統一模型

```text
Quest.pat
    -> QuestDefinition / eligibility / reward / presentation data

itemdata.pat
    -> ItemDefinition / category / UI-effect inputs / durability defaults

weaponparts.pat
    -> Weapon -> candidate part relation / runtime part groups

partsability.pat
    -> Part -> numeric ability/config parameters

maplist.pat
    -> Map catalog / binding / runtime map parameters

RecommandItem.pat
    -> recommendation / concept-type selection data
```

而：

```text
msgtableres.lang
    -> MessageId ordinal -> localized format string
```

這是另一條 text-localization pipeline。

## 14. 與 Wiki 的三方交叉規則

### 已達 `[X]`

1. `partsability.pat` 的公開 stat domain：實際 header + C column accessor + Wiki 武器零件 stat columns 一致。citeturn732847search0turn642310search0
2. `weaponparts.pat` 是 weapon-part relation layer：實際 header + 八組 runtime resolver + `PARTS01..07/DOTSIGHT` UI consumer + Wiki weapon-part subsystem 一致。citeturn732847search0
3. `Quest.pat` 是 static Quest definition：actual loader + Quest runtime separation + Wiki 的 channel/character/avatar/mode/map/weapon eligibility 一致。citeturn517885view1
4. `itemdata.pat` durability：C current/base consumers + Wiki durability behaviour 一致。

### 仍 `[OPEN]`

```text
itemdata.pat raw 21 MB 全檔逐 byte schema
maplist.pat +816/+820/+824/+828/+832 的每一個 public 名稱
Quest.pat 每一個 numeric offset -> public enum 的完整名稱
weaponparts runtime PARTS06/PARTS07 -> public Ⅰ..Ⅴ 的逐項 mapping
partsability +108/+1132/+2156/+3180 四個 blob/string 的 public semantic
itemdata category-dependent 7-value / 7-ID 的全域欄位命名
```

以上項目不能因「數值看起來像」而提前命名。

## 15. Server reconstruction 建議的 static-definition layer

目前 resource/domain 層可以穩定建模成：

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
├─ OwnedItem
├─ CharacterState
├─ EquipmentState
├─ WeaponPartEquipState
├─ QuestProgress / QuestChallengeState
└─ Match / Gameplay State
```

其中 `StaticDefinition` 不應直接寫入 player-owned state；`RuntimeState` 也不應依賴 `.pat` row memory layout。

## 16. Sources / evidence anchors

### IDA C

```text
sub_711720 / sub_7117D0  .pat decoder
sub_408080              message ordinal lookup
sub_684770              .lang exporter
sub_6849D0              CyMsgTableID exporter
sub_931790              Quest.pat loader
sub_52E1C0              ItemData.pat loader
sub_723B10              maplist.pat loader
sub_95CA10              weaponparts.pat loader
sub_958140/958530       weaponparts / partsability accessors
sub_958360              aggregated part ability calculator
sub_95BC90              aggregated part runtime object
sub_9F5C80              RecommandItem.pat loader
```

### Extracted resource

```text
Extracted/ui/lang/msgtableres.lang
Extracted/ui/cfg/Quest.pat
Extracted/ui/cfg/RecommandItem.pat
Extracted/ui/cfg/itemdata.pat
Extracted/ui/cfg/maplist.pat
Extracted/ui/cfg/partsability.pat
Extracted/ui/cfg/weaponparts.pat
Extracted/ClientDataList.xml
Extracted/0.xml
```

### PaperMan Wiki

```text
https://wikiwiki.jp/paperman/クエストシステム
https://wikiwiki.jp/paperman/武器パーツアップシステム
https://wikiwiki.jp/paperman/各種ゲージ詳細
https://wikiwiki.jp/paperman/MAP・ルール詳細
```
