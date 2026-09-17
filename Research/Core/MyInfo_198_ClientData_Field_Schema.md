# `GL_MYINFO_ACK (198)` ClientData 完整結構

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 更新基準：2026-09-17。
>
> 本文件整合原本 `MyInfo_198_ClientData_Field_Schema.md` 與 `MyInfo_198_Composite_Codec_Evidence.md`。現在它是 `198` 的唯一主文件：同時保存 wire schema、nested decoder、ClientData/resource 驗證與下游 MyInfo/Avatar evidence。

## 1. 封包角色

```text
197 GL_MYINFO_REQ
    payload = 0 bytes

198 GL_MYINFO_ACK
    = 複合式 ClientData bootstrap / update
```

198 不是一個扁平 struct。Client 會依固定順序串接多個可獨立驗證的 decoder：

```text
status
→ first scalar
→ sub_523BF0
→ sub_524010
→ sub_524660
→ sub_527550
→ sub_527D00
→ u16
→ u32
→ count + variable u8 list
→ ClientData／MyInfo／Avatar hydration
```

因此 Server reconstruction 應把 198 當成 composite codec chain，而不是一次性解析成一個猜測的大類別。

## 2. 最前端 status 與 scalar

`sub_570550()` 先讀取：

```text
+0x00 u8 status
```

只有 status 非零時才進入成功 bootstrap parser。接著讀取：

```text
u32 first_scalar
```

所以目前結構至少是：

```text
198 +0x00 = u8 status
198 +0x01 = u32 first_scalar
```

`first_scalar` 會進入 local ClientData/狀態 setter，因此不是 padding；但其正式公開名稱仍 `[OPEN]`。[C]

## 3. `sub_523BF0`：固定 Profile/Base Data 區塊

實際讀取順序是：

```text
ASCII-Z string
u8
u32 × 4
u32 × 5
u32 × 4
u32 × 4
u32 × 5
u8
u8
u8
u32 × 3
raw[48]
u8
```

主要 C++ object destination 分布並非單純遞增，部分欄位會透過 derived calculation 或 re-read 寫入：

```text
string → this +15
u8     → this +22
多組 u32 → +23..+51 的 profile state
u8     → +76 / +305 / +306
raw[48] → +52
final u8 → +1
```

其中 `sub_592500(..., 0x30)` 明確複製 48 bytes，因此該部分在 wire 上應保持 `raw[48]`，不能未經證據改成 12 個 u32 或字串。[C]

對應 serializer `sub_523E10()` 可寫出相同 profile object 的多組 string/u32/u8/raw block，證明這不是 receive-only 偶然結構。[C]

### 3.1 語意邊界

目前沒有足夠唯一 consumer 將所有 profile scalar 命名為 `level`、`PG`、`CASH`、`characterId` 等。這些概念雖然出現在 UI，但不能只因概念存在就替未知欄位命名。[OPEN]

## 4. `sub_524010`：20 筆複合外觀／資源記錄

開頭：

```text
u8 count
```

Client 將 count 限制在 20。

每筆固定讀取：

```text
u8  record_selector
u16 field[0]
u16 field[1]
u16 field[2]
u16 field[3]
u16 field[4]
u16 field[5]
u16 field[6]
u16 field[7]
u16 field[8]
u16 field[9]
u16 field[10]
u16 field[11]
```

所以每筆 wire record 固定：

```text
1 + 12 × 2 = 25 bytes
```

Client 的 canonical in-memory storage 另有自己的 compact layout；不可把 memory stride 直接當成 wire width。

## 5. 20 筆記錄的 Resource Namespace 語意

`sub_5280F0()` 會驗證其中 11 個 u16 resource values，直接把它們轉換到不同 ClientData namespace：

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

每個 canonical resource identity 再由 `sub_535020()` 等檢查。[C]

因此已直接證明這不是通用數值陣列，而是**多個不同 Resource namespace 組合成的角色／外觀資料結構**。[C][X]

### 5.1 `r[0]`

第一個 u8 是記錄 selector／slot index；不是 resource ID。[C]

### 5.2 `r[1]`

屬於 19.9M namespace，可透過 ClientData getter 取回完整 resource identity。[C]

### 5.3 `r[2]..r[11]`

各自對應不同的 100,000-wide namespace。Client 有獨立 getter，因此不能合併成一個 generic `AvatarParts[]` 而不保留 namespace identity。[C]

### 5.4 `r[12]`

最後一個 u16 會被序列化，也有自己的 getter/resource path，但沒有被前述 11 個 validation rule 消費；正式公開 semantic `[OPEN]`。[C][OPEN]

## 6. Avatar Resource Cross-check

上述 19.9M 與 10M–10.9M namespace 最後會進入 `AVATAR` 相關 UI/resource pipeline，例如：

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

並被 `sub_4BFA50()`／`sub_6A9950(..., L"AVATAR", ...)` 等路徑使用。[C]

`Extracted` 同時存在 avatar、body、hair、face、set、`acc1..acc4` 等資源結構，因此可以證明這個 record family 確實與複合 Avatar/Character state 有關。[RES][X]

但在 wire-field 一一 mapping 尚未完全閉合前，不應把十餘個欄位直接命名成固定 wardrobe 名稱。[OPEN]

