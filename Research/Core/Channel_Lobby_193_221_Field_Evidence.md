# PaperMan 2016 JP — Channel / Lobby 193–221 封包欄位證據

> 研究日期：2026-09-17  
> Target：日本版 PaperMan 2016 服務終了時的最終 Client  
> 本文件責任：保存 `193–221` 封包本身的 dispatcher、top-level wire grammar、欄位寬度與直接資料流。`198` 的 nested ClientData codec 由 [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md) + [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) 維護；本文件不重複其中的 Family A/B/C/D 內部欄位。

## 1. Dispatcher 基線

最終 TCP receive dispatcher `sub_58B010()` 直接路由：

```text
194 → sub_56FE90
196 → sub_570100
198 → sub_570550
200 → sub_570AB0
201 → sub_95A3B0
202 → sub_95AE40
203 → sub_571D50
205 → sub_571910
207 → sub_571B60
209 → sub_572B80
210 → sub_572D30
211 → sub_572D80
212 → sub_572E20
213 → sub_572E70
214 → sub_572F30
215 → sub_572F80
216 → direct byte/state path
218 → sub_572FC0
219 → sub_573230
220 → nested weapon/config serializer family
221 → sub_5735F0
```

研究時以實際 dispatcher + parser/serializer 為準，不以 registration-table 相鄰性推導欄位。

## 2. 194 — channel state/result

Receiver：`sub_56FE90()`。

實際連續讀取五次 `sub_592940`：

```text
194
u8 × 5
```

五個 byte 原樣寫入：

```text
byte_BEFF76[0..4]
```

之後驅動 `dword_E9FDE0` 相關 channel state transition。[C]

目前只能確認：

```text
body = 5 bytes
用途 = channel/state transition input
```

五個 byte 的公開名稱仍 `[OPEN]`。

## 3. 196 — channel-entry response

Receiver：`sub_570100()`。

第一欄：

```text
u8 state/result
```

### state == 1

```text
u8  v28
ASCII-Z string cp
u16 hostshort
u8  trailing
```

string、`u16`、trailing byte 分別由對應 fixed-width/string helper 讀取；`cp + hostshort` 送入 `sub_596E60()` 建立後續網路/channel 物件。[C]

`hostshort` 在資料流上與 endpoint string 綁定，屬 `port_like_u16` 高信度判定，但正式公開名稱仍保守保留。

### 其他 state

state `0/2/3` 等分支不消費相同 endpoint grammar，而是清理 channel/lobby 狀態並進入 localized UI/error path。[C]

因此：

```text
196 = state-discriminated variable payload
```

不能實作成所有狀態共用同一固定 body。

## 4. 197 — `GL_MYINFO_REQ`

Sender：`sub_5704B0()`。

```text
opcode = 197
payload = 0 bytes
```

建包後直接送出，沒有 body writer。[C]

完整成功資料由 198 提供；198 的 composite schema 不在本文件重複。

## 5. 198 — `GL_MYINFO_ACK`

Receiver：`sub_570550()`。

Top-level grammar：

```text
u8 status
if status != 0:
    u32 first_scalar
    ProfileBlock
    AppearanceRecords
    LoadoutRecords
    ItemSlotValidation
    SkillSlotValidation
    u16 standalone_0
    u32 standalone_1
    u8 list_count
    repeat:
        u8 list_value
```

其中：

```text
ProfileBlock          = sub_523BF0
AppearanceRecords     = sub_524010 / Family D
LoadoutRecords        = sub_524660 / Family A
ItemSlotValidation    = sub_527550
SkillSlotValidation   = sub_527D00
```

完整 nested wire schema、Resource namespace、validation error、MyInfo/Avatar hydration 見 [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md) 與 [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)。[C][RES]

本文件只保留 top-level 邊界；不在此複製 198 的共用 decoder 欄位。

## 6. 199 — item/bootstrap request

Sender：`sub_570A00()`。

```text
opcode = 199
payload = 0 bytes
```

送出後 client 顯示 loading/information 類狀態。[C]

