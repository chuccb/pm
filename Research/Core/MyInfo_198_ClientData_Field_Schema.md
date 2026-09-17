# `GL_MYINFO_ACK (198)` ClientData 完整結構

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 更新基準：2026-09-17。
> 文件角色：`198` 唯一主文件。本文只保存 198 的封包組合順序、198 特有的 Profile／MyInfo／Avatar 關聯，以及最終未閉合項目；共用 ClientData wire family 的完整結構統一見 `ClientData_Shared_Decoder_Field_Evidence.md`。

## 1. 封包定位

```text
197 GL_MYINFO_REQ
    payload = 0 bytes

198 GL_MYINFO_ACK
    = 複合式 ClientData bootstrap / update
```

`sub_570550()` 顯示 198 並非單一扁平結構，而是依固定順序串接多個可獨立驗證的 decoder：

```text
u8  status
u32 first_scalar
ProfileBlock              = sub_523BF0
AppearanceRecords         = sub_524010        // Family D
LoadoutConfigRecords      = sub_524660        // Family A
ItemSlotValidation        = sub_527550
SkillSlotValidation       = sub_527D00
u16 standalone_0
u32 standalone_1
u8  list_count
u8[list_count]
MyInfo / Avatar hydration
```

因此 Server reconstruction 應保留這些 codec 邊界，不應把 198 做成一個巨大且無法對應 Client parser 的 struct。

## 2. 198 頂層結構

成功分支：

```text
+0x00  u8  status
+0x01  u32 first_scalar
+...   ProfileBlock
+...   AppearanceRecords
+...   LoadoutConfigRecords
+...   ItemSlotValidation
+...   SkillSlotValidation
+...   u16 standalone_0
+...   u32 standalone_1
+...   u8  list_count
+...   list_count × u8
```

`status == 0` 時不進入完整 bootstrap；因此後續欄位只適用於成功分支。[C]

`first_scalar` 確實被 ClientData／狀態 setter 使用，不是單純 padding；正式公開語意仍 `[OPEN]`。[C][OPEN]

## 3. `sub_523BF0`：198 特有 ProfileBlock

`sub_523BF0()` 的直接讀取順序為：

```text
ASCII-Z string
u8
u32 × 4
u32 × 5
u32 × 4
u32 × 4
u32 × 5
u8 × 3
u32 × 3
raw[48]
u8
```

其中：

```text
string → this +15
u8     → this +22
多組 u32 → +23..+51 等 Profile state
raw[48] → +52
部分 u8 → +76 / +305 / +306
final u8 → +1
```

`sub_592500(..., 0x30)` 明確以 48 bytes 處理最後的 raw block，因此不能因 Hex-Rays 表面型別而改寫成字串或 12 個 DWORD。[C]

對應 `sub_523E10()` 存在 serializer，可反向證明此 ProfileBlock 不是只在接收端偶然出現的記憶體形狀。[C]

目前未取得足夠唯一 consumer 將這些 Profile scalar 全部正式命名為 `Level`、`CharacterId` 等；因此維持 raw／`[OPEN]`。[C][OPEN]

## 4. Family D：`sub_524010` Appearance / Character records

198 使用 `sub_524010()` 解析最多 20 筆記錄。

完整 Family D wire schema 不在本文重複；唯一真相位於：

```text
Research/Core/ClientData_Shared_Decoder_Field_Evidence.md
```

該 family 已閉合為：

```text
u8 count <= 20
repeat:
    u8  record_selector
    u16 field[0]
    u16 field[1]
    ...
    u16 field[11]
```

單筆固定 **25 bytes**。[C]

### 4.1 198 特有的 Resource namespace evidence

`sub_5280F0()` 對該 record 的多個 u16 執行不同 namespace 驗證，目前可直接記錄：

```text
r[1]  → 19,900,000 + (r[1] % 100,000)
r[2]  → 10,000,000 + (r[2] % 100,000)
r[3]  → 10,100,000 + (r[3] % 100,000)
r[4]  → 10,200,000 + (r[4] % 100,000)
r[5]  → 10,300,000 + (r[5] % 100,000)
r[6]  → 10,400,000 + (r[6] % 100,000)
r[7]  → 10,500,000 + (r[7] % 100,000)
r[8]  → 10,600,000 + (r[8] % 100,000)
r[9]  → 10,700,000 + (r[9] % 100,000)
r[10] → 10,800,000 + (r[10] % 100,000)
r[11] → 10,900,000 + (r[11] % 100,000)
```

這證明該記錄是多個 Resource namespace 的複合資料，而不是通用 16-bit 數值陣列。[C][X]

`r[0]` 為 selector／slot 類欄位，不是 resource ID。[C]

`r[12]` 有獨立 getter／resource path，但尚未取得足夠證據給出公開名稱，因此保持 `[OPEN]`。[C][OPEN]

### 4.2 Avatar 交叉驗證

這些 namespace 最終進入 `AVATAR` 相關 UI／Resource pipeline，包括：

```text
sub_525F10
sub_525F60
sub_525FB0
sub_526000
sub_526050
sub_5260A0
sub_5260F0
sub_526140
sub_526190
sub_5261E0
sub_526230
sub_526280
```

並由 `sub_4BFA50()`、`sub_6A9950(..., L"AVATAR", ...)` 等路徑使用。[C]

`Extracted/` 中存在 avatar、body、hair、face、set、`acc1..acc4` 等資料，可作為 Resource 層旁證；但尚未足以把每一個 wire u16 一一命名成固定外觀欄位。[RES][X][OPEN]

## 5. Family A：`sub_524660` Loadout / Configuration

