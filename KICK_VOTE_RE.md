# PaperMan Kick Vote Reverse-Engineering Notes

> Research snapshot: 2026-09-16
>
> Scope: the in-game kick-vote subsystem visible in the Japanese PaperMan client. This document deliberately separates **direct evidence** from **interpretation** so it can be used safely by both humans and LLMs during server reimplementation.

## Evidence policy

- **[WIKI]** = documented player-facing behavior from the archived PaperMan Wiki.
- **[C]** = directly observed in `PaperMan.exe.c` (Hex-Rays output).
- **[RES]** = extracted client-resource evidence / packaging structure.
- **[X]** = cross-checked by two or more evidence classes.
- **[OPEN]** = plausible interpretation that still needs a stronger proof path.

Hex-Rays output is not source code. Variable names/types can be wrong, and some functions in this region contain explicit `positive sp value` / `variable possibly undefined` warnings. Preserve addresses and raw behavior before renaming or simplifying anything.

---

## 1. Player-facing behavior

The archived Japanese Wiki documents the following:

| Item | Documented behavior | Evidence |
|---|---|---|
| Open kick vote | Press `P` during a game | [WIKI] |
| Modes | Free-for-All, Bomb Mission, Team Survival, Steel, Team Tactical | [WIKI] |
| Disabled modes | Practice and Chat Room | [WIKI] |
| Vote window | 70 seconds | [WIKI] |
| Non-vote | Invalid vote; kick requires all valid votes to agree | [WIKI] |
| Target voting right | Target cannot vote | [WIKI] |
| Scope | Team Kick or Full Kick | [WIKI] |
| Team Kick | Only users in applicant's team can be targeted and vote | [WIKI] |
| Full Kick | All participants can be targeted and vote | [WIKI] |
| Reason count | 6 | [WIKI] + [C] |
| Reason 1 | Cheat behavior | [WIKI] |
| Reason 2 | Gameplay obstruction | [WIKI] |
| Reason 3 | Abuse / harassment | [WIKI] |
| Reason 4 | AFK character | [WIKI] |
| Reason 5 | Abuse / exploit | [WIKI] |
| Reason 6 | Other violation | [WIKI] |
| Target selection | Numeric keys | [WIKI] |
| Target paging | `0` advances page when Full Kick has 9+ participants | [WIKI] + [C, internal key value 10] |
| Per-game request limit | One kick request per game | [WIKI] |
| Minimum size | Team Kick requires 3+ team members; Full Kick requires 3+ participants | [WIKI] |
| Result | Results are sent to the operation team | [WIKI] |

Primary wiki source: `https://wikiwiki.jp/paperman/%E6%93%8D%E4%BD%9C%E3%82%AC%E3%82%A4%E3%83%89`

The vocabulary page separately describes game-time kick as a player-vote system, while waiting-room kick is a room-master authority. Source: `https://wikiwiki.jp/paperman/%E7%94%A8%E8%AA%9E%E9%9B%86/%E3%81%8B%E8%A1%8C`

---

## 2. Input binding: `P` is directly confirmed in the client

The C decomp contains the actual key-setting registration:

```c
sub_71A060(this + 452, User__, L"Kick Vote", L"P", v132);
```

and the corresponding load/update side uses the same logical action name:

```c
sub_71ADA0(this + 904, L"Kick Vote", a2);
```

Address: approximately `0x?` in the exported C around the key-setting subsystem; source line around 30-490 in the semantic search result.

**Conclusion:** [X] Wiki's `P` binding is not merely documentation; the client itself exposes a `Kick Vote` action bound to `P`.

C evidence: `PaperMan.exe.c`, search result containing `L"Kick Vote", L"P"`.

---

## 3. Protocol registration: kick request / acknowledgement

The protocol-registration block contains adjacent kick messages:

```c
v1163 = sub_402060(v0, L"PM_KICKUSER_REQ");
v1162 = sub_9EAF50(v3184, 396, v0[0]);
...
v1160 = sub_402060(v0, L"PM_KICKUSER_ACK");
v1159 = sub_9EAF50(v3181, 397, v0[0]);
```

Thus the registration table establishes:

| Message | Registered ID | Status |
|---|---:|---|
| `PM_KICKUSER_REQ` | **396** | [C] directly observed |
| `PM_KICKUSER_ACK` | **397** | [C] directly observed |

