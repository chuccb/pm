# PaperMan 2016 JP — Channel / Lobby / Account Protocol 193–221 Field Evidence

> 研究日期：2026-09-17  
> Target：日本版 PaperMan 2016 結束營運時最終 Client  
> Primary evidence：IDA `PaperMan.exe.c` exact dispatcher + exact parser/serializer width + caller/data-flow  
> Resource evidence：`Extracted/ClientDataList.xml` confirms the extracted client data domains include `ui`, `data.pat`, `convars.pat`, `datarevision.txt` and related client data. fileciteturn285file0L2-L4  
> Rule：packet registration names are context, never a substitute for parser/serializer evidence. Suspicious/unnamed fields stay raw.

## 1. Highest-confidence dispatcher map

The final TCP receive dispatcher `sub_58B010()` directly routes this range as follows:

```text
194 → sub_56FE90
198 → sub_570550
200 → sub_570AB0
201 → sub_95A3B0
202 → sub_95AE40
203 → sub_571D50
205 → sub_571910
207 → sub_571B60
209 → sub_572B80
211 → sub_572D80
213 → sub_572E70
215 → sub_572F80
219 → sub_573230
221 → sub_5735F0
```

The dispatcher is stronger evidence than a registration-table ordering. The same C export also contains registration strings for `GC_CHANNEL_*`, `GL_MYITEM_*`, `GS_BUYITEM_*`, `GS_SELLITEM_*`, `GM_*`, `GI_*`, `GP_*`, `GL_LOBBYIN_*`, etc., but those names must be paired with an opcode only where the direct protocol path closes it.

## 2. 194 — five-byte channel-state/result body

Receiver: `sub_56FE90()`.

Exact parser:

```c
for (i = 0; i < 5; ++i) {
    sub_592940(a1, &v3);
    byte_BEFF76[i] = v3;
}
```

Therefore:

```text
194
+0x00 u8
+0x01 u8
+0x02 u8
+0x03 u8
+0x04 u8
body = exactly 5 bytes consumed by this handler
```

All five values are copied byte-for-byte into `byte_BEFF76[0..4]`.

The handler then drives a state transition through `dword_E9FDE0` and its virtual methods when present. This is evidence that the five bytes feed a connection/channel state machine, but it is not enough to name the five bytes as player counts, channel id, server id, etc.

**Confidence:** A for width and destination; semantic names OPEN.

## 3. 196 — channel-entry response has explicit state code + conditional endpoint

Receiver: `sub_570100()`.

First byte:

```c
sub_592940(a1, &n3);
```

So:

```text
196 +0x00 u8 state/result code
```

### 3.1 state == 1

The handler then reads exactly:

```text
+0x01 u8      v28
+0x02 string  cp
+...  u16     hostshort
+...  u8      unk_1D0CFE4
```

The string is consumed by `sub_592730()`, then the `u16` by `sub_592A40()` and the following byte by `sub_592940()`.

The decoded endpoint is passed to:

```c
*sub_417D00() = v28;
sub_596E60(&unk_1326908, &cp, hostshort);
```

Thus the path is demonstrably:

```text
196 state=1
    → byte-like mode/status
    → string endpoint/host-like value
    → u16 port-like value
    → one additional byte
    → network/channel bootstrap object
```

`hostshort` is strongly suggestive of a port because it is passed together with the decoded string into a network setup routine, but the final field label remains `port_like_u16` until lower-level `sub_596E60()` is checked at ASM/callsite level.

### 3.2 state == 0, 2, 3 and other nonzero values

These branches do not consume the same endpoint structure. They instead clear lobby/channel UI state and display localized resource strings.

Important consequence:

```text
196 body is variable by first-byte state code.
```

It is therefore incorrect to model 196 as a fixed `status + endpoint` packet for every response.

**Confidence:** A for branch structure and field widths; A/B for endpoint interpretation; exact enum labels OPEN.

