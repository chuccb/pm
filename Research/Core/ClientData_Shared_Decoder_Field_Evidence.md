# PaperMan 2016 JP — Shared ClientData Decoder / Serializer Field Evidence

> 研究日期：2026-09-17  
> Target：日本版 PaperMan 2016 final Client  
> Purpose：把 198/200/203/218/220/221 等 packet 共用或近似的 ClientData routines 分開，避免因函式名稱／資料結構相似而錯把不同 wire schema 合併。  
> Rule：wire width 一律以 `sub_5929xx` helper 實際讀寫為準；Hex-Rays local type 不作 protocol truth。

## 1. Helper width baseline

已由 helper body 直接確認：

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

因此不能因變數宣告成 `char` / `short` / `int` 就直接推 wire width。

---

## 2. Record family A — `sub_524660` / `sub_524880` / `sub_524A50`

這三個函式確實描述同一類四-slot ClientData record。

### 2.1 `sub_524660(this, packet)` decoder

先讀：

```text
u8 record_count
```

並 clamp 到最多 4。

每個 record：

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

所以單一 record 的 wire size 是：

```text
type == 3, primary == 0:       3 bytes
type == 3, primary != 0:      35 bytes
type != 3, primary == 0:       9 bytes
type != 3, primary != 0:      41 bytes
```

沒有額外的 trailing field；`sub_524660` 讀完上述資料後直接呼叫 `sub_527DB0()` 做 resource/slot validation。

最大 record 數：4。

### 2.2 `sub_524880(this, packet)` decoder

單次解一個 record，格式與 A family 相同：

```text
u8 type
u16 primary
if type != 3:
    3 × u16
if primary != 0:
    8 × u32
```

它把資料寫入 `this + 144204 ...` 對應的 ClientData slot。

### 2.3 `sub_524A50(this, type, packet)` serializer

與上述 decoder 對稱：

```text
u8 type
u16 primary
if type != 3:
    3 × u16
if primary != 0:
    8 × u32
```

因此 packet 220 的 nested record 可以直接閉合，而不是「未知 nested blob」。

### 2.4 `sub_527DB0` 的 semantic bridge

`sub_527DB0()` 把 record 中的四個 `u16` semantic field 視為四個不同 resource domain 驗證：

```text
record[1] → `stru_B8A19C.action` domain
record[2] → 12200000 + index (`papereff`)
record[3] → 12300000 + index (另一個 resource domain)
record[4] → `byte_BD3580` domain
```

每一個非零值都會以 `sub_535020(dword_EE3E98, resource_id)` 驗證是否存在，並且再驗證 index 是否落在其對應 table range。

失敗時 `sub_528960()` 使用：

```text
error 8 → E_CRI_ERR_INVALID_WEAPON_SLOT
```

這證明該 record family 至少參與 **weapon-slot validity** 檢查。

同一 ClientData subsystem 的其他 validation path 還明確存在：

```text
error 7 → E_CRI_ERR_INVALID_AVATA_SLOT
error 8 → E_CRI_ERR_INVALID_WEAPON_SLOT
error 9 → E_CRI_ERR_INVALID_SKILL_SLOT
error 10 → E_CRI_ERR_INVALID_ITEM_SLOT
error 11 → E_CRI_ERR_INVALID_VOICE_SLOT
```

但不能因此把 record[1..4] 直接命名為 Avatar/Weapon/Skill/Item 四欄；目前僅能說它們跨多個 resource-domain/slot validation。

---

## 3. Record family B — `sub_5244E0` / packet 218

**這一族不是 family A。**

`sub_5244E0(this, index, packet)` 由 packet 218 的 `sub_572FC0()` 呼叫。

它寫出的順序是：

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
```

更精確地說：

```text
+0x00 u8 record index
+0x01 u16 first
+0x03 u16 second
+0x05 u16 third
+0x07 u16 fourth
+0x09 u16 fifth
+0x0B u16 sixth
+0x0D u16 seventh
+0x0F u16 eighth
+0x11 u16 ninth
+0x13 u16 tenth
+0x15 u16 eleventh
+0x17 u16 twelfth
```

即 **25-byte nested record**：1 + 12×2。

它沒有 8×u32，也沒有 `if primary != 0` 的 optional block。

### 3.1 Packet 218 top-level schema

`sub_572FC0()`：

```text
+0x00 u8 current/aggregate state = *(a2 + 88)
+0x01 u8 changed_count
+0x02 repeat changed_count:
       25-byte family-B record
