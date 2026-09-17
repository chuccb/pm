# PaperMan 2016 JP — ClientData／MyInfo／共用 Wire Protocol 整合研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 `198` MyInfo bootstrap 與 `200/203/218/220/221` 共用 ClientData wire family、decoder／serializer、resource validation 與 packet 邊界。
>
> 核心原則：**共用的是 ClientData runtime state，不是所有 packet 都共用同一個 wire record。**

## 1. 一眼看懂

```text
198 GL_MYINFO_ACK
    = 多個 ClientData component 的 composite bootstrap

200 GL_MYITEM_ACK
    = collection / item record family

203 / 220 / 221
    = Family-A weapon/config-like record

218
    = Family-B delta record

198 中的 appearance component
    = Family-D record

Family A/B/C/D
    ≠ 同一個 wire struct
```

閱讀順序固定：

```text
先看本文件 → 確認 packet 組合／wire family
    ↓
再看 Character_Inventory_Equipment.md → 確認 runtime/domain 語意
    ↓
需要 Resource → Resource_Pack_Model.md / Extracted/
```

## 2. Common helper width baseline

實際 helper body 已確認：

```text
sub_592900  read 1 byte
sub_592920  write 1 byte
sub_592940  read 1 byte
sub_5929E0  write 2 bytes
sub_592A00  read 2 bytes
sub_592A20  write 4 bytes
sub_592A40  read 4 bytes
sub_592AA0  write 4 bytes
sub_592AC0  read 4 bytes
sub_592AE0  write 8 bytes
sub_592B00  read 8 bytes
sub_592B20  write 4 bytes
sub_592B40  read 4 bytes
```

因此：

```text
Hex-Rays local type ≠ wire width
```

所有 schema 均以實際 helper implementation 為準。[C]

## 3. 四個明確 ClientData wire family

| Family | 主要函式／packet | wire 結構 | 主要用途 |
|---|---|---|---|
| A | `sub_524660` / `524880` / `524A50`; `203/220/221` | `u8 type + u16 primary + optional 3×u16 + optional 8×u32` | weapon/config-like slot data |
| B | `sub_5244E0`; `218` | `u8 index + 12×u16` | selective/delta synchronization |
| C | `sub_524B70`; `200` | `u32 cursor + repeated (5×u32 + u8 + u16)` | collection/item records |
| D | `sub_524010` / `5241C0`; `198` | `u8 count + repeated (u8 + 12×u16)` | bootstrap composite appearance data |

Server 必須為四族建立不同 codec；不能用單一 `ClientDataRecord` 壓平。[C]

## 4. Family A — `sub_524660` / `sub_524880` / `sub_524A50`

### 4.1 Record wire grammar

```text
u8  type
u16 primary
if type != 3:
    u16 field1
    u16 field2
    u16 field3
if primary != 0:
    u32 value0
    u32 value1
    u32 value2
    u32 value3
    u32 value4
    u32 value5
    u32 value6
    u32 value7
```

Record sizes：

```text
type == 3, primary == 0  →  3 bytes
type == 3, primary != 0 → 35 bytes
type != 3, primary == 0  →  9 bytes
type != 3, primary != 0 → 41 bytes
```

最多 4 records。[C]

### 4.2 Resource／slot validation

`sub_527DB0()` 將 record 中的四個 u16 candidate 分別交給不同 resource domain／range validation：

```text
record[1] → `stru_B8A19C.action` domain
record[2] → 12200000 + index (`papereff`)
record[3] → 12300000 + index
record[4] → `byte_BD3580` domain
```

非零值經 `sub_535020(...)` 驗證；失敗由 `sub_528960()` 回報：

```text
error 8 → E_CRI_ERR_INVALID_WEAPON_SLOT
```

另外還直接存在：

```text
error 7 → INVALID_AVATA_SLOT
error 9 → INVALID_SKILL_SLOT
error 10 → INVALID_ITEM_SLOT
error 11 → INVALID_VOICE_SLOT
```

