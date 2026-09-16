# PaperMan 2016 JP — Drop / Pickup Weapon Protocol

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact parser/serializer trace + dispatcher + Resource/action table + Wiki

## 1. Confirmed packet family

Gameplay TCP dispatcher：

```text
960 → sub_566B30
961 → sub_566BF0
963 → sub_5672E0
```

Client request serializer：

```text
sub_566F50
    → Packet opcode 962
    → sub_555090(send)
```

Current names / direction:

```text
960 Server → Client  GameNetwork::OnGGWeaponPickUpDestroyNotify
961 Server → Client  dropped weapon/world-object update
962 Client → Server  GameNetwork::OnSendGGDropWeaponGetAndDropReq
963 Server → Client  GameNetwork::OnGGDropWeaponGetAndDropAck
```

These form a stateful dropped-object protocol, not a single request/response struct.

---

## 2. Packet 960 — `OnGGWeaponPickUpDestroyNotify`

Parser:

```text
u8 count
repeat up to count:
    u16 dropped_object_id
```

Loop exits early when `dropped_object_id == 0`.

Each nonzero ID is passed to:

```text
sub_95F8F0(dropManager, dropped_object_id, 0)
```

`sub_95F8F0()` is a thin wrapper over `sub_962DF0()`.

The diagnostic string is explicit:

```text
GameNetwork::OnGGWeaponPickUpDestroyNotify
```

### Semantic

High confidence:

```text
count = number of IDs in destruction notification
u16 ID = dropped-world-object instance key
```

Because the ID is consumed by the drop-object manager's destroy/remove routine, do not call it a resource template ID.

---

## 3. Packet 961 — server dropped-object/world-object update

`sub_566BF0()` parser begins:

```text
u8 count
repeat count:
    u16 object_or_weapon_id
    u8  control
    u32 value_0
    u16 value_1
    u16 value_2
    u16 value_3
    u16 value_4
    u16 value_5
    u32 value_2_32
    u32 value_3_32
    0x20-byte raw block
```

The decompiler's local-variable packing is not sufficiently clean to freeze every displayed temporary name as a public field name. What is reliable is the serializer-reader width sequence and the downstream use.

The function constructs a world-object representation, transforms its position, performs Resource lookup, and invokes:

```text
sub_95E7D0(dropManager, 0, src, 0)
```

Resource path:

```text
sub_5F5BE0(resourceTable, id)
sub_5BB9F0(resource)
```

### Semantic boundary

High-confidence:

```text
961 = server→client dropped-world-object appearance/state record
```

Unresolved until `sub_95E7D0` is fully modeled:

```text
first u16: object instance ID vs resource/template ID
control byte
all secondary u16/u32 values
0x20-byte block
coordinate packing/unit
```

---

## 4. Packet 962 — `GameNetwork::OnSendGGDropWeaponGetAndDropReq`

Serializer begins with:

```text
Packet opcode = 962
```

The actual helper widths are direct Client evidence:

```text
sub_592920 → 1 byte
sub_5929E0 → 2 bytes
sub_592B20 → 4 bytes
```

Therefore apparent Hex-Rays `char` argument types must not be used to infer wire width.

### 4.1 Current wire sequence

The current best raw sequence is:

```text
field_00 : 2 bytes = a1
field_02 : 2 bytes = a2 / action-table-related value
field_04 : 1 byte  = v21 = *a5
field_05 : 2 bytes = packed a3-related value
field_07 : 2 bytes = a4
field_09 : 4 bytes = float-like v26
```

`field_05` is explicitly flagged for ASM/LST verification because Hex-Rays represents the caller's temporary as a packed 64-bit object and passes `SBYTE4()` into a 2-byte serializer.

### 4.2 `a2` — action/resource relation

The Client forms:

```text
&stru_B8A19C.action + a2
```

and passes the entry through:

```text
sub_535020(actionTable, entry)
sub_533FF0(actionTable, entry)
```

Thus `a2` is strongly tied to action/resource selection.

### 4.3 `v21 = *a5` — local slot/index candidate

It indexes:

```text
byte_F6D8F8[playerStride * localSlot + 40 * v21]
```

so it is a local weapon/action slot/index candidate.

### 4.4 Final 4-byte value — quantitative action/weapon state

The `v26` value starts at `0.0` and may become an action-entry value (`+1202`) or a calculation via:

```text
sub_A1D480
sub_534A70
```

with fallback constants.

The value is therefore quantitative action/weapon state. It is **not yet proven to be durability**.

---

## 5. Packet 963 — `GameNetwork::OnGGDropWeaponGetAndDropAck`

