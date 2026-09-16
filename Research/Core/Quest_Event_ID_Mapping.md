# PaperMan 2016 JP — Quest Event ID / Client Mapping

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact function body + all visible callers + stat/UI cross-reference + PaperMan Wiki

## 0. Critical parameter-order correction

`sub_92EF00()` signature from the Client export is:

```c
char __stdcall sub_92EF00(int quest_or_event_id, char sub_type, int amount, int filter)
```

The first integer is compared against `quest + 2324` (the active Quest condition ID). The second byte is then used only for the compound conditions 7–17.

Therefore a call such as:

```text
sub_92EF00(35, 23, 1, 0)
```

does **not** prove Quest 35 progress, because the condition for Quest 35 additionally requires the second argument to be `35`.

This correction invalidates several earlier interpretations that treated the second argument (`23`) as the QuestIndex or claimed `(35,23)` / `(36,23)` updated Quest35/36. Those claims are removed here.

---

## 1. Exact condition matching implemented by `sub_92EF00()`

For every active/eligible quest, Client compares `quest + 2324` against the **first** argument.

### Direct conditions

```text
Quest 1  ← first arg == 1   → += amount
Quest 2  ← first arg == 2   → += amount
Quest 3  ← first arg == 3   → += 1
Quest 4  ← first arg == 4   → += 1
Quest 5  ← first arg == 5   → += 1
Quest 6  ← first arg == 6   → += 1
```

### Compound conditions

```text
Quest 7  ← first arg == 3  && second arg == 1  → += 1
Quest 8  ← first arg == 3  && second arg == 2  → += 1
Quest 9  ← first arg == 3  && second arg == 3  → += 1
Quest 10 ← first arg == 3  && second arg == 4  → += 1

Quest 11 ← first arg == 11 && second arg == 5  → += 1
Quest 12 ← first arg == 12 && second arg == 6  → += 1
Quest 13 ← first arg == 13 && second arg == 7  → += 1
Quest 14 ← first arg == 14 && second arg == 8  → += 1
Quest 15 ← first arg == 15 && second arg == 9  → += 1
Quest 16 ← first arg == 16 && second arg == 10 → += 1
Quest 17 ← first arg == 17 && second arg == 11 → += 1
```

### Direct conditions 18–36

```text
Quest 18 ← first arg == 18 → += amount
Quest 19 ← first arg == 19 → += amount
Quest 20 ← first arg == 20 → += amount
Quest 21 ← first arg == 21 → += amount
Quest 22 ← first arg == 22 → += amount
Quest 23 ← first arg == 23 → += amount
Quest 24 ← first arg == 24 → += amount
Quest 25 ← first arg == 25 → += amount
Quest 26 ← first arg == 26 → += amount
Quest 27 ← first arg == 27 → += amount
Quest 28 ← first arg == 28 → = amount
Quest 29 ← first arg == 29 → = amount
Quest 30 ← first arg == 30 → = amount
Quest 31 ← first arg == 31 → = amount
Quest 32 ← first arg == 32 → += amount
Quest 33 ← first arg == 33 → = amount
Quest 34 ← first arg == 34 → = amount
Quest 35 ← first arg == 35 → += amount
Quest 36 ← first arg == 36 → += amount
```

This is **exact Client control flow**. It tells us how an already-identified Quest condition is updated; it does not by itself identify the public Japanese label of every condition.

---

## 2. Quest eligibility is part of the contract

Before any condition mutation, `sub_92EF00()` checks the active quest and several predicates:

```text
sub_924210
sub_9244A0
sub_924590
sub_924660
sub_924730
sub_924F60
sub_925110
sub_925200
```

Thus:

```text
matching ID ≠ unconditional progress
```

The relevant quest must be active and pass all mode/state/eligibility checks. After a successful mutation, the Client computes completion/progress and may emit UI notification.

---

## 3. Cleanly confirmed Quest 11–17 mapping

This is the strongest fully closed Quest semantic chain currently available.

The Client maintains result-stat globals:

```text
EE8D60 = DOUBLEKILL
EE8D64 = TRIPLEKILL
EE8D68 = MULTIKILL
EE8D6C = ULTRAKILL
EE8D70 = GENOCIDE
EE8D74 = KILLINGMACHINE
EE8D78 = DIABLO
```

Dedicated server packet handlers then call:

