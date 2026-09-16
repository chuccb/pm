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
record-relative byte offset
+0   DWORD-like field
+4   resource/item identity-like field
+8   DWORD-like field
+12  DWORD-like field
+16  DWORD-like field
+20  optional u8/type-like field
+22  u16 item-associated value
+24  second u16 copy of the same item-associated value
+26  residual bytes / exact public meaning OPEN
```

The record is laid out in a 28-byte temporary structure by `sub_524F70()`. Its arguments populate byte offsets 4, 8, 12, 16, 20, 22, and 24, with the same `u16` value written at offsets 22 and 24.

The item parser (`sub_524B70`) reads the corresponding values in the same order: identity, three/four scalar values, an optional byte, then a 16-bit value. Immediately after reading that 16-bit value, the Client stores it in the item-associated auxiliary state and passes it to `sub_534450(resource identity, int16 value)`. This is the strongest direct evidence that the item-associated `u16` is the source value for the durability runtime bridge.

The collection supports find, update, remove and compaction. It is therefore runtime-owned player item state, not merely UI cache.

### Current semantic status

- record +4: item/resource identity-like value — **A**
- record +8/+12/+16: item-associated DWORD values — **A**, public semantics still OPEN
- record +20: optional/type-like byte — **A**, exact semantic OPEN
- record +22 and +24: duplicated item-associated `u16` from the same parser value — **A**
- canonical public name of that `u16`: **strongly tied to durability; use `ItemAssociatedValue` until protocol field naming is frozen**

## 4. Major result: durability runtime chain

`sub_524F70()` is an internal 28-byte record builder. In the important parser caller, the 16-bit value read immediately before the call is written to both record offsets +22 and +24, then separately fed to `sub_534450()` using the item/resource identity.

`sub_534450()` accepts `(resource identity, int16 value)` and writes that value into the matched resource runtime entry at both `+1200` and `+1202`. The same helper is called while loading/parsing the 5120-item records.

```text
Item record
    ├─ item/resource identity (+4)
    └─ item-associated u16 (+22 / +24)
             │
             ├──────────────► stored in item record
             │
             └──────────────► sub_534450(identity, value)
                                  │
                                  ▼
                         Resource runtime entry
                           ├─ +1200
                           └─ +1202
```

Direct code evidence: `PaperMan.exe.c` around `sub_524F70`, `sub_524B70`, and `sub_534450`.

Important distinction: the two item-record copies (+22/+24) and the resource-runtime copies (+1200/+1202) are distinct storage locations. Do not model them as one physical field merely because the values are propagated together.

## 5. Current/base percentage calculation

`sub_534530(resourceManager, resourceId)` computes:

```text
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base * 100
```

`sub_534A70()` searches runtime entries whose identity namespace is type `21` or `22` and returns the stored `word_EE900A[...]` value. `sub_534B60()` performs the corresponding resource-manager lookup and returns entry `+1204` as the base value.

Therefore the strongest current interpretation is:

```text
CurrentDurability ≈ runtime current state
BaseDurability    = resource definition field +1204
DurabilityPercent = CurrentDurability / BaseDurability × 100
```

Confidence:

- existence of current/base percentage computation: **A**
- association with weapon/item durability: **A/B**
- exact canonical network field name: **OPEN**

Do not rename the raw protocol field to `Durability` solely from a decompiler variable name. The data-flow now strongly identifies its role, but the protocol-level public label should remain provenance-linked until the surrounding packet schema is fully closed.

## 6. Weapon durability is split by loadout category

`sub_534660()` reads the four-slot weapon state but has explicit branches for the first two component positions:

```text
four-slot block
├─ +144206 → primary identity
├─ +144208 → secondary identity
├─ +144210 → melee identity
└─ +144212 → throw identity
```

For the relevant primary/secondary path, the Client resolves the resource entry and computes current-versus-base durability percentage. This is consistent with the historical Japanese Wiki description of permanent main/sub weapons having repair durability, while duration weapons use a different model.

The exact degradation threshold is not yet closed by Client constants; Wiki evidence places gameplay degradation onset at approximately 19%, so treat that threshold as **C**, not A.

## 7. Historical Wiki cross-check: 2016 weapon durability

The Japanese Wiki page `武器耐久値情報`, last modified 2016-03-19, documents the 2016-era rule that permanent PG/CASH main/sub weapons have repair durability, battle use reduces durability, mid-match exit applies a penalty, degradation begins at roughly 19%, repair restores durability to 100%, and duration weapons do not use this durability/repair system.

Use this as historical external corroboration, not as a substitute for Client field recovery.

## 8. Composite appearance/resource state

The 20-record composite has up to 20 records, each 13 words / 26 bytes.

Wire/serialization helpers:

- `sub_524010()` parses the composite record collection.
- `sub_5241C0()` serializes the collection.
- `sub_5244E0(index)` serializes one specified record.
- `sub_525450()` compares the composite record field-by-field.

Current safe model:

```text
CompositeAppearanceState
├─ Base resource identity (+158)
├─ Component resource identities (+159..+163)
├─ Additional derived/resource fields (+164..+169)
└─ resource/runtime resolution
```

Do not assign public names such as hair/face/set/accessory to individual wire words until the Resource ↔ field mapping is closed.

## 9. `sub_522580()` component regeneration — exact masks

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

## 10. Resource namespace encoding

The Client uses systematic numeric namespaces:

```text
19900000-series → base character/resource namespace
10000000-series → derived component/resource namespace
```

`sub_533F50(x)` returns `(x - 10000000) / 100000` and `sub_533F80(x)` returns `(x - 10000000) % 100000`.

`sub_4148D0()` converts the supplied absolute identities back into local namespace numbers before passing them into the resource/rendering pipeline. This is direct evidence that the numeric IDs are structured resource identities, not ordinary small enums.

## 11. AVATA / appearance bridge

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

## 12. Weapon loadout — four categories closed

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

## 13. `SwitchWeaponSlot` is separate from the four persisted slots

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

Exact gameplay semantics of `SwitchWeaponSlot` remain OPEN: it may represent an active switch/index state rather than another equipment slot. Do not model it as a fifth weapon slot.

## 14. Four weapon blocks — exact conditional record shape

`sub_524880()` parses one weapon record as:

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

The last point is now closed against the serializer primitive rather than inferred from the decompiler prototype: `sub_592AA0()` is declared by Hex-Rays with a `char` parameter, but its implementation calls `sub_592580(..., 4u)`, so it writes **4 bytes**. Therefore the eight trailing values emitted by `sub_524A50()` are **32 bytes total**.

`sub_524A50()` serializes the exact inverse shape. The record is therefore conditionally sized:

```text
Type 3:
    1 × u8
  + 1 × u16
  + 8 × 4 bytes (when component0 != 0)

