# PaperMan 2016 JP — Result / Long-Term Stat Packet Protocol 223–245 / 381–389

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact dispatcher/parser/serializer + Client UI labels + Quest callsites + Wiki timing cross-check  
> Confidence：直接 Client code = A；未閉合 semantic 保留 raw opcode/field name

## 1. Architectural distinction

這一族不是 TCP 166 的即時 actor event，也不是 UDP movement。

它主要同步 Client 的長期/結果統計值，部分 packet 再觸發 Quest condition progress。

```text
Server result/stat state
    ↓
223–245 / 381–389
    ↓
Client global stat variables
    ↓
MyInfo / GameRoom / Result UI
    ↓
Quest condition evaluation
```

不要把這些 global result variables 與：

```text
player +240600 / +240604   ← round/live participant result
player +60150 / +60151     ← result-screen MY K/D fields
```

混為同一層。

---

## 2. Dispatcher：已證實的 packet → parser mapping

`sub_58B010()`：

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
381 → sub_556CB0
383 → sub_556D10
385 → sub_556D70
387 → sub_556DD0
389 → sub_556E30
```

這是直接 dispatcher evidence。[A]

---

## 3. Long-term record counters

Client UI 明確把以下 globals 顯示成：

```text
EE8D40 → GAMEROOM_RECORDWIN / RECORDWIN
EE8D44 → GAMEROOM_RECORDLOSE / RECORDLOSE
EE8D48 → GAMEROOM_KILL / KILL
EE8D4C → GAMEROOM_DEATH / DEATH
```

MyInfo/record UI 亦直接顯示相同四個值：

```text
TOTAL_WIN
TOTAL_LOSE
MY_KILL
MY_DEATH
```

因此這一層是 Client 的 long-term/per-profile result records，而不是單局 actor state。[A]

### 3.1 Packet 229

Parser：

```c
sub_592A40(a1, dword_EE8D40);
sub_92EF00(5, 23, 1, 0);
```

即：

```text
u32 → EE8D40
```

UI semantic：

```text
EE8D40 = RECORDWIN / TOTAL_WIN
```

並在收到 packet 後執行 Quest condition 5。

**可確定：229 的 body 是一個 u32 long-term win/record value。**[A]

Quest5 的正式公開名稱仍應以 Quest resource row 再核，但它與 `TOTAL_WIN` 的 Client state source 已閉合。[A]

### 3.2 Packet 231

Parser：

```c
sub_592A40(a1, dword_EE8D44);
sub_92EF00(6, 23, 1, 0);
```

即：

```text
u32 → EE8D44
```

UI semantic：

```text
EE8D44 = RECORDLOSE / TOTAL_LOSE
```

因此 231 是一個 `u32` 的 long-term loss/record state synchronization packet。[A]

**注意：不能因此直接把 Quest6 命名成「敗數 Quest」；Wiki 公開條件列表主要使用「勝數」「プレイ回数」等名稱，正式 Quest6 label 仍需 resource row。[C/A]

### 3.3 Packet 233

Parser：

```c
sub_592A40(a1, &v2);
dword_EE8DAC += v2 - *dword_EE8D48;
*dword_EE8D48 = v2;
```

即：

```text
u32 server value
    ↓
EE8D48 = KILL record
    ↓
EE8DAC += delta
```

所以 `EE8D48` 是 server-provided absolute/monotonic kill record value，Client 同時維護一個 `EE8DAC` 的 delta accumulation。

不要把 `EE8DAC` 自動當成另一個 K/D 顯示欄位；目前 exact UI label 尚未找到。[A]

### 3.4 Packet 235

```c
sub_592A40(a1, dword_EE8D4C);
```

即：

```text
u32 → EE8D4C = DEATH record
```

目前這個 parser 沒有額外 Quest call。[A]

---

## 4. Special-shot / result-stat pair packets

這一組都使用共同 helper：

```c
sub_556A00(int *state, packet)
```

其實際行為：

```text
u32 newCurrent
u32 associatedValue
```

兩個 consecutive `u32`。[A]

### 4.1 Packet 237

```text
old current = *EE8D50
read u32 current
read u32 associated
associated → EE8DB0
old/global current ← current
```

UI：

```text
EE8DB0 = HEADSHOT
```

所以：

```text
237 = 2×u32 special/result stat record
       → updates HEADSHOT result value
