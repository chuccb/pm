# Character / Inventory / Equipment — Deep Evidence

> Target: Japanese PaperMan final client (2016 service-ending version)
> Evidence-first reconstruction. Keep Client C/LST/ASM, Extracted resources, and Wiki/history cross-validation separate.
>
> Status updated: 2026-09-16

## 1. Scope and evidence discipline

This document records only conclusions that are backed by explicit client data flow or by cross-source agreement. Hex-Rays function names and variable names are not treated as authoritative semantics. When a public field name is not closed, keep a neutral structural name and mark the semantic as OPEN.

Evidence levels used here:

- A: direct Client/resource/ASM proof
- B: multiple Client chains agree
- C: Wiki/player-test evidence plus indirect Client agreement
- D: inference
- E: unverified

Historical version, region, mode, and legacy/current status must be recorded before using a finding as a reconstruction rule.

## 2. CClientData major layers

The constructor initializes multiple independent state domains:

```text
CClientData
├─ 20 × 13-word composite records
├─ 5120 × 7-DWORD item records (28 bytes)
├─ 4 × 22-word weapon/loadout blocks
└─ tItemSlotToClient
     └─ 9 indexed mappings
```

The 5120-item collection and four weapon blocks are distinct structures. Do not flatten them into one inventory table.

## 3. 5120-item collection: verified wire/runtime shape

Each item record is 7 DWORD / 28 bytes. The parser reads:

```text
+0   DWORD-like field
+4   resource/item identity-like field
+8   parsed value
+12  parsed value
+16  parsed value
+20  optional value (when caller requests it)
+24  auxiliary value
```

The parser also stores an auxiliary value at the separate 14-word-per-entry area beginning around `this + 431`, and updates the resource runtime state through `sub_534450(resourceManager, itemIdentity, int16Value)`. Evidence: `PaperMan.exe.c` around `sub_524B70`; the copy/parse path calls `sub_534450` after the record is materialized.

The collection supports find, update, remove and compaction. It is therefore runtime-owned player item state, not merely UI cache.

### Current semantic status

- `+211` (the 4-byte field at record-relative word 1): item/resource identity-like value — **A**
- `+214` (record-relative word 4): mutable item-associated value — **A**, public semantic still OPEN
- `+215`: optional field — **A**, exact semantic OPEN
- separate `+431/+432` state associated with item identity — **A** as runtime resource state bridge; exact canonical field name still OPEN

## 4. Major new result: durability runtime chain

A previously vague auxiliary field can now be tied directly to a durability architecture.

`sub_534450()` accepts `(resource identity, int16 value)` and writes that value into the matched resource runtime entry at both `+1200` and `+1202`. The same helper is called when the 5120-item records are loaded/parsed.

```text
Owned item record
    │
    ├─ item/resource identity
    └─ associated int16 value
             │
             ▼
      sub_534450()
             │
             ▼
Resource runtime entry
    ├─ +1200
    └─ +1202
```

Direct code evidence is in `PaperMan.exe.c` around `sub_534450` and `sub_524B70`.

### 4.1 Current/base percentage calculation

`sub_534530(resourceManager, resourceId)` computes:

```text
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base * 100
```

`sub_534A70()` searches runtime entries whose identity namespace is type `21` or `22` and returns the stored `word_EE900A[...]` value. `sub_534B60()` performs the corresponding resource-manager lookup and returns entry `+1204`.

Therefore the strongest current interpretation is:

```text
CurrentDurability ≈ runtime current state
BaseDurability    = resource definition field +1204
DurabilityPercent = CurrentDurability / BaseDurability × 100
```

Confidence:

- existence of current/base percentage computation: **A**
- association with weapon/item durability: **A/B**
- canonical network field name: **OPEN**

Do not yet rename the raw packet field as `Durability` in a protocol schema until the exact serializer field is closed.

## 5. Weapon durability is split by loadout category

`sub_534660()` reads the four-slot weapon state but has explicit branches for the first two component positions:

```text
four-slot block
├─ +144206 → primary identity
├─ +144208 → secondary identity
├─ +144210 → melee identity
└─ +144212 → throw identity
```

For the relevant primary/secondary path, the Client resolves the resource entry and computes current-versus-base durability percentage. This is consistent with the historical Japanese Wiki description of permanent main/sub weapons having repair durability, while duration weapons use a different model.

The exact degradation threshold is not yet closed by Client constants; Wiki evidence places the gameplay degradation onset at approximately 19%, so treat that threshold as **C**, not A.

## 6. Historical Wiki cross-check: 2016 weapon durability

The Japanese Wiki page `武器耐久値情報`, last modified 2016-03-19, documents the 2016-era rule that permanent PG/CASH main/sub weapons have repair durability, battle use reduces durability, mid-match exit applies a penalty, degradation begins at roughly 19%, repair restores durability to 100%, and duration weapons do not use this durability/repair system.

Use this as historical external corroboration, not as a substitute for Client field recovery.