Registration context 指向 `GL_MYITEM_REQ`，但 Server 語意仍以 200 的實際 receiver 為準。

## 7. 200 — item collection/bootstrap response

Receiver：`sub_570AB0()`。

```text
+0x00 u8 status/result
```

成功分支直接委派：

```text
sub_524B70(...)
```

`sub_524B70` 是 Shared Decoder 的 **Family C**；完整 collection grammar 不在本文件重複。[C]

成功後還會設定：

```text
sub_41BF20(byte_BF0724)
byte_EE8C05 = 1
```

因此 200 不只是 status ACK，而是 item/client-data subsystem initialization point。[C]

## 8. 201 / 202 — 17-byte logical collection record

兩者均先讀：

```text
u32 count
```

每筆 logical record：

```text
u32 field0
u32 field1
u8  field2
u32 field3
u32 field4
```

故 wire record 明確為：

```text
4 + 4 + 1 + 4 + 4 = 17 bytes
```

但 Client 內部會配置 `0x14`（20）byte object；這不能反推 wire record 為 20 bytes。[C]

### 201

`sub_95A3B0()` 讀取 records 並插入 `sub_95A4A0()` collection。[C]

### 202

`sub_95AE40()` 讀取相同 17-byte logical record，之後呼叫：

```text
sub_95A800(this, field1, field0)
```

尾端兩個 `u32` 在該函式 body 沒有進入這個 call，因此其公開業務語意保持 `[OPEN]`。[C]

結論：201/202 是 collection synchronization family，不應簡化成 `item_id + quantity`。

## 9. 203 — Family-A direct delegation

Receiver：`sub_571D50()`：

```c
return sub_524660(&p_p_p_p_p_n1189, a1);
```

因此：

```text
203
    = Family-A codec
```

Family-A 完整 byte grammar 與四個 resource-domain validation 見 Shared Decoder。[C]

## 10. 204 — variable item/data change request

Sender：`sub_571100()`。

Top-level：

```text
u8 count
repeat:
    u32 key/id
    u8  category
    u16 value
    if category ∈ {12,13,17}:
        u16 secondary_value
```

optional `u16` 確定實際出現在 wire 上，因為 caller 只有在這三種 category 才呼叫對應 writer。[C]

204 與 206 共用 category/value validation machinery，應視為同一資料域的不同 message，而非兩套獨立規則。[C]

## 11. 205 — repeated item/state synchronization + economy tail

Receiver：`sub_571910()`。

前段：

```text
u8 count
repeat:
    u8 present
    if present:
        u32 id
        u32 field1
        u32 field2
        u32 field3
        u8  field4
        u16 field5
```

present record 會進入：

```text
sub_534450(resourceIdentity, id, field5)
sub_524F70(..., id, field3, field1, field2, field4, field5)
```

因此這是真正與 ClientData item/runtime state 相連的 record。[C]

list 後還有七個 `u32` tail values。其中特定位置已由 `Currency_State_Field_Evidence.md` 直接閉合為：

```text
u32 trailing_0
u32 PG
u32 trailing_2
u32 CASH
u32 trailing_4
u32 trailing_5
u32 CP
```

剩餘 tail field 維持中性名稱；完整 PG/CASH/CP 證據見 [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md)。[C]

## 12. 206 — four-field change request

Sender：`sub_571620()`。

```text
u32 a2
u32 a3
u8  category
u32 value
```

依序使用 4-byte / 4-byte / 1-byte / 4-byte writer。[C]

最後 `u32 value` 與 204 使用相同 category/value validation machinery，證明兩個 packet 共享資料模型。[C]

## 13. 207 / 208 — collection removal/update family

### 208

`sub_572AD0(char a1)` 雖然表面參數是 `char`，實際使用 `sub_592A20`，故：

```text
208 +0x00 = u32
```

wire width 是 4 bytes，不能按 Hex-Rays prototype 寫成 u8。[C]

### 207

Receiver：`sub_571B60()`。

狀態欄：

