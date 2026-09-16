# PaperMan 2016 JP — Quest Event ID / Client Mapping

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `sub_92EF00()` + exact gameplay producers + Resource/UI strings + Wiki cross-check

## 1. Why this matters

`sub_7463E0()` passes the 166 subtype 2/16 `n2` field into `sub_92EF00(3/4, n2, 0, resource_id)`. Therefore Quest progression is coupled directly to gameplay event processing, not merely calculated from a later scoreboard.

---

## 2. Exact Client-side QuestIndex mapping

`quest + 2324` is the Client-side quest condition/category ID.

### 2.1 Direct one-to-one conditions

```text
1  ↔ n2 1
2  ↔ n2 2
3  ↔ n2 3
4  ↔ n2 4
5  ↔ n2 5
6  ↔ n2 6
18 ↔ n2 18
19 ↔ n2 19
20 ↔ n2 20
21 ↔ n2 21
22 ↔ n2 22
23 ↔ n2 23
24 ↔ n2 24
25 ↔ n2 25
26 ↔ n2 26
27 ↔ n2 27
28 ↔ n2 28
29 ↔ n2 29
30 ↔ n2 30
31 ↔ n2 31
32 ↔ n2 32
33 ↔ n2 33
34 ↔ n2 34
35 ↔ n2 35
36 ↔ n2 36
```

Direct mutation type is not uniform:

```text
+= a3 : 1..6, 18..27, 32, 35, 36
=  a3 : 28,29,30,31,33,34
```

### 2.2 Conditional compound mappings

```text
Quest 7  ↔ n2==3  && n2_1==1
Quest 8  ↔ n2==3  && n2_1==2
Quest 9  ↔ n2==3  && n2_1==3
Quest 10 ↔ n2==3  && n2_1==4

Quest 11 ↔ n2==11 && n2_1==5
Quest 12 ↔ n2==12 && n2_1==6
Quest 13 ↔ n2==13 && n2_1==7
Quest 14 ↔ n2==14 && n2_1==8
Quest 15 ↔ n2==15 && n2_1==9
Quest 16 ↔ n2==16 && n2_1==10
Quest 17 ↔ n2==17 && n2_1==11
```

These are exact condition tests from Client code, not public Japanese labels.

---

## 3. Confirmed semantic producers

### 3.1 Quest 35 = Soccer Goal

`sub_566200()` is explicitly logged as:

```text
GameNetwork::OnGLUserGoalFootballACK
```

It parses:

```text
u8 goal/control flag
u8 player id
```

updates football player state, and when the acknowledged player is the local player:

```text
sub_92EF00(35,23,1,0)
```

Therefore:

```text
QuestIndex 35 = Soccer Goal condition
```

Confidence A.

The Wiki independently documents Soccer Mode and goal-based conditions; this corroborates the behavior-level meaning. citeturn703110search2turn703110search5

### 3.2 Quest 36 = Assist

`sub_5676D0()` is dispatched by TCP opcode `994` and processes repeated server records. When a record matches the local player, the Client:

```text
plays ui\\sounds\\assist.wav
sub_92EF00(36,23,1,0)
```

Therefore:

```text
QuestIndex 36 = Assist condition
```

Confidence A.

The same function has a record-type byte `n0x64`; when `n0x64 == 107 (0x6B)`, it additionally executes:

```text
sub_92EF00(32,23,1,0)
```

The Assist UI renderer maps event type `0x6B` to:

```text
ASSIST_OCCUPY
```

Thus Quest 32 is strongly linked to the **Occupation-mode Assist/occupation participation condition**.

Do not collapse Quest 32 into generic Occupation without further resource/quest-row evidence; the direct Client evidence is specifically `ASSIST_OCCUPY` event type + Quest32 increment.

Confidence for Quest32 semantic: A for the `ASSIST_OCCUPY` event linkage; B/C for the final public quest label.

The Wiki independently lists Occupation as an Assist Point source and describes occupation participation as a 2-point/1-point team event. citeturn703110search0turn703110search5

---

## 4. Client Assist event-type mapping

Independent UI rendering code maps Assist event node `+110` to exact resources:

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

This is one of the strongest semantic bridges in the Client because the value is used directly as a Resource/UI lookup key.

