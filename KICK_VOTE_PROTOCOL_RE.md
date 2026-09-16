# PaperMan Kick Vote Protocol / State Reconstruction

> Research snapshot: **2026-09-16**
>
> This file records the protocol and state-machine portion of the Japanese PaperMan client kick-vote reverse engineering. It is intentionally written around observable behavior and byte widths so that both humans and LLMs can use it when implementing a compatible server.

## Evidence legend

- **[C]** — directly observed in `PaperMan.exe.c` (Hex-Rays export).
- **[WIKI]** — archived Japanese PaperMan Wiki behavior.
- **[RES]** — extracted client resource / resource-tree evidence.
- **[X]** — two or more evidence classes agree, or a direct call chain removes the ambiguity.
- **[OPEN]** — plausible but not yet sufficiently proven; do not hard-code from this note alone.

Hex-Rays output is decompiler output, not original source. Preserve the original address/function name alongside any reconstructed semantic name.

---

## 1. Packet direction and current protocol map

The voting packets are handled by `IVotingNetwork::sub_9BF430`. The parser switches on the packet ID and then consumes the fields with fixed-width readers.

| ID | Registered name | Direction | Payload proven from C | Confidence |
|---:|---|---|---|---|
| **718** | `GR_START_VOTING_REQ` | client → server | `u32 scope`, `u32 reason`, `u32 target_id` = 12 bytes | **[X]** |
| **719** | `GR_START_VOTING_ACK` | server → client | `u8` | **[C]** |
| **720** | `GR_START_VOTING` | server → client | `u32 reason`, `u32 applicant_id`, `u32 target_id`, `u32 control`, `u8 flag` = 17 bytes | **[X]** |
| **721** | `GR_DO_VOTING` | client → server | `u8 vote` | **[X]** |
| **722** | `GR_VOTING_RESULT` | server → client | `u32 voter_id`, `u8 vote` = 5 bytes | **[X]** |
| **723** | `GR_END_RESULT` | server → client | `u8 value`, `u32 player_id` = 5 bytes | **[X]** |

The packet registration table directly contains 718–723 names/IDs for these entries. In particular, 722 is registered as `GR_VOTING_RESULT` and 723 as `GR_END_RESULT`.

### 1.1 Direction is not inferred from the names

The direction is confirmed from behavior:

- 718 is constructed by `IVotingNetwork::sub_A191D0`, then passed to the normal send path.
- 721 is constructed by `IVotingNetwork::sub_A192B0`, then passed to the normal send path.
- 719, 720, 722, 723 are parsed by `IVotingNetwork::sub_9BF430`, which is the client receive-side voting dispatcher.

This is important because an apparently symmetric `REQ/ACK` pair does not by itself prove direction.

---

## 2. Exact 718 request layout

`IVotingNetwork::sub_A191D0` is the client-side request constructor:

```c
if ( sub_A17340(this - 48, a2) != 3 )
    return 0;

Packet::possible_ctor_or_dtor_0(v7, 718);
v4 = sub_592A20(v7, a2);
v5 = sub_592A20(v4, a3);
sub_592A20(v5, a4);
sub_58D7D0(byte_13242F8, v7);
```

`sub_592A20` writes exactly 4 raw bytes. Therefore:

```text
GR_START_VOTING_REQ (718)
+0x00  u32 scope/mode
+0x04  u32 reason_index
+0x08  u32 target_player_id
size = 12 bytes
```

### 2.1 Semantic mapping of the three fields

The call site in target selection eventually invokes the packet constructor with:

```text
(this + 16, this + 4, selected_target_id)
```

The same manager fields are established by the keyboard-driven state machine:

- `this + 16` = selected scope index, accepted only as `0` or `1`.
- `this + 4` = selected reason index, accepted only as `0..5`.
- selected target = returned from `sub_A1ACA0(...)` and is a player ID.

Therefore the reconstructed 718 layout is **high confidence**:

```text
field0 = scope
field1 = reason
field2 = target player ID
```

Do not reorder these fields on the server.

---

## 3. Scope mapping: Team vs Full

The UI state accepts exactly two scope choices:

```c
v17 = n10 - 1;
sub_A19060(this, n10 - 1);
if ( n10 - 1 >= 2 )
    return 1;
*(this + 16) = v17;
```

The target list has two modes:

```c
if ( v15 != nullptr && v15 != v14 && a2 == 1 )
    include;
else if ( a2 == 0 && v15 != v14 )
    include_if_sub_67DDD0(v15);
```

So the two internal scopes are structurally:

```text
scope 0 -> filtered candidate set
scope 1 -> all non-requesters
```

The Wiki defines the corresponding public operations as Team Kick and Full Kick. Because the filtered set is exactly the kind of same-team candidate set described by Team Kick, while the other set is the all-participant set described by Full Kick, the practical mapping is:

```text
0 = Team Kick
1 = Full Kick
```

**Confidence: high behavioral cross-check [X], but the literal Japanese UI label for the two numeric scope choices has not yet been extracted from a dedicated voting XML file.**

For a server implementation, this mapping is usable, but retain the evidence note above until the UI string/resource path is recovered.

---

## 4. Why the client enforces the 3-player minimum

`CVoteTargetList::sub_A177C0` counts two populations after excluding the local requester:

```c
++v5;                 // every non-requester
if ( sub_67DDD0(v4) )
    ++v6;             // filtered subset
```

The manager copies those counts into `this + 36` and `this + 40`.

`sub_A17290` then gates the two scopes separately:

```c
v4 = a2 == 0 && *(this + 36) >= 2;
v3 = a2 == 1 && *(this + 40) >= 2;
if ( v4 || v3 )
    return 3;
```

The requester is excluded from the target/candidate population, so `>= 2` other eligible users corresponds to a minimum of 3 users including the requester.

This matches the Wiki's public rule that both Team Kick and Full Kick require 3 or more participants.

---

## 5. Candidate list and target selection

### 5.1 Requester is excluded

The target-list rebuild compares each candidate pointer against the current local player pointer and rejects equality:

```c
if ( v15 != nullptr && v15 != v14 ... )
```

This is direct proof that the requester never appears as a kick target.

### 5.2 Full scope

For the second scope, every active non-requester is accepted.

### 5.3 Team scope

For the first scope, every active non-requester is passed through `sub_67DDD0`.

`sub_67DDD0` computes the player's slot index from the global player table:

```c
n0x10 = (a1 - byte_F33120) / 0x3AC8C;
return n0x10 < 0x10 && sub_67D3F0(n0x10);
```

The slot-space itself therefore has a fixed maximum of 16 player records, and the Team-scope filter uses a separate team/group predicate.

### 5.4 Target list entry size

`sub_A1ACA0` indexes entries with a **36-byte stride**:

```c
*(36 * a2 + *(this + 5))
```

and copies a name-like field from entry `+4` plus the player ID at the entry start.

This is the client-side list-storage stride, not necessarily a server packet structure.

---

## 6. Six reasons and their index domain

The input state explicitly limits reason selection to six entries:

```c
v16 = n10 - 1;
v15[1] = 6;
if ( n10 - 1 >= 6 || sub_A19090(this, v16) != 0 )
    return 1;
```

Thus the wire-level reason field in 718/720 is most naturally represented as:

```text
u32 reason_index, valid client range 0..5
```

The UI builder labels the corresponding area with:

```text
1_TARGET_VOTING_REASON
```

The Wiki independently documents six kick reasons.

### Important caution

The numeric order `0..5` should not yet be published as a definitive Japanese reason-text mapping solely from enumeration order. That mapping should come from the localization/resource side.

---

## 7. Target paging

The target-selection state accepts visible target positions 1–8:

```c
if ( n10 <= 0 || n10 >= 9 ) {
    if ( n10 == 10 ) {
        ... page handling ...
    }
}
```

The selected target index is calculated as:

```c
8 * current_page + (n10 - 1)
```

The paging state separately checks whether there are more than 8 entries.

The Wiki describes `0` as the page-advance key for Full Kick when the participant count exceeds one page. The C-side input representation uses an internal value of `10`; therefore **10 is an internal translated key/action value, not the physical key label to expose to users**.

---

## 8. Exact 721 vote request layout

`IVotingNetwork::sub_A192B0` constructs packet 721 and writes one byte:

```c
Packet::possible_ctor_or_dtor_0(v5, 721);
sub_5928E0(v5, a2);
sub_58D7D0(byte_13242F8, v5);
```

`sub_5928E0` is the 1-byte writer.

Therefore:

```text
GR_DO_VOTING (721)
+0x00  u8 vote
size = 1 byte
```