## 7. `sub_524660`：最多四筆變長 Loadout/Configuration

開頭：

```text
u8 count
```

count 最大 4；每筆：

```text
u8  type
u16 selector
if type != 3:
    u16 value0
    u16 value1
    u16 value2
if selector != 0:
    8 × u32 reference
```

所以單筆可能是：

```text
type == 3, selector == 0  → 3 bytes
type == 3, selector != 0  → 35 bytes
type != 3, selector == 0  → 9 bytes
type != 3, selector != 0  → 41 bytes
```

這是由實際 parser/writer 結構直接閉合。[C]

後續透過 `sub_527DB0()` 驗證 Resource namespace；錯誤處理也明確區分 weapon/config slot。[C]

## 8. `sub_527550`：9 × u32 Item-slot Resource Validation

`sub_527550()` 委派給 `sub_522480()`，後者固定讀取：

```text
9 × u32
```

每個非零值會對 Client Resource DB 做驗證；失敗走 error 10，而該 error 對應 `E_CRI_ERR_INVALID_ITEM_SLOT`。[C]

因此 198 內存在獨立的「9 × u32 item-slot/resource validation component」。

## 9. `sub_527D00`：Skill-slot Resource Validation

先讀：

```text
u8 context
```

再由 `sub_527AF0()` 讀：

```text
7 × u32
```

失敗對應 error 9：

```text
E_CRI_ERR_INVALID_SKILL_SLOT
```

因此這一段與 9 × u32 Item-slot validation 是兩個不同資料域，不能合併。[C]

## 10. Indexed ClientData item collection

`sub_524B70()` 以前已有獨立研究其結構；它具有：

```text
u32 start_index/base
```

並在有限 window 內讀取多個 entry，每個 entry 包含多個 u32、可選 u8 與 u16。其資料最後進入 28-byte canonical item record 與 Resource runtime state。[C]

這一層與 `sub_524010` 的 20 筆角色／Avatar resource record 必須分開看待：

```text
20 × 25-byte composite appearance record
≠
indexed owned-item collection
```

完整 Item/耐久度研究已集中於 `Character_Inventory_Equipment.md`。[C]

## 11. `sub_570550` 最後的 standalone fields

主要 parser 後續還會讀：

```text
u16 standalone_0
u32 standalone_1
u8  count
repeat count:
    u8 value
```

這是一個真正的 variable-length byte list，而不是固定 20-byte buffer。

Client 會以 local bound 處理並呼叫：

```text
sub_5A9B30(...)
```

正式 semantic 仍需繼續從 caller／consumer 確認。[C][OPEN]

## 12. 完整 Composite Codec 形狀

目前最適合的 structural schema：

```text
198
  u8 status
  if status != 0:
      u32 first_scalar
      ProfileBlock          = sub_523BF0(packet)
      AppearanceRecords     = sub_524010(packet)   // <=20 × 25B
      LoadoutConfigRecords  = sub_524660(packet)   // <=4, variable-size
      ItemSlotValidation    = sub_527550(packet)   // 9 × u32
      SkillSlotValidation   = sub_527D00(packet)   // u8 + 7 × u32
      u16 standalone_0
      u32 standalone_1
      u8 list_count
      repeat min(list_count,20):
          u8 list_value
```

這比把 198 寫成單一巨大 C# class 更符合 Client 實際 parser 邊界。[C]

## 13. 重要反編譯與重建規則

### Wire order 不等於 Object offset order

C++ object 的欄位 offset 可能非單調排列；Server 必須遵循實際 serializer／parser 呼叫順序，不可依 object offset 重新排序。

### Memory stride 不等於 Wire record size

例如 20 筆外觀記錄明確是 25-byte wire records，但 Client in-memory layout 可以是不同 compact representation。

### Helper prototype 不等於實際寫入寬度

任何 `char`、`short` 類表面 prototype 都必須追到底層 serializer helper。例如其它 Client helper 已出現「表面是 char，底層實際寫 4 bytes」的情形；198 也必須遵循同一原則。

### Resource validation 是重要 semantic evidence

錯誤碼與 namespace 驗證可以證明資料域，例如：

```text
error 8  → weapon slot
error 9  → skill slot
error 10 → item slot
```

但仍應以實際 caller/data-flow 決定單一欄位的正式名稱。

## 14. 目前最重要的 OPEN 項目

```text
1. ProfileBlock 各 scalar 的正式公開語意
2. 20 筆 record 的各 resource namespace 對應到哪個公開 Avatar 元件
3. r[12] 的獨立公開語意
4. <=4 LoadoutConfigRecords 每個 u16/u32 的正式語意
5. 9 × u32 Item-slot validation 各 index 的公開角色
6. 7 × u32 Skill-slot validation 各 index 的公開角色
7. standalone u16/u32 的語意
8. variable u8 list 的實際用途
9. 198 與後續 MyInfo/Avatar UI 的完整 consumer mapping
10. Server 端實際 198 sender 的 state source
```

沒有新的 C/LST/Resource/Wiki 證據前，上述欄位維持 raw／`[OPEN]`，不可為方便 Server 實作而自行填入猜測值。