```text
243 → update EE8D60
     → sub_61FE40(..., 5, 0, 0, 110)
     → sub_92EF00(11, 5, 0, 0)

245 → update EE8D64
     → sub_61FE40(..., 6, 0, 0, 110)
     → sub_92EF00(12, 6, 0, 0)

381 → update EE8D68
     → sub_61FE40(..., 7, 0, 0, 110)
     → sub_92EF00(13, 7, 0, 0)

383 → update EE8D6C
     → sub_61FE40(..., 8, 0, 0, 110)
     → sub_92EF00(14, 8, 0, 0)

385 → update EE8D70
     → sub_61FE40(..., 9, 0, 0, 110)
     → sub_92EF00(15, 9, 0, 0)

387 → update EE8D74
     → sub_61FE40(...,10, 0, 0, 110)
     → sub_92EF00(16,10, 0, 0)

389 → update EE8D78
     → sub_61FE40(...,11, 0, 0, 110)
     → sub_92EF00(17,11, 0, 0)
```

Therefore:

```text
Quest 11 = Double Kill
Quest 12 = Triple Kill
Quest 13 = Multi Kill
Quest 14 = Ultra Kill
Quest 15 = Genocide
Quest 16 = Killing Machine
Quest 17 = Diablo
```

Confidence A: Client result-stat label + packet state update + exact `sub_92EF00` compound match all agree.

The Wiki independently describes the multi-kill progression and specifically notes that the seventh consecutive kill counts as Killing Machine and the eighth and later kills count as Diablo, which corroborates the result-stat structure. citeturn739532search7turn739532search9

---

## 4. Important correction to earlier Quest 1/2/5/6/18–36 claims

Visible callers such as:

```text
sub_92EF00(1, 23, v16, 0)
sub_92EF00(2, 23, v14, 0)
sub_92EF00(5, 23, 1, 0)
sub_92EF00(6, 23, 1, 0)
sub_92EF00(18,23,n10_2,0)
sub_92EF00(19,23,1,0)
sub_92EF00(20,23,...,0)
sub_92EF00(22,23,1,0)
sub_92EF00(23,23,1,0)
sub_92EF00(24,23,1,0)
sub_92EF00(25,23,1,0)
sub_92EF00(26,23,1,0)
sub_92EF00(27,23,1,0)
sub_92EF00(28,23,...,0)
sub_92EF00(29,23,...,0)
sub_92EF00(30,23,...,0)
sub_92EF00(31,23,...,0)
sub_92EF00(32,23,1,0)
sub_92EF00(33,23,...,0)
sub_92EF00(34,23,...,0)
sub_92EF00(35,23,1,0)
sub_92EF00(36,23,1,0)
```

do **not** by themselves update those numbered conditions because the second argument is `23`, not the required condition ID. Earlier notes that treated these calls as direct Quest progress have therefore been retracted.

These callers remain valuable as evidence that the Client contains a generic Quest/event API and that `23` is used as a recurring source/subtype value in many contexts, but the semantic role of that `23` is still unresolved.

---

## 5. Assist packet 994 — what is actually proven

`sub_5676D0()` handles TCP opcode 994 and parses repeated server records:

```text
u8 record_type = n0x64
u8/record player id
u32 value0
u32 value1
u32 value2
```

For the local-player record, it updates player state and, when `value0 == dword_EE8CB4`, plays:

```text
ui\\sounds\\assist.wav
```

and updates local assist-related state.

If:

```text
record_type == 107 (0x6B)
```

an additional branch executes.

Independent Client Assist UI code maps:

```text
1    → ASSIST_DAMAGE
2    → ASSIST_AIRSHOT
3    → ASSIST_HP
0x65 → ASSIST_BOMB_PLANT
0x66 → ASSIST_BOMB_EXPLO
0x67 → ASSIST_BOMB_DESTROY
0x68 → ASSIST_DYE
0x69 → ASSIST_PULP
0x6A → ASSIST_PULP_DESTROY
0x6B → ASSIST_OCCUPY
0x6C → ASSIST_GOAL
```

Therefore:

```text
994 record_type 0x6B
    ↔ ASSIST_OCCUPY
```

is a strong A-level Client linkage.

However, the calls:

```text
sub_92EF00(36,23,1,0)
sub_92EF00(32,23,1,0)
```

must **not** be cited as proof that 994 directly increments Quest36/Quest32. Under the actual `sub_92EF00` condition checks, they do not match those conditions.

The Wiki independently documents Assist Points from damage, airshot, healing, bomb, dye, pulp, occupation, and soccer actions. citeturn739532search3turn739532search1

---

## 6. Soccer Goal packet — what is actually proven

`sub_566200()` is explicitly logged:

```text
GameNetwork::OnGLUserGoalFootballACK
```

and processes football goal/player state.

It calls:

```text
sub_92EF00(35,23,1,0)
```

for the local player, but this does **not** satisfy the Quest35 condition in `sub_92EF00()`.

