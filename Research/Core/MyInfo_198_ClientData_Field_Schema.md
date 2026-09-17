# `GL_MYINFO_ACK (198)` ClientData 複合協定

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是 `198` 的唯一主文件。它只負責 **198 的封包邊界、組合順序、198 特有 state／hydration 與未閉合欄位**；共用 ClientData record 的完整 wire schema 統一由 [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) 維護。

## 1. 封包角色

```text
197 GL_MYINFO_REQ
    payload = 0 bytes

198 GL_MYINFO_ACK
    = 複合式 ClientData bootstrap / update
```

198 不是一個扁平 struct。成功路徑會依固定呼叫順序串接多個可獨立驗證的 decoder，因此 Server 不應把它寫成一個依 C++ object offset 拼出的巨大 record。

## 2. 198 的組合順序

`sub_570550()` 成功分支目前可安全整理成：

```text
u8 status
u32 first_scalar
sub_523BF0()
sub_524010()
sub_524660()
sub_527550()
sub_527D00()
u16 standalone_0
u32 standalone_1
u8 list_count
repeat list_count:
    u8 list_value
```

其中 `sub_523BF0`、`sub_524010`、`sub_524660`、`sub_527550`、`sub_527D00` 的共用 wire schema 不在此重複；請直接以 [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) 為唯一真相。[C]

目前已確認的四個共用 record family 為：

```text
Family A = sub_524660 / sub_524880 / sub_524A50
Family B = sub_5244E0 / packet 218
Family C = sub_524B70 / packet 200
Family D = sub_524010 / sub_5241C0
```

Family A/B/C/D 雖然可共用部分 `CClientData` state，但 wire layout 不同，不能互相替代。[C]

## 3. Leading status 與 `first_scalar`

`sub_570550()` 首先讀取：

```text
+0x00 u8 status
```

只有非零狀態才進入完整 bootstrap parser。其後緊接：

```text
+0x01 u32 first_scalar
```

`first_scalar` 會流入 ClientData／狀態設定流程，因此不是 padding；目前尚無足夠唯一 consumer 將其正式命名為 `level`、`characterId`、貨幣或其他公開欄位。[C][OPEN]

## 4. `sub_523BF0`：Profile / Base Data component

此 component 是 198 composite codec 的第一個大型 nested block。

目前已確認：

- 包含 NUL 結束字串與多組 `u32`／`u8`。[C]
- 內含明確 `raw[48]` copy；wire 上必須保留為 48-byte raw block，不能依表面 scalar 型別改寫。[C]
- 對應 serializer `sub_523E10()`，因此不是 receive-only 偶然資料。[C]
- 其部分資料寫入 ClientData／Profile state，但各 scalar 的公開業務名稱尚未全部閉合。[C][OPEN]

完整欄位順序與寬度見 Shared Decoder 文件，避免在 198 文件建立第二份 schema。

## 5. `sub_524010`：Composite Appearance component

198 將一個最多 20 筆的複合外觀資料組件嵌入 bootstrap。

```text
u8 count <= 20
repeat:
    Family-D record
```

Family-D 單筆 wire record 為：

```text
u8 selector/index
12 × u16 resource/value fields
= 25 bytes
```

其最重要的 198-specific 語意不是「這些欄位的每一個名稱」，而是它會把角色／外觀所需的多個 Resource namespace 一起帶入 ClientData，之後進入 `MYINFO` / `AVATAR` hydration。各 namespace 與 field-by-field resource 驗證已集中於 Shared Decoder；個別 `field[0..11]` 公開名稱仍應保持證據驅動的 raw／`[OPEN]` 狀態。[C][RES][OPEN]

## 6. `sub_524660`：Loadout / configuration component

198 還會串接 Family-A：

```text
u8 count <= 4
repeat:
    Family-A record
```

Family-A 的 conditional wire branches、8 × `u32` 尾端、`sub_527DB0()` resource validation 與 packet 203/220/221 的共用關係，全部以 Shared Decoder 為準。

198 文件只保留一個關鍵架構結論：**這是獨立於 20×25-byte appearance family 的另一個 wire component**。[C]

## 7. Item-slot 與 Skill-slot validation components

