# PaperMan Kick Vote — UI / Timer / Localization Reconstruction

> Research snapshot: **2026-09-16**
>
> This is a supplemental note to `KICK_VOTE_PROTOCOL_RE.md`. It records discoveries that become important when reproducing the Japanese client behavior exactly, especially the relationship between the 720 packet, the local countdown UI, and the localization/resource table.

## Evidence legend

- **[C]** — directly observed in the Hex-Rays `PaperMan.exe.c` export.
- **[WIKI]** — Japanese PaperMan Wiki behavior.
- **[RES]** — extracted resource-tree / resource evidence.
- **[X]** — cross-validated by multiple evidence paths.
- **[OPEN]** — still insufficiently proven; do not hard-code its semantic name.

---

## 1. 720 field 3 is a millisecond countdown duration

The server-to-client packet `GR_START_VOTING (720)` is parsed as:

```text
u32 reason
u32 applicant_player_id
u32 target_player_id
u32 field3
u8  field4
```

The fourth field (`field3`) is passed as `a5` into `IVotingNetwork::sub_A19460`, then into:

```c
sub_A17130(this - 48, v7, a5);
```

`sub_A17130` stores its third argument in the Voter object's `+20` field:

```c
*(this + 20) = a3;
```

The timer tick routine `sub_A17380` subtracts elapsed milliseconds from that field and clamps at zero:

```c
if ( *(this + 5) < a2 )
    v4 = 0;
else
    v4 = *(this + 5) - a2;
*(this + 5) = v4;
```

Because the `this + 5` DWORD corresponds to the Voter's `+20` byte offset, this is the same duration field initialized from packet 720.

The state/UI update path then copies the remaining value into the voting-state UI's `+68`, and `CVotingStateUI::sub_A1BF30` renders:

```c
*(this + 68) / 0x3E8u
```

through the resource/object named `Vote_Digit`.

### Consequence

**720 field 3 is not a generic opaque integer. It is a millisecond countdown/duration used directly by the voting UI. [X]**

This is particularly important for a compatible server: the value is transmitted by the server and consumed as milliseconds by the client.

---

## 2. Wiki 70-second rule + client millisecond timer

The Japanese Wiki states that an active kick vote has a **70-second** limit, and users who do not vote within that limit produce an invalid/non-vote. citeturn762823search0

The client independently proves that the 720 fourth field is a millisecond countdown.

Therefore the protocol-compatible value that naturally corresponds to the documented 70-second public rule is:

```text
70 seconds = 70,000 milliseconds = 0x11170
```

### Evidence classification

- **70 seconds:** [WIKI], directly documented. citeturn762823search0
- **milliseconds:** [C], directly proven by subtraction plus `/1000` display.
- **720 field 3 carries the duration:** [X], direct data flow.
- **The exact literal `70000` inside the decompiled client:** **not proven**. A search of the relevant C region did not expose a `70000`/`0x11170` constant.

Thus `70000` is the **strong cross-source expected value for a compatible server**, not a literal recovered from the client binary.

Do not incorrectly replace the 720 field with a local hard-coded `3000`: the client contains separate 3000-ms local UI/state timers that are unrelated to the public 70-second voting period.

---

## 3. The 3000-ms values are separate from the 70-second vote window

There are at least two distinct local 3000-ms assignments in the voting code.

### 3.1 Post-result/local-target timer

`sub_A17180` does:

```c
*(this + 44) = a2;
if ( *(this + 8) == *(this + 12) && *(this + 44) == 1 )
    *(this + 24) = 3000;
```

This field is only set to 3000 under the local-target + result-byte condition.

### 3.2 VotingStateUI display timer

`CVotingStateUI::sub_A1B900` begins with:

```c
*(this + 76) = 3000;
sub_A1BEF0(this, 2);
```

This is a UI/message-state timer, not the duration received in 720.

### Rule for server reconstruction

Never infer `3000 ms = vote duration`. The actual vote-window duration enters through 720 field 3 and is processed separately.

---

## 4. Exact localization/resource indices discovered in the voting UI

The C code resolves a group of localization entries through `sub_408080`.

### 4.1 YES/NO choices

`CVotingApprovalUI::sub_A18B90` loads two resource IDs:

```c
ArgList = sub_408080(v3, 0x369u);
v8      = sub_408080(v4, 0x36Au);
```

and then formats them literally as:

```c
Source   = sub_401A60(L"1. %s", ArgList);
Source_1 = sub_401A60(L"2. %s", v8);
```

So:

```text
resource 0x369 -> approval choice 1
resource 0x36A -> approval choice 2
```

The surrounding voter code sends vote values as a single byte and the accounting code treats nonzero as the YES/approval count and zero as the NO/rejection count. Therefore the UI's two textual choices correspond to the two wire-level vote values, although the exact Japanese text itself should still be read from the localized resource rather than guessed from the numeric index.

### 4.2 Six kick-reason resources

`CVotingStateUI` loads:

```text
0x373 -> v47[0]
0x374 -> v47[1]
0x375 -> v47[2]
0x376 -> v47[3]
0x377 -> v47[4]
0x378 -> v47[5]
```

Then the reason index selects `v47[index]` with the client restricting the reason domain to `0..5`.

Therefore the mapping is now structurally proven:

```text
reason 0 -> resource 0x373
reason 1 -> resource 0x374
reason 2 -> resource 0x375
reason 3 -> resource 0x376
reason 4 -> resource 0x377
reason 5 -> resource 0x378
```

The Japanese Wiki independently lists exactly six public kick reasons. citeturn762823search0

**Still open:** the actual localized Japanese strings behind resource IDs `0x373..0x378` have not yet been extracted from the localization store, so do not claim a byte-for-byte text mapping from ID order alone.

### 4.3 Page-advance label

Resource `0x379` is loaded separately and formatted as:

```c
Source_2 = sub_401A60(L"0. %s", v9);
```

It is displayed only when:

```c
if ( sub_A1AE00(this) > 8 )
```

So `0x379` is the **target-list page-advance / `0.` choice**, not one of the six kick reasons.

This matches the Wiki's physical `0` key page-advance behavior when the target list exceeds one screen. citeturn762823search0

---

## 5. Voting-state UI visibility is controlled by several independent flags

`CVotingStateUI::sub_A1BF30` contains a useful distinction that prevents a common reverse-engineering mistake:

```c
if ( *(this + 93) != 0 )
{
    if ( *(this + 91) == 1 && *(this + 88) == 0 )
        draw remaining time;

    if ( *(this + 91) != 0 )
    {
        if ( *(this + 88) != 0 )
            use "TargetUserVotingUI";
        else
            use "VoterState";

        install at "VotingStatePos";
    }

    if ( *(this + 92) != 0 )
        install "VotingAble";
}
```

This establishes at least three distinct concepts:

```text
+88 = local-client/applicant-or-target-side UI role
+91 = voting-state/UI eligibility/display flag
+92 = whether the VotingAble UI is enabled
+93 = whether the voting-state UI update is active
```

The important point is that these are **not interchangeable**.

In particular, `+88` is set from:

```c
*(this - 40) == *(this - 36)
```

inside the 720 handler, so it represents the local-player relation to the applicant. It is not the raw 720 field 4.

The raw 720 byte is stored earlier as `this-32`, and when it is zero the client invokes a user-info provider predicate to derive `v25`; that derived value becomes UI `+91`.

Therefore:

```text
720 field4 != UI +88
720 field4 -> eligibility/permission derivation -> UI +91
720 applicant_id == local_id -> UI +88
```

The exact public semantic name of 720 field4 remains **OPEN**.

---

## 6. 719 status handling: strong candidate, but keep virtual-slot provenance

The receive dispatcher parses 719 as exactly one byte and calls a virtual method with one integer/byte-like argument.

`IVotingNetwork::sub_A19380(int a2)` is a very strong semantic candidate for this handler because it is in the same protocol cluster and consumes one status-like value:

```c
if ( *(this - 20) == 0 )
    return 0;

sub_A1A680(0);
*(this - 20) = 0;

switch ( a2 )
{
    case 0:
        *(this - 20) = 1;
        return 1;
    case 1:
        ui->message(878);
        *(this - 20) = 1;
        ...
    case 2:
        ui->message(880);
        ...
    case 3:
        ui->message(879);
        ...
}
```

However, the decompiler export does not expose the `VoterMgr` vtable as a directly readable function-pointer array here. Therefore the safe statement is:

```text
719 payload = u8 status/value [C]
sub_A19380 is a highly plausible handler for that status [OPEN]
status values 0..3 have distinct client-side reactions [C]
exact public meaning of 0/1/2/3 [OPEN]
```