The local voting state consumes the same `a2` as the later YES/NO accounting, so the intended values are:

```text
0 = No
1 = Yes
```

Do not send a DWORD here. The client writes exactly one byte.

---

## 9. Exact 722 result layout and YES/NO mapping

The receive parser contains:

```c
case 722:
    v7 = sub_592A40(a2, &v15);   // u32
    sub_592900(v7, &v14);         // u8
    LOBYTE(v8) = v14;
    (*(*this + 16))(this, v15, v8);
```

The target handler resolves the first field as a player identity, then forwards the byte to `sub_A1A9D0`.

`sub_A1A9D0` performs the definitive vote accounting:

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

So the second field is a boolean-like vote value where:

```text
1 / nonzero -> YES count
0            -> NO count
```

The client therefore expects:

```text
GR_VOTING_RESULT (722)
+0x00  u32 voter_player_id
+0x04  u8  vote
size = 5 bytes
```

This is one of the cleanest field-semantic recoveries in the subsystem because the receive width, target lookup and yes/no counters all agree.

---

## 10. Exact 720 start-notification layout

The receive parser is:

```c
case 720:
    v3 = sub_592A40(a2, &v17); // u32 field 0
    v4 = sub_592A40(v3, &v19); // u32 field 1
    v5 = sub_592A40(v4, &v20); // u32 field 2
    v6 = sub_592AC0(v5, &v18); // u32 field 3
    sub_592940(v6, &v16);      // u8  field 4
    (*(*this + 8))(this, v17, v20, v19, v18, v16);
```

The target method is `IVotingNetwork::sub_A19460(this,a2,a3,a4,a5,a6)`.

### 10.1 Field 0 = reason index

`sub_A19460` immediately executes:

```c
sub_A19090(this - 48, a2);
```

and `sub_A19090` stores the selected reason index.

Thus:

```text
720 field 0 = u32 reason_index
```

### 10.2 Field 1 = applicant ID

`sub_A19460` copies its second argument to `this - 40` and repeatedly compares it to the local player ID:

```c
*(this - 40) = a3;
...
v17 = *(this - 40);
v16 = *(this - 36);
v17 != v16
```

It also resolves this same ID through the user-info provider.

Most importantly, the UI call derives:

```c
*(this - 40) == *(this - 36)
```

to determine whether the applicant is the local player.

Therefore:

```text
720 field 1 = u32 applicant_player_id
```

This is directly stronger than merely assuming an "applicant" field from the parameter order.

### 10.3 Field 2 = target ID

`sub_A19460` places the third packet argument in `this + 8` and resolves it through the same player-info provider as the applicant. It is paired with the applicant identity in the voting UI.

Therefore:

```text
720 field 2 = u32 target_player_id
```

### 10.4 Field 3 = control/state integer

The fourth packet field is copied through `a5` into the base-voter state:

```c
sub_A17130(this - 48, v7, a5);
```

and eventually into the voting-state UI as `+17`.

Its exact public semantic is **not yet proven**. Keep it as:

```text
720 field 3 = u32 control/state (OPEN semantic label)
```

Do not rename it to `duration`, `vote_count`, `status`, etc. until the timer/state call graph proves that meaning.

### 10.5 Field 4 = byte control/permission flag

The fifth packet field is consumed as `a6`. In `sub_A19460` it controls a branch which may call a user-information predicate before UI state is built:

```c
*(this - 32) = a6;
...
if ( *(this - 32) == 0 )
    v25 = (*(**(this + 12) + 28))(...);
```

It is therefore a boolean-like control flag, but its exact server-facing semantic remains **OPEN**.

Do not confuse this raw packet byte with the later locally computed `applicant_id == local_id` flag passed to `sub_A1A830`.

### 10.6 Proven 720 schema

```text
GR_START_VOTING (720)
+0x00  u32 reason_index
+0x04  u32 applicant_player_id
+0x08  u32 target_player_id
+0x0C  u32 control_state
+0x10  u8  control_flag
size = 17 bytes
```

Only the first three semantics are currently strong enough to use as stable names. The last two should remain raw/control fields in a protocol implementation until further evidence is recovered.

---

## 11. 719 ACK layout

`GR_START_VOTING_ACK` is parsed as exactly one byte:

```c
case 719:
    sub_592940(a2, &v21);
    v22 = v21;
    (*(*this + 12))(this, v21);
```

So:

```text
GR_START_VOTING_ACK (719)
+0x00  u8 result/status
size = 1 byte
```

The exact mapping of byte values to user-facing error/success messages is not yet proven here. A server should preserve the byte as an enum-like numeric field, not invent a string or multi-byte response.

---

## 12. 723 `GR_END_RESULT`

Registration proves:

```text
723 = GR_END_RESULT
```

The receive parser proves its shape:

```c
case 723:
    v9 = sub_592900(a2, &v12); // u8
    sub_592A40(v9, &v13);       // u32
    LOBYTE(v10) = v12;
    (*(*this + 20))(this, v10, v13);
```

Therefore:

```text
GR_END_RESULT (723)
+0x00  u8  end/result value
+0x01  u32 player_id
size = 5 bytes
```

The DWORD is definitely treated as a player identity because `IVotingNetwork::sub_A19770` stores it as the player-related value and resolves it through the user-info subsystem.

The exact meaning of the first byte is still **OPEN**. It is later fed to `sub_A17180`, which changes the base voting state, so it should be treated as a state/result byte rather than arbitrarily named `success`.

---

## 13. Packet object / wire framing

The client packet object is separate from the logical voting payload.

Relevant recovered layout:

```text
packet object
  +0x18  buffer base / wire start
  +0x20  payload start
  +0x04  packet ID storage in the surrounding packet header object
```

The packet constructor ultimately stores the packet ID through `sub_591EC0`.

`sub_591F20` establishes the packet's logical length and a related `+8` value, while the send routine uses:

```c
Buffers.buf = a2 + 24;
Buffers.len = sub_591F00(a2) + 8;
```

Thus the TCP/UDP send buffer used by this packet path includes an **8-byte wire header** in addition to the logical packet payload.

### Important implementation consequence

The 12-byte 718 payload does **not** mean a 12-byte wire packet. Likewise, a 5-byte 722 payload does not mean a 5-byte wire packet. The protocol implementation must preserve the game's outer packet header/framing separately from the logical voting schema.

---

## 14. Voting packet dispatch chain

The vote messages do not appear in the generic application-network switch used for unrelated game packets.

The receive path first enters the game-rule layer, and the game-rule object forwards into the voting network interface. The relevant high-level chain is:

```text
network receive
    -> game/network dispatch
    -> CGameRule::sub_67CF90(...)
    -> voting network vtable
    -> IVotingNetwork::sub_9BF430(packet)
    -> switch(packet_id)
       719 / 720 / 722 / 723
```

This explains why searching only the generic packet switch can miss the voting opcodes.

For reverse engineering, **follow the protocol object and vtable path**, not only literal `case 718` searches.

---

## 15. Local voting state / UI that surrounds the protocol

The voting manager creates distinct objects:

```text
CVotingApprovalUI   0x08 bytes
CVotingStateUI      0xE8 bytes
CVotingTargetUI     0x28 bytes
CVoteTargetList     0x20 bytes
```

The target UI is linked to the target list, and the state UI is responsible for the visible vote-state/remaining-time area.

The client directly references these UI keys:

```text
VotingStatePos
VotingAble
TargetUserVotingUI
VoterState
Vote_Digit
1_TARGET_VOTING_REASON
2_APPLICANT_USER_NAME
2_TARGET_NICK
2_REASON
```

`CVotingStateUI::sub_A1BF30` displays remaining time through `Vote_Digit`, using the value at `+68` divided by `1000` for the visible digit value.

**Do not equate the various internal `3000` initializations with the Wiki's public 70-second duration.** The 3000 values are local state/UI timers or state defaults; the actual network voting duration has not been proven to be encoded there.

---

## 16. Result counting and target exclusion are local UI behavior, not server authority

The client locally tracks YES and NO counts. `sub_A1A9D0` increments them when a `GR_VOTING_RESULT` arrives.

This does not establish that the client decides the final kick result itself. The protocol design strongly suggests that the authoritative decision is represented by later server-originated state/result messages, especially 719/720/723.

For server reimplementation, treat the client-side counters as **presentation/state**, while the server remains authoritative for:

```text
eligible voters
valid target
scope membership
duplicate voting
vote completion
final kick result
```

These server-side rules are consistent with the Wiki's player-facing behavior but are not all independently proven in this particular client code region.

---

## 17. Resource cross-check status