## 7. Composite appearance/resource state

The 20-record composite has up to 20 records, each 13 words / 26 bytes.

Wire/serialization helpers:

- `sub_524010()` parses the composite record collection.
- `sub_5241C0()` serializes the collection.
- `sub_5244E0(index)` serializes one specified record.
- `sub_525450()` compares all 12 component words (`+158..+169`).

Current safe model:

```text
CompositeAppearanceState
├─ Base resource identity (+158)
├─ Component resource identities (+159..+163)
├─ Additional derived/resource fields (+164..+169)
└─ resource/runtime resolution
```

Do not assign public names such as hair/face/set/accessory to individual wire words until the Resource ↔ field mapping is closed.

## 8. `sub_522580()` component regeneration — exact masks

`sub_522580(mask, record)` derives five component fields from the base resource object:

```c
base = &unk_12FA660 + (baseId % 100000);

if (mask & 0x01) recordField[+159] = sub_402FF0(base) + 27008;
if (mask & 0x02) recordField[+160] = sub_4030A0(base) - 7456;
if (mask & 0x04) recordField[+161] = sub_403150(base) + 23616;
if (mask & 0x08) recordField[+162] = sub_403200(base) - 10848;
if (mask & 0x10) recordField[+163] = sub_4032B0(base) - 10400000;
```

Observed callers independently target these exact record-relative fields. This proves the first five component words are not unrelated arbitrary IDs; they form a mask-driven derived resource representation.

The `19900001..19900015` tables used by the helper are direct lookup tables for the base resource namespace, but the public semantic labels remain OPEN.

## 9. Resource namespace encoding

The Client uses systematic numeric namespaces:

```text
19900000-series → base character/resource namespace
10000000-series → derived component/resource namespace
```

`sub_533F50(x)` returns `(x - 10000000) / 100000` and `sub_533F80(x)` returns `(x - 10000000) % 100000`.

`sub_4148D0()` converts the supplied absolute identities back into local namespace numbers before passing them into the resource/rendering pipeline. This is direct evidence that the numeric IDs are structured resource identities, not ordinary small enums.

## 10. AVATA / appearance bridge

The client contains an explicit `AVATA` UI/resource path, while extracted resource schemas contain avatar-like components such as:

```text
avatar
body
hair
face
set
...

handTexture
head
face
set
acc1..acc4
SoundFolderName
```

This provides strong cross-source support that the composite record eventually feeds avatar rendering/presentation. It does **not** by itself prove a one-to-one wire mapping between `+159..+169` and those public labels.

## 11. Weapon loadout — four categories closed

The Client literally resolves four persistent/selectable UI/state names:

```text
+144206 → PRIMARYSLOT
+144208 → SECONDARYSLOT
+144210 → MELEESLOT
+144212 → THROWSLOT
```

This is direct A-level Client evidence. The Japanese Wiki independently uses the corresponding player-facing categories main/sub/melee/throwing, providing external corroboration.

Keep the Client spelling and the Wiki terminology side by side in final protocol documentation:

```text
Client: Primary / Secondary / Melee / Throw
Wiki:   Main / Sub / Melee / Throwing
```

`Primary ≈ Main` and `Secondary ≈ Sub` is strongly supported, but the canonical server enum name should remain a project-level choice rather than being presented as a recovered wire string.

## 12. `SwitchWeaponSlot` is separate from the four persisted slots

`SWITCHWEAPONSLOT` maps to `+144338`.

It is independently compared and updated in UI/gameplay code and is not serialized as a fifth member of the four 44-byte weapon blocks. The safest model is:

```text
WeaponLoadout
├─ Primary
├─ Secondary
├─ Melee
└─ Throw

SwitchWeaponSlot
└─ independent selected/active state
```

Exact gameplay semantics of `SwitchWeaponSlot` remain OPEN: it could encode an active switching state/index rather than another equipment slot. Do not model it as a fifth weapon slot.

## 13. Four weapon blocks — wire record is conditional length

`sub_524880()` parses one weapon record as:

```text
u8 type
u16 component0

if type != 3:
    u16 component1
    u16 component2
    u16 component3

if component0 != 0:
    8 additional serializer units
```

`sub_524A50()` serializes the exact inverse.

This means a reconstruction must **not** assume one fixed payload size for every weapon record. In particular, `type == 3` omits component1..component3.

The eight trailing values are preserved as `8 × serializer units`; their exact primitive width/name should be closed by tracing `sub_592AA0` before being normalized into the server protocol schema.

## 14. 220/221 weapon sync supports delta and full snapshot

```text
220 GI_CHANGEWP_REQ
221 GI_CHANGEWP_ACK
```

`sub_573340()` scans slots 0..3 and serializes only changed slots when generating a delta update. A separate caller writes count `4` and serializes all four slots for a full snapshot.

`sub_5735F0()` reads the count, parses each record with `sub_524880()`, then applies the resulting temporary `CClientData` through `sub_523370()`.

Therefore:

```text
220/221
├─ variable-length delta (changed slots)
└─ full snapshot (count = 4)
```

Do not hardcode `count == 1` or `count == 4` for every message.

## 15. Weapon resource validation

`sub_527DB0()` validates the four major weapon components through distinct resource namespaces:

- action-related namespace
- `+12,200,000`
- `+12,300,000`
- `byte_BD3580[value]`

Invalid component categories trigger distinct error IDs 21–24. This strongly suggests the four components have separate resource meanings; it does not yet prove the public names of all four subcomponents.

## 16. `tItemSlotToClient`

`tItemSlotToClient` is a separate C++ structure containing 9 indexed values.

- constructor clears the mapping
- indices are valid for `< 9`
- parser reads exactly 9 values
- serializer emits all 9 values

Keep this domain separate from item inventory slots and weapon loadout categories.

## 17. Character creation request — stronger than a generic 4-field packet

`214 GM_CREATECHAR_REQ` serializes exactly four fields:

```text
u8
u16
u8
u16
```

Total payload: 6 bytes.

A caller in the character-selection flow computes several of these values directly from the currently selected character/resource pointer:

```text
character/resource pointer
├─ base namespace index: pointer - &unk_12FA660
├─ derived value: sub_4030A0(pointer) - 7456
└─ derived value: sub_402FF0(pointer) + 27008
```

The first argument is a separate state byte (`*(this + 160)` in that call path) and is currently seen as `0` in that flow.

This proves the request is not safely modeled as an arbitrary `characterId / gender / name / slot` tuple. The exact public semantics of all four fields remain OPEN, but two values are demonstrably resource-derived.

`215 GM_CREATECHAR_ACK` currently parses one byte and feeds it into the character-selection state object. Exact result semantics are still OPEN.

## 18. `GP_CHPLAYC_REQ/ACK` remain unresolved

Registration is explicit:

```text
222 GP_CHPLAYC_REQ
223 GP_CHPLAYC_ACK
```

However, the current ACK parser (`sub_556730`) reads one 32-bit value and writes it to `dword_EE8D34` after a timing/state comparison. Existing xrefs are insufficient to prove that this is literally a "character change" operation.

Therefore do not silently equate opcode name with server semantics. Next required work:

1. find the true 222 sender and its payload;
2. trace all `dword_EE8D34` xrefs;
3. connect that value to character/UI/resource state;
4. only then rename it.

## 19. Cross-validation corrections made in this pass

The following earlier labels are now explicitly superseded:

```text
Old: item + auxiliary fields = unknown metadata
New: one associated int16 enters the resource runtime durability path
     and is used by current/base percentage calculation.
```

```text
Old: four weapon blocks are generic four slots
New: Client UI/state literals directly close them as
     Primary / Secondary / Melee / Throw.
```

```text
Old: weapon durability is mostly Wiki-derived
New: Client directly implements current/base percentage computation
     and resource-runtime durability state.
```

```text
Old: weapon records can be treated as one fixed wire structure
New: type == 3 conditionally omits component1..component3.
```

## 20. Server reconstruction model — current safest form

```text
PlayerProfile
│
├─ Character / Appearance
│    ├─ CompositeAppearanceState (up to 20)
│    │    ├─ BaseIdentity
│    │    ├─ Component identities
│    │    ├─ Derived resource identities
│    │    └─ AVATA presentation bridge
│    │
│    └─ Character-selection/create state
│
├─ ItemCollection (up to 5120 × 28-byte runtime records)
│    ├─ ItemIdentity
│    ├─ Item-associated values
│    └─ Durability runtime bridge (current/base)
│
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
│
├─ SwitchWeaponSlot
│
└─ tItemSlotToClient (9 mappings)
```

For an eventual C# server, use domain objects/records with neutral names until packet semantics are closed. Do not introduce fake enums simply because an offset looks enum-like.

## 21. Unresolved high-priority questions

### P0 — item durability

- exact wire field corresponding to the current durability value
- whether `record +214`, `record +215`, or the separate auxiliary field is the canonical persistent source
- exact decrease event and packets
- repair request/ack
- zero-durability behavior
- duration expiry versus permanent durability
- client-side 19% degradation threshold implementation

### P0 — weapon variants

- the three selectable entries per Primary/Secondary/Melee category
- exact semantics of all four core weapon component words
- exact 8 trailing serializer fields
- how weapon definition resource IDs map to owned item IDs

### P0 — appearance

- exact public names of `+159..+169`
- mapping to `body/hair/face/set/acc1..acc4`
- which fields are authoritative for render versus inventory ownership

### P1 — character lifecycle

- `214/215` exact field semantics and validation
- `222/223` exact character-switch semantics
- profile/item/appearance synchronization around 197–200

## 22. Research hygiene

Keep this file synchronized with the broader `Research/Core` documents. Prefer updating an existing section when a conclusion changes rather than creating duplicate MD files. Never promote a D-level inference to a protocol fact merely because the name looks obvious.