The surrounding registrations are sequential:

- `MASTER_ROOMINFO_REQ` = 394
- `MASTER_ROOMINFO_ACK` = 395
- `PM_KICKUSER_REQ` = 396
- `PM_KICKUSER_ACK` = 397
- `MASTER_SVRCLASS_REQ` = 398
- `MASTER_SVRCLASS_ACK` = 399

### Important protocol caveat

These numbers are **client protocol-registration IDs observed in the constructor/registration table**. Do not yet assume they are the final on-wire opcode bytes/shorts without tracing the packet dispatch/serialization path for these exact message objects.

This distinction matters when rebuilding a server.

C evidence: `PaperMan.exe.c` around lines 675986-676009 in the extracted C representation.

---

## 4. Vote subsystem class structure

The client has a coherent C++ object cluster dedicated to voting:

```text
Voter
└── VoterMgr / IVotingNetwork
    ├── CVoteTargetList
    ├── CVotingTargetUI
    ├── CVotingStateUI
    └── CVotingApprovalUI
```

Observed constructors / vtables:

- `Voter::possible_ctor_or_dtor`
- `IVotingNetwork::possible_ctor_or_dtor`
- `VoterMgr::sub_A19940` etc.
- `CVoteTargetList::sub_A17450`
- `CVotingTargetUI`
- `CVotingStateUI`
- `CVotingApprovalUI`

A setup path allocates:

```c
operator new(8u);     // CVotingApprovalUI
operator new(0xE8u);  // CVotingStateUI
operator new(0x28u);  // CVotingTargetUI
operator new(0x20u);  // CVoteTargetList
```

The target UI is explicitly linked to the target list:

```c
*(*(this + 68) + 28) = *(this + 60);
```

and both state/target UI objects are initialized before the manager enters its initial state.

**Conclusion:** [X] the vote UI is not a single generic popup. It has separate objects for target selection, voting state/approval, and the candidate list.

C evidence: `PaperMan.exe.c` around `0x00A19B10` and associated constructors.

---

## 5. Internal state machine: strongest currently recoverable facts

The `Voter` base stores several state fields. Relevant functions:

### `sub_A17130(this, a2)`

```c
*(this + 31) = 0;
*(this + 44) = 0;
*(this + 24) = 0;
*(this + 20) = a3;
*(this + 29) = a2;
*(this + 32) = 1;
*(this + 30) = 0;
```

### `sub_A17180(this, a2)`

```c
*(this + 44) = a2;
if ( *(this + 8) == *(this + 12) && *(this + 44) == 1 )
    *(this + 24) = 3000;
*(this + 29) = 0;
*(this + 32) = 0;
```

### `sub_A17220(this, a2)` resets a request/session

```c
*(this + 31) = 0;
*(this + 44) = 0;
*(this + 12) = a2;
*(this + 29) = 0;
*(this + 28) = 0;
*(this + 32) = 0;
*(this + 8) = -1;
```

### `sub_A17290(this, a2)` is a key gate

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

### `sub_A17340(this, a2)` starts a valid vote transition

```c
n3 = sub_A17290(this, a2);
if ( n3 != 3 )
    return n3;
*(this + 28) = 1;
return 3;
```

**Strong inference:** the two mode values `a2 = 0` and `a2 = 1` are independently gated by two participant-count fields (`+36` and `+40`), both requiring at least 2 *other* eligible voters before the vote can start.

This aligns with the Wiki's 3-person minimum when the requester is included in the total participant count.

**Do not yet hard-code `a2=0 => Team` / `a2=1 => Full` from this function alone.** The remaining work is to identify the exact caller/vtable path that feeds `a2` into `CVoteTargetList::sub_A17450` and map the corresponding count field to Team vs Full unambiguously.

C evidence: `PaperMan.exe.c`, `0x00A17220` through `0x00A17380`.

---

## 6. Target list: target exclusion and Team/Full mechanics

`CVoteTargetList::sub_A17450(this, a2)` rebuilds the candidate list by enumerating active players.

Core behavior:

```c
v15 = sub_67DE10(0, 1);

if ( sub_67D110() >= 0 )
    v14 = &byte_F33120[240780 * sub_67D110()];

if ( v15 != nullptr && v15 != v14 && a2 == 1 )
    v13 = true;
else if ( a2 == 0 && v15 != v14 )
    v13 = sub_67DDD0(v15);
```

