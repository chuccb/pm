# Character / Inventory / Equipment Research

> Target: Japanese PaperMan final client (2016 service-ending version)
> Updated: 2026-09-16

## Purpose

This document is the high-level, server-reconstruction-oriented summary. Detailed C/LST evidence is kept in `Character_Inventory_Equipment_DeepEvidence.md`.

## Closed / high-confidence structure

```text
PlayerProfile
├─ Character / Appearance
│    └─ CompositeAppearanceState (up to 20 records)
├─ ItemCollection (up to 5120 × 28-byte records)
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
├─ SwitchWeaponSlot (separate state)
└─ tItemSlotToClient (9 mappings)
```

## Character / appearance

The Client maintains up to 20 composite records, each 13 words / 26 bytes. The records are parsed/serialized by the `sub_524010` / `sub_5241C0` family and compared field-by-field.

The five component fields `+159..+163` are generated from a base resource identity by `sub_522580()` according to mask bits `1/2/4/8/16`. This is direct Client evidence that the fields form a derived resource composition rather than unrelated integer properties.

The numeric resource namespaces are structured: the Client uses a base `19900000`-series and derived `10000000`-series identities, with explicit namespace decoding helpers. The composite state also reaches an AVATA presentation/resource path.

Public labels such as body/hair/face/set/accessory are still kept OPEN at individual wire-field level. The extracted avatar resource schemas support those concepts, but resource topology alone is insufficient to assign each one to a specific wire word.

## Items

The Client allocates a maximum of 5120 item records, each 7 DWORD / 28 bytes. The collection supports lookup, update, removal and compaction, so it is runtime-owned state rather than a UI-only cache.

### Recovered item record shape

The important parser/record-builder chain now closes the following structural layout:

```text
record-relative byte offset
+0   DWORD-like field
+4   item/resource identity
+8   DWORD-like field
+12  DWORD-like field
+16  DWORD-like field
+20  optional/type-like u8
+22  item-associated u16
+24  duplicate copy of the same u16
```

The exact public meaning of +8/+12/+16/+20 remains OPEN.

### Durability runtime chain

The item parser reads the `u16` immediately before constructing the 28-byte record, stores the same value at the record's +22 and +24 positions, and sends that value with the item/resource identity into `sub_534450()`.

`sub_534450()` writes the value into the matched resource runtime entry. The Client then calculates:

```text
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base × 100
```

`sub_534B60()` returns the resource definition field `+1204` as the base; `sub_534A70()` retrieves the current runtime value for resource namespaces type 21/22.

This is direct Client evidence of a current-versus-base durability/value architecture. The strongest interpretation is:

```text
OwnedItem
├─ ItemIdentity
├─ ItemAssociatedValues
└─ DurabilityState
     ├─ Current
     └─ Base (resource-definition derived)
```

Do not collapse the duplicated item-record values and the resource-runtime copies into one physical field.

## Historical durability cross-check

The Japanese Wiki's 2016-era `武器耐久値情報` describes permanent PG/CASH main/sub weapons with repair durability, battle-use reduction, mid-match exit penalties, degradation beginning around 19%, and repair back to 100%; duration weapons are described separately from this repair-durability system.

This is historical corroboration for the Client architecture. The exact protocol field name, mutation packets, repair packet, duration/expiry path, and the Client's exact ~19% threshold are still OPEN.

## Weapons

The four persisted/selectable loadout slots are directly closed by Client UI literals and state offsets:

```text
+144206 → PRIMARYSLOT
+144208 → SECONDARYSLOT
+144210 → MELEESLOT
+144212 → THROWSLOT
```

The Japanese Wiki independently presents the corresponding player-facing Main/Sub/Melee/Throwing weapon categories. Keep Client names and Wiki terminology side-by-side rather than silently replacing one with the other.

`SWITCHWEAPONSLOT` maps to `+144338` and is a separate selected/active state, not a fifth persisted equipment slot. Exact gameplay semantics remain OPEN.

### Weapon record wire shape

`sub_524880()` / `sub_524A50()` show a conditional per-slot record:

```text
u8 type
u16 component0

if type != 3:
    u16 component1
    u16 component2
    u16 component3

if component0 != 0:
    8 × 4-byte serializer units
```

The last line is now verified against `sub_592AA0()`: despite a misleading Hex-Rays `char` parameter prototype, it calls the underlying byte-copy primitive with size `4`. Therefore the eight trailing values occupy 32 bytes total.

### 220/221

`GI_CHANGEWP_REQ/ACK` supports both:

```text
variable-length delta → changed slots only
full snapshot           → count = 4
```

The Client compares all four weapon blocks, serializes changed blocks for delta updates, and can serialize all four for a full snapshot. On receive, it parses a variable count and applies the result into the four-slot loadout state.

Do not hardcode one record per packet or always assume four records.

## Character creation

`GM_CREATECHAR_REQ = 214` has a 6-byte payload:

```text
u8
u16
u8
u16
```

The character-selection flow computes two of the values from the selected character/resource pointer, proving this is not safely modeled as a generic `characterId/gender/name/slot` tuple. Exact public semantics remain OPEN.

`GM_CREATECHAR_ACK = 215` currently parses one byte and feeds it into the character-selection state machine. Exact result semantics remain OPEN.

## 197–200 bootstrap

```text
197 GL_MYINFO_REQ   → 0-byte request
198 GL_MYINFO_ACK   → complex CClientData/profile sync
199 GL_MYITEM_REQ   → 0-byte request
200 GL_MYITEM_ACK   → item collection synchronization
```

198 is not merely a success byte: the Client constructs a temporary `CClientData`, parses multiple profile/appearance/equipment structures, and applies the result. 200 populates the 5120-capacity item collection.

## Package vs Item

Historical Wiki research supports separating package grants from individual item instances. Character Packages can bundle Character + Set Avatar + Paper Puzzle; general packages can combine weapons/titles/avatar. Do not model a package as simply another inventory item.

## Resource topology

The repository's extracted resources include:

```text
Extracted/character/
Extracted/item/avatar/
Extracted/item/object/
Extracted/item/thumb/
Extracted/item/weapon/
```

The Client also explicitly loads item/avatar resources. Resource identity, render asset identity, and owned item identity must remain distinct domain concepts until an explicit mapping closes them.

Current item data revision in the repository is `811034967`.

## Evidence / uncertainty policy

Closed facts should be based on direct Client/resource proof wherever possible. Wiki is historical corroboration and can establish player-visible rules, but it cannot override direct packet/data-flow evidence. Hex-Rays names are not treated as authoritative.

Important packet-primitives rule: a decompiler prototype can understate the actual serialized width. `sub_592AA0()` is a concrete example: its `char` argument is copied as 4 bytes. Protocol research must therefore verify helper implementations and byte counts instead of trusting C parameter types.

Public semantic names remain OPEN when the actual field/resource mapping is not closed.

See `Character_Inventory_Equipment_DeepEvidence.md` for detailed evidence chains, function references, corrections, and unresolved P0 questions.