### 5.1 Status

First byte:

```text
u8 status = v49
```

`status != 0` causes early return. Zero is the success path.

### 5.2 Main success body

Current raw parse:

```text
u8  player/network id = n16
u32 state/value        = v32
u16 dropped_object_id  = v26
u8  control             = p_k
u16 resource/action id = n2789
u16 value_1             = v46
u16 value_2             = v47
u16 value_3             = v14
```

When `n2789 != 0`, additional fields are consumed:

```text
u16 value_4
u16 value_5
u16 value_6
u32 float-like/raw scalar
0x20-byte raw block
```

Exact public semantics of these secondary fields remain open.

### 5.3 Critical namespace separation

`v26` is used by:

```text
sub_95F600(dropManager, v26, ...)
sub_95F8F0(dropManager, v26, 0)
```

`sub_95F600()` searches the drop-object list by:

```text
*(dropObject + 22) == v26
```

Therefore:

```text
v26 = dropped-world-object instance ID
```

Confidence A.

By contrast, `n2789` is passed inside `sub_960250()` to:

```text
sub_534D20(actionTable, n2789)
sub_5F5BE0(resourceTable, n2789)
```

Therefore:

```text
n2789 = Resource/Action ID
```

Confidence A.

These two u16 values must not be merged in the server model.

### 5.4 ACK application chain

```text
963
 ↓
sub_960250(...)
 ↓ resource/action + world-object state
sub_95F920(...)
 ↓ player weapon/action state
sub_95F8F0(dropManager, v26, 0)
 ↓ remove/resolve picked drop object
```

This proves that 963 is a state-changing ACK, not merely a success notification.

---

## 6. `sub_95F600` — dropped-object lookup

`sub_95F600(dropManager, id, ...)` iterates active drop objects and compares their object field `+22` with `id`.

On match it exposes object state including:

```text
+38
+40
+44
+128
+132
+136
+48..+76 (8 DWORD state values)
+20
```

This is the structural bridge between the 963 object ID and the internal dropped-object object.

The same object should be traced backward into 961's `sub_95E7D0()` creation path to close the server representation.

---

## 7. `sub_95F920` — confirmed player/action state mutation

For the local-player branch, `sub_95F920()` directly updates player structures around:

```text
+238740
+238964
+144208
+144210
+144220..+144248
+239576
```

It stores the received action/resource ID into the selected local slot and invokes:

```text
sub_956BB0(...)
sub_95B9B0(...)
sub_5F66A0(...)
sub_5F67A0(...)
sub_5F3A90(...)
sub_5FF2C0(...)
```

against Resource/action metadata and current weapon state.

Therefore a successful 963 can mutate actual player weapon/action state.

The exact mapping of these mutations to ammo, PG, temporary item level/effect or weapon selection remains unresolved; that semantic must be established from these helpers rather than inferred from the Wiki alone.

---

## 8. Wiki cross-check

The 2015 PaperMan Wiki `出現アイテム一覧` states that a drop can appear when a player who has at least one kill is killed, when Item Battle is enabled. Picking it up replenishes main-weapon ammunition by 20% of original total ammo and awards PG; item level changes effect strength/duration, and honor level affects drop weighting. With Item Battle disabled, a money-bundle style item still provides ammo/PG. citeturn926445search6

The Wiki also has a separate `ウェポンピックアップシステム` entry, confirming weapon pickup as its own gameplay subsystem. citeturn703110search3

These facts validate the overall gameplay role of the protocol but do not identify individual wire fields.

---

## 9. Current protocol model

```text
961 Server → Client
    ↓
create/update dropped-world object
    ↓
resource/template + transform + object state

962 Client → Server
    ↓
GetAndDropReq
    ↓
local action/weapon slot + request parameters

963 Server → Client
    ↓
status
    ↓
player id + dropped-object instance id + resource/action state
    ↓
apply player/world-object state
    ↓
remove/resolve picked object

960 Server → Client
    ↓
explicit dropped-object instance-id destroy list
```

The most important invariant recovered so far is:

```text
DroppedObjectInstanceId != ResourceOrActionId
```

---

## 10. Remaining proof targets

```text
1. 961 exact field widths/order after ASM/LST correction
2. 961 instance-ID assignment in sub_95E7D0
3. sub_960250 exact semantics of all ACK state values
4. sub_95F920 exact ammo/PG/item effects
5. 962 a1/a3/a4 packed-wire semantics via ASM/LST
6. 963 optional block discriminator n2789
7. Extracted resource IDs for Item Battle drops and levels
8. server-side sender patterns for 960/961/963 recoverable from client references
```
