# PaperMan Kick Vote — Audit Notes (2026-09-16)

## A. Team-scope filtering is now directly grounded in the player-group subsystem

The target-list filter ultimately calls `sub_67D3F0(slot)` through `sub_67DDD0(record)`.

The relevant implementation is:

```c
BOOL __cdecl sub_67D3F0(unsigned int slot)
{
    if (slot >= 0x10)
        return false;
    if (sub_67EB70())
        return true;

    v = sub_67D520(slot);
    return v == sub_67D240();
}
```

`sub_67D520(slot)` obtains a per-player grouping/team value from the player-manager object, while `sub_67D240()` obtains the local participant's corresponding value.

Therefore, outside the special `sub_67EB70()` path, the predicate is literally an equality comparison against the local player's grouping/team value.

This materially strengthens the previous wording:

```text
scope 0 filtering -> same-team / same-group eligibility
scope 1 filtering -> no such same-team restriction
```

The Japanese Wiki independently describes Team Kick as restricted to users on the applicant's team, while Full Kick covers all participants. Thus the behavioral mapping is strongly cross-validated.

### Important nuance

`sub_67EB70()` can force the predicate true. The exact circumstances represented by that global/mode helper still need independent recovery. Therefore the implementation should model the observed special-case override rather than replacing the predicate with an unconditional `teamId == localTeamId` rule.

## B. 718: do not trust Hex-Rays' apparent `char` types for the second and third parameters

The decompiled sender currently appears as:

```c
IVotingNetwork::sub_A191D0(char *this, int scope, char reason, char target)
```

But its serializer calls `sub_592A20` for **all three values**:

```c
v4 = sub_592A20(v7, scope);
v5 = sub_592A20(v4, reason);
sub_592A20(v5, target);
```

`sub_592A20` is the raw 4-byte integer writer used throughout this packet layer.

Even more importantly, the target-selection callback obtains `v7` from a 36-byte target-list entry where the first field is stored/read as a DWORD player ID, and passes that value to the request callback.

Therefore the safe reconstruction is:

```text
718 logical fields:
  field 0 = scope value, serialized as 4 bytes
  field 1 = reason index, serialized as 4 bytes
  field 2 = target player ID, serialized as 4 bytes

payload = 12 bytes
```

The apparent `char` types on the Hex-Rays function signature are a decompiler type-recovery artifact / untrusted prototype, not sufficient evidence for a 1-byte wire field.

### Rule for future RE work

For Packet layouts, prioritize this evidence order:

1. actual serializer width (`sub_592A20`, `sub_5928E0`, etc.);
2. receiver parser width (`sub_592A40`, `sub_592940`, etc.);
3. caller data-flow and field origin;
4. only then Hex-Rays' displayed C parameter type.

This avoids a common false schema where a 32-bit target player ID is accidentally reduced to `u8` merely because Hex-Rays inferred a byte parameter on an indirectly-dispatched method.

## C. Current 718/721 width status

```text
718 = u32 + u32 + u32 = 12-byte logical payload
721 = u8 = 1-byte logical payload
720 = u32 + u32 + u32 + u32 + u8 = 17-byte logical payload
722 = u32 + u8 = 5-byte logical payload
723 = u8 + u32 = 5-byte logical payload
719 = u8 = 1-byte logical payload
```

The Packet send path adds an outer 8-byte framing/header region; these numbers are therefore logical payload sizes, not total TCP packet lengths.

## D. Evidence anchors

### C source

- `sub_A191D0` / 718 serializer: C export around lines 699767–699787.
- `sub_67D3F0` / same-group comparison: C export around lines 287387–287415 and 287700–287728.
- `sub_67D520` / per-slot group value: C export around lines 287390 onward.
- `sub_A190C0` / target selection callback: C export around lines 699730–699775.

### Wiki

The Japanese `操作ガイド` states that Team Kick is limited to the applicant's team, Full Kick applies to all participants, and the corresponding minimum participant rules apply. It also states the 70-second voting limit and the six reasons. citeturn629729search0

## E. Still-open items

- Exact internal symbolic name/enum for scope 0/1.
- Exact semantics of `sub_67EB70()` special override in the kick-vote context.
- 719 status enum values.
- 723 result enum values.
- Exact server-side timeout/final tally algorithm.
- Actual 396/397 master-room packet bodies.
