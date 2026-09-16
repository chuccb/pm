# PaperMan 2016 JP — `GL_MYINFO_ACK (198)` Composite ClientData Codec Evidence

> 研究日期：2026-09-17  
> Target：日本版 PaperMan 2016 final Client  
> Evidence：IDA `PaperMan.exe.c` direct receiver `sub_570550`, reusable decoder/serializer bodies, downstream `CClientData` state and Resource validation.  
> Status：wire widths are A where directly read/written; public business names remain OPEN unless downstream evidence closes them.

## 1. 198 is a composite codec chain, not one opaque snapshot

`sub_570550()` first reads:

```text
+0x00 u8 status
```

On nonzero status it then consumes, in this exact order:

```text
u32                         // leading account/profile scalar
sub_523BF0(CClientData, ...) // fixed profile/state block
sub_524010(...)              // <=20 × 25-byte records
sub_524660(...)              // <=4 × Family-A ClientData records
sub_527550(...)              // 9 × u32 validation/resource record
sub_527D00(...)              // u8 mode + 7 × u32 skill/resource validation record
u16                         // standalone state/value
u32                         // standalone state/value
u8 count
count × u8                  // max 20 locally copied bytes
```

It then selects/copies ClientData state through `sub_525680()` / `sub_522CE0()` and performs additional MyInfo/Avatar hydration.

This chain is the correct reconstruction boundary: a server implementation should model 198 as several independently testable codecs composed in this order.

---

## 2. First scalar in 198

Direct receiver evidence:

```c
sub_592900(a1, &status);
if (status != 0) {
    sub_592A40(a1, &v19);
    ...
}
```

Therefore:

```text
198 +0x00 = u8 status
198 +0x01 = u32 first_scalar
```

`first_scalar` is passed into local state `v24/v8` and then into:

```c
sub_5392A0(byte_EE8968, v1, first_scalar);
```

It is therefore not padding. Its exact public label is still OPEN.

---

## 3. Composite component `sub_523BF0`

`sub_523BF0()` consumes this exact sequence:

```text
string
u8
u32 × 4
u32 × 5
u32 × 4
u32 × 4
u32 × 5
u8
u8
u8
u32 × 1
u32 × 2
u8 × 48-byte binary block
u8
```

More precisely from the C destinations:

```text
1  string              → this + 15
2  u8                  → this + 22
3  u32                 → this + 23
4  u32                 → this + 24
5  u32                 → this + 25
6  u32                 → this + 26
7  u32                 → this + 34
8  u32                 → this + 35
9  u32                 → this + 36
10 u32                 → this + 37
11 u32                 → this + 38
12 u32                 → this + 39
13 u32                 → this + 40
14 u32                 → this + 41
15 u32                 → this + 42
16 u32                 → this + 43
17 u32                 → this + 45
18 u32                 → this + 46
19 u32                 → this + 44
20 u32                 → this + 47
21 u32                 → this + 48
22 u32                 → this + 49
23 u32                 → this + 50
24 u32                 → this + 51
25 u8                  → this + 76
26 u8                  → this + 305
27 u8                  → this + 306
28 u32                 → this + 26 (re-read/derived overwrite by code)
29 u32                 → this + 28
30 u32                 → this + 29
31 0x30-byte block     → this + 52
32 u8                  → this + 1
```

The non-monotonic offsets are a property of the C++ object layout, not wire reordering beyond what the helper calls show. For protocol implementation, preserve the read order above, not the destination offset order.

### 3.1 0x30-byte block

`sub_592500(a2, this + 52, 0x30)` copies exactly 48 bytes.

Because the reader is byte-copy based, the wire component must remain:

```text
raw[48]
```

until its consumer is decoded. Do not reinterpret it as 12 u32 or a string without evidence.

### 3.2 String

The first component is read with `sub_592730`, so it is the protocol's existing string encoding used elsewhere in the client. Its exact maximum encoded size/termination rules come from `sub_592730`, not `strlen` assumptions.

---

## 4. `sub_523E10` confirms the same profile object has a serializer

The corresponding serializer writes:

```text
string (this + 60)
u8    (this + 88)
u32 × 4   (92,96,108 plus related state)
u32 × 5   (136,140,144,148,152)
u32 × 4   (156,160,164,168)
u32 × 4   (172,180,184,176)
u32 × 5   (188,192,196,200,204)
u8 × 3   (304,305,306)
u32 × 3   (104,112,116)
raw[48]   (208)
```

This is valuable evidence that the profile object has a stable wire representation rather than being an accidental receive-only structure. The exact field correspondence between receive object offsets and serializer object offsets requires the object's copy/normalization methods; therefore do not align fields only by ordinal position.

---

## 5. `sub_524010` component

Already closed independently:

```text
u8 record_count  (clamped to 20)
repeat record_count:
    u8
    12 × u16
```

Record wire size:

```text
1 + 12×2 = 25 bytes
```

`sub_5241C0()` is the direct serializer counterpart and writes the same 25-byte record family.

The record is subsequently processed by `sub_5280F0()`, so its fields have client semantics and should not be treated as padding.

---

## 6. `sub_524660` component inside 198

This is Family A from `ClientData_Shared_Decoder_Field_Evidence.md`:

```text
u8 count ≤ 4
repeat:
    u8 type
    u16 primary
    if type != 3:
        3 × u16
    if primary != 0:
        8 × u32
```

Maximum record count is 4.

After decode each record passes through `sub_527DB0`, which validates four resource-domain fields and can emit invalid weapon-slot diagnostics. Therefore this section is active configuration/loadout data, not arbitrary binary.

---

## 7. `sub_527550` component

`sub_527550()` delegates to:

```c
sub_522480(this + 36095, packet, &badIndex, &badIndex2, &badResource)
```

and `sub_522480()` reads exactly:

```text
9 × u32
```

then validates each nonzero value against the Client Resource database. If validation fails, `sub_528960(..., error 10, ...)` is used.

However, the literal for error 10 is:

```text
E_CRI_ERR_INVALID_ITEM_SLOT
```

Therefore 198 contains a distinct **9-u32 item-slot/resource validation component**.

Do not merge it with the 7-u32 skill-slot component below.

---

## 8. `sub_527D00` component

`sub_527D00()` first reads:

```text
u8 n5
```

then `sub_527AF0()` reads exactly:

```text
7 × u32
```

The values are validated as resources. On failure:

```text
error 9 → E_CRI_ERR_INVALID_SKILL_SLOT
```

Thus 198 has a separate **7-u32 skill/resource slot component**.

The byte `n5` selects/identifies the validation context; exact enum meaning requires caller/resource mapping and stays OPEN.

---

## 9. Standalone values and bounded byte list

After the composite ClientData decoders, `sub_570550()` reads:

```text
u16 v15
u32 v20
u8  count
repeat count (locally only while i < 20):
    u8 value
```

The code copies these byte values into a local 17-element int array and calls:

```c
sub_5A9B30(v14, count);
```

This is a real variable-length byte list. It is not a fixed 20-byte field: the count is transmitted separately.

The parser's local memory is 17 integers, but only the first `min(count,20)` wire bytes are consumed by the loop. Therefore for protocol reconstruction, enforce the client-side decode bound and separately investigate `sub_5A9B30` to determine whether values beyond 17 are accepted elsewhere.

---

## 10. Downstream MyInfo / Avatar evidence

After these decoders the client calls:

```text
sub_525680(... four ClientData slots ...)
sub_522CE0(...)
```

and the broader login path initializes an object under:

```text
INFORMATION
  → MYINFO
      → AVATAR
```

The Client therefore uses 198 to hydrate several classes of account/profile/loadout state before normal UI operation.

The `Extracted/ClientDataList.xml` evidence confirms that the extracted client data set contains `ui`, `ui_temp`, `data.pat`, `convars.pat`, `datarevision.txt`, and other client-data domains. fileciteturn285file0L2-L4

That resource inventory is supporting evidence for treating the decoded structures as data-driven client state, but it does not by itself assign a public name to an unknown numeric field.

---

## 11. Important protocol corrections / traps

### Trap A — don't collapse all 198 substructures

198 is not one homogeneous object. At minimum it includes:

```text
scalar
profile block
20×25-byte record family
4-slot Family-A record family
9×u32 item-slot validation
7×u32 skill-slot validation
u16 + u32
count + variable u8 list
```

### Trap B — don't infer object size as wire size

Internal C++ arrays/objects use strides such as 26/44/22/28 bytes. Those are not automatically wire record sizes.

### Trap C — don't use Hex-Rays signedness

For example `sub_527D00`'s `n5` and many object fields appear as `char` in the decompiler, but the actual wire reads must follow the explicit one-byte helper. Conversely, `sub_572AD0(char)` demonstrates that a C `char` parameter may still serialize as u32.

### Trap D — validation itself is semantic evidence

The following literals are direct bridges:

```text
error 6 → INVALID_ITEM
error 7 → INVALID_AVATA_SLOT
error 8 → INVALID_WEAPON_SLOT
error 9 → INVALID_SKILL_SLOT
error 10 → INVALID_ITEM_SLOT
error 11 → INVALID_VOICE_SLOT
```

They prove the ClientData/loadout subsystem has distinct slot-validation domains, but only the exact call/data-flow can assign a given packet field to one domain.

---

## 12. Current 198 reconstruction skeleton

```text
198
  u8 status
  if status != 0:
      u32 first_scalar
      ProfileBlock = sub_523BF0(packet)
      ItemRecordList = sub_524010(packet)          // <=20 × 25B
      LoadoutFamilyA = sub_524660(packet)          // <=4 records
      ItemSlotCheck = sub_527550(packet)           // 9×u32
      SkillSlotCheck = sub_527D00(packet)          // u8 + 7×u32
      u16 standalone_0
      u32 standalone_1
      u8 list_count
      repeat min(list_count,20):
          u8 list_value
```

This is now an implementation-grade structural schema while still correctly leaving the public business names of the unknown fields open.

## 13. Next highest-value semantic targets

```text
sub_5280F0  → name the 25-byte repeated record fields
sub_533FF0  → map resource category values to those fields
sub_535020  → map concrete resource domains
sub_5A9B30  → identify the final variable byte list
198 caller   → determine first_scalar meaning
MyInfo UI    → map ProfileBlock u32 fields to visible labels
Extracted resources → map 19.9M / 10M..10.9M namespaces to actual ClientData tables
```
