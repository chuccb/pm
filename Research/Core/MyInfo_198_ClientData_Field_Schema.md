# PaperMan 2016 JP Final — `GL_MYINFO_ACK (198)` Deep ClientData Schema

> 研究日期：2026-09-17  
> Target：日本版 2016 Final Client  
> Scope：只記錄已由 `PaperMan.exe.c` 的 parser / nested decoder / consumer 封死的 wire structure 與語意。未封死欄位保留 raw。

## 1. Packet role

`197 GL_MYINFO_REQ` has zero payload.

`198 GL_MYINFO_ACK` is the corresponding large bootstrap/update response. It does not represent one flat struct. The Client invokes reusable `CClientData` decoders:

```text
sub_523BF0
sub_524010
sub_524660
sub_524B70
```

plus additional scalar/list parsing and UI hydration.

Extracted ClientData domains include `ui`, `ui_temp`, `data.pat`, `convars.pat`, `character.dat`, `item.dat`, `map.dat`, `pepachi.dat`, `pmClient.dat`, and `sounds*.dat`, so this bootstrap is resource-backed rather than an isolated account status reply.

## 2. `sub_523BF0` — fixed personal/base-data segment

Exact read order:

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
u32
u32
u32
u32
raw48
u8
```

Important destination fields:

```text
+15  string
+22  u8
+23..27  u32 group
+34..38  u32 group
+39..42  u32 group
+43..46  u32 group
+47..51  u32 group
+76  u8
+305 u8
+306 u8
+25  derived from +24 through sub_403360()
+26  u32
+28  u32
+29  u32
+52..99 raw48
+1   final u8
```

The important implementation rule is that these are independent scalar fields, not one compressed blob. The Client directly copies these values into its persistent profile state and later uses the profile state to generate UI and avatar data.

### 2.1 Provenance limitation

The current Client build does not provide unique public labels for every member of this segment. Therefore names such as `level`, `PG`, `CASH`, `characterId` must not be assigned merely because those concepts exist in the UI.

## 3. `sub_524010` — 20-entry item-slot record array

The parser first reads:

```text
u8 count
```

then clamps the count to 20.

For each entry `i` it consumes exactly:

```text
u8  slot_index_or_type
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

Therefore each record is exactly:

```text
1 + 12*2 = 25 bytes
```

The Client stores it at:

```text
base = this + 157 + 13*i
```

because the in-memory canonical slot record is compressed to 13 bytes by storing the initial u8 plus twelve 16-bit values.

Immediately after reading each record, the Client executes `sub_5280F0()`.

## 4. Semantic closure of the 20-entry slot record

`sub_5280F0()` validates eleven of the twelve u16 resource values against ClientData namespaces.

Let the record be:

```text
r[0] = u8 slot index/type
r[1..12] = 12 × u16
```

The Client proves these namespaces:

```text
r[1]  -> 19,900,000 + (r[1] % 100,000)
r[2]  -> 10,000,000 + (r[2] % 100,000)
r[3]  -> 10,100,000 + (r[3] % 100,000)
r[4]  -> 10,200,000 + (r[4] % 100,000)
r[5]  -> 10,300,000 + (r[5] % 100,000)
r[6]  -> 10,400,000 + (r[6] % 100,000)
r[7]  -> 10,500,000 + (r[7] % 100,000)
r[8]  -> 10,600,000 + (r[8] % 100,000)
r[9]  -> 10,700,000 + (r[9] % 100,000)
r[10] -> 10,800,000 + (r[10] % 100,000)
r[11] -> 10,900,000 + (r[11] % 100,000)
```

Each reconstructed ID is checked with `sub_535020(dword_EE3E98, id)` and the allowed range is independently bounded.

This is direct evidence that the record contains a family of **resource IDs belonging to distinct ClientData namespaces**.

### 4.1 Field 0: record selector

`r[0]` is used as the slot/index selector for the 20-entry array. It is not a resource ID.

### 4.2 Field 1: 19.9M namespace

`r[1]` is a resource index whose canonical ClientData ID is `19,900,000 + index`.

The Client's `sub_525790/sub_525B50` accessors expose it directly. It participates in avatar/profile resource matching.

### 4.3 Fields 2–11: ten separate resource namespaces

Each of these fields is normalized to its own 100,000-wide ID namespace as shown above. The Client has dedicated getters for each field:

```text
r[2]  -> sub_5257E0 / sub_525BA0  + 10,000,000
r[3]  -> sub_525830 / sub_525BF0  + 10,100,000
r[4]  -> sub_525880 / sub_525C40  + 10,200,000
r[5]  -> sub_5258D0 / sub_525C90  + 10,300,000
r[6]  -> sub_525920 / sub_525CE0  + 10,400,000
r[7]  -> sub_525970 / sub_525D30  + 10,500,000
r[8]  -> sub_5259C0 / sub_525D80  + 10,600,000
r[9]  -> sub_525A10 / sub_525DD0  + 10,700,000
r[10] -> sub_525A60 / sub_525E20  + 10,800,000
r[11] -> sub_525AB0 / sub_525E70  + 10,900,000
```

The Client then resolves these values into an `AVATAR` UI resource set. Thus these fields are not generic inventory quantities.