```

[A]

### 4.2 Packet 239

```text
old current = *EE8D54
read 2×u32
second → EE8DB4
first → EE8D54
```

UI：

```text
EE8DB4 = AIRCOMBO
```

因此：

```text
239 = AIRCOMBO result-stat pair
```

[A]

### 4.3 Packet 241

```text
old current = *EE8D5C
read 2×u32
second → EE8DBC
first → EE8D5C
```

UI：

```text
EE8DBC = CRITICALSHOT
```

因此：

```text
241 = CRITICALSHOT result-stat pair
```

[A]

### 4.4 Packet 239/241/237 ordering must not be inferred from opcode numbers

The public semantic comes from Client UI consumers:

```text
237 → HEADSHOT
239 → AIRCOMBO
241 → CRITICALSHOT
```

rather than from numeric adjacency.

---

## 5. Heartbreak result stat

Packet 243 is **not** Heartbreak.

Heartbreak is:

```text
EE8DB8 → SOLO_RESULT_R_HEARTCNT
```

and MyInfo uses:

```text
*EE8D58 → HEARTBREAK
```

The parser that updates this is:

```text
sub_556AF0 → packet 241 in the main dispatcher
             or corresponding legacy/current route depending on dispatcher table
```

Therefore the exact mapping between `EE8D58`/`EE8DB8` and packet opcode is retained at function-level, not guessed from variable order. [A]

> **Important correction:** do not assume packet 241 because of the sequential offset pattern; exact dispatcher evidence should be consulted when implementing.

---

## 6. Multi-kill / combo stat packet family 243–389

### Packet 243

Parser:

```c
v2[0] = *dword_EE8D60;
sub_556A00(v2, a1);
dword_EE8DC0 = v2[1];
*dword_EE8D60 = v2[0];
sub_61FE40(&dword_1D09130, 5, 0, 0, 110);
sub_92EF00(11, 5, 0, 0);
```

UI:

```text
EE8D60 = DOUBLEKILL current/record state
EE8DC0 = secondary value
```

The Client MyInfo UI directly displays `EE8D60` under:

```text
DOUBLEKILL
```

Quest condition 11 is evaluated with source/discriminator `5`.

### Packet 245

A client-side request constructor exists:

```c
Packet::possible_ctor_or_dtor_0(v1, 244);
sub_592A20(v1, a1);
*dword_EE8D64 = a1;
```

and parser 245 does:

```c
v2[0] = *dword_EE8D64;
sub_556A00(v2, a1);
dword_EE8DC4 = v2[1];
*dword_EE8D64 = v2[0];
sub_61FE40(..., 6, 0, 0, 110);
sub_92EF00(12, 6, 0, 0);
```

UI:

```text
EE8D64 = TRIPLEKILL
EE8DC4 = secondary value
```

Thus 244/245 form a request/result pair with the request carrying one `u32` baseline/current value and the server response carrying a 2×u32 state pair.[A]

### Packets 381 / 383 / 385 / 387 / 389

All are parser-only Server→Client paths in the current C export:

```text
381 → sub_556CB0 → EE8D68 / EE8DC8 → DOUBLE/MULTI chain source 7 → Quest13
383 → sub_556D10 → EE8D6C / EE8DCC → source 8 → Quest14
385 → sub_556D70 → EE8D70 / EE8DD0 → source 9 → Quest15
387 → sub_556DD0 → EE8D74 / EE8DD4 → source 10 → Quest16
389 → sub_556E30 → EE8D78 / EE8DD8 → source 11 → Quest17
```

Client MyInfo labels prove:

```text
EE8D68 = MULTIKILL
EE8D6C = ULTRAKILL
EE8D70 = GENOCIDE
EE8D74 = KILLINGMACHINE
EE8D78 = DIABLO
```

And the Quest mapping is direct:

```text
Quest11 ← source5
Quest12 ← source6
Quest13 ← source7
Quest14 ← source8
Quest15 ← source9
Quest16 ← source10
Quest17 ← source11
```

The Wiki independently documents the consecutive-kill hierarchy: Killing Machine is the 7th consecutive kill; the 8th and later are Diablo, with the chain governed by the short consecutive-kill interval.[C]

This gives a strong semantic bridge between the Client's stat labels and the Wiki behavior, while the exact 381–389 packet body remains `2×u32` until more server-side semantics are recovered.[A/C]

---

## 7. Packet 223: play-time synchronization

Parser:

```c
u32 v2;
sub_592A40(a1, &v2);
sub_92EF00(21, 23, v2 - dword_EE8D34, 0);
dword_EE8D34 = v2;
```

Thus:

```text
223 body = u32
223 u32 = monotonically tracked time-like server value
Quest21 amount = delta from previous value
```

Wiki cross-check says Play Time progress is measured in minutes and discards sub-60-second remainder, but the Client packet's raw unit should remain `u32 time-like` until more producer evidence closes the exact unit.[C]

---

## 8. Packet 225 / 227: state values without direct Quest mutation

```text
225 → u32 → EE8D38
227 → u32 → EE8D3C
```

Their current exact public semantics are not proved by their local parser alone.

They are displayed/used elsewhere as record-layer state, but the final public labels must be derived from surrounding Client UI/producer context rather than variable order.

Keep raw:

```text
EE8D38 = u32 state/value from 225
EE8D3C = u32 state/value from 227
```

until further mapping.

---

## 9. Client→Server request packets

### 9.1 Opcode 230

`sub_5567F0(int a1)`:

```text
Packet opcode 230
body: u32 a1
store same value into EE8D44
```

This is Client→Server because the function constructs a Packet and invokes `sub_555090(socket, packet)`.[A]

### 9.2 Opcode 232

`sub_5568E0(int a1)`:

```text
Packet opcode 232
body: u32 a1
store same value into EE8D48
```

Client→Server.[A]

### 9.3 Opcode 244

`sub_556B90(int a1)`:

```text
Packet opcode 244
body: u32 a1
store same value into EE8D64
```

Client→Server.[A]

These request constructors do not by themselves prove the business meaning of the outgoing value; their state coupling is proven by the matching global variable and result parser.[A]

---

## 10. Result UI: exact current stat storage map

From Client UI:

```text
Long-term / MyInfo:
    EE8D40 → RECORDWIN
    EE8D44 → RECORDLOSE
    EE8D48 → KILL
    EE8D4C → DEATH
    EE8D50 → HEADSHOT
    EE8D58 → HEARTBREAK
    EE8D5C → CRITICALSHOT
    EE8D54 → AIRCOMBO
    EE8D60 → DOUBLEKILL
    EE8D64 → TRIPLEKILL
    EE8D68 → MULTIKILL
    EE8D6C → ULTRAKILL
    EE8D70 → GENOCIDE
    EE8D74 → KILLINGMACHINE
    EE8D78 → DIABLO
