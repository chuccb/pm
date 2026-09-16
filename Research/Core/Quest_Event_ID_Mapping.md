# PaperMan 2016 JP — Quest Event ID / Client Mapping

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `sub_92EF00()` exact mapping + PaperMan Wiki quest-system cross-check

## 1. Why this matters to packet reconstruction

`sub_7463E0()` calls:

```text
sub_92EF00(3, n2, 0, resource_id)
```

or:

```text
sub_92EF00(4, n2, 0, resource_id)
```

Therefore the `n2` field in 166 subtype 2/16 is not merely a generic visual effect selector. It is also consumed by the Quest progress subsystem.

The Wiki confirms that PaperMan quests have explicit progress types including kill count, special shot, multi-shot, assist, play time, wins, play count, item/EXP/PG collection, PVE, and single mode. It also documents that most in-match conditions update during a match, while some conditions update at match end/channel exit.[C]

---

## 2. Exact QuestIndex mappings observed in `sub_92EF00()`

`quest + 2324` is the Client-side Quest condition/category ID.

### Direct mappings

```text
QuestIndex 1  ↔ n2 1   : progress += a3
QuestIndex 2  ↔ n2 2   : progress += a3
QuestIndex 3  ↔ n2 3   : progress += a3
QuestIndex 4  ↔ n2 4   : progress += a3
QuestIndex 5  ↔ n2 5   : progress += a3
QuestIndex 6  ↔ n2 6   : progress += a3
```

### Conditional multi-purpose mapping

```text
QuestIndex 7  ↔ n2_1==1 && n2==3  : progress += 1
QuestIndex 8  ↔ n2_1==2 && n2==3  : progress += 1
QuestIndex 9  ↔ n2_1==3 && n2==3  : progress += 1
QuestIndex 10 ↔ n2_1==4 && n2==3  : progress += 1

QuestIndex 11 ↔ n2_1==5  && n2==11 : progress += 1
QuestIndex 12 ↔ n2_1==6  && n2==12 : progress += 1
QuestIndex 13 ↔ n2_1==7  && n2==13 : progress += 1
QuestIndex 14 ↔ n2_1==8  && n2==14 : progress += 1
QuestIndex 15 ↔ n2_1==9  && n2==15 : progress += 1
QuestIndex 16 ↔ n2_1==10 && n2==16 : progress += 1
QuestIndex 17 ↔ n2_1==11 && n2==17 : progress += 1
```

### One-to-one mappings for 18–36

```text
QuestIndex 18 ↔ n2 18 : progress += a3
QuestIndex 19 ↔ n2 19 : progress += a3
QuestIndex 20 ↔ n2 20 : progress += a3
QuestIndex 21 ↔ n2 21 : progress += a3
QuestIndex 22 ↔ n2 22 : progress += a3
QuestIndex 23 ↔ n2 23 : progress += a3
QuestIndex 24 ↔ n2 24 : progress += a3
QuestIndex 25 ↔ n2 25 : progress += a3
QuestIndex 26 ↔ n2 26 : progress += a3
QuestIndex 27 ↔ n2 27 : progress += a3
QuestIndex 28 ↔ n2 28 : progress = a3
QuestIndex 29 ↔ n2 29 : progress = a3
QuestIndex 30 ↔ n2 30 : progress = a3
QuestIndex 31 ↔ n2 31 : progress = a3
QuestIndex 32 ↔ n2 32 : progress += a3
QuestIndex 33 ↔ n2 33 : progress = a3
QuestIndex 34 ↔ n2 34 : progress = a3
QuestIndex 35 ↔ n2 35 : progress += a3
QuestIndex 36 ↔ n2 36 : progress += a3
```

The `=` versus `+=` distinction is direct code behavior and matters for server reconstruction: some quest conditions represent counters, while others are state/value assignments.

---

## 3. Quest prerequisite filters are part of the semantic contract

Before applying the mapping, `sub_92EF00()` checks multiple quest-state / acceptance predicates, including:

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

It also checks the selected Quest entry, list bounds, and quest state.

Therefore the mere existence of `n2 == X` does not guarantee that a quest counter changes; the relevant quest must be active/eligible and the function's condition filters must pass.

---

## 4. Client UI strings expose only part of the mapping

When a quest progress event occurs, the client can generate a progress notification. The displayed text is selected by `quest +2324`:

```text
1 → localization string 0x453
2 → 0x454
3 → 0x455
4 → 0x456
5 → 0x457
6 → 0x458
7..17 → 0x459
18 → 0x45A
19 → 0x45B
20 → 0x45C
21..27 → 0x45D
28 → 0x4B0
29 → 0x4B0
30 → 0x4B0
31 → 0x4B0
33 → 0x4B0
34 → 0x4B0
35/36 → 0x45D-family path
```

These localization IDs are not yet mapped to their final Japanese text resource in `Extracted`; therefore they should not be converted into English semantic names without the matching localization table.

---

## 5. Wiki cross-check and important limitation

The Wiki's Quest system page states:

- Quest system introduced 2012-10-31.
- There are daily quests and free quests, with additional character/event/special variants.
- Conditions include kill count, win count, special shot, multi-shot, assist, play time, item collection, mode/map/weapon restrictions, PVE and single-mode conditions.
- For ordinary versus modes, kill count, special shot, multi-shot and assist are updated during the match; wins/play time/item collection are commonly evaluated at match end or channel exit depending on condition.

This aligns with the existence of a dedicated Client event-progress function, but it does **not** independently identify which numeric QuestIndex 1–36 corresponds to which public quest label.

Therefore the current safe chain is:

```text
gameplay event
  → n2 / n2_1
  → sub_92EF00()
  → quest +2324 matching
  → progress mutation
  → quest notification / UI
```

Not:

```text
n2 == 3 = definitely Kill
```

That stronger semantic requires the actual Quest resource/table rows and their displayed condition text to be matched.

---

## 6. Immediate next resource cross-check

The next proof step is to match `quest +2324` against the Quest records in `Extracted` and the Wiki's Quest lists. In particular:

```text
QuestIndex 1..36
    ↔ extracted quest condition row
    ↔ Japanese display text
    ↔ n2 / n2_1 producer
    ↔ gameplay mode/context
```

Once this is closed, `166 subtype 2/16` can distinguish event categories without guessing from numeric values alone.