Therefore the safe conclusion is:

```text
Soccer goal event = proven
Quest35 ← Soccer Goal = NOT proven from this call
```

The Wiki separately documents Soccer goal-based behavior, so Soccer Goal remains a distinct gameplay event; its relation to Quest condition 35 needs the actual Quest resource row / another producer. citeturn739532search0

---

## 7. Play-time packet 223 — what is actually proven

`sub_556730()` reads:

```text
u32 value
```

then:

```text
sub_92EF00(21,23,value - dword_EE8D34,0)
dword_EE8D34 = value
```

Because the second parameter is `23`, this still does not prove that the call increments condition 21 under the current `sub_92EF00` body.

What is proven is:

```text
223 payload = u32 timing/state value
EE8D34 = previous/current baseline
```

and the code attempts to feed the delta into the generic Quest API.

The Wiki independently describes Play Time as a distinct Quest condition and notes that progress is measured in one-minute units with sub-minute remainder discarded. citeturn739532search0

Therefore:

```text
223 = play-time-related state candidate
Quest21 = play-time candidate from external Quest semantics
Direct 223 → Quest21 mutation = currently not proven
```

---

## 8. Dedicated stat packet family 229–389

The strongest closed pairings are:

```text
229 → EE8D40 = Record/Total Win value
231 → EE8D44 = Record/Total Lose value
232 → EE8D48 = Kill/My Kill value
234/nearby → EE8D4C = Death/My Death value
243 → DoubleKill
245 → TripleKill
381 → MultiKill
383 → UltraKill
385 → Genocide
387 → KillingMachine
389 → Diablo
```

The exact opcode of the `EE8D4C` Death field must still be checked against dispatcher context because the nearby handler naming/numbering must not be inferred merely from source order.

The stats themselves are directly labeled by Client UI:

```text
EE8D40 = GAMEROOM_RECORDWIN / TOTAL_WIN / RECORDWIN
EE8D44 = GAMEROOM_RECORDLOSE / TOTAL_LOSE / RECORDLOSE
EE8D48 = GAMEROOM_KILL / MY_KILL / KILL
EE8D4C = GAMEROOM_DEATH / MY_DEATH / DEATH
EE8D50 = HEADSHOT
EE8D54 = AIRCOMBO
EE8D58 = HEARTBREAK
EE8D5C = CRITCALSHOT
EE8D60 = DOUBLEKILL
EE8D64 = TRIPLEKILL
EE8D68 = MULTIKILL
EE8D6C = ULTRAKILL
EE8D70 = GENOCIDE
EE8D74 = KILLINGMACHINE
EE8D78 = DIABLO
```

These labels are direct Client evidence; packet-to-field assignments are recorded only where the corresponding parser has been located.

---

## 9. Wiki timing/behavior cross-check

The Wiki's Quest system distinguishes conditions updated during the match from result/exit-time conditions. It explicitly includes kill count, special shot, multi-shot, assist, play time, wins, play count, and item/EXP/PG collection, with mode-specific exceptions. citeturn739532search0

The Assist Points page states that the feature was introduced on 2014-09-17 and lists damage, airshot, healing, bomb, dye, pulp, occupation and soccer conditions. citeturn739532search3

The kill-log page independently identifies normal kill, special shot, and assist/objective log types, including occupation and soccer goal assist icons. citeturn739532search1

These Wiki facts are behavior-level validation and should not replace direct wire parsing evidence.

---

## 10. Current server-reconstruction rule

Quest should be modeled as a consumer of several event/stat sources:

```text
Gameplay event
    → generic Quest API

Dedicated server stat synchronization
    → result-stat globals
    → generic Quest API

Specialized Assist / Football events
    → gameplay/UI state
    → possibly Quest, but only when exact condition/source IDs match
```

Do not assume:

```text
second argument 23 = QuestIndex
```

and do not assume:

```text
Quest ID == event packet ID
```

unless the full `sub_92EF00` condition and caller-side source ID both match.

---

## 11. Remaining proof targets

```text
1. Recover Quest condition labels 1–10 and 18–36 from actual Extracted Quest records/localization.
2. Identify the true meaning of recurring source/subtype 23.
3. Locate producers that call sub_92EF00 with matching source IDs for Quest 1–6 and 18–36.
4. Resolve EE8D4C Death packet opcode by dispatcher and caller context.
5. Match 243/245/381–389 two-u32 payloads to result-state semantics.
6. Cross-match Assist 994 records with actual AssistPoint state and server stat updates.
7. Continue Resource ID mapping for gameplay events before naming raw `n2`/`n10`/`n10_1` fields.
```