## 4. 197 — zero-payload request

Sender: `sub_5704B0()`.

Exact constructor:

```c
Packet::possible_ctor_or_dtor_0(v1, 197);
sub_555090(&dword_1321D00, v1);
```

No body writer occurs.

```text
197
payload = 0 bytes
```

The surrounding state machine performs MyInfo initialization after this request, so the protocol role is clearly an information/bootstrap request, but its server-side data set must be reconstructed from 198.

**Confidence:** A for wire width; semantic packet-role A from registration + callsite.

## 5. 198 — large player/account bootstrap response

Receiver: `sub_570550()`.

This is one of the most structurally important packets in the 193–221 range.

### 5.1 Leading status

```text
+0x00 u8 success/branch value
```

If zero, the handler closes the state and reports a localized error. If nonzero, a large bootstrap record is consumed.

### 5.2 First major scalar and reusable player-data decoders

Immediately after the leading byte:

```text
+0x01 u32
sub_523BF0(...)
sub_524010(...)
sub_524660(...)
sub_527550(...)
sub_527D00(...)
```

These called readers consume further packet material and populate the client-data/player model. They must be treated as nested schema components rather than collapsed into unnamed padding.

### 5.3 Additional fields with direct width evidence

Later the parser reads:

```text
u16  → i_23
u32  → v20
u8   → count i_1
u8 × i_1 (bounded by 20) → v14[]
```

Specifically:

```c
sub_592A00(a1, v15);          // 2 bytes
sub_592A40(a1, &v20);         // 4 bytes
sub_592940(a1, &i_1);         // 1 byte count
for (...) sub_592940(a1, &v16); // 1 byte each
```

The `u8` list is passed to `sub_5A9B30(v14, i_1)`, so it is an actual logical variable-length byte list, not padding.

### 5.4 Avatar/profile/resource hydration

The parser invokes `sub_522CE0`, `sub_525680`, and later `sub_551E80`, and initializes client-data state before synchronizing the UI.

A particularly important object path resolves:

```text
INFORMATION
  └── MYINFO
       └── AVATAR
```

and invokes:

```c
sub_6A9950(..., L"AVATAR", ..., &p_p_p_p_p_n1189);
```

Therefore 198 is materially more than an authentication ACK: it hydrates account/profile/client-data state used by the MyInfo layer.

### 5.5 What is NOT yet closed

Do not currently rename the unknown fields to:

```text
level
PG
CASH
character_id
weapon_id
inventory_count
```

merely because those concepts exist in the game. Each requires a direct destination/resource/UI/data-flow proof.

**Confidence:** A for parser structure and widths; semantic subfield labels remain mixed A/B/C depending on downstream function.

## 6. 199 — zero-payload request

Sender: `sub_570A00()`.

Exact constructor:

```c
Packet::possible_ctor_or_dtor_0(v3, 199);
sub_555090(&dword_1321D00, v3);
```

No serializer follows.

```text
199
payload = 0 bytes
```

Immediately after sending, the client displays a localized loading/information message. This strongly supports a data-fetch/bootstrap request.

The registration table contains `GL_MYITEM_REQ` at the corresponding protocol-family position; however the server meaning should still be validated through 200's actual parser rather than through the name alone.

## 7. 200 — item/account-data response: status + nested item data

Receiver: `sub_570AB0()`.

Leading byte:

```text
+0x00 u8 result/status
```

If nonzero:

```c
sub_524B70(&p_p_p_p_p_n1189, a1, 1);
```

This is important because `sub_524B70` is a real nested decoder, so the packet's body is not simply a status byte.

Afterwards:

```c
sub_41BF20(byte_BF0724);
byte_EE8C05 = 1;
```

Thus reception sets the local item/data subsystem into an initialized state.

**Confidence:** A for `u8 status`; A for nested decoder existence; exact nested item schema is still open and must be recovered from `sub_524B70` and its sibling readers.

