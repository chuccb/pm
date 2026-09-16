# PaperMan 2016 JP — TCP 166 Field Detail: Subtype 3–15

> 研究日期：2026-09-17
> Evidence：IDA `PaperMan.exe.c` exact parser + reader widths + downstream calls

## Reader widths

```text
sub_592940 = u8
sub_5929C0 = u16
sub_592A00 = u16
sub_592A40 = u32
sub_592AC0 = u32
sub_592B40 = 4-byte copy
sub_592730 = opaque/variable copy
```

## Subtype 3 / 20 — shared impact/status wire form

Parser `sub_747980` reads, in order:

```text
u32 gate_v21
u8  target_or_other_player = n16_1
u16 resource_id = v19[0]
u8  state_type = n20
u8  state_a = v15
u8  state_b = v18
u32 aux_a6 = v16
u32 aux_n26
u8  aux_n0x1E
```

Body footprint: **19 bytes**.

Acceptance requires `gate_v21 == dword_F2A65C`.

Then:

```text
sub_747460(outer_actor, n16_1, resource_id,
           state_type, aux_a6, aux_n26, aux_n0x1E, subtype)
```

For non-local outer actor also calls:

```text
sub_747B90(resource_id, n16_1, state_a, state_b, outer_actor)
```

These two subtypes are therefore wire variants of one Resource-driven gameplay state/impact family, not independently named packet classes yet.

## Shared `sub_747460`

The function resolves two player objects, compares target controller `+16` against `aux_a6`, and drives animation/state/sound paths. Resource metadata is queried by `resource_id`.

If `sub_7473E0(subtype, aux_n26, aux_n0x1E)` succeeds, it calls:

```text
sub_74CB20(..., resource_id, ..., resource_category)
```

It can also call `sub_993E40` when Resource category `sub_5EFE00(resource) == 7`.

Therefore `resource_id` is semantically real; do not model it as an opaque decorative value.

## Subtype 4 — six-parameter Resource/effect record

`sub_748860` reads:

```text
u32 control_or_time = n0x64
u16 control = n0xA
u32 resource_id = v22
u32 p0 = v13
u32 p1 = v14
u32 p2 = v15
u32 p3 = v18
u32 p4 = v19
u32 p5 = v20
```

Body footprint: **34 bytes**.

All six DWORD parameters are passed to:

```text
sub_61BA90(object, control, p0,p1,p2,p3,p4,p5,
           control_or_time, resource_id)
```

Resource categories 1–7 have additional presentation paths (with category-5/subtype-8 exception). Exact public semantics of p0–p5 remain unresolved.

## Subtype 5 — Resource category 10

`sub_748A50` reads:

```text
u32 v19
u8  v18
u32 resource_id
u32 p0
u32 p1
u32 p2
u32 p3
u32 p4
u32 p5
```

Body footprint: **29 bytes**.

Only Resource category `10` reaches the main special branch. Local-player and remote-player routes use different downstream helpers (`sub_84C...` vs `sub_5B7050/sub_5B6C40`).

## Subtype 6 — Resource category 10 / 15

`sub_748CD0` reads:

```text
u32 v10
u16 v5
u32 resource_id = v12
u32 p0 = v2
u32 p1 = v3
u32 p2 = v4
u32 p3 = v7
u32 p4 = v8
u32 p5 = v9
u8  v13
```

Body footprint: **33 bytes**.

Main operation only applies when Resource category is `10` or `15`, then calls `sub_5B6C40` with the resource and six DWORD parameters.

## Subtype 7 — opaque event/text body

`sub_748E40` clears a 256-byte local buffer, calls `sub_592730`, then:

```text
sub_61FCB0(&dword_1D09130, actor_id, buffer, nullptr)
```

The reliable explicit consumed length is not recoverable from this function alone. Keep it as an opaque payload with a 256-byte local destination, not a guessed string packet.

## Subtype 8 / 9 / 18 / 25 — indirect object callback family

`sub_748EB0` forwards actor id, subtype and Packet object through a vtable callback slot `+56`; it does not expose the callback's internal fields.

Subtype 18 additionally toggles a global gameplay state before the callback.

Therefore the packet body must be decoded from the indirect callback, not assumed empty.

## Subtype 10 — FIRE_BOMB action/effect family

Dispatcher first reads:

```text
u8 secondary_player_id
u8 n13
```

Then `sub_749230` / `sub_749520` consume:

```text
u8  n0x1E
u32 resource_or_action_id
u32 n26
u32 value
```

Tail footprint: **13 bytes**.

Resource resolution includes direct fallback to `L"FIRE_BOMB"`.

For `n13 == 9 || 10`, a Resource-derived 16-bit value is stored into target effect slots and `sub_74CB20` runs.

For `n13 == 13`, target state flag/timing is changed and Resource-derived timing/effect setup runs; local-player route additionally invokes particle/sound helpers.

The public meaning of `n13=9/10/13` remains unresolved.

## Subtype 11 — timer/effect reset family

Dispatcher reads `u8 n7`:

```text
n7 == 1 → sub_7494B0
otherwise → sub_749810
```

`sub_749810` accepts `1..20` and clears two indexed player state locations, then timestamps special slots:

```text
n7 == 5 → player[109] = timeGetTime()
n7 > 7   → player[n7 + 209] = timeGetTime()
n7 == 13  → player[79] = 0; local route calls sub_716E30(0,0,...)
```

This is a state/timer reset event; public enum names are unresolved.

## Subtype 12 — two control u16

Body:

```text
u16 a
u16 b
```

Passed to:

```text
sub_67CD20(n9_0, a, b, 2 - !sub_67F2F0())
```

Both widths are directly verified as 2 bytes.

## Subtype 14 — transform sample

Body:

```text
u32 sample_or_time
s16 sample_a
s16 sample_b
s16 sample_c
s16 sample_d
u8  flag
```

Footprint: **13 bytes**.

Passed to `sub_5B3DD0`, which stores transform samples later consumed by interpolation logic. The four signed 16-bit values are spatial/orientation sample components; exact axis/angle assignment remains unresolved.

## Subtype 15 — target Resource/state transition

`sub_748420` reads:

```text
u8  target_player_id
u16 resource_id
u8  state_39
u8  state_30
u8  state_35
u32 target_controller_state
u32 auxiliary
u8  n0x1E
```

Body footprint: **15 bytes**.

Direct mutation:

```text
target_controller +16 = target_controller_state
```

The Resource table indexed by `resource_id` then feeds additional state/effect handling. If `auxiliary == 0` and target is local, `sub_747E50` receives a Resource-derived parameter block.

This proves subtype 15 is a real target state/resource transition, not merely a visual notification.

---

## Do not infer

The following names are intentionally not assigned without further Resource/ASM/caller proof:

```text
subtype 3/20 = Hit
subtype 4 = Projectile
subtype 5/6 = Skill
subtype 11 = Reload/WeaponStop
subtype 12 = Team/Slot
subtype 15 = Death/Stun/Skill
```

The raw widths/order and downstream call graph are already established; public semantics are the next proof layer.