For every accepted candidate it stores at least:

```c
v10 = *(v15 + 3);       // player id
v12 = *(v15 + 60149);   // another player attribute
sub_A178E0(this + 4, &v10);
```

The current local player is explicitly excluded (`v15 != v14`).

### Exact meaning of `sub_67DDD0`

```c
unsigned int n0x10 = (a1 - byte_F33120) / 0x3AC8C;
return n0x10 < 0x10 && sub_67D3F0(n0x10);
```

This proves the filter is derived from the per-player slot/index and a separate predicate `sub_67D3F0`. Nearby code uses `sub_67DDD0` as a discriminator when counting players in the current grouping, but the naming does not prove the semantic label of that group by itself.

### What is definitely established

- [X] the requester is excluded from the target list;
- [X] one target-list mode uses a predicate-based subset (`sub_67DDD0`);
- [X] the other mode includes all non-requesters;
- [X] the list stores player IDs and player-name-related data;
- [X] the implementation has separate total and filtered counts.

### What remains open

`a2 == 0` is **very likely** the same-team target scope and `a2 == 1` the full-room scope because the behavior matches the Wiki exactly, but the final label mapping should be confirmed by tracing the mode-selection UI and the caller that supplies `a2`.

---

## 7. Target-list counts and the 3-player minimum

`CVoteTargetList::sub_A177C0` counts non-requesters and the `sub_67DDD0` subset:

```c
++v5;                 // every non-requester
if ( sub_67DDD0(v4) )
    ++v6;             // filtered subset
```

Then it publishes both counts through its virtual interface:

```c
(*(*this + 4))(this, v6);
(**this)(this, v5);
```

Later `VoterMgr::sub_A19940` copies the two values into manager fields:

```c
*(this + 40) = (*(**(this + 60) + 12))(*(this + 60));
*(this + 36) = (*(**(this + 60) + 8))(*(this + 60));
```

Combined with `sub_A17290` requiring either `+36 >= 2` or `+40 >= 2`, this gives a clean native-side explanation for the Wiki minimum of 3 total participants.

**[X] This is one of the strongest Wiki ↔ C correlations currently recovered.**

---

## 8. Exactly 6 kick reasons is independently visible in code

The Wiki lists six kick reasons. The input handler for one vote-selection state contains an explicit six-item bound:

```c
v16 = n10 - 1;
v15[1] = 6;
if ( n10 - 1 >= 6 || sub_A19090(this, v16) != 0 )
    return 1;
```

The state/UI side also labels the displayed value as:

```c
L"1_TARGET_VOTING_REASON"
```

and later stores the chosen reason index in the voting-state UI.

**[X] The six-option count is not just a Wiki artifact; the client logic enforces a six-entry range.**

The exact semantic mapping of reason index `0..5` to the six Japanese Wiki labels should still be treated as a resource/localization extraction task rather than assumed from order alone.

---

## 9. Target UI: 8 users per page + page advance control

The vote input handler has a dedicated target-selection state (`n2 == 2`). It accepts target numbers `1..8`:

```c
if ( n10 <= 0 || n10 >= 9 ) {
    if ( n10 == 10 ) {
        ... page handling ...
    }
}
else {
    v13 = 8 * v9;
    if ( sub_A1ACA0(*(this + 60), v13 + n10 - 1, ...) != 0 ) {
        ... select target ...
    }
}
```

This matches the Wiki's observation that the full-target UI becomes pageable once there are 9 or more participants.

The C input representation uses internal numeric value **10** for the page action. The Wiki explicitly documents the visible key as **`0`**.

**[X] Safe interpretation:** `n10 == 10` is the internal input value corresponding to the Wiki's `0` page key. Keep both values documented until the generic keyboard-translation function is recovered.

The paging test itself is also explicit:

```c
if ( *(v6 + 24) == 0 && sub_A1AE00(v6) > 8 )
    ...
```

So the client-side target-page model is directly consistent with an 8-entry page.

---

## 10. Target-list indexing / storage layout

`sub_A1ACA0` validates the requested index against the list length and then copies both the target's player-name data and player identifier:

```c
sub_402920(a4, (*(this + 5) + 36 * a2 + 4), 0, 0xFFFFFFFF);
*a3 = *(36 * a2 + *(this + 5));
```

Therefore the target-entry stride is **36 bytes** at the logical list-storage level.