## 8. 201 / 202 — item-store collection packets: exact nested record shape

### 201 parser

`sub_95A3B0()` consumes:

```text
u32 count
for count records:
    u32 field0
    u32 field1
    u8  field2
    u32 field3
    u32 field4
```

That is exactly:

```text
body:
+0x00 u32 count
+0x04 repeat count times:
       u32
       u32
       u8
       u32
       u32
```

Each 5-field record is allocated as a 0x14-byte object (20 bytes), confirming the sum:

```text
4 + 4 + 1 + 4 + 4 = 17 bytes
```

The discrepancy is deliberate: the C++ object allocator reserves 20 bytes, while the wire record only reads 17 bytes. Therefore **do not infer 20-byte wire records from `operator new(0x14)`**.

The record is inserted into `sub_95A4A0()` and is keyed/compared by its internal 4-byte members. This is a collection-management path, not a plain scalar ACK.

### 202 parser

`sub_95AE40()` reads:

```text
u32 count
repeat count:
    u32 field0
    u32 field1
    u8  field2
    u32 field3
    u32 field4
```

and then calls:

```c
sub_95A800(this, field1, field0);
```

Notably, the two trailing u32 values are parsed but are not used by `sub_95A800` in this function body. This is a classic case where the wire fields may still matter elsewhere or may be retained for compatibility but cannot yet be given business names.

**High-confidence conclusion:** 201 and 202 are paired collection synchronization packets with repeated 17-byte wire records, not simple `item_id + quantity` messages.

## 9. 203 — nested client-data/configuration update

Receiver: `sub_571D50()` is only:

```c
return sub_524660(&p_p_p_p_p_n1189, a1);
```

Therefore the entire wire schema is delegated to `sub_524660`.

This is a major reconstruction clue: **the packet boundary is known, but its field list is the field list of a shared reusable decoder**.

The next correct step is not to rename the packet by protocol registration name, but to recover `sub_524660`'s exact read sequence and map every destination.

**Confidence:** A for delegation; field schema OPEN until nested decoder extraction.

## 10. 204 — variable-length item/data-change request, not a fixed record

Sender `sub_571100(i, a2, a3)` creates packet 204.

Wire construction:

```text
+0x00 u8 count
for each entry:
    +0x00 u32 key/id
    +0x04 u8  resource/type category
    +0x05 u16 value
    if category in {12,13,17}:
        +0x07 u16 derived/secondary value
```

Before serialization the client validates the value range against category-specific constraints.

Therefore 204 has a genuine variable-size entry format:

```text
u8 count
repeat count:
    u32 id
    u8 category
    u16 value
    [optional u16 when category is 12/13/17]
```

The optional 2-byte field is written by `sub_5929E0(v14, ...)` and is therefore **wire-present only for those categories**.

This is strong evidence of an item/configuration change protocol with resource-category validation. Exact public field names remain open until `sub_533FF0`, `sub_535DE0`, and `sub_5354B0` are fully decoded against Resource data.

## 11. 205 — repeated record synchronization

Receiver `sub_571910()` starts with:

```text
u8 count
repeat count:
    u8 present
    if present:
        u32 id
        u32 field1
        u32 field2
        u32 field3
        u8  field4
        u16 field5
```

The exact reads are:

```text
u8 count
repeat:
    u8 flag
    if flag != 0:
        u32
        u32
        u32
        u32
        u8
        u16
```

Each present record is handed to:

```c
sub_534450(dword_EE3E98, id, field5);
sub_524F70(&p_p_p_p_p_n1189, id, field3, field1, field2, field4, field5);
```

So `id + 5 remaining values` is a real semantic record passed to a reusable player/item-data subsystem.

After the list, the parser consumes five additional u32 pairs/values:

```text
u32 v22
u32 v16
u32 v26
u32 v20
u32 v15
u32 v27
u32 v18
```

