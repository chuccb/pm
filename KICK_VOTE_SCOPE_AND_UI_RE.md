# PaperMan Kick Vote — Scope / UI / Eligibility Cross-Validation

> Research snapshot: **2026-09-16**
>
> Supplemental to `KICK_VOTE_PROTOCOL_RE.md` and `KICK_VOTE_UI_AND_TIMER_RE.md`.

## 1. Client target-selection states map directly to the public Kick Vote workflow

`CVotingTargetUI::sub_A1C2E0` renders three distinct input states from `*(this + 20)`:

```text
state 0: exactly 2 options
state 1: exactly 6 options
state 2: target list, up to 8 visible entries + optional 0. page control
```

[C] In state 0 it loads resource IDs `892` and `893` and formats them as:

```text
1. <resource 892>
2. <resource 893>
```

[C] The manager's input state `n2 == 0` accepts exactly two choices (`n10-1 < 2`) and stores that value as the voting scope. Therefore the two resource entries are the two Kick Vote scope choices, not yes/no answers.

[X] Combined with the Japanese Wiki's two public scopes, the structural mapping is:

```text
scope 0 -> UI option 1 -> Team Kick
scope 1 -> UI option 2 -> Full Kick
```

The exact Japanese localized text behind resources `892/893` remains unextracted.

---

## 2. The six public reasons have an explicit client-side resource table

[C] In state 1, the client loops `i = 0..5`, loads `resource = i + 883`, and formats:

```text
1. resource 883
2. resource 884
3. resource 885
4. resource 886
5. resource 887
6. resource 888
```

The manager's reason-selection path independently enforces a maximum of 6 values (`0..5`).

[X] The Japanese Wiki independently documents exactly six Kick Vote reasons.

A later voting-state display path also uses a second six-entry resource table `373..378`, indexed by the same reason index. This means the client has separate localization/UI entries for selecting a reason and displaying the selected reason during the active voting state.

Do not assume `883 == 373` etc.; the binary proves two separate resource-key sets, not equality of their text.

---

## 3. Approval voting is a separate UI stage

[C] `CVotingApprovalUI::sub_A18B90` loads resources `0x369` and `0x36A`, then formats them as `1. %s` and `2. %s`.

[C] The actual vote packet `721` is one byte, and the vote-accounting routine increments the YES/approval counter for any nonzero value and the NO/rejection counter for zero.

Therefore the flow is structurally:

```text
Scope selection
    -> Reason selection
        -> Target selection
            -> Start vote (718)
                -> Approval choice (721)
```

The `369/36A` resources must not be confused with the `892/893` scope resources.

---

## 4. 720 field 4 is a scope-sensitive eligibility gate

`IVotingNetwork::sub_A19460` receives the final byte of packet 720 as `a6` and stores it at the Voter object before deciding the UI-state permission value.

The relevant shape is:

```c
*(this - 32) = a6;
*(this - 40) = applicant_id;
...
v25 = 1;
if (*(this - 32) == 0)
    v25 = targetListVirtualSlot28(applicant_id);
```

The VoterMgr constructor proves that `this + 60` is the `CVoteTargetList` object, and the voting UI is separately stored at `this + 68`. Thus this call is on the target-list subsystem rather than a generic unrelated user-info object.

The resulting `v25` is later passed into `sub_A1A830(..., a7=v25)`, where it becomes VotingStateUI `+91`.

This makes the strongest current interpretation:

```text
720 field 4 = server-provided scope/eligibility control

field4 == 0:
    ask the target-list/team eligibility mechanism about applicant

field4 != 0:
    treat eligibility as already satisfied
```

[X] This aligns closely with 718 scope polarity and the Wiki distinction between Team Kick and Full Kick.

**Current confidence:** high for “scope-sensitive eligibility gate”; high-but-inferred for `0 = Team`, `1 = Full`; still OPEN for the original symbol/enum name and the exact virtual method implementing the `field4 == 0` check.

---

## 5. `VotingAble` is not a generic UI toggle; it reflects whether this client can still cast its vote

`VoterMgr::sub_A19940` performs:

```c
sub_A17380(this, elapsed_ms);
stateUI->timer = voter->duration;
stateUI->VotingAble = sub_A1A6D0(this);
stateUI->active = ...;
```

`sub_A1A6D0` is:

```c
return *(this + 32) == 1
    && *(this + 29) == 1
    && *(this + 30) == 0;
```

And the state transitions show:

```text
+29 = voting-eligibility/state set when vote session starts
+30 = set to 1 by sub_A171F0 after this voter casts a vote
```

Therefore `[C][X]` UI `+92` (“VotingAble”) means approximately:

```text
this local participant is in the active voting state
AND has not yet cast their vote
AND the state allows voting
```

Once the local user successfully selects an approval vote, `sub_A171F0` sets `+30 = 1`, making `sub_A1A6D0` false and removing the `VotingAble` UI.

This gives a strong client-side proof that repeated local voting is blocked by state, independently of the server's validation.

---

## 6. Local applicant UI role is independent from field 4

The 720 handler eventually calls:

```c
sub_A1A830(
    stateUI,
    reason,
    targetName,
    applicantName,
    duration,
    applicant_id == local_player_id,
    v25);
```

`sub_A1A830` stores its sixth argument into UI `+88`, while its seventh argument becomes UI `+91`.

So the client distinguishes:

```text
UI +88 = “I am the applicant” role
UI +91 = eligibility/display result derived from 720 field4
```

This distinction is important when recreating the server protocol because a client receiving 720 does not simply copy all five fields into a presentation object.

---

## 7. Target selection and the 9+ participant rule are byte-for-byte structurally aligned

[C] Target UI displays at most eight target entries per page.

[C] It adds resource `0x379` as a `0. %s` page control when `sub_A1AE00(this) > 8`.

[C] The input handler recognizes internal action value `10` for that page control and changes the page state.

[WIKI] The Japanese guide says the physical `0` key advances the target list when a Full Kick target list reaches 9 or more participants.

[X] This is one of the clearest Wiki ↔ C ↔ resource matches in the Kick Vote subsystem.

---

## 8. 3-player minimum is encoded as requester-excluded target counts

`CVoteTargetList::sub_A177C0` counts only users for whom:

```c
v4 != nullptr && v4 != local_requester
```

The Voter's scope eligibility test later requires at least two such users:

```c
a2 == 0 && targetListCountFiltered >= 2
or
a2 == 1 && targetListCountAll >= 2
```

Thus:

```text
requester (1)
+ at least 2 other eligible users
= at least 3 participants
```

[X] This exactly explains the Wiki's minimum of 3 for both Team Kick and Full Kick, while retaining the distinction between filtered/team count and all-participant count.

---

## 9. Practical protocol implications

For a server implementation intended to reproduce this client:

```text
718 request:
  scope = 0 or 1
  reason = 0..5
  target = player_id

720 broadcast:
  reason = same reason index
  applicant = requester player_id
  target = selected target player_id
  duration_ms = server-supplied countdown duration
  field4 = scope-sensitive eligibility mode/control

721 client vote:
  0 = no
  nonzero = yes

722 broadcast:
  voter player_id
  vote byte

723 end/result:
  result/status byte
  player_id
```

For the documented Japanese service behavior, the public scope interpretation remains:

```text
0 = Team Kick
1 = Full Kick
```

with high behavioral confidence, but the original internal symbolic enum name is not recovered.

---

## 10. Evidence gaps deliberately not filled

The following are still not asserted as facts:

- The literal Japanese text behind resources `892`, `893`, `883..888`, `369`, `36A`, `373..378`, `379`.
- Exact `719` status enum names for values `0..3`.
- Exact `723` result enum names.
- Exact virtual method behind `CVoteTargetList` vtable slot used by 720 field 4.
- Exact server-side decision algorithm for timeout/no-vote completion.
- Exact packet body of the separately registered `PM_KICKUSER_REQ (396)` / `PM_KICKUSER_ACK (397)` messages.

These remain explicit RE gaps rather than being filled with plausible but unsupported names.

---

## 11. Primary C anchors

- `CVoteTargetUI::sub_A1C2E0` around `0x00A1C2E0`: resources `892/893`, `883..888`, `379` and their displayed numeric choices.
- `VoterMgr::sub_A19940` around `0x00A19940`: timer propagation and `VotingAble` derivation.
- `sub_A1A6D0` around `0x00A1A6D0`: local voting-ability predicate.
- `Voter::sub_A171F0` around `0x00A171F0`: marks local vote as submitted.
- `IVotingNetwork::sub_A19460` around `0x00A19460`: 720 field ordering and eligibility gate.
- `CVotingApprovalUI::sub_A18B90` around `0x00A18B90`: approval resources `369/36A`.
- `CVoteTargetList::sub_A17450` / `sub_A177C0`: target filtering and requester-excluded counts.