```

`changed_count` 最多 20。

只有在：

```text
changed_count != 0
```

或：

```text
*(a2 + 88) != *(a1 + 88)
```

時才送 packet 218。

若兩者都沒有變化，client 不送 218，反而進入：

```c
sub_4BCF00(n255_, a1, 1u);
sub_522440(dword_EE3950);
```

這表示 218 是 **selective/delta synchronization request**，並非固定 snapshot。

### 3.2 Important correction

先前若把 packet 218 nested data 寫成：

```text
u8 + u16 + optional 3×u16 + optional 8×u32
```

是錯的。

正確是：

```text
u8 index + 12×u16
```

這個修正以 `sub_5244E0()` 每一次 serializer call 的實際 helper 為直接證據。[A]

---

## 4. Nested collection family C — `sub_524B70` / packet 200

`sub_570AB0()` 收到 packet 200 時，在成功 branch 呼叫：

```c
sub_524B70(&p_p_p_p_p_n1189, a1, 1);
```

`sub_524B70()` 先讀：

```text
u32 base/start index
```

之後最多讀 100 logical entries，或到 5120 total bound。

每個 entry：

```text
u32 field0
u32 resource_id
u32 field2
u32 field3
u32 field4
u8  extra_flag        // present because packet 200 passes a3 = 1
u16 extra_value
```

即每個 logical entry 的 wire size：

```text
5×u32 + u8 + u16 = 23 bytes
```

### 4.1 Resource proof

第二個 u32 `resource_id` 會立即進：

```c
sub_535020(dword_EE3E98, resource_id)
```

若 resource 不存在，Client 走：

```text
sub_528960(..., error 6, ..., resource_id, ...)
```

而 error 6 的 literal 是：

```text
E_CRI_ERR_INVALID_ITEM Error
```

因此這個欄位至少可確認為 **resource/item identifier candidate with direct validity check**，遠比泛稱 `field1` 有語意。

但其具體 domain（weapon / item / avatar / etc.）仍由 caller/resource table 決定，不能只靠 error 6 在所有情況命名成 `item_id`。

### 4.2 Stateful pagination/index behavior

`u32 base/start index` 會影響 `this + 209` 的 collection cursor；entry range 最多從 `base` 起連續處理 100 個 index。

若 resource/id 無效，會發送 protocol 799 diagnostic packet，並停止該 decode。

因此 packet 200 不是一般「item count + items」的最簡化模型，而是：

```text
status
→ paged collection cursor
→ bounded resource records
→ optional per-record byte/u16 metadata
```

---

## 5. `sub_524010` / `sub_5241C0` — another distinct fixed record family used by bootstrap

這一族同樣不能和 A/B family 合併。

`sub_524010()`：

```text
u8 record_count (max 20)
repeat:
    u8 field0
    12 × u16 fields
```

因此單一 record 是：

```text
1 + 24 = 25 bytes
```

`sub_5241C0()` 是對應 serializer，確認其實際順序亦為：

```text
u8 count
repeat:
    u8 field0
    12×u16
```

它由 bootstrap / ClientData object 路徑使用，因此很可能是 198 等大型登入後資料的一部分；但具體 public semantics 仍需把每一個 12-word field 和 Resource/UI destination 逐項對上。

`sub_5280F0()` 在 decode 後立即對該 25-byte record 做驗證/整理，因此這不是隨意 padding。

---

## 6. `sub_527D00` / `sub_527AF0` — seven-u32 skill/resource-style validation record

`sub_527D00()`：

```text
u8 validation mode/type n5
then `sub_527AF0(..., 0x1C bytes, ...)`
```

`sub_527AF0()` 會用 `sub_592500(a2, this, 0x1C)` 一次讀取 **28 bytes**，即：

```text
7 × u32
```

然後逐個檢查 7 個 u32 resource candidates：

```text
if field != 0:
    require field to be either within permitted resource ranges
    and `sub_535020(...) != 0`
```

失敗會呼叫：

```c
sub_528960(this, 9, field_index, field_index, bad_resource, n5);
```

error 9 literal：

```text
E_CRI_ERR_INVALID_SKILL_SLOT
```

這是一條比「技能欄位猜測」更直接的 Client evidence：

```text
packet/bootstrap validation record
    → 7 × u32 resource IDs
    → invalid → INVALID_SKILL_SLOT diagnostic
```

目前仍不把 7 個欄位命名為具體 skill slot 0..6，因為 `sub_527AF0` 是 validation-only and range-based；需再用 Resource ID mapping/UI slot binding 閉合。

---

## 7. Why these families must stay separate

目前四個明確 family：

```text
A: 524660 / 524880 / 524A50
   u8 + u16 + optional 3×u16 + optional 8×u32

B: 5244E0 / packet 218
   u8 + 12×u16

C: 524B70 / packet 200
   u32 cursor + repeated (5×u32 + u8 + u16)

D: 524010 / 5241C0
   u8 + repeated (u8 + 12×u16)
```

這些資料結構甚至共享部分 `ClientData` object state，但 wire format 完全不同。

因此 reconstructed server 不應建立一個模糊的 `ClientDataRecord` 然後讓 203/218/220/221 共用同一 serialization。應建立至少四種明確 wire DTO/codec。

---

## 8. Protocol impact

已可直接更新以下 packet schema：

```text
200:
    u8 status
    if success:
        u32 base/start
        repeated <=100:
            u32 field0
            u32 resource_id
            u32 field2
            u32 field3
            u32 field4
            u8  extra_flag
            u16 extra_value

203:
    u8 count <=4
    repeat:
        family-A record

218:
    u8 aggregate/current state
    u8 changed_count <=20
    repeat:
        family-B record = u8 index + 12×u16

220:
    u8 count
    repeat:
        family-A record

221:
    u8 count
    repeat:
        family-A record
```

198 還有 family-D bootstrap component，不能只以單一「large profile packet」表示。

---

## 9. Remaining semantic closure targets

Still need to map exact public names for:

```text
Family A:
    type
    primary
    field1/2/3
    8×u32 payload slots

Family B:
    12×u16 meanings
    a2 + 88 aggregate/current state

Family C:
    field0
    field2/3/4
    extra_flag
    extra_value
    collection cursor semantics

Family D:
    12×u16 bootstrap meanings
```

Best evidence paths are:

```text
Resource ID → resource table → UI/XML label → caller → mutation
```

and:

```text
packet serializer caller
→ source object offsets
→ write helper
```

not packet names alone.
