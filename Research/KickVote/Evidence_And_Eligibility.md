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

`sub_A17340()` is not a pure query: if the preflight succeeds it sets `+28 = 1` before the request is serialized. Therefore `+28` is a request/active-lock-like state, but its exact original semantic name remains OPEN.

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
u32 duration
u8  control
```

`duration` is passed to `sub_A17130(..., duration)` and becomes the Voter countdown value. `sub_A17380(elapsed)` subtracts elapsed time and clamps to zero.

`VoterMgr::sub_A19940()` then copies the remaining time into the active voting UI.

The UI converts the remaining value with `/ 0x3E8u` before feeding the displayed value to `Vote_Digit`.

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

## 7. 720 final byte gates an applicant predicate; it is not copied to StateUI +91

Direct `sub_A19460()` flow:

```c
*(this - 32) = field4;
v25 = 1;
if ( *(this - 32) == 0 )
{
    v18 = *(this - 40); // applicant id
    v25 = (*(**(this + 12) + 28))(*(this + 12), v18);
}
```

Then:

```c
sub_A1A830(
    StateUI,
    reason,
    target_display,
    applicant_display,
    duration,
    applicant == local_player,
    v25
);
```

`sub_A1A830()` stores the final argument in `CVotingStateUI +91`.

Therefore the corrected model is:

```text
720 field4 == 0
    -> execute applicant-id eligibility/predicate virtual call
    -> v25 = predicate result

720 field4 != 0
    -> skip predicate
    -> v25 stays 1

StateUI +91
    -> v25 predicate result
```

This explicitly corrects the previous false mapping:

```text
OLD / WRONG: StateUI +91 <- 720 field4
NEW / VERIFIED: 720 field4 -> predicate gate; StateUI +91 <- predicate result
```

Exact server-side meaning and allowed values of field4 remain OPEN.

## 8. Applicant identity, voter eligibility, and UI state are independent

`sub_A1A830()` stores:

```text
+88 <- applicant == local_player
+91 <- applicant predicate result (v25)
```

Separately, `VoterMgr::sub_A19940()` updates:

```text
StateUI +92 <- sub_A1A6D0()     // local voting-able state
StateUI +93 <- active/display-update condition
```

Therefore the Client contains distinct notions for:

```text
I am the applicant
Applicant/target-related predicate result
I am currently able to vote
I have already voted
The active voting UI is being updated
```

A server model should not compress these into one boolean.

## 9. 719 concrete dispatch is now high confidence

Parser:

```c
case 719:
    sub_592940(a2, &v21);
    (*(*this + 12))(this, v21);
```

The same `IVotingNetwork` concrete class defines:

```c
IVotingNetwork::sub_A19380(int status)
```

with:

```text
0 -> clear UI pulse/state, retain active-flow marker
1 -> message 878, retain active-flow marker
2 -> message 880
3 -> message 879
```

Its one-argument shape matches the 719 virtual call and it is part of the same IVotingNetwork/VoterMgr implementation region. Therefore:

```text
719 -> sub_A19380
```

is now **high confidence** as the concrete dispatch mapping.

What remains OPEN is not the target function, but the product-level enum names for `0..3` and the exact localization meaning of 878/879/880.

## 10. 3000 ms is not the 70-second voting timeout

The Client has separate `3000`-ms state paths, including:

```c
Voter::sub_A17180:
    *(this + 24) = 3000;

CVotingStateUI result/phase path:
    *(this + 76) = 3000;
```

These belong to local result/approval/UI phases. They must not be confused with the 720 voting-duration DWORD.

## 11. 723 result byte must remain unnamed

Parser:

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770()`:

```text
store player identity
feed result byte to sub_A17180()
```

`sub_A17180()` stores the result byte, clears active voting state, and for the local-target + result==1 condition starts the separate 3000ms Voter phase.

After that, `sub_A19770()` performs a player-side lookup; only if the lookup succeeds does it invoke `sub_A1A970()` for result presentation, followed by `sub_A18F80(..., 0)` for voting UI cleanup.

This proves a result/UI transition chain, but not a direct room occupancy mutation.

Therefore:

```text
723 final result -> Voter result state -> optional result UI -> cleanup
```

The result enum and final server action remain OPEN.

## 12. 139 is a voting lifecycle/control packet but its exact semantic is open

`VoterMgr::sub_A19A70()` builds opcode 139, sends it, then sets:

```c
byte_2317C68 = 1;
```

`sub_A17380()` checks this byte before continuing a particular result/phase countdown update.

Therefore 139 belongs to the voting lifecycle/control path, but the current Client evidence is insufficient to name it as `END_VOTE`, `CANCEL_VOTE`, or another literal enum.

## 13. 396/397 is a separate Master/Room protocol family

The registration/dispatcher family is:

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397 is dispatched by a different handler:

```c
case 397u:
    sub_58E410(a1, a4);
```

`sub_58E410()` reads exactly one status byte and branches on `0/1/2/default` to different message/resource paths.

Therefore:

```text
397 payload = u8 status
```

The Client export still contains no direct serializer proof for 396, so its request body remains unknown.

There is also no evidence in the 723→`sub_A19770` chain that it constructs 396 directly.

## 14. Current evidence graph

```text
Wiki
  |
  | mode / reasons / 70 sec / min participants
  v
Client UI
  |
  | scope / reason / target selection
  v
CVoteTargetList
  |
  | candidate records + player/session eligibility
  v
Voter
  |
  | request preflight + active-vote state
  v
718
  |
  v
Server
  |
  +--> 719 status
  +--> 720 reason/applicant/target/duration/control
           |
           +--> applicant predicate gate
           +--> timer / UI state
           +--> 721 vote
           +<-- 722 voter result
           +--> 723 final result
                    |
                    +--> Voter result state
                    +--> UI result/cleanup
                    +--> [actual kick/removal unresolved]

Separate:
Room/Master
   |
   +--> 396 PM_KICKUSER_REQ
   +<-- 397 PM_KICKUSER_ACK
```

## 15. Server reconstruction implications

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

## 16. Remaining high-value traces

```text
A. 719
   localization 878/879/880
   -> exact user-visible status semantics

B. 720 field4
   -> server-originating construction
   -> all possible values
   -> concrete virtual predicate at this+12

C. 723
   -> result enum
   -> downstream target state mutation outside voting subsystem
   -> actual kick/forceout side effect

D. 396
   -> construction caller
   -> request body
   -> relationship, if any, to final vote action

E. sub_67D520 / sub_67D240
   -> exact player/session state comparison
   -> candidate/voter eligibility meaning

F. localization/resource store
   -> 878 / 879 / 880
   -> 892 / 893
   -> 0x369 / 0x36A
   -> 0x373..0x379
