# Kick Vote — Evidence Ledger: Eligibility / State / Protocol

> Research date: 2026-09-16
> Target: Japan PaperMan final service-period Client (2016)

## Scope

This file records the deeper evidence chain recovered from `PaperMan.exe.c` during the 2026-09-16 Kick Vote pass. It supplements `Protocol.md`, `UI_State.md`, and `Master_Room.md` with explicit data-flow facts so that later server reconstruction does not collapse distinct concepts.

## 1. 718 request is gated before serialization

### Code path

```text
IVotingNetwork::sub_A191D0
    -> sub_A17340(this - 48, scope)
        -> sub_A17290(Voter, scope)
    -> only if result == 3:
        Packet ctor(opcode=718)
        write DWORD scope
        write DWORD reason
        write DWORD target_player_id
        send
```

### `sub_A17290`

```c
if ( *(this + 28) == 1 )
    return 0;
if ( *(this + 32) == 1 )
    return 1;

v4 = a2 == 0 && *(this + 36) >= 2;
v3 = a2 == 1 && *(this + 40) >= 2;
if ( v4 || v3 )
    return 3;
return 2;
```

### What is directly established

```text
scope 0 -> candidate/count field +36 must be >= 2
scope 1 -> candidate/count field +40 must be >= 2
+28 == 1 -> request is rejected as already-used/already-entered state
+32 == 1 -> special early return; exact lifecycle meaning remains OPEN
```

Do not hard-code the server rule as only `players >= 3`. The Client first derives candidate/count state and then uses that derived state in the request gate.

The Wiki says Team Kick and Full Kick require at least 3 participants. The Client comparison is `>= 2`, so `+36/+40` must not be mislabeled as raw total room population; its counting domain excludes at least one local/role dimension.

## 2. Scope mapping is behavioral, not merely an enum guess

Client UI has two scope choices. The Wiki names them:

```text
チームキック
全体キック
```

The target-list code uses the same two logical modes and feeds their resulting statistics into the 718 preflight gate. Therefore:

```text
scope=0 -> Team Kick behavior
scope=1 -> Full Kick behavior
```

Confidence: cross-source high. The original internal enum name is still unknown.

## 3. Candidate list and voter eligibility are different sets

`CVoteTargetList::sub_A17450(mode)` rebuilds 36-byte target records.

`sub_A177C0()` walks the player list while excluding the local player and tracks two quantities:

```text
all non-local candidates
candidates that satisfy sub_67DDD0()
```

`sub_67DDD0(slot)`:

```c
if ( slot >= 0x10 )
    return false;
if ( sub_67EB70() )
    return true;
v2 = sub_67D520(slot);
return v2 == sub_67D240();
```

Therefore the candidate eligibility model has at least:

```text
16-slot domain
+ player/session-state comparison
```

`sub_67D520()` and `sub_67D240()` still need to be mapped against the broader player/session subsystem before assigning a more specific semantic name.

## 4. Local duplicate-vote lock is real Client state

`sub_A1A6D0()`:

```c
return *(this + 32) == 1
    && *(this + 29) == 1
    && *(this + 30) == 0;
```

`Voter::sub_A171F0()`:

```c
if ( *(this + 29) == 0 )
    return 0;
*(this + 30) = 1;
return 1;
```

Hence:

```text
+29 = current local voting eligibility/state
+30 = local player has already voted
```

This proves a local second-vote lock for the same voting state. It does NOT prove that the server trusts the client; a compatible server must independently reject duplicate votes.

## 5. 721 and 722 vote byte semantics are closed

721 serializer writes one byte:

```text
+0x00 u8 vote
```

722 parser reads:

```text
+0x00 u32 voter_player_id
+0x04 u8 vote
```

`sub_A1A9D0` increments separate counters:

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

Therefore the Client semantic model is:

```text
0       -> NO / 反對
nonzero -> YES / 贊成
```

The exact permitted wire values beyond 0/1 remain a server-validation question; the Client treats every nonzero value as the YES branch in this local aggregation function.

## 6. 720 fourth DWORD is a millisecond timer

720 parsing order is:

```text
u32 reason
u32 applicant_id
u32 target_id
u32 field3
u8  field4
```

`field3` is passed to `sub_A17130(..., a5)` and becomes the Voter countdown value. `sub_A17380(elapsed)` subtracts elapsed time and clamps to zero.

`VoterMgr::sub_A19940()` then copies the remaining time into the active voting UI.

`CVotingStateUI::sub_A1BF30()` uses:

```c
remaining / 0x3E8u
```

and sends the displayed result to `Vote_Digit`.

Thus:

```text
720 field3 = voting duration / remaining timer
unit = millisecond scale
```

The Wiki states a 70-second voting limit. Consequently a server implementation compatible with the documented behavior should use:

```text
70000 ms
```

This is a Wiki + Client behavioral inference, not a directly recovered `70000` binary literal.

## 7. 3000 ms is not the 70-second voting timeout

The Client has separate `3000`-ms state paths, including:

```c
Voter::sub_A17180:
    *(this + 24) = 3000;

CVotingStateUI result/phase path:
    *(this + 76) = 3000;
```

These belong to local result/approval/UI phases. They must not be confused with the 720 voting-duration DWORD.

## 8. Applicant, voter eligibility, and active UI are independent flags

`sub_A1A830()` stores:

```text
+88 <- applicant == local_player
+91 <- 720 final control byte
+92 <- VotingAble() result
+93 <- active/display-update state
```

This means at least four independent notions exist:

```text
I am the applicant
I am eligible to vote
I have already voted
The active voting UI should be shown/updated
```

A server model that compresses these into `isVoter`, `isOwner`, or one boolean is structurally wrong.

## 9. 719 status is structurally known but semantically open

Parser:

```c
case 719:
    sub_592940(a2, &v21);
    (*(*this + 12))(this, v21);
```

So payload is exactly one byte.

`sub_A19380(int)` has branches for values 0–3 and maps them to different local state/message paths, but the exported C does not yet prove that this function is the concrete implementation of dispatcher vtable slot `+12`.

Therefore:

```text
719 status width = confirmed
719 status enum = OPEN
719 status human meaning = OPEN
```

## 10. 723 result byte must remain unnamed

Parser:

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770()` stores player identity and feeds the result byte into `sub_A17180()`.

This proves the two fields are separate, but it is not sufficient to call result byte `SUCCESS`, `KICKED`, or any other final enum label.

## 11. 396/397 is a separate protocol family

The packet registration table explicitly maps:

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397 is dispatched outside the 718–723 voting dispatcher:

```c
case 397u:
    sub_58E410(a1, a4);
    break;
```

`sub_58E410()` reads one status byte and branches to message/resource paths for 0/default, 1, and 2.

So:

```text
397 payload = u8 status
```

396 request body has not yet been recovered from a direct serializer/caller path.

## 12. Current evidence graph

```text
Wiki
  |
  | mode / reason / 70 sec / min participants / target cannot vote
  v
Client UI
  |
  | scope, reasons, target selection
  v
CVoteTargetList
  |
  | candidate records + player/session eligibility
  v
Voter
  |
  | preflight gate
  v
718
  |
  v
Server
  |
  +--> 719 status
  +--> 720 vote session state
              |
              +--> timer
              +--> local eligibility
              +--> 721 vote
              +<-- 722 voter result
              +--> 723 final result
```

The separate room/master path is:

```text
Room/Master
   |
   +--> 396 PM_KICKUSER_REQ
   +<-- 397 PM_KICKUSER_ACK
```

There is currently no direct evidence that successful 723 automatically constructs 396. That relationship must remain OPEN until the actual call/data-flow is found.

## 13. Server reconstruction implications

The minimum conceptual server state for Kick Vote should therefore separate:

```text
KickVoteSession
  scope
  reason_index
  applicant_player_id
  target_player_id
  duration_ms
  control
  eligible_voter_set
  submitted_votes
  yes_count
  no_count
  started_at
  ended_at
  result_state
```

And separately retain:

```text
Room / Master kick operation
  request body
  requester/master identity
  target identity
  ACK status
```

Do not collapse these into a single `Kick()` operation until the client/server call graph proves they share one protocol/state path.

## 14. Remaining high-value traces

```text
A. 719
   vtable +12
   -> concrete implementation
   -> localization 878/879/880

B. 720 field4
   -> all readers/writers
   -> relationship with +91
   -> target eligibility semantics

C. 723
   -> result byte enum
   -> target state mutation
   -> actual kick/forceout side effect

D. 396
   -> construction caller
   -> serializer body
   -> whether any 723 path reaches it

E. sub_67D520 / sub_67D240
   -> player/session state model
   -> exact candidate/voter eligibility meaning

F. localization/resource store
   -> 0x369 / 0x36A
   -> 0x373..0x379
   -> 0x892 / 0x893
   -> 878 / 879 / 880
```
