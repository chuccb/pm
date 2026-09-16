# PaperMan 2016 JP — Drop / Pickup Weapon Protocol

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact parser/serializer trace + dispatcher + Resource cross-check + Wiki

## 1. Confirmed packet family

Gameplay TCP receive dispatcher contains:

```text
960 → sub_566B30
961 → sub_566BF0
963 → sub_5672E0
```

Client send path:

```text
sub_566F50
    → Packet opcode 962
    → sub_555090(send)
```

Therefore the DropWeapon family is at least:

```text
960  Server → Client  GGWeaponPickUpDestroyNotify
961  Server → Client  GGDropWeapon... state/appearance notify
962  Client → Server  GGDropWeaponGetAndDropReq
963  Server → Client  GGDropWeaponGetAndDropAck
```

The exact public names of 961 beyond the extracted Client string are still kept conservative.

---

## 2. Packet 960 — `OnGGWeaponPickUpDestroyNotify`

Exact parser:

```text
u8 count
repeat count:
    u16 dropped_weapon_id
```

Loop terminates early if `dropped_weapon_id == 0`.

For each nonzero ID:

```text
sub_95F8F0(dropWeaponManager, dropped_weapon_id, 0)
```

and diagnostic string explicitly identifies:

```text
GameNetwork::OnGGWeaponPickUpDestroyNotify
```

### Semantic

This is a Server→Client notification telling the client to remove/destroy one or more existing dropped-weapon objects by ID.

The `count` is a repeated-record count, but zero ID acts as an additional terminator.

Do not interpret the u16 IDs as item template/resource IDs solely from width; they are specifically passed to the dropped-weapon object manager as destroy targets. The exact ID namespace remains unresolved.

---

## 3. Packet 961 — dropped weapon/object spawn or state notification

`sub_566BF0()` begins:

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
    0x20-byte opaque/raw block
```

Then it:

```text
sub_5689A0(src)
sub_728440(...)
resource lookup using object_or_weapon_id
sub_95E7D0(dropWeaponManager, 0, src, 0)
```

Coordinates are reconstructed from three 16-bit values:

```text
x = value_1
z = value_2-like
...
position construction applies:
    y + 5.0
    y - 1000.0
```

The function also performs Resource lookup through:

```text
sub_5F5BE0(resourceTable, object_or_weapon_id)
sub_5BB9F0(resource)
```

and applies the resource matrix/visual data.

### Current semantic boundary

High-confidence:

```text
961 = server→client dropped-weapon/object appearance/state records
```

Unresolved:

```text
exact object ID vs resource ID distinction
control byte
all u16/u32 state values
0x20-byte block
coordinate packing/unit
```

These must be solved from `sub_95E7D0`, `sub_5689A0`, Resource records and actual object structures before assigning public field names.

---

## 4. Packet 962 — `OnSendGGDropWeaponGetAndDropReq`

Serializer starts with:

```text
Packet opcode = 962
```

The decompiler output is affected by helper signatures that take `char` while copying 2/4 bytes; serializer definitions prove the actual copy widths:

```text
sub_592920  → exactly 1 byte
sub_5929E0  → exactly 2 bytes
sub_592B20  → exactly 4 bytes
```

The request logically serializes:

```text
field_00 : 2-byte a1
field_02 : 2-byte a2 / action-id-like value
field_04 : 1-byte v21 = *a5
field_05 : 2-byte a3
field_07 : 2-byte a4
field_09 : 4-byte float-like value derived from v26
```

Important: the decompiled `SLOBYTE(v13)` at the final `sub_592B20()` call must **not** be interpreted as a 1-byte wire field. `sub_592B20()` copies 4 bytes from its argument storage; in this path `v13` is the float-like value derived from `v26`.

### 4.1 `a1`

Directly passed to first `sub_5929E0()` and logged as argument 1. Therefore wire width = 2 bytes.

Likely object/weapon action identifier; exact namespace unresolved.

### 4.2 `a2`

Used to resolve:

```text
p_action = &stru_B8A19C.action + a2
sub_535020(actionTable, p_action)
sub_533FF0(actionTable, p_action)
```

Thus `a2` is strongly connected to an action/resource selection, not merely a random slot index.

### 4.3 `v21 = *a5`

Used to index local player's weapon/action state:

```text
byte_F6D8F8[playerStride * localSlot + 40 * v21]
```

so this byte is a local weapon/action slot/index candidate.

### 4.4 `a3`, `a4`

Serialized as 2-byte values after `v21`. They are logged separately and participate in request-state calculation. Exact public semantics remain unresolved.

### 4.5 Final 4-byte field

`v26` starts as `0.0`; when an action/resource entry exists, it may become:

```text
*(v24 + 1202)
```

or a calculated value from `sub_A1D480` / `sub_534A70`; otherwise default/invalid branches use `0.0` or `100000.0`.

This strongly indicates a quantitative action/weapon parameter (possibly derived durability/energy/weight-like state), but **do not name it durability without further proof**.

### 4.6 Request-side validation/calculation

The Client resolves an action entry through `dword_EE3E98` and checks local player state. A special branch exists when action index is in a specific range and `n2` is one of:

```text
2, 6, 8, 9, 15
```

and `v20 == 0`; then a calculation through `sub_A1D480()` / `sub_534A70()` provides the final float.

Therefore 962 is not a blind "pickup ID" packet: it is assembled from local weapon/action state.

---

## 5. Packet 963 — `OnGGDropWeaponGetAndDropAck`

Parser begins after gameplay gate:

```text
u8 status_or_result = v49
```

If `v49 != 0`, the handler returns early.

On success (`v49 == 0`), exact sequence:

```text
u8  player/network id       = n16
u32 value_0                 = v32
u16 drop/object id          = v26
u8  p_k/control              = p_k
u16 value_1                 = n2789
u16 value_2                 = v46
u16 value_3                 = v47
u16 value_4                 = v14
```

Then, **only when `n2789 != 0`**:

```text
u16 value_5 = v13
u16 value_6 = v34
u16 value_7 = v12
u32 float-like value_8 = v43
0x20-byte block = v35
```

Important type warning:

```text
sub_592B40(..., &v43)
```

copies 4 bytes even though `v43` is shown as `float`; therefore `value_8` should currently be recorded as raw 4-byte scalar / float-like, not an inferred integer.

Before applying the ACK, Client queries:

```text
sub_95F600(dropWeaponManager, v26, v30, v31, &v33, &v17, &v27)
sub_95F440(dropWeaponManager, v26)
```

Then:

```text
if v48 != nullptr && *v48 == 0:
    v27 = v46
    v28 = v47
    v29 = v14
