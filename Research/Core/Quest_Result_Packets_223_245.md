# PaperMan 2016 JP — Quest/Result Server Packets 223–245

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` dispatcher + parser/writer + Quest mutation

## 1. Packet family

TCP dispatcher routes:

```text
223 → sub_556730
225 → sub_556780
227 → sub_5567A0
229 → sub_5567C0
231 → sub_5568B0
233 → sub_5569A0
235 → sub_5569E0
237 → sub_556A30
239 → sub_556A70
241 → sub_556AF0
243 → sub_556B30
245 → sub_556C50
```

This is a server-side state/progress synchronization family around gameplay/result/Quest conditions.

---

## 2. Opcode 223

Parser:

```text
u32 value
```

Then:

```c
sub_92EF00(21, 23, value - dword_EE8D34, 0);
dword_EE8D34 = value;
```

Therefore:

```text
223 payload = u32 cumulative/monotonic timing-like state
```

Quest 21 progress is incremented by the delta between consecutive 223 values.

The timing unit must still be validated against the originating server timer; do not assume milliseconds merely from arithmetic.

Current semantic:

```text
223 = server/client synchronized elapsed-time state feeding Quest 21
```

Quest 21 remains a play-time candidate until the Quest resource row is matched.

---

## 3. Opcode 225

Parser:

```text
u32 value
```

Stored in:

```text
unk_EE8D38
```

No direct Quest mutation in this parser.

The writer counterpart is not emitted in the nearby code block, so exact request/response pairing remains unresolved.

---

## 4. Opcode 227

Parser:

```text
u32 value
```

Stored in:

```text
unk_EE8D3C
```

No direct Quest mutation in this parser.

---

## 5. Opcode 229 / 231 — Quest condition updates

### 229

Reads:

```text
u32 value → *dword_EE8D40
```

then:

```text
sub_92EF00(5, 23, 1, 0)
```

Thus the opcode's value is stored into the Client state and receipt itself completes one QuestIndex 5 progress unit.

### 231

Reads:

```text
u32 value → *dword_EE8D44
```

then:

```text
sub_92EF00(6, 23, 1, 0)
```

Thus opcode 231 is the direct trigger for QuestIndex 6 progress.

The exact public labels for Quest 5/6 require matching stored values against the Quest resource row.

---

## 6. Opcode 233 / 235

### 233

Reads u32 into a local `v2`, then:

```text
dword_EE8DAC += v2 - *dword_EE8D48
*dword_EE8D48 = v2
```

This is another cumulative/delta state counter. No direct Quest update is present in this parser.

### 235

Reads one u32 directly into:

```text
*dword_EE8D4C
```

No direct Quest update is present here.

---

## 7. Opcode 237 / 239 / 241 / 243 / 245

These share helper:

```text
sub_556A00(dst, packet)
```

which reads exactly:

```text
u32 value_A
u32 value_B
```

Therefore each packet has an 8-byte scalar body after the opcode/header layer.

### 237

Stores:

```text
value_A → *dword_EE8D50
value_B → dword_EE8DB0
```

### 239

Stores:

```text
value_A → *dword_EE8D54
value_B → dword_EE8DB4
```

### 241

Stores:

```text
value_A → *dword_EE8D58
value_B → dword_EE8DB8
```

### 243

Stores:

```text
value_A → *dword_EE8D60
value_B → dword_EE8DC0
```

then:

```text
sub_61FE40(&dword_1D09130, 5, 0, 0, 110)
sub_92EF00(11, 5, 0, 0)
```

### 245

Stores:

```text
value_A → *dword_EE8D64
value_B → dword_EE8DC4
```

then:

```text
sub_61FE40(&dword_1D09130, 6, 0, 0, 110)
sub_92EF00(12, 6, 0, 0)
```

The same structural pattern continues for locally neighboring handlers 247/255 and 381/383/385/387/389; these should be analyzed as one result/Quest state family rather than independently.

---

## 8. Extended neighboring mapping: 381 / 383 / 385 / 387 / 389

The same `sub_556A00()` two-u32 parser appears at:

```text
381 → sub_556CB0
383 → sub_556D10
385 → sub_556D70
387 → sub_556DD0
389 → sub_556E30
```

and each maps to:

```text
381 → Quest13 / n2=7
383 → Quest14 / n2=8
385 → Quest15 / n2=9
387 → Quest16 / n2=10
389 → Quest17 / n2=11
```

with:

```text
sub_61FE40(..., 7..11, 0, 0, 110)
sub_92EF00(13..17, 7..11, 0, 0)
```

This gives a coherent protocol pattern:

```text
server sends 2×u32 state for condition selector 7..11
    ↓
Client stores current + previous/secondary value
    ↓
sub_61FE40(..., selector, ..., 110)
    ↓
sub_92EF00(QuestIndex, selector, 0, 0)
```

The exact public labels of these conditions remain unresolved until the extracted Quest data is matched.

---

## 9. What the two-u32 pairs likely represent — and what is not proven

The two values are clearly a pair because every relevant parser reads them through the same helper and stores both. They appear to be a current value plus a secondary historical/threshold/result value, but this is not yet safe to rename universally.

For server reconstruction preserve:

```text
uint ValueA;
uint ValueB;
```

until the Quest/resource field names are recovered.

---

## 10. Quest architecture now visible

There are at least three distinct ways Client Quest progress changes:

```text
A. Gameplay event direct
   166 subtype 2/16
   → n2
   → sub_92EF00(...)

B. Dedicated server progress/result packets
   223..245 / 381..389
   → server state value(s)
   → sub_92EF00(...)

C. Specialized gameplay result events
   994 → Assist
   353/309/etc → player result/state
   35 → Soccer Goal
```

Therefore Quest is a cross-cutting consumer of several network/event families. A server implementation should not treat Quest as being driven only by kill packets or only by opcode 166.

---

## 11. Remaining proof targets

```text
1. Match QuestIndex 5/6/11–17 with Extracted Quest rows and Japanese text
2. Resolve what each pair ValueA/ValueB means
3. Locate request/send counterparts for 225/227/233/235/237/239/241/243/245
4. Continue neighboring 247/255/381–389 as the same result-state family
5. Cross-check all values with Wiki Quest timing/update rules
```