但不能因此把 Family-A 四個欄位直接命名成 Avatar/Weapon/Skill/Item；它們目前只是跨 resource-domain slot validation。[C]

### 4.3 Packet usage

```text
203 → Family-A
220 → repeated Family-A
221 → repeated Family-A
```

其中 `220/221` top-level 為：

```text
u8 count
repeat:
    Family-A record
```

## 5. Family B — packet 218

`sub_5244E0(this, index, packet)`：

```text
u8  index
u16 field0
u16 field1
u16 field2
u16 field3
u16 field4
u16 field5
u16 field6
u16 field7
u16 field8
u16 field9
u16 field10
u16 field11
```

即：

```text
u8 + 12×u16 = 25 bytes
```

### 5.1 Top-level 218

`sub_572FC0()`：

```text
u8 current_or_aggregate_state = *(a2 + 88)
u8 changed_count   // <=20
repeat changed_count:
    Family-B record
```

只有 `changed_count != 0` 或 aggregate/current state 改變時才送 218；無變化時走本地更新 path。[C]

因此 218 是：

```text
selective / delta synchronization
```

不是 Family-A，也沒有 optional `8×u32`。[C]

### 5.2 重要修正

不要把 218 寫成：

```text
u8 + optional 3×u16 + optional 8×u32
```

這是錯誤模型；正確就是：

```text
u8 index + 12×u16
```

## 6. Family C — packet 200 collection records

`sub_524B70()`：

```text
u32 base/start index
```

之後最多處理 100 logical entries，或達到 ClientData 5120 total bound。

每筆：

```text
u32 field0
u32 resource_id
u32 field2
u32 field3
u32 field4
u8  extra_flag
u16 extra_value
```

單筆：

```text
5×u32 + u8 + u16 = 23 bytes
```

### 6.1 Resource identity evidence

第二個 u32 立即進：

```text
sub_535020(dword_EE3E98, resource_id)
```

找不到 Resource 時走：

```text
sub_528960(..., error 6, ..., resource_id, ...)
```

error 6 literal：

```text
E_CRI_ERR_INVALID_ITEM Error
```

因此它至少是 resource/item identifier candidate with direct validation；具體 public domain 仍應由 caller/resource table 決定。[C]

### 6.2 Cursor behaviour

`base/start index` 會影響 `this + 209` 的 collection cursor；entry range 最多連續處理 100 個 index。遇到 invalid resource/id 可發送 protocol 799 diagnostic 並停止 decode。[C]

因此 200 的最小正確模型是：

```text
status
→ collection cursor
→ bounded records
→ optional per-record metadata
```

## 7. Family D — `sub_524010` / `sub_5241C0`

```text
u8 record_count    // <=20
repeat:
    u8 field0
    12 × u16 fields
```

單筆：

```text
1 + 12×2 = 25 bytes
```

`sub_5241C0()` 為對應 serializer；`sub_5280F0()` 在 decode 後進行 validation/整理。[C]

它是 `198` composite bootstrap 中的 appearance-related component，但 `field0..11` 的 public semantics 仍須用 Resource/UI data-flow 逐項閉合。[C][RES][OPEN]

## 8. Family skill/resource validation block

`sub_527D00()`：

```text
u8 validation mode/type n5
then 28-byte block
```

`sub_527AF0()` 實際一次讀：

```text
7 × u32 = 28 bytes
```

非零欄位需通過 resource range 與 `sub_535020(...)` 驗證；失敗：

```text
error 9 → E_CRI_ERR_INVALID_SKILL_SLOT
```

這可確認其為 skill-slot/resource validation record，但尚不足以將 7 欄 public 命名為具體 skill slot 0..6。[C]

## 9. `198 GL_MYINFO_ACK`：Composite bootstrap

`197 GL_MYINFO_REQ`：

```text
payload = 0 bytes
```

`198` 是複合式 ClientData bootstrap／update，不是扁平 struct。[C]

### 9.1 Top-level order

`sub_570550()` 成功分支：

