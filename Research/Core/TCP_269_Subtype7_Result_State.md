# PaperMan 2016 JP — TCP 269 Subtype 7 / Server-Provided Result State

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact parser trace + result UI cross-reference  
> Confidence：直接 Client code = A；尚未有 server-side source 時保留 raw semantics

本文件記錄一個重要 correction：`dword_F6DCF8` / `dword_F6DCFC` 並非只在 gameplay kill event 中產生；它們由 TCP opcode `269` 的 `subtype 7` repeated player records 直接灌入。

---

## 1. 269 dispatch

TCP dispatcher：

```text
sub_58B010 / central TCP dispatcher
    ↓
case 269
    ↓
sub_574B20(a2, a3, a4)
```

`sub_574B20()`：

```text
u8 n7
```

並依 `n7` 分派。`n7 == 7` 是大型 player/game-state synchronization branch。

---

## 2. Subtype 7 前綴 fields

在 `n7 == 7` branch 開頭，依序：

```text
u32  field_00 = v395
u32  field_04 = n0x1770
u8   field_08 = v370
u8   field_09 = jj_1
u8   field_0A = v431
u8   field_0B = v358
u16  field_0C = v374
u8   field_0E = thisa_1
u8   field_0F = v343
u16  field_10 = v371
u8   field_12 = v388
u32  field_13 = v437
u16  field_17 = v432
u32  field_19 = v347
u32  field_1D = v364
u32  field_21 = v378
u32  field_25 = v382
u32  field_29 = v392
u32  field_2D = v360
u32  field_31 = v439
```

這些欄位會大量直接寫入 channel/game controller state。例如：

```text
field_00 -> dword_F2A65C
field_0A -> channel/lobby game controller +129 / routing context
field_10 -> controller +144
field_17 -> controller +148
field_19 -> controller +150
field_21/25/29/2D/31 -> controller / mode state helpers
```

目前不要因名稱猜測 `field_00` 是 timestamp；Client 只直接使用它作為 gameplay/session state token 並存入 `dword_F2A65C`。

---

## 3. `field_09 = jj_1` 是 repeated-player-record count

後續：

```c
for (jj = 0; jj < jj_1; ++jj)
```

因此 `field_09` 確定是本 subtype 7 packet 後續 repeated record 的數量／迭代上限。

這是目前 `269 subtype 7` 最重要的 framing field 之一。

---

## 4. 每個 repeated player record

每次迭代讀取：

```text
u32  record field_00 = v407[0]
u8   record field_04 = n16_3
str  record field_05 = v399   (ASCII, null-terminated)
u8   record field_?? = v381
u8   record field_?? = v427
u32  record field_?? = v433
u32  record field_?? = v383
u32  record field_?? = v389[0]
u8   record field_?? = v413
u8   record field_?? = v344
```

因為 `v399` 是變長 ASCII string，後續欄位不能僅用固定 byte offset 描述；正確 framing 是：

```text
u32
u8
stringZ
u8
u8
u32
u32
u32
u8
u8
```

---

## 5. `record field_04 = n16_3` 是 player identifier

直接寫入：

```text
dword_F6DCF4[60195 * slot] = n16_3
```

因此這裡的 `n16_3` 是 server 傳入的 player/actor identity，並與 slot mapping 綁定。

---

## 6. K/D server state：最重要的新證據

同一 repeated record 直接做：

```c
dword_F6DCF8[60195 * slot] = v433;
dword_F6DCFC[60195 * slot] = v383;
```

即：

```text
record u32 v433
    ↓
F6DCF8[slot]

record u32 v383
    ↓
F6DCFC[slot]
```

這說明這兩個 K/D-related state 並非由 `sub_7463E0()` 進行唯一初始化，而是至少存在一條 **server → client player-state hydration path**。

---

## 7. Final/team result UI 直接證明兩者名稱

完整 result rendering 有：

```text
TEAM_RESULT_B_TEXT_KILL
    ↓
dword_F6DCF8[60195 * slot]

TEAM_RESULT_B_TEXT_DEATH
    ↓
dword_F6DCFC[60195 * slot]
```