```

Finally:

```text
sub_960250(...,
    n16,
    v13,
    v32,
    n2789,
    v34,
    v12,
    raw_float_bits(v43),
    &v35,
    &v27)

sub_95F920(
    a1,
    v26,
    v13,
    v15,
    n2789,
    v33,
    v32,
    n16,
    &v17,
    v30[0],
    v31[0],
    p_k)

sub_95F8F0(dropWeaponManager, v26, 0)
```

### Semantic boundary

High-confidence:

```text
963 = successful/failed server ACK for DropWeapon Get/Drop operation
v49 = success/error gate
n16 = player/network identity
v26 = dropped-weapon object ID / lookup key
n2789 = conditional-extra-data flag or mode/state discriminator
```

The remaining fields need object-manager (`sub_960250`, `sub_95F920`, `sub_95F600`) and Resource cross-tracing before public names are assigned.

---

## 6. Wiki cross-check

The PaperMan Wiki's 2015 `出現アイテム一覧` documents the gameplay behavior of item drops:

```text
An item can appear when a player who has at least one kill is killed,
when Item Battle is enabled.

Picking it up replenishes main-weapon ammunition by 20% of original total ammo
and grants PG.

When Item Battle is disabled, a money-bundle style item drops and still grants ammo/PG.
```

Higher-level items can provide stronger/longer effects, and honor level affects the likelihood of stronger drops. This is an external behavior-level anchor for the drop/pickup system; it does not by itself identify packet fields. citeturn463414search1

The weapon Wiki also separately confirms FIRE BOMB as a projectile weapon/resource, supporting the broader resource-ID approach used elsewhere in the Client, but it does not identify 962/963 fields. citeturn463414search10

---

## 7. Current packet relationship

```text
961 Server → Client
    ↓
create/update dropped-weapon world object

962 Client → Server
    ↓
GetAndDropReq
    ↓
local action/weapon state participates in request

963 Server → Client
    ↓
GetAndDropAck
    ↓
update/apply drop result
    ↓
remove/resolve dropped object via 95F8F0/95F920/960250

960 Server → Client
    ↓
destroy/remove dropped objects by u16 object IDs
```

This is a **stateful object protocol**, not a single `DropItem { id, x, y, z }` message.

---

## 8. Remaining proof targets

```text
1. `sub_95E7D0()` exact dropped-object structure and ID namespace
2. `sub_960250()` exact semantics of ACK values
3. `sub_95F920()` exact inventory/ammo/PG side effects
4. Resource IDs for dropped item types and their level variants
5. 961 coordinate and opaque 0x20-byte block semantics
6. 962 a1/a3/a4 and final float semantic using callers/ASM
7. 963 conditional block (`n2789`) and all scalar widths
8. Server-side packet send construction for 960/961/963 if recoverable from client callsites/symbol names
9. Cross-check with Wiki `出現アイテム`, honor-gauge drop weighting, ammo/PG effects, and item-level behavior
```