The Wiki's Assist Point page independently lists:

```text
55%+ damage then another player kill
airbomb/airshot assist
20%+ teammate heal
Bomb plant / explosion / defuse
Dye delivery
Pulp delivery / destruction
Occupation participation
Soccer goal
```

This is behavior-level corroboration, not a replacement for the Client event-type evidence. citeturn703110search0

---

## 5. Quest 21 — strong play-time candidate

A separate gameplay receive path calls:

```text
sub_92EF00(21,23,delta,0)
```

where `delta` is derived from elapsed server/client timing state rather than a player identity or item ID. This is consistent with the Wiki's explicit **Play Time quest** behavior, where progress is measured in minutes and sub-60-second remainders are discarded for progress display/update.

Current classification:

```text
Quest 21 = Play Time candidate
```

Confidence B/C until the exact packet/function name and timing unit are fully cross-verified against the extracted Quest row.

The Wiki documents Play Time as a separate quest condition and says progress is represented in one-minute units with sub-minute remainder discarded. citeturn703110search5

---

## 6. Quest 28–31 — match-result state candidates

`sub_76E450()` is a match-result/update path and calls:

```text
sub_92EF00(28,23,ExecutingCollection,0)
sub_92EF00(29,23,v25[0],0)
sub_92EF00(30,23,v17[5],0)
sub_92EF00(31,23,v16[12],0)
```

All four use assignment (`=`), not increment (`+=`).

Therefore these conditions are strongly associated with end/result-state values rather than simple event counters.

Exact public Quest labels remain unresolved until the corresponding Quest resource rows are matched.

The Wiki independently states that item/EXP/PG-style quest conditions can be finalized at match end/channel exit, so result-stage Quest updates are expected; this does not identify 28–31 individually. citeturn703110search5

---

## 7. Quest 33 / 34 — mode-specific result/state candidates

`sub_67C810()` in its mode-specific path calls:

```text
sub_92EF00(34,23,v11,0)
sub_92EF00(33,23,player+60162,0)
```

The surrounding function contains explicit PVE/AI mode state:

```text
pve_01_sounds\\AI3_continue_fail.wav
mode-specific state checks
n9 == 9/18/25 path
```

Thus Quest 33/34 are mode-specific state/result conditions and should not be given generic Kill/Win names without the Quest resource row.

Confidence B for mode-specific linkage; public semantic unresolved.

---

## 8. Quest 32/35/36 and Assist UI explain a larger design pattern

The Client does not represent all Assist conditions as separate Quest IDs.

Instead:

```text
Gameplay action
    ↓
Assist event type (1/2/3/0x65..0x6C)
    ↓
Assist UI/resource
    ↓
Quest condition update where applicable
```

This means:

```text
ASSIST_OCCUPY (0x6B)
    → Quest32

ASSIST_GOAL (0x6C)
    → Soccer Goal event / Quest35

ordinary Assist event
    → Quest36
```

That distinction is important for Server reconstruction: `AssistPointState`, `AssistEventType`, and `QuestProgress` should be modeled separately even though one gameplay action may affect multiple layers.

---

## 9. Eligibility and update timing

`sub_92EF00()` performs multiple quest-state/eligibility checks before mutation, including:

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

Therefore the wire/gameplay event itself does not guarantee quest progress; the relevant quest must be active/eligible.

The Wiki similarly distinguishes in-match conditions from result/exit conditions. citeturn703110search5

---

## 10. Still unresolved

```text
Quest 1..6 public labels
Quest 7..17 public labels / n2_1 meaning
Quest 18..20 public labels
Quest 21 exact producer/opcode and timing unit
Quest 22/23 exact mode/gameplay meaning
Quest 24..27 public labels
Quest 28..31 exact result metrics
Quest 33/34 exact PVE/mode labels
Quest 32 final public label despite confirmed ASSIST_OCCUPY linkage
```

These must be resolved by matching:

```text
QuestIndex
 ↔ Extracted Quest record
 ↔ Japanese text/localization
 ↔ direct gameplay producer
 ↔ mode/context
 ↔ Wiki behavior
```

No guessed English condition names should be used in the final protocol specification until this chain is closed.
