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

The Client maintains up to 20 composite records, each 13 words / 26 bytes. The records are parsed/serialized by the `sub_524010` / `sub_5241C0` family and compared field-by-field by `sub_525450`.

The five component fields `+159..+163` are generated from a base resource identity by `sub_522580()` according to mask bits `1/2/4/8/16`. This is direct Client evidence that the fields form a derived resource composition rather than unrelated integer properties.

The numeric resource namespaces are structured: the Client uses a base `19900000`-series and derived `10000000`-series identities, with explicit namespace decoding helpers. The composite state also reaches an AVATA presentation/resource path.

Public labels such as body/hair/face/set/accessory are still kept OPEN at individual wire-field level. The extracted avatar resource schemas support those concepts, but resource topology alone is insufficient to assign each one to a specific wire word.

## Items

The Client allocates a maximum of 5120 item records, each 7 DWORD / 28 bytes. The collection supports lookup, update, removal and compaction, so it is runtime-owned state rather than a UI-only cache.

The item parser also updates a separate resource-runtime state via `sub_534450(resource identity, int16 value)`.

### Durability breakthrough

The Client contains a direct current-versus-base percentage calculation:

```text
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base × 100
```

`sub_534A70()` retrieves the current runtime value for resource types 21/22; `sub_534B60()` retrieves resource definition field `+1204` as the base. `sub_534450()` writes the item-associated value into the runtime durability state table.

Therefore the current best model is:

```text
OwnedItem
├─ ItemIdentity
├─ Item-associated persistent values
└─ DurabilityRuntime
     ├─ CurrentDurability
     └─ BaseDurability
```

This aligns with the 2016 Japanese Wiki's permanent main/sub weapon repair-durability rules, but the exact canonical packet field and all durability mutation packets are still OPEN.

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

### Weapon wire structure

`sub_524880()` / `sub_524A50()` show a conditional per-slot record:

```text
u8 type
u16 component0
if type != 3:
    u16 component1
    u16 component2
    u16 component3
if component0 != 0:
    8 trailing serializer units
```

Thus the wire record is not fixed-size for every type. Do not hardcode one payload length before tracing the underlying serializer primitives.

### 220/221

`GI_CHANGEWP_REQ/ACK` supports both:

```text
variable-length delta → changed slots only
full snapshot           → count = 4
```

The Client compares all four weapon blocks, serializes changed blocks for delta updates, and can serialize all four for a full snapshot. On receive, it parses a variable count and applies the result into the four-slot loadout state.

## Character creation

`GM_CREATECHAR_REQ = 214` has a 6-byte payload:

```text
u8
u16
u8
u16
```

The character-selection flow computes two of the values from the currently selected character/resource pointer using explicit resource-derived lookup functions. Therefore the packet must not be guessed as a generic `characterId/gender/name/slot` tuple. Exact public semantics remain OPEN.

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

Closed facts should be based on direct Client/resource proof wherever possible. Wiki is historical corroboration and can establish player-visible rules, but it cannot override direct packet/data-flow evidence. Hex-Rays names are not treated as authoritative. Public semantic names remain OPEN when the actual field/resource mapping is not closed.

See `Character_Inventory_Equipment_DeepEvidence.md` for the detailed evidence chain, function references, corrections, and unresolved P0 questions.