`sub_A17700` separately resolves a player ID back to a wide string name using the active-player table.

This is useful for a server-side implementation because the client does not appear to require a rich target object for the selection protocol; a stable player ID plus the selected reason/mode is enough to describe the conceptual operation.

---

## 11. Voting / approval UI state

Three distinct UI classes are visible in the object graph:

```text
CVotingTargetUI      -> target selection
CVotingStateUI       -> current vote state/countdown/text
CVotingApprovalUI    -> yes/no approval input
```

`CVotingStateUI::sub_A1B0A0` builds UI strings using localization entries `0x367`, `0x368`, etc., and inserts data under keys such as:

- `1_TARGET_VOTING_REASON`
- `2_APPLICANT_USER_NAME`
- `2_TARGET_NICK`
- `2_REASON`

`CVotingStateUI::sub_A1BF30` also uses runtime UI assets/controls named:

- `Vote_Digit`
- `TargetUserVotingUI`
- `VoterState`
- `VotingStatePos`
- `VotingAble`

and renders the remaining vote time when the state is appropriate.

One state field is initialized to `3000`, which is consistent with an internal millisecond-style timer, but **do not equate `3000` directly with the Wiki's 70-second public vote duration**. The relationship between this timer and the network-updated countdown has not yet been fully traced.

---

## 12. UI input state machine

`sub_A1A090(this, n10)` dispatches numeric input according to internal UI state.

Observed branches:

- `n2 == 0`: a small two-option state;
- `n2 == 1`: a six-entry state;
- `n2 == 2`: target-selection state with 8 entries per page and a page action value of 10.

This is an unusually strong structural match for the documented UI flow:

```text
Kick mode selection
    -> reason selection (6)
    -> target selection (8/page)
    -> voting
```

The mode-selection labels themselves still need a direct resource/string extraction pass before renaming `n2` values in code.

---

## 13. Vote-state transitions and network hooks

`IVotingNetwork::sub_A191D0(this, a2, a3, a4)` only sends after:

```c
if ( sub_A17340(this - 48, a2) != 3 )
    return 0;
```

It then creates a packet with constructor ID **718** and serializes three values:

```c
Packet::possible_ctor_or_dtor_0(v7, 718);
v4 = sub_592A20(v7, a2);
v5 = sub_592A20(v4, a3);
sub_592A20(v5, a4);
sub_58D7D0(byte_13242F8, v7);
```

This strongly suggests a vote-network message containing three scalar fields, but the corresponding protocol string / registration entry has **not yet been unambiguously mapped**.

`IVotingNetwork::sub_A192B0(this, a2)` creates packet constructor ID **721**, writes one byte-like field, and sends it:

```c
Packet::possible_ctor_or_dtor_0(v5, 721);
sub_5928E0(v5, a2);
sub_58D7D0(byte_13242F8, v5);
```

These are likely vote-session state messages, but remain **[OPEN]** until the packet registration table and receive handlers are connected to them.

---

## 14. Vote result accounting

`sub_A1A9D0(this, a2, a3)` updates separate counters depending on the answer value:

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    this = ++*(this + 21);
```

It then forwards the result through a virtual call:

```c
return (*(*this_1 + 24))(this_1, a3, this);
```

This is direct evidence that the client tracks positive and negative vote totals separately.

What is not yet proven from this function alone is whether those two counters are exactly the `yes/no` totals in the final server decision, or an intermediate UI/network accounting layer.

---

## 15. Candidate activity predicate and team discrimination

`sub_67DDD0` maps a player object to a 0..15 slot and calls `sub_67D3F0(slot)`.

Nearby generic gameplay code uses this predicate to split active players into two populations:

```c
if ( sub_67DDD0(v25) )
    ++n2;
else
    ++n2_1;
```

This is consistent with a team/group discriminator, and the vote target list reuses exactly the same predicate. That reuse is important evidence that the vote subsystem is selecting by the client's authoritative player grouping rather than performing a second ad-hoc team calculation.

The exact meaning of `sub_67D3F0` remains an open RE target.

---

## 16. Resource-side cross-check

The extracted client-data manifest confirms that UI data is a first-class extracted resource group:

```xml
<List>
    <DataList key="BulletHole" />
    <DataList key="effect" />
    <DataList key="ui" />
    <DataList key="ui_temp" />
    ...