198 也會呼叫 `sub_524660()`，最多 4 筆。

完整 wire schema 不在本文重複；請以 `ClientData_Shared_Decoder_Field_Evidence.md` 的 Family A 為唯一定義。

198 只關心其在 composite chain 中的順序與 downstream validation：

```text
sub_524660
    ↓
sub_527DB0
    ↓
Resource / slot validation
```

Family A 的存在至少能確認與 loadout／配置資料及多個 Resource domain 有關；尚不足以把每個 u16/u32 直接命名成公開武器／技能／物品欄位。[C][OPEN]

## 6. Item-slot 與 Skill-slot validation

### 6.1 `sub_527550`

`sub_527550()` 委派 `sub_522480()`，固定讀取：

```text
9 × u32
```

非零值會向 Client Resource DB 驗證；失敗對應：

```text
error 10
E_CRI_ERR_INVALID_ITEM_SLOT
```

因此 198 成功資料中存在一個獨立的 9 × u32 Item-slot / Resource validation component。[C]

各 index 對應哪個公開物品槽位仍 `[OPEN]`。

### 6.2 `sub_527D00`

先讀：

```text
u8 context
```

再由 `sub_527AF0()` 讀：

```text
7 × u32
```

非零值會驗證 Resource；失敗對應：

```text
error 9
E_CRI_ERR_INVALID_SKILL_SLOT
```

因此它是與 Item-slot validation 分離的 Skill-slot 資料域。[C]

## 7. Indexed Item collection 的邊界

`sub_524B70()` 是另一個明確的 ClientData item collection decoder。它不應與 Family D 的 20 筆外觀記錄混為一談：

```text
AppearanceRecords
    = 20 × 25-byte Family D records

OwnedItemCollection
    = indexed collection handled by sub_524B70
```

`sub_524B70()` 的完整 wire family 已集中於 `ClientData_Shared_Decoder_Field_Evidence.md`；物品、耐久度與角色層語意則集中於 `Character_Inventory_Equipment.md`。[C]

這裡只保留 198 的關係，避免再次建立第三份 Item schema。

## 8. 198 最後的獨立欄位

`sub_570550()` 在各 nested decoder 完成後，仍會直接讀取：

```text
u16 standalone_0
u32 standalone_1
u8  list_count
repeat min(list_count, 20):
    u8 list_value
```

`list_count` 有本地上限控制，資料會進入 `sub_5A9B30(...)`。

這幾個欄位不是 Family A/B/C/D 的 nested record，應維持為 198 專屬尾端欄位。公開語意目前 `[OPEN]`。[C][OPEN]

## 9. 198 完整 composite schema

```text
198 GL_MYINFO_ACK
│
├─ u8  status
│
└─ if status != 0:
   │
   ├─ u32 first_scalar
   ├─ ProfileBlock                 sub_523BF0
   ├─ AppearanceRecords            sub_524010 / Family D
   ├─ LoadoutConfigRecords         sub_524660 / Family A
   ├─ ItemSlotValidation           sub_527550 / 9×u32
   ├─ SkillSlotValidation          sub_527D00 / u8 + 7×u32
   ├─ u16 standalone_0
   ├─ u32 standalone_1
   ├─ u8  list_count
   └─ list_count × u8
```

這是 198 的唯一 composite 結構描述。Family A/B/C/D 的內部格式只在共用文件維護。[C]

## 10. MyInfo / Avatar hydration

198 的意義不能只停留在 wire parser。Client 在解碼後會進入：

```text
INFORMATION
    ↓
MYINFO
    ↓
AVATAR / Character / Item data
```

並使用 `AVATAR` key、Character／ClientData object 與 Resource lookup 建立後續 UI 狀態。[C]

因此 198 是 Login 後的實際玩家資料 bootstrap 節點之一。

## 11. Reconstruction 邊界

Server implementation 應採：

```text
GL_MYINFO_ACK
    ↓
198 codec chain
    ├─ ProfileBlockCodec
    ├─ AppearanceFamilyDCodec
    ├─ LoadoutFamilyACodec
    ├─ ItemSlotValidationCodec
    ├─ SkillSlotValidationCodec
    └─ 198TailFields
```

不可：

```text
把所有 nested record 塞進一個 ClientDataRecord
```

也不可：

```text
Client object offset
    = wire offset
    = server database column
```

這三者必須維持獨立。

## 12. Evidence / OPEN policy

目前所有正式公開名稱都必須能追溯到至少一條直接資料流：

```text
serializer / parser
    → 實際 helper width
    → caller / callee
    → state field / object mutation
    → Resource / UI / Wiki
```

尚未閉合時保持：

```text
field_N
unknown_N
selector_value
raw_N
[OPEN]
```

只有 `C + Resource + caller/data-flow` 等證據真正形成閉環後，才提升 semantic 名稱。不要因 Server coding 方便而先把未知欄位填 `0`、硬編碼或 guessed enum。

## 13. 198 專屬 OPEN 項目

```text
1. first_scalar 正式語意
2. ProfileBlock 各 scalar 正式語意
3. Family D 的 r[12]
4. Family A 每個欄位的公開語意
5. 9 個 Item-slot index 的公開角色
6. 7 個 Skill-slot index 的公開角色
7. standalone_0 / standalone_1 語意
8. 尾端 u8 list 的用途
9. MyInfo / Avatar hydration 的完整 consumer mapping
10. Server 端 198 sender 的 state source
```

後續若新增證據，優先更新本文件的 198-specific 部分；共用 Family A/B/C/D 的 wire 定義只更新 `ClientData_Shared_Decoder_Field_Evidence.md`，不要再複製一份。