因此：

```text
F6DCF8 = team/result KILL value
F6DCFC = team/result DEATH value
```

confidence A。

此外，`sub_759030()` 用 `F6DCF8` 作第一排序 key、`F6DCFC` 作第二排序 key，進一步表明它們是正式 result/stat state，而非 transient rendering variables。

---

## 8. 與 166 subtype 2/16 的關係

166 `sub_7463E0()` 另有：

```text
+240600
+240604
```

它們在 gameplay event 中被 participant-directed increment：

```text
first participant → +240600 ++
second participant → +240604 ++  (a4 == 0)
```

因此目前必須區分兩個層級：

```text
166 subtype 2/16
    = live gameplay event
    = immediate round-local counter mutation

269 subtype 7
    = server-provided player-state synchronization
    = F6DCF8/F6DCFC K/D state hydration
```

不要因兩者都最終顯示 Kill/Death，就假定它們是同一 wire fields 或同一 update event。

---

## 9. `+60150/+60151` 又是第三層

Result-screen local fields：

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前 exact C export：

```text
+60151
    → 有 direct gameplay death-path write

+60150
    → 目前沒有找到 direct gameplay write
```

所以目前最可靠的資料分層為：

```text
F6DCF8/F6DCFC
    = server-provided per-player team/result K/D state

+240600/+240604
    = live round/mode participant Kill/Death counters

+60150/+60151
    = local player result-screen MY Kill/Death fields
```

其中三者可能在正常結果下數值相互關聯，但 **不能因 UI 相似而合併**。

---

## 10. `record field_??` surrounding state

在 K/D 欄位前後還有：

```text
record string v399
→ sub_548940(player, &v399, v381)

record byte v427
→ sub_548B00(player, v427)

record u32 v407[0]
→ dword_F3312C[slot]

record byte v413
→ byte_F6DD00[slot]

record byte v344
→ byte_F6DD11[slot]
```

所以 K/D 欄位位於一個更大的 server player-state record 中，不能把 repeated record 抽象成只有 K/D。

---

## 11. Resource / equipment fields in the same subtype

當 `v413 == 0` 時，還會繼續讀：

```text
u32
u16
u16
u16
u16
u8
```

並保存到：

```text
dword_F6DD04
word_F6DD08
word_F6DD0A
word_F6DD0C
word_F6DD0E
byte_F6DD10
```

此外後續會重複讀取最多四組 item/resource blocks；每組至少：

```text
u16 resource id
u16 secondary resource id
u16 action/effect id
u16 property
[u32 × 8 when primary resource != 0]
```

並透過：

```text
sub_5F5400(resourceTable, id)
sub_956BB0(...)
sub_5F67A0(...)
```

接入 Resource / action metadata。

這說明 subtype 7 是大型 **player state hydration packet**，而非只有 gameplay score。

---

## 12. Research correction

之前若把：

```text
F6DCF8/F6DCFC
```

描述成「只在 gameplay kill event 內維護的 K/D counters」，應修正為：

> 它們是 Client 正式使用的 Kill/Death result state，且已找到明確 Server→Client hydration source：TCP `269 subtype 7` repeated player record 的兩個 u32 欄位。166 subtype 2 的 live event 另外會更新 `+240600/+240604`；兩者不能混為一談。

這個修正對 Server reconstruction 很重要：Server 必須能在 player-state synchronization 階段提供 K/D，而不是只在每次 kill event 時傳一個即時 increment。

---

## 13. Remaining proof targets

```text
1. 解析 repeated record 中 v433 / v383 的固定 field offsets（需以 stringZ 長度扣除）
2. 找到 269 subtype 7 的 server sender/corresponding request path
3. 找到 +60150 的完整 write/source；優先找 result-stage hydration/copy
4. 找到 F3319C Assist result array 的真正 writer（目前 direct symbol search 只有 reads）
5. 把 subtype 7 的四組 resource blocks 與 Extracted item/effect/resource tables 逐一對 id
6. 比較 269 subtype 7 與 166 subtype 13/14 的 state precedence
```