Other types:
    1 × u8
  + 4 × u16
  + 8 × 4 bytes (when component0 != 0)
```

The semantic names of component0..component3 and the eight trailing values remain OPEN.

## 15. 220/221 weapon sync supports delta and full snapshot

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

## 16. Weapon resource validation

`sub_527DB0()` validates the four major weapon components through distinct resource namespaces:

- action-related namespace
- `+12,200,000`
- `+12,300,000`
- `byte_BD3580[value]`

Invalid component categories trigger distinct error IDs 21–24. This strongly suggests the four components have separate resource meanings; it does not yet prove the public names of all four subcomponents.

## 17. `tItemSlotToClient`

`tItemSlotToClient` is a separate C++ structure containing 9 indexed values.

- constructor clears the mapping
- indices are valid for `< 9`
- parser reads exactly 9 values
- serializer emits all 9 values

Keep this domain separate from item inventory slots and weapon loadout categories.

## 18. Character creation request — stronger than a generic 4-field packet

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

## 19. `GP_CHPLAYC_REQ/ACK` remain unresolved

Registration is explicit:

```text
222 GP_CHPLAYC_REQ
223 GP_CHPLAYC_ACK
```

However, the current ACK parser (`sub_556730`) reads one 32-bit value and writes it to `dword_EE8D34` after a call to the large generic `sub_92EF00()` telemetry/diagnostic path. The ACK parser itself is a small state-write routine; existing xrefs are insufficient to prove that `dword_EE8D34` is literally a character identifier.

A full search found only the direct assignment in `sub_556730` and two later reads inside validation/timing-related code. This is not enough to override the packet registration name with a guessed server-side semantic.

Therefore:

- opcode names remain useful registration metadata;
- `223` body = one 32-bit value — **A**;
- business meaning of that value — **OPEN**;
- `dword_EE8D34` may participate in timing/state validation; do not label it `CurrentCharacterId` yet.

The next required work is to find the true 222 sender/payload and correlate the 223 value against character-selection state, room/lobby transitions, and any relevant resource identity.

## 20. Packet primitive verification rule

This client contains several misleading Hex-Rays helper prototypes where a small C type is passed to a helper that actually copies a larger fixed byte count. Example:

```c
void* sub_592AA0(void* this, char a2) {
    sub_592580(this, &a2, 4u);
}
```

Therefore protocol research must trust the primitive implementation (`sub_592580` byte count) rather than the decompiler's surface parameter type. This rule is especially important for packet serializers and conditional record sizing.

## 21. Cross-validation status after this research round

### Closed / high confidence

- Four weapon loadout categories: Primary / Secondary / Melee / Throw.
- `SwitchWeaponSlot` is a separate state from the four loadout blocks.
- 220/221 supports changed-slot delta updates and full count=4 snapshots.
- Weapon record conditional structure includes `type == 3` omission of component1..3.
- Eight trailing weapon serializer values are 8 × 4-byte units = 32 bytes.
- 5120 item records are 28-byte runtime records.
- The parsed item-associated `u16` is duplicated in two record positions and is also propagated to the resource runtime state by `sub_534450`.
- Client computes current-versus-base percentage using runtime current state and resource-definition `+1204`.

### Corroborated but not fully named

- The item-associated `u16` is the current durability value for the weapon/item resource runtime architecture.
- Primary/Secondary are the durability-relevant loadout categories in the recovered Client logic.
- The Wiki's 2016 permanent main/sub repair-durability rules match this Client architecture.

### Still OPEN

- Canonical protocol field name of the durability `u16`.
- Exact mutation packets/events that decrease durability.
- Exact repair request/response and repair cost path.
- Expiry/duration packet path.
- The Client constant/path that implements the Wiki's ~19% degradation onset.
- Exact meanings of item record +8/+12/+16 and +20.
- Exact public names of the four weapon record components.
- Exact meaning of the eight weapon tail values.
- Exact semantics of `SwitchWeaponSlot`.
- Exact `+159..+169` public appearance-field mapping.
- True 222 request sender and 223 business semantic.

## 22. Reconstruction guidance

For a server implementation, preserve the evidence hierarchy in the object model:

```text
PlayerProfile
├─ CharacterAppearanceState
├─ ItemCollection
│    └─ OwnedItem
│         ├─ Identity
│         ├─ ItemAssociatedValues
│         └─ DurabilityState
│              ├─ Current
│              └─ Base (definition-derived)
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
├─ SwitchWeaponSlot
└─ ItemSlotToClient[9]
```

Do not merge `OwnedItem`, resource-definition objects, and UI presentation objects merely because the Client propagates the same identity among them. The recovered architecture explicitly bridges these layers rather than collapsing them.