```text
u8 status
if status != 0:
    u32 first_scalar
    sub_523BF0()       // Profile/Base component
    sub_524010()       // Family D appearance component
    sub_524660()       // Family A loadout/config component
    sub_527550()       // item-slot validation component
    sub_527D00()       // skill-slot validation component
    u16 standalone_0
    u32 standalone_1
    u8 list_count
    repeat:
        u8 list_value
```

wire 順序不可依 C++ object offset、UI 顯示順序或推測的 business order 重排。[C]

### 9.2 `first_scalar`

`first_scalar` 會流入 ClientData/state hydration，但目前沒有唯一 consumer 可安全命名成 level、characterId、currency 等。[C][OPEN]

### 9.3 Profile/Base component：`sub_523BF0`

目前已確認：

```text
NUL-terminated string data
多組 u32 / u8
raw 48-byte block
```

對應 serializer：

```text
sub_523E10
```

因此不是 receive-only accident data；各 scalar public semantic 尚未全部閉合。[C][OPEN]

### 9.4 Item-slot / Skill-slot components

```text
sub_527550
    → 9 × u32
    → INVALID_ITEM_SLOT / error 10

sub_527D00
    → validation context + 7 × u32
    → INVALID_SKILL_SLOT / error 9
```

這兩個資料域要保持分離，不能合成 `ClientDataSlots[]`。[C]

### 9.5 198 standalone tail

最後還有：

```text
u16 standalone_0
u32 standalone_1
u8 list_count
repeat list_count:
    u8 list_value
```

byte list 會送進：

```text
sub_5A9B30(...)
```

因此是真正 variable data，不是 padding；三者 semantics 目前 `[OPEN]`。[C]

## 10. `198` → MyInfo / Avatar hydration

198 接收後會進入：

```text
INFORMATION
  └─ MYINFO
       └─ AVATAR
```

可見後續流程包括：

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

但 `MYINFO`／`AVATAR` 路徑不能單獨拿來反推每一個 wire field 名稱。[C][RES][OPEN]

## 11. `200/203/218/220/221` 與 198 的關係

```text
198 → composite bootstrap
200 → Family C collection
203 → Family A
218 → Family B delta
220 → Family A repeated
221 → Family A repeated
```

它們可以共同修改 `CClientData` runtime state，但 wire grammar 不同。[C]

## 12. Protocol 對 Server 的最低要求

Server codec 應直接依 packet/family 寫明確 DTO：

```text
FamilyARecord
FamilyBRecord
FamilyCRecord
FamilyDRecord
ProfileBlock
SkillValidationBlock
```

`198` writer 必須保持：

```text
status
→ firstScalar
→ ProfileBlock
→ FamilyD records
→ FamilyA records
→ ItemSlotValidation
→ SkillSlotValidation
→ standalone fields
→ variable byte list
```

未知欄位保持：

```text
unknown_*
raw_*
selector_value
```

不要填 `0` 來偽裝已閉合。

## 13. 與角色／背包／裝備主文件的邊界

```text
本文件
    = ClientData wire protocol / parser / serializer / validation

Character_Inventory_Equipment.md
    = Character / Appearance / Inventory / Weapon Loadout runtime model

Resource_Pack_Model.md
    = Resource pack / loader / runtime boundary
```

尤其：

```text
wire record
    ≠
CClientData memory layout
    ≠
Server domain model
```

## 14. 目前 OPEN 與下一步

```text
198 first_scalar
198 ProfileBlock 全部 public semantics
198 standalone_0 / standalone_1 / list_value[]
Family A type / primary / 3×u16 / 8×u32 public semantics
Family B 12×u16 semantics
Family C field0/2/3/4 + extra fields semantics
Family D 12×u16 semantics
7×u32 skill validation exact slot mapping
203/220/221 top-level count/context specifics
200 invalid-resource / diagnostic path completeness
```

最高價值證據鏈：

```text
wire field
→ caller/callee
→ state destination
→ Resource ID
→ Extracted record/UI label
→ Wiki behavior
```