and, when the list is non-empty, copies selected values into:

```text
EE8D18
ArgList
EE8D1C
```

Their public labels are not yet proven.

## 12. 206 — four-field change request

Sender `sub_571620()` constructs packet 206 as:

```text
u32 a2
u32 a3
u8  n12
u32 a4
```

Exact serializer order:

```c
sub_592A20(v10, *a2);
sub_592A20(v4, *a3);
sub_592920(v5, n12);
sub_592A20(v6, *a4);
```

Before sending it validates `a4` against the same category/value policy used by packet 204.

This is useful cross-packet evidence: 204 and 206 share the same category validation machinery, so they operate on a common data model. They should not be implemented independently in the reconstructed server.

## 13. 207 / 208 — deletion/removal family, compact request side

### 208 sender

`sub_572AD0(char a1)` creates packet 208:

```text
+0x00 u32 a1
```

Important: the decompiler prototype says `char a1`, but the serializer is `sub_592A20`, i.e. **4 bytes on the wire**. This is precisely the class of Hex-Rays prototype/type error that must not leak into a reconstructed protocol.

### 207 receiver

`sub_571B60()` first consumes:

```text
u8 status/present
```

If nonzero it closes/updates state; otherwise it consumes:

```text
u32
u32
u8
u32
u32
```

allocates a 20-byte internal record, inserts it into the same `sub_95A4A0()` collection used by packet 201, then reads six more u32 values and updates `EE8D18`, `ArgList`, and `EE8D1C`.

This strongly indicates that 207 is another collection/state synchronization event tied to the same client-data subsystem as 201/202, but its exact business operation remains OPEN.

## 14. 209 / 210 — player/account object collection removal path

### 209 receiver

`sub_572B80()` begins:

```text
u8 flag
if flag != 0:
    u32
    u32
    u32
```

It then looks up one of these values in:

```text
dword_EE8FF8[7*i]
```

and shifts a 28-byte internal record array after removal. Finally:

```c
*dword_EE8D18 = v9;
```

So this is definitively a **remove/delete from a client-side collection** operation.

### 210 sender

`sub_572CD0(CHAR *lpString)` constructs packet 210 with:

```text
string
```

No scalar precedes it.

### 210/209 pairing remains partially open

The direct code proves the wire widths and collection mutation, but not the public names of the collection entries. Those need to be tied to the resource IDs and UI that consume `dword_EE8FF4[]` / `EE8FF8[]` / `EE9008[]`.

## 15. 211 / 212 and 213 / 214 — byte/string and structured request pairs

### 211 receiver

`sub_572D80()`:

```text
u8 → sub_41BBB0(byte_BF0724, value)
```

### 212 sender

`sub_572DC0(string)`:

```text
packet 212
body = string
```

### 213 receiver

`sub_572E70()`:

```text
u8 → sub_41BD40(byte_BF0724, value)
```

### 214 sender

`sub_572EB0(a1, a2, a3, a4)`:

```text
u8
u16
u8
u16
```

This gives a valuable asymmetry: the 211/212 and 213/214 protocol pairs do not all have symmetric wire shapes. Request and ACK payloads must therefore be modeled independently.

## 16. 215 / 216 and 217 / 218 — object/data change paths

### 215 receiver

`sub_572F80()`:

```text
u8 → sub_41BEA0(byte_BF0724, value)
```

### 216 sender

A separate constructor found in the C export creates packet 216 with:

```text
u8 a
```

The exact caller context must be followed further before assigning a public field name.

### 217/218

Packet 218 sender `sub_572FC0(a1, a2)` constructs:

```text
+0x00 u8 current/player-like value
+0x01 u8 count
+0x02 variable repeated payloads produced by sub_5244E0(...)
```

`count` is bounded to 20. The packet is only sent when either:

```text
count != 0
```

or a compared state value differs.

This is strong evidence for a **delta list / selective change synchronization packet**, not a fixed snapshot.