Do not label these as `SUCCESS`, `ALREADY_VOTING`, `DENIED`, etc. until the virtual-slot mapping or localization/error path is proven.

---

## 7. 723 result byte remains deliberately unresolved

`GR_END_RESULT (723)` is parsed as:

```text
u8 value
u32 player_id
```

and the handler forwards the first byte into `sub_A17180`.

`sub_A17180` stores it at the Voter's `+44`, then treats value `1` specially when the local player is the selected target by starting a separate 3000-ms state timer.

This proves that byte `1` has a special end-state meaning for the local target path, but it does **not** yet prove that the byte means simply `KICKED=1` or `SUCCESS=1` globally.

Keep the wire field name as:

```text
GR_END_RESULT.value : u8
```

until more server-side/virtual-call evidence is recovered.

---

## 8. Why the Wiki's "invalid/no vote" rule matters to protocol implementation

The Wiki says a participant who does not submit a vote within 70 seconds contributes an invalid vote, and a kick occurs only when all valid votes agree to the kick; one opposing vote prevents the kick. citeturn762823search0

The client-side packet evidence establishes only the per-voter vote notification (`722`) and local yes/no counters; it does **not** by itself prove that the client is authoritative for the final kick decision.

For server reconstruction, therefore, treat:

```text
721 = individual vote submission
722 = server broadcast/notification of an individual voter's vote
723 = server-side end/result notification
```

and make the final kick decision server-authoritative unless later evidence proves otherwise.

This is also consistent with the architectural role implied by the server-to-client 720/722/723 messages: the client maintains presentation state while the server distributes the vote lifecycle.

---

## 9. Current implementation-grade model

For a compatible PaperMan server, the currently justified model is:

```text
Client -> Server
  718
    u32 scope
    u32 reason_index
    u32 target_player_id

Server -> Clients
  719
    u8 start_request_status

  720
    u32 reason_index
    u32 applicant_player_id
    u32 target_player_id
    u32 vote_duration_ms
    u8  eligibility/control_byte   // semantic name OPEN

Client -> Server
  721
    u8 vote

Server -> Clients
  722
    u32 voter_player_id
    u8 vote

  723
    u8 end_result_value            // semantic enum OPEN
    u32 player_id
```

For the documented Japanese client behavior:

```text
vote_duration_ms = 70000   // strongly expected from Wiki 70 s + C millisecond timer
reason_index     = 0..5
scope            = 0 Team, 1 Full  // high behavioral confidence
vote             = 0 No, nonzero Yes
```

The `70000` value should be tagged as **cross-source inferred**, not as a recovered literal.

---

## 10. Remaining highest-value evidence gaps

1. Recover the localized strings behind `0x369`, `0x36A`, `0x373..0x378`, `0x379`.
2. Recover the `VoterMgr` virtual table entries so the 719 handler and its exact status enum can be proven.
3. Trace the user-info-provider virtual slot used by 720 field 4 to give that byte a semantic name.
4. Trace all uses of the Voter `+44` end-result state to map the 723 byte values.
5. Recover the actual master/game-server-side 396/397 `PM_KICKUSER_REQ/ACK` packet path if it is separate from the 718–723 game-rule voting channel.
6. Trace final yes/no completion and no-vote timeout handling to reproduce the exact server decision predicate.

---

## 11. Source anchors

### IDA / C

- `Voter::possible_ctor_or_dtor` / `sub_A17130` / `sub_A17180` / `sub_A17380` around `0x00A170A0..0x00A17420`.
- `IVotingNetwork::sub_A191D0` through `sub_A198...` around `0x00A191D0..0x00A19890`.
- `CVotingApprovalUI::sub_A18B90` around `0x00A18B90`.
- `CVotingStateUI::sub_A1B900` / `sub_A1BF30` around `0x00A1B900..0x00A1BF30`.

### Wiki

- Japanese PaperMan `操作ガイド`: kick key, supported modes, two scopes, six reasons, 70-second vote window, target exclusion, 3-player minimum, paging and result behavior. citeturn762823search0
- Japanese PaperMan `既知の不具合`: historical evidence that a passed kick vote could fail to eject some floating/AFK-like players at the room/game layer. citeturn762823search1

### Extracted resource tree

The repository currently contains the extracted `ui` resource tree and other client resources, while the dedicated voting resource strings above are referenced by C but their final localized text store has not yet been conclusively located.