```text
u8 status/present
```

非狀態分支會讀一個與 201/202 相同形狀的 collection record：

```text
u32
u32
u8
u32
u32
```

並進入同一 `sub_95A4A0()` collection subsystem。[C]

record 後另有六個 `u32`，其中 Currency 文件已閉合為：

```text
trailing_0
trailing_1
trailing_2
CASH
PG
CP
```

因此 207 同時承載 collection state 與 economy synchronization。[C]

## 14. 209 — removal/update request

Receiver：`sub_572B80()`。

開頭為：

```text
u8 flag
```

依 flag 及後續條件最多消費三個 `u32` 欄位；其資料用來定位／移除 Client-side collection record，並對 28-byte internal record table 做壓縮／位移。[C]

目前欄位 business name 保持 `[OPEN]`；不要因它作用在 item collection 就直接命名為 `item_id` / `slot`。

## 15. 210–216 — 小型 control/state family

目前以直接 reader width 為真相：

```text
210 → string request
211 → u8
212 → string
213 → u8
214 → u8 + u16 + u8 + u16
215 → u8
216 → u8
```

其中 210/212 是 NUL 結束字串；其餘 scalar 依 fixed-width helper 讀取。[C]

這些 packet 的更高層 public labels 尚未全部閉合，因此只保存 raw grammar，不把變數名當語意。

## 16. 218 — Family-B delta synchronization request

Receiver／sender 路徑：`sub_572FC0()`。

Top-level：

```text
u8 current_or_aggregate_state
u8 changed_count   // <=20
repeat changed_count:
    Family-B record
```

Family-B 單筆固定：

```text
u8 index
12 × u16
= 25 bytes
```

它沒有 Family-A 的 optional `8 × u32` block。`changed_count == 0` 且 aggregate state 未改變時，Client 不建立變更資料封包而走本地更新路徑。[C]

完整 Family-B schema 見 Shared Decoder。

## 17. 219 — compact state/control packet

Receiver：`sub_573230()`。

```text
u8 value
```

目前僅確認 byte width 與直接 state 更新用途；公開欄位語意 `[OPEN]`。[C]

## 18. 220 / 221 — Family-A repeated synchronization

這兩個 packet 使用 Shared Decoder 的 Family-A record：

```text
u8 count
repeat:
    Family-A record
```

Family-A：

```text
u8 type
u16 primary
if type != 3:
    3 × u16
if primary != 0:
    8 × u32
```

Family-A 的 resource-domain validation 與 weapon/config slot bridge 見 [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)。[C]

不要在本文件另寫第二份 Family-A field map。

## 19. 與其他研究文件的責任切分

```text
193–221 top-level packet grammar
    → 本文件

198 composite order / MyInfo / Avatar hydration
    → MyInfo_198_ClientData_Field_Schema.md

524660 / 524880 / 524A50 Family A
5244E0 Family B
524B70 Family C
524010 / 5241C0 Family D
    → ClientData_Shared_Decoder_Field_Evidence.md

Character / Inventory / Equipment runtime model
    → Character_Inventory_Equipment.md

PG / CASH / CP
    → Currency_State_Field_Evidence.md
```

這個邊界是刻意維持的：**共用的是 ClientData state，不是 wire format；top-level packet 與 nested codec 也不是同一層責任。**

## 20. 目前重要 OPEN

```text
194 五個 state byte 的正式名稱
196 status enum 與 endpoint trailing byte
198 first_scalar / standalone fields / byte-list semantics
199 server-side dataset
201/202 各五欄正式業務語意
204 category/value 的完整公開對應
205/207 剩餘 economy tail fields
209 三個 u32 的條件式具體語意
210–216 各 control code 的 public labels
218 Family-B 12×u16 的公開對應
219 public field meaning
220/221 Family-A 各欄位的業務語意
```

除非找到新的 `PaperMan.exe.c`／LST／ASM、`Extracted/` 或日本 Wiki 證據，以上項目保持 `[OPEN]`，不得為 Server 實作方便而改成猜測值。