## 17. 219 / 220 — aggregate update packet with up to four categories

### 219 receiver

`sub_573230()` reads:

```text
u8 value
```

and passes it into `sub_4BCF00(n255_, ..., value)`.

The decompiler marks the secondary arguments as undefined, so do not invent them. The only closed wire field is the leading u8.

### 220 sender

`sub_573340(a1)` constructs packet 220 only when at least one of four categories passes `sub_525680()`.

Wire begins with:

```text
u8 count
```

Then for every selected category, it calls:

```c
sub_9591F0(byte_2313148, v8, &v4, 1);
sub_524A50(&p_p_p_p_p_n1189, category, v10);
```

The packet therefore contains a variable-length list of category-specific nested records. The exact bytes emitted by `sub_524A50` are not repeated inline and must be recovered from that function.

A second caller also constructs packet 220 with:

```text
u8 count = 4
repeat 4:
    sub_524A50(...)
```

which confirms packet 220 is a **category list / aggregate synchronization request**, with the nested record schema delegated to a shared serializer.

## 18. Critical decompiler/type findings from this range

The 193–221 area contains several places where naïvely translating the Hex-Rays C would produce a wrong protocol:

1. `sub_572AD0(char a1)` writes `u32`, not `u8`.
2. `operator new(0x14)` in packet 201/207 allocates 20 bytes, but the wire record itself is only 17 bytes.
3. Several ACK parsers consume `u8` flags followed by variable nested records; they are not fixed-size status packets.
4. Shared functions (`sub_524660`, `sub_524A50`, `sub_5244E0`, `sub_524B70`, etc.) hide additional packet fields; the caller's local variable list is not the whole wire schema.
5. Some decompiled function return values and local types are clearly distorted by compiler/decompiler reconstruction; wire width must always be taken from `sub_592900/920/940/9A00/A20/A40/AC0/...`.

## 19. Current protocol-family model

```text
Channel / entry
  194  ← 5-byte channel-state/result body
  196  ← state-coded endpoint/channel response

MyInfo / account bootstrap
  197  → empty request
  198  ← large profile/client-data bootstrap

Item / client-data bootstrap
  199  → empty request
  200  ← status + nested item-data decoder

Collection / item-store state
  201  ← count + repeated 17-byte logical records
  202  ← same repeated record shape
  203  ← shared client-data decoder
  204  → count + variable entries (u32,u8,u16,[u16])
  205  ← repeated flagged records + trailing u32 state
  206  → u32,u32,u8,u32
  207  ← status + shared collection record + trailing state
  208  → u32
  209  ← collection deletion
  210  → string
  211  ← u8
  212  → string
  213  ← u8
  214  → u8,u16,u8,u16
  215  ← u8
  216  → u8 (direct constructor found)
  218  → u8 count + nested delta list
  219  ← u8
  220  → u8 count + nested category records
  221  ← u8 count + nested ClientData records
```

The important result is architectural: this range is not one homogeneous "lobby protocol". It contains channel connection state, profile bootstrap, item/client-data collections, category-based delta updates, and reusable ClientData serializers. Server reconstruction should mirror those shared data models rather than implementing each opcode as an isolated switch case.

## 20. Next closure targets

Highest value follow-up functions are:

```text
sub_524660      → closes 203 / part of 198/related bootstrap
sub_524B70      → closes nested body of 200
sub_524A50      → closes nested body of 220
sub_5244E0      → closes variable body of 218
sub_524F70      → closes record semantics in 205/207
sub_595E80/...  → correlate resulting state with transport/game session
sub_596E60      → close 196 endpoint field meaning
sub_533FF0      → category/resource mapping used by 204/206
sub_535DE0      → category modifier semantics
sub_5354B0      → derived value in 204
```

Only after these are decoded should the remaining `field0`, `value`, `category`, `status`, or `state` placeholders be promoted into public protocol names.