The extracted repository resource tree proves that UI resources are organized under `Extracted/ui`, while `ClientDataList.xml` references the broader `ui` and `ui_temp` data lists.

Example resource evidence:

- `Extracted/ClientDataList.xml` references `ui` and `ui_temp`.
- `Extracted/ui/GameInChat.xml` is a normal extracted XML UI definition.
- `Extracted/ui/Popup_Room_Identity.xml` is another normal XML UI definition.

However, exact XML definitions named after the voting keys (`VotingStatePos`, `TargetUserVotingUI`, etc.) have **not** been recovered as standalone extracted files yet. The safest interpretation is that these names belong to a UI/resource layer that is either packaged elsewhere or loaded through another resource path.

Therefore:

```text
C string present          = proven
matching standalone XML   = not yet proven
```

Do not fabricate a resource filename from the C symbol name.

---

## 18. Current server-side protocol skeleton

The strongest evidence-supported logical model is:

```text
CLIENT                                  SERVER
------                                  ------
P / Kick Vote UI
    |
    | GR_START_VOTING_REQ (718)
    | u32 scope
    | u32 reason
    | u32 target_id
    v
                                  validate request
                                  validate scope membership
                                  validate target
                                  create vote
    ^
    | GR_START_VOTING_ACK (719)
    | u8 status
    |
    | GR_START_VOTING (720)
    | u32 reason
    | u32 applicant_id
    | u32 target_id
    | u32 control_state
    | u8 control_flag
    |
    | display voting UI
    |
    | GR_DO_VOTING (721)
    | u8 vote
    v
                                  record vote
                                  broadcast voter result
    ^
    | GR_VOTING_RESULT (722)
    | u32 voter_id
    | u8 vote
    |
    | ... repeat until server-side completion ...
    |
    | GR_END_RESULT (723)
    | u8 result/state
    | u32 player_id
    v
```

The exact semantics of 719's byte, 720 fields 3–4, and 723's byte remain open. They should be decoded before producing a final compatible server packet implementation.

---

## 19. High-value facts to preserve in future LLM prompts

When asking an LLM to implement the PaperMan server, the following should be treated as hard evidence rather than guesses:

```text
718 = GR_START_VOTING_REQ, client -> server
718 payload = u32 scope, u32 reason, u32 target_id

719 = GR_START_VOTING_ACK, server -> client
719 payload = u8

720 = GR_START_VOTING, server -> client
720 payload = u32 reason, u32 applicant_id, u32 target_id, u32 control_u32, u8 control_flag

721 = GR_DO_VOTING, client -> server
721 payload = u8 vote

722 = GR_VOTING_RESULT, server -> client
722 payload = u32 voter_id, u8 vote
vote 0 = NO, nonzero/1 = YES in client accounting

723 = GR_END_RESULT, server -> client
723 payload = u8 result/state, u32 player_id

scope 0 = filtered/team-like target set; scope 1 = all non-requesters
reason index = 0..5
requester excluded from target list
minimum = requester + 2 other eligible users
8 target positions per page
internal page-action value = 10; Wiki physical key = 0
```

### Do not silently change these

- Do not change the 4-byte fields to shorts merely because IDs look small.
- Do not change 721 from 1 byte to a 4-byte boolean/integer.
- Do not treat packet payload length as total wire length; the outer packet framing adds its header.
- Do not assume 720 field 3 is a timer until the remaining call graph proves it.
- Do not assume 723 byte is `success=1` until its result-state consumers are traced.
- Do not infer a standalone voting XML filename from a C-side UI key.

---

## 20. Remaining evidence gaps

The next highest-value targets are:

1. Trace the vtable slot `+12` used by packet 719 to identify exact ACK status values and client error/success transitions.
2. Trace every writer/consumer of the 720 `control_u32` field and determine whether it is a timer, vote state, participant count, or another control value.
3. Trace the 720 `control_flag` producer on the server-facing side and identify all branches for zero/nonzero.
4. Trace 723's first byte through `sub_A17180` and all result-state consumers to derive the exact result enum.
5. Extract the resource/localization path for IDs `0x366..0x379` and the voting UI keys.
6. Cross-check the server-authoritative voting rules against more Wiki pages / archived UI documentation before implementing edge cases such as disconnected voters and duplicate requests.

Until these are solved, the raw schemas above are safe to use; the unresolved fields should remain explicitly typed as `u8` / `u32 control` instead of receiving speculative semantic names.