198 成功 bootstrap 還包含兩個明確不同的 validation component：

```text
sub_527550()
    -> 9 × u32
    -> INVALID_ITEM_SLOT（error 10）

sub_527D00()
    -> u8 context + 7 × u32
    -> INVALID_SKILL_SLOT（error 9）
```

這裡要保留的是「資料域不同」這個 198 composite invariant；兩者完整 byte layout 與 Resource range validation 規則請以 Shared Decoder 為準。[C]

不要把 9 個 item-slot values、7 個 skill-slot values 或 Family-A 的 4 個 semantic fields 互相合併成一個 generic `ClientDataSlots[]`。[C]

## 8. 198 後段 standalone fields

共用 decoder 結束後，`sub_570550()` 還會讀取：

```text
u16 standalone_0
u32 standalone_1
u8  list_count
repeat:
    u8 list_value
```

其中 byte list 會送入：

```text
sub_5A9B30(...)
```

因此它是真正的變長資料，不是固定 buffer 或 padding。[C]

目前：

```text
standalone_0   = [OPEN]
standalone_1   = [OPEN]
list_value[]   = [OPEN]
```

直到找到唯一 consumer／producer／Resource 對照前，不應自行命名。

## 9. `198` → MyInfo / Avatar hydration

198 的特殊價值在於它是 ClientData bootstrap 的組合入口。接收後會進入 profile、character、item 與 UI hydration 路徑，包含：

```text
INFORMATION
  └─ MYINFO
       └─ AVATAR
```

並可看到 `sub_522CE0`、`sub_525680`、`sub_551E80` 等後續流程，以及 `sub_6A9950(..., L"AVATAR", ...)` 類 resource/UI path。[C][RES]

因此：

```text
198
  != authentication-only ACK
198
  = login 後 ClientData / MyInfo bootstrap carrier
```

但「某一個 wire field 就是某一個公開角色欄位」仍需要單獨 data-flow 證據；不能由 `MYINFO`／`AVATAR` 路徑反推全部欄位名稱。[C][OPEN]

## 10. 與 200–221 的關係

198、200、203、218、220、221 雖然都會觸碰 `CClientData`，但各自使用不同或部分重疊的 decoder：

```text
198 → composite bootstrap
200 → Family-C collection decoder
203 → Family-A decoder
218 → Family-B delta record
220 → Family-A repeated records
221 → Family-A repeated records
```

這也是為什麼不能建立單一 `ClientDataRecord` class 讓所有 packet 共用相同 serializer。共用的是資料域／runtime state，不是 wire format。[C]

## 11. Server reconstruction 規則

`198` Server codec 應保持「組合式」：

```text
ReadU8(status)
if status != 0:
    ReadU32(firstScalar)
    ReadProfileBlock()
    ReadAppearanceRecords()
    ReadLoadoutRecords()
    ReadItemSlotValidation()
    ReadSkillSlotValidation()
    ReadU16(standalone0)
    ReadU32(standalone1)
    ReadU8(listCount)
    ReadBytes(listCount)
```

實際 C# model 可以把這些 component 分成明確 DTO，但 wire writer 必須完全按照上述順序。不可按照 Client memory offset、UI 顯示順序或猜測的業務順序重排。[C]

另外：

```text
wire width
    = actual serializer/reader helper width

NOT
    = Hex-Rays parameter declaration
```

這條規則與 Shared Decoder 的 helper baseline 一致。

## 12. 目前 OPEN 項目

```text
1. first_scalar 的正式公開語意
2. sub_523BF0 各 Profile scalar 的正式公開語意
3. Family-D 12×u16 各字段的公開對應
4. Family-A 各欄位的公開對應
5. 9×u32 Item-slot 各 index 的公開角色
6. 7×u32 Skill-slot 各 index 的公開角色
7. standalone_0 / standalone_1 的語意
8. variable u8 list 的用途
9. 198 Server-side sender 的完整 state source
```

上述未知值維持 `[OPEN]`。只有新的 `PaperMan.exe.c`／LST／ASM、`Extracted/` 或日本 Wiki 證據閉合後，才提升欄位名稱與 Server model 的語意層級。
