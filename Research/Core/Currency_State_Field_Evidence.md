# PaperMan 2016 JP — Currency / Profile State Field Closure

> 研究日期：2026-09-17  
> Evidence：IDA `PaperMan.exe.c` UI binding + packet receiver writes.  
> Purpose：把先前被暫時寫成 `EE8D18 / ArgList / EE8D1C` 的未知值正式閉合，並回填 packet 205/207 的 trailing fields。

## 1. Three global profile-economy fields are directly UI-labelled

The `INFORMATION → MYINFO → RECORD_TAB` construction directly formats these globals into named UI fields:

```text
*dword_EE8D18 → "PG"
*ArgList      → "CASH"
*dword_EE8D1C → "CP"
```

This is direct Client UI evidence, not inference from packet names.

The same routine also shows:

```text
*dword_EE8D40 → TOTAL_WIN
*dword_EE8D44 → TOTAL_LOSE
*dword_EE8D48 → MY_KILL
*dword_EE8D4C → MY_DEATH
*ArgList      → CASH
*dword_EE8D18 → PG
*dword_EE8D1C → CP
```

So the economy variables are now closed as:

```text
EE8D18 = PG
EE8D1C = CP
CASH   = global ArgList used by these routines
```

The `ArgList` symbol is a Hex-Rays/global-name artifact; use a semantic alias such as `g_Cash` in reconstructed code, while preserving the raw address as provenance.

---

## 2. Packet 205 trailing currency fields

`sub_571910()` parses the repeated collection records and then reads:

```text
u32 v22
u32 v16
u32 v26
u32 v20
u32 v15
u32 v27
u32 v18
```

If `i_1 != 0`, it assigns:

```c
*dword_EE8D18 = v16;
*ArgList      = v20;
*dword_EE8D1C = v27;
```

Therefore the packet portion is now unambiguously:

```text
... repeated records ...
u32 trailing_0
u32 PG
u32 trailing_2
u32 CASH
u32 trailing_4
u32 trailing_5
u32 CP
```

The remaining four u32 values are still unresolved.

The Client explicitly updates the live PG/CASH/CP globals from these fields, so a reconstructed server cannot omit them from the success path.

**Confidence:** A.

---

## 3. Packet 207 trailing currency fields

`sub_571B60()` first decodes/updates one collection record and then reads six trailing u32 values:

```text
u32 v21
u32 v19
u32 v13
u32 v18
u32 v14
u32 v22
```

It directly assigns:

```c
*dword_EE8D18 = v14;  // PG
*ArgList      = v18;  // CASH
*dword_EE8D1C = v22;  // CP
```

Thus packet 207 also carries live economy synchronization.

Exact body tail:

```text
... collection record ...
u32 trailing_0
u32 trailing_1
u32 trailing_2
u32 CASH
u32 PG
u32 CP
```

where the first three positions remain raw because the current C consumer does not attach public names to them.

**Confidence:** A for PG/CASH/CP position.

---

## 4. Why this changes the reconstruction model

The 201/202/205/207 collection protocol is not only item-list synchronization. It also synchronizes account-economy state.

The client architecture is therefore closer to:

```text
collection/item mutation
        ↓
item/resource record table
        ↓
PG / CASH / CP totals
        ↓
MYINFO UI + purchase/item UI
```

This also explains why these packets trigger `sub_522440(dword_EE3950)` and other UI refresh paths after parsing.

---

## 5. Direct economy write callsites

The same C file contains dedicated functions which write and immediately bind the globals to UI labels:

```text
sub_45FCA0(a2)
    → *dword_EE8D18 = a2
    → UI label "PG"

sub_45FD80(a2)
    → *ArgList = a2
    → UI label "CASH"

sub_45FE60(a2)
    → *dword_EE8D1C = a2
    → UI label "COUPON"
```

Therefore `CP` is represented as the client economy variable that the UI layer labels `COUPON`.

Use both names in research:

```text
raw/global: EE8D1C
semantic: CP
UI label: COUPON
```

rather than treating `CP` and `COUPON` as two independent currencies.

---

## 6. Remaining economy questions

Still open:

```text
205 trailing_0 / trailing_2 / trailing_4 / trailing_5
207 first three trailing u32
```

These should be resolved by finding their writers/consumers, not by assuming they are another currency. Candidate domains include rank/experience/coupon-adjacent account state, but no public name is assigned yet.

Likewise, packet 223's u32 must not automatically be called PG/CASH/CP simply because it updates a nearby result structure; its own downstream path remains the authority.