```

Result-screen globals:

```text
EE8DB0 → SOLO_RESULT_R_HEADSHOT
EE8DB4 → SOLO_RESULT_R_AIRCOMBO
EE8DB8 → SOLO_RESULT_R_HEARTCNT
EE8DBC → SOLO_RESULT_R_CRITICAL
```

Per-player result fields:

```text
player +31    → SOLO_RESULT_R_ASSIST
player +60150 → SOLO_RESULT_R_MY_KILL
player +60151 → SOLO_RESULT_R_MY_DEATH
```

This is a three-layer statistic model, not one flat scoreboard.

---

## 11. Quest timing cross-check

The 2016-02-19 Wiki Quest system states:

```text
Kill count / special shot / multi-shot / assist
    → updated during the match

Play time / wins / play count / EXP/PG item collection
    → generally updated at match end / leave
```

and explicitly says play-time progress is represented in one-minute units with sub-minute remainder discarded. citeturn392521search0

This supports the architectural distinction between:

```text
live gameplay event packets
```

and:

```text
result/record/stat synchronization packets
```

but does not replace direct packet field evidence.

---

## 12. Do not over-interpret these fields

Still unresolved:

```text
225 EE8D38 exact public semantic
227 EE8D3C exact public semantic
233 EE8DAC exact lifetime accumulator semantic
243/245 and 381–389 secondary u32 semantic
exact Quest5/6 public labels
exact 28–34 Quest public labels
server-side generation rules for 223–245/381–389
sequence/checksum/header/encryption outer framing
```

All unresolved fields remain raw `u32`/`2×u32` in the protocol spec.