The exact human-readable name of each ten resource namespace (hair/top/bottom/etc.) is not yet uniquely proven by the C export, so the protocol specification should retain the namespace IDs rather than inventing wardrobe labels.

### 4.4 Field 12

`r[12]` (the final u16 at storage offset +169) is serialized and exposed through `sub_525B00/sub_526280`, but is not consumed by `sub_5280F0()`'s eleven namespace validation checks. It is therefore a real wire field but its independent public semantic is still OPEN.

## 5. Reverse confirmation: ClientData avatar getters

The following getters directly expose the slot record as full ClientData IDs:

```text
sub_525F10 -> record field r[1]
sub_525F60 -> r[2] + 10,000,000
sub_525FB0 -> r[3] + 10,100,000
sub_526000 -> r[4] + 10,200,000
sub_526050 -> r[5] + 10,300,000
sub_5260A0 -> r[6] + 10,400,000
sub_5260F0 -> r[7] + 10,500,000
sub_526140 -> r[8] + 10,600,000
sub_526190 -> r[9] + 10,700,000
sub_5261E0 -> r[10] + 10,800,000
sub_526230 -> r[11] + 10,900,000
sub_526280 -> r[12] transformed through its own resource table
```

These are then consumed by `sub_4BFA50()` / `sub_6A9950(..., L"AVATAR", ...)` and related character/avatar UI paths.

## 6. `sub_524660` — up to four independent slot-indexed configuration records

Leading field:

```text
u8 count
```

Count is clamped to 4.

Before reading, all four destination slots are reset.

For each entry `j`:

```text
u8  type
u16 selector
if type != 3:
    u16 value0
    u16 value1
    u16 value2
if selector != 0:
    u32 reference0
    u32 reference1
    u32 reference2
    u32 reference3
    u32 reference4
    u32 reference5
    u32 reference6
    u32 reference7
```

Wire record size is therefore:

```text
if type == 3 and selector == 0 : 3 bytes
if type == 3 and selector != 0 : 35 bytes
if type != 3 and selector == 0 : 9 bytes
if type != 3 and selector != 0 : 41 bytes
```

`sub_527DB0()` immediately validates the resource references and can raise `sub_528960(..., 8, ...)` when an invalid resource/category combination is found.

The record is also copied into other ClientData structures by `sub_523370` where each slot has a 44-byte canonical storage structure.

The four slots are therefore independently addressable and are not one flat variable-length array.

## 7. `sub_527DB0` semantic validation

`sub_527DB0()` confirms four independent resource classes by checking:

```text
field r[1] against the `action` ClientData table
field r[2] against 12,200,000 + index (`papereff` namespace)
field r[3] against 12,300,000 + index
field r[4] against another dedicated ClientData object/table
```

Invalid nonzero values do not silently become zero; the Client records an error category through:

```text
sub_528960(this, 8, category, selector, invalid_value, 0)
```

This proves that the optional four-record structure is resource/category-validated configuration state.

## 8. `sub_524B70` — 5,020/5,120 ClientData collection segment

Leading field:

```text
u32 start_index/base
```

The Client clamps it to the `[0, 5020]` domain and processes at most 100 logical entries, ending before 5120.

For each entry:

```text
u32 entry_value0
u32 entry_value1
u32 entry_value2
u32 entry_value3
u32 entry_value4
[if packet-context flag != 0: u8 entry_flag]
u16 entry_value5
```

So each logical entry is 21 bytes without the optional u8 or 22 bytes when the caller passes the optional flag.

The Client validates `entry_value1` through `sub_535020(dword_EE3E98, ...)`; invalid resource IDs trigger `sub_528960()`.

The same collection is exposed by `sub_5231C0()` as 28-byte canonical records, with:

```text
record +4 = the validated resource/item key
```

and `sub_534450()` updates the ClientData collection's associated state from this key.

Therefore this segment is a genuine indexed ClientData collection, not padding or an arbitrary inventory blob.

## 9. Why 198 must not be implemented as one giant struct

The actual Client model is:

```text
198
 ├─ fixed personal/base-data (`sub_523BF0`)
 ├─ 20 × 25-byte item/avatar slot records (`sub_524010`)
 ├─ ≤4 variable-size slot/config records (`sub_524660`)
 └─ indexed ClientData collection (`sub_524B70`)
```

Each nested parser has its own count, bounds, validation and persistent destination.

A compatible Server implementation should preserve those boundaries.

## 10. Current semantic confidence

### Fully closed

```text
198 leading status field = u8
20-record array count = u8, max 20
20-record item/resource record width = 25 bytes
20-record field widths = u8 + 12×u16
resource namespaces 19.9M and 10.0M–10.9M = directly proven
≤4 slot/config records = u8 count, max 4
conditional width rules of each config record = proven
u32 indexed collection start index = proven
indexed collection max processing window = 100 entries
indexed collection entry width = 21/22 bytes
```

### Still intentionally raw

```text
exact public wardrobe names of the eleven resource namespaces
final semantic of 20-record field r[12]
individual public labels of most scalar members in sub_523BF0
public labels of the five u32 members in sub_524B70 records
server-side business meaning of several resource references
```

No field in these OPEN groups should be filled with invented `level/weapon/avatar/etc.` names without another direct consumer.