</List>
```

The pack manifest also maps multiple client archives into the extracted tree, including `pmClient.dat` and the `ui` resource area.

Sources:

- `Extracted/ClientDataList.xml`
- `Extracted/0.xml`

### Important resource limitation

The current extracted `ui` filename set does **not yet expose a standalone `Kick.xml` / `Voting.xml` file**. Therefore the vote-specific UI labels seen in C (`VoterState`, `VotingAble`, `TargetUserVotingUI`, `Vote_Digit`, and `1_TARGET_VOTING_REASON`) should **not** be falsely reported as having been independently confirmed from a dedicated extracted XML file.

The resource evidence currently proves the packaging/extraction relationship and the existence of a dedicated UI data domain; the precise vote-widget definition still needs a resource-level search inside the relevant `.pat` / packed client resources or a more complete extraction.

This is intentionally marked [OPEN] rather than promoted to [X].

---

## 17. Current triple-source confidence map

### Confirmed by Wiki + C

- `P` opens kick voting.
- There are 6 reason choices.
- Target requester is excluded.
- Target selection uses numeric input.
- Target UI is paged at 8 entries.
- The vote subsystem has separate target/state/approval UI layers.
- There are two distinct candidate-population modes.
- Minimum eligible-voter logic is consistent with the documented 3-person minimum.
- Kick request / acknowledgement protocol names exist in the client, with registration IDs 396/397.

### Confirmed by C only so far

- Internal state fields and transitions described above.
- Packet constructor IDs 718 and 721 in vote-network functions.
- 36-byte target-list entry stride.
- Positive/negative vote accounting counters.
- Localization/UI object keys and runtime widget names.

### Resource + C, but not yet vote-specific resource XML confirmation

- UI is loaded from a dedicated extracted resource domain.
- `pmClient.dat` / `ui` are part of the extracted client-data packaging.
- Vote UI text/assets appear to be fetched indirectly through the client's localization/resource system.

### Still open and should not be hard-coded from current evidence

1. `a2=0` vs `a2=1`: exact Team Kick / Full Kick label mapping.
2. Exact wire serialization of `PM_KICKUSER_REQ` / `_ACK` beyond registration IDs 396/397.
3. Exact field layout of the kick request packet.
4. Exact meaning of packet constructors 718 and 721.
5. Exact localization index mapping for the six reason codes.
6. Exact server-side decision state machine and when the 70-second timer is created/updated.
7. Exact mapping between internal key value `10` and physical `0` through the generic keyboard translation layer.
8. Exact team predicate implementation inside `sub_67D3F0`.
9. Direct resource-file definition of the voting widgets.

---

## 18. Recommended next RE pass

Do **not** start implementing the server packet solely from the Wiki. The next evidence pass should trace these exact edges:

```text
P input
  -> Kick Vote action handler
  -> mode selection value (a2)
  -> CVoteTargetList::sub_A17450
  -> target id + reason
  -> PM_KICKUSER_REQ (396)
  -> receive/update handlers
  -> vote yes/no accounting
  -> PM_KICKUSER_ACK (397)
  -> final kick decision
```

Priority symbols/functions:

- `sub_A17290`
- `sub_A17340`
- `sub_A17450`
- `sub_A177C0`
- `sub_A17880`
- `sub_A19060`
- `sub_A19090`
- `sub_A191D0`
- `sub_A192B0`
- `sub_A19460`
- `sub_A19770`
- `sub_A19890`
- `sub_A1A090`
- `sub_A1A830`
- `sub_A1A970`
- `sub_A1A9D0`
- `sub_A1ACA0`
- `sub_A1AE00`
- `sub_67DDD0`
- `sub_67D3F0`

For each, record:

1. callers / xrefs;
2. argument provenance;
3. state-field writes;
4. packet constructor ID;
5. exact serializer order and type;
6. corresponding receive/ACK path;
7. corresponding resource/localization key.

Only after this chain is closed should the server-side packet schema be considered protocol-verified.

---

## Sources

- Japanese PaperMan Wiki — 操作ガイド: `https://wikiwiki.jp/paperman/操作ガイド`
- Japanese PaperMan Wiki — 用語集/か行: `https://wikiwiki.jp/paperman/用語集/か行`
- Repository: `PaperMan.exe`
- Repository: `PaperMan.exe.c`
- Repository: `Extracted/0.xml`
- Repository: `Extracted/ClientDataList.xml`
