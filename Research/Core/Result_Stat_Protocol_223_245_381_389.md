# `223–245`／`381–389` 結果、長期統計與 Quest 協定

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是 `223–245`、`381–389` 結果／長期統計／Quest 網路資料域的唯一主文件。原本 `Quest_Result_Packets_223_245.md` 與 `Score_State.md` 的研究已整合至此。`Quest_Event_ID_Mapping.md` 仍保留，因它是跨多個網路事件的 Quest ID 字典，而不是本文件的結果封包副本。

## 1. 架構定位

這一族不是 TCP 166 即時 actor event，也不是 UDP movement。它主要同步 Client 的長期紀錄、結果統計與部分 Quest condition state。

```text
Server result / record state
    ↓
223–245 / 381–389
    ↓
Client global statistics
    ↓
MyInfo / GameRoom / Result UI
    ↓
Quest condition evaluation
```

必須與以下資料層分開：

```text
player +240600 / +240604
    = live round / participant K/D-like state

player +60150 / +60151
    = local result-screen My K/D

F6DCF8 / F6DCFC
    = per-player Server-provided result K/D
```

## 2. Dispatcher

`sub_58B010()` 直接路由：

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

這是直接 dispatcher 證據。[C]

## 3. 長期個人紀錄欄位

Client UI 明確使用：

```text
EE8D40 → RECORDWIN / TOTAL_WIN
EE8D44 → RECORDLOSE / TOTAL_LOSE
EE8D48 → KILL
EE8D4C → DEATH
EE8D50 → HEADSHOT
EE8D54 → AIRCOMBO
EE8D58 → HEARTBREAK
EE8D5C → CRITICALSHOT
EE8D60 → DOUBLEKILL
EE8D64 → TRIPLEKILL
EE8D68 → MULTIKILL
EE8D6C → ULTRAKILL
EE8D70 → GENOCIDE
EE8D74 → KILLINGMACHINE
EE8D78 → DIABLO
```

Result-screen globals：

```text
EE8DB0 → SOLO_RESULT_R_HEADSHOT
EE8DB4 → SOLO_RESULT_R_AIRCOMBO
EE8DB8 → SOLO_RESULT_R_HEARTCNT
EE8DBC → SOLO_RESULT_R_CRITICAL
```

Per-player result fields：

```text
player +31    → SOLO_RESULT_R_ASSIST
player +60150 → SOLO_RESULT_R_MY_KILL
player +60151 → SOLO_RESULT_R_MY_DEATH
```

這證明 Result／MyInfo 並不是單一平坦 scoreboard，而是多層 state。[C]

## 4. Packet 229 / 231：Win／Lose long-term records

### 229

```c
sub_592A40(a1, dword_EE8D40);
sub_92EF00(5, 23, 1, 0);
```

因此：

```text
229 body = u32
229 value → EE8D40 = TOTAL_WIN / RECORDWIN
receipt → Quest condition 5
```

Quest 5 的正式公開名稱仍以 Quest resource row 為準。[C]

### 231

```c
sub_592A40(a1, dword_EE8D44);
sub_92EF00(6, 23, 1, 0);
```

因此：

```text
231 body = u32
231 value → EE8D44 = TOTAL_LOSE / RECORDLOSE
receipt → Quest condition 6
```

不能因此自行把 Quest 6 命名成「敗數 Quest」；Quest 公開 label 仍待 Resource 對照。[C][OPEN]

## 5. Packet 233 / 235：長期 Kill／Death record

### 233

```c
sub_592A40(a1, &v2);
dword_EE8DAC += v2 - *dword_EE8D48;
*dword_EE8D48 = v2;
```

因此：

```text
233 body = u32
233 value → EE8D48 = absolute / monotonic KILL record
EE8DAC   = delta accumulator
```

`EE8DAC` 目前沒有足夠 UI evidence 形成正式公開名稱。[C][OPEN]

### 235

```c
sub_592A40(a1, dword_EE8D4C);
```

因此：

```text
235 body = u32
235 value → EE8D4C = long-term DEATH record
```

目前 parser 沒有直接 Quest call。[C]

## 6. Packet 223：Play-time / timing-like state

```c
sub_592A40(a1, &v2);
sub_92EF00(21, 23, v2 - dword_EE8D34, 0);
dword_EE8D34 = v2;
```

因此：

```text
223 body = u32
223 value = monotonically tracked time-like state
Quest21 amount = delta from previous value
```

Wiki 的 Quest 規則指出 Play Time 以分鐘計算並捨棄不足一分鐘的餘數；但 packet raw unit 尚不能單憑除法就命名為 milliseconds。[C][WIKI][OPEN]

## 7. Packet 225 / 227：鄰近 state values

```text
225 → u32 → EE8D38
227 → u32 → EE8D3C
```

目前沒有足夠直接 consumer evidence 完成正式公開名稱，因此保持：

```text
EE8D38 = raw u32 state from 225
EE8D3C = raw u32 state from 227
```

後續應從 UI、producer 與 resource 對照閉合。[C][OPEN]

## 8. `237 / 239 / 241 / 243 / 245`：雙 `u32` 統計配對

共同 helper：

```c
sub_556A00(state, packet)
```

直接讀取：

```text
u32 ValueA
u32 ValueB
```

所以這些 packet 都具有 8-byte logical body。[C]

### 8.1 237：HEADSHOT

```text
ValueA → EE8D50
ValueB → EE8DB0
```

UI 對應 `HEADSHOT` / `SOLO_RESULT_R_HEADSHOT`。[C]

### 8.2 239：AIRCOMBO

```text
ValueA → EE8D54
ValueB → EE8DB4
```

UI 對應 `AIRCOMBO` / `SOLO_RESULT_R_AIRCOMBO`。[C]

### 8.3 241：CRITICALSHOT／相關 result state

Client 具有：

```text
ValueA → EE8D5C
ValueB → EE8DBC
```

UI 對應 `CRITICALSHOT` / `SOLO_RESULT_R_CRITICAL`。[C]

研究時不可只依 opcode 相鄰性命名，應依 Client UI consumer 與 data-flow。[C]

### 8.4 243：DOUBLEKILL

```text
ValueA → EE8D60
ValueB → EE8DC0
```

UI 對應 `DOUBLEKILL`；收到後還會：

```text
sub_61FE40(..., 5, 0, 0, 110)
sub_92EF00(11, 5, 0, 0)
```

因此 `243` 同時是長期統計同步與 Quest condition 11 的觸發點。[C]

### 8.5 245：TRIPLEKILL

parser：

```text
ValueA → EE8D64
ValueB → EE8DC4
```

並：

```text
sub_61FE40(..., 6, 0, 0, 110)
sub_92EF00(12, 6, 0, 0)
```

UI 對應 `TRIPLEKILL`。[C]

另存在 Client→Server opcode 244 request：

```c
Packet::possible_ctor_or_dtor_0(v1, 244);
sub_592A20(v1, a1);
*dword_EE8D64 = a1;
```

因此：

```text
244 = request carrying u32
245 = result/state carrying 2×u32
```

這是 request/result 結構差異的直接證據。[C]

## 9. 381 / 383 / 385 / 387 / 389：連續擊殺統計族

共同使用兩個 u32 state：

```text
381 → EE8D68 / EE8DC8 → source 7 → Quest13
383 → EE8D6C / EE8DCC → source 8 → Quest14
385 → EE8D70 / EE8DD0 → source 9 → Quest15
387 → EE8D74 / EE8DD4 → source 10 → Quest16
389 → EE8D78 / EE8DD8 → source 11 → Quest17
```

UI 直接命名：

```text
EE8D68 = MULTIKILL
EE8D6C = ULTRAKILL
EE8D70 = GENOCIDE
EE8D74 = KILLINGMACHINE
EE8D78 = DIABLO
```

每個 packet 都透過共同 2×u32 解析器更新 current/secondary state，再觸發：

```text
sub_61FE40(..., source 7..11, ..., 110)
sub_92EF00(Quest13..17, source 7..11, 0, 0)
```

日本 Wiki 另描述 consecutive-kill hierarchy，包括 Killing Machine 與 Diablo 的連續擊殺條件；這可作為 public behavior 的外部旁證，但不替代 packet field proof。[C][WIKI]

## 10. Quest condition 的三條主要網路來源

Client Quest progress 至少存在：

```text
A. Gameplay event
   166 subtype 2/16
   → n2 / resource
   → sub_92EF00(...)

B. Dedicated result/record packets
   223–245 / 381–389
   → state value(s)
   → sub_92EF00(...)

C. Specialized gameplay result events
   994 / Assist
   353/309 等 player/result event
   35 / Soccer Goal
```

因此 Quest 是橫跨 gameplay、result、長期紀錄的共同消費者，不應被 Server 寫成「只靠 Kill packet 驅動」。[C]

## 11. Score／K-D State：與 166 及 Result UI 的三層分離

### 11.1 Server-provided player Result K/D

`TCP 269 subtype 7` 直接將：

```text
v433 → dword_F6DCF8[60195 * slot]
v383 → dword_F6DCFC[60195 * slot]
```

Result UI 又直接讀取：

```text
F6DCF8 = KILL
F6DCFC = DEATH
```

因此這是 Server-provided per-player result/stat hydration。[C]

### 11.2 Live round participant K/D

`Y_TCP_INF_ACK (166)` subtype 2/16 的 death/gameplay 路徑會：

```text
participant A → +240600 ++
participant B → +240604 ++（a4=0）
```

這屬於即時 round/mode-local state。[C]

### 11.3 Local result-screen My K/D

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前對 `+60151` 找得到直接 death-path write，但對 `+60150` 尚未找到同等直接 gameplay increment。[C][OPEN]

因此三層必須分開：

```text
live participant state
    ≠
server result synchronization
    ≠
local result-screen presentation state
```

## 12. Result ranking comparator

`sub_6482C0(a1, a2)` 實際比較：

```c
if (KillA != KillB)
    return KillA >= KillB;

if (DeathA == DeathB)
    return F33184A < F33184B;

return DeathA < DeathB;
```

因此 C 直接證明的 comparator 是：

```text
1. Kill 高者優先
2. Kill 相同 → Death 低者優先
3. 兩者相同 → dword_F33184 低者優先
```

`dword_F33184` 的寫入來源目前未閉合。不得因 Wiki 的某項 tie-break 規則就把它命名成 participant count 或其它公開欄位。[C][OPEN]

## 13. High-score selector

`sub_759030()` 掃描 16 個 player slot，使用同一 Kill/Death/`F33184` 比較鏈尋找高成績玩家。它的結果再交給 Individual Survival mode display。[C]

因此 Kill/Death comparator 不只是 UI 排序，也參與 mode/runtime 選擇。[C]

## 14. Wiki × C 的模式驗證

日本 Wiki 的個人サバイバル規則以「時間內擊殺數」決定勝負，並列出 20/30/40/50 Kill 及 10/15/20 分等條件；C 則直接以 `F6DCF8` 顯示 KILL、`F6DCFC` 顯示 DEATH，並用 Kill/Death comparator 選取高成績。[WIKI][C][X]

チームサバイバル則以隊伍累積擊殺數作為模式層勝負條件，但 Client result state 仍是 per-player K/D，因此 Server 應拆成：

```text
PlayerScore
├─ Kill
└─ Death

TeamRule
└─ mode-specific aggregation
```

不可把 `F6DCF8` 命名成 `TeamKills`。[WIKI][C]

## 15. Resource 分層證據

`Extracted/0.xml` 直接列出：

```xml
<PackFile key="character" filename="Data\\character.dat" folderpath="character\\" />
<PackFile key="item" filename="Data\\item.dat" folderpath="item\\" />
<PackFile key="map" filename="Data\\map.dat" folderpath="map\\" />
<PackFile key="pmClient" filename="Data\\pmClient.dat" folderpath="" />
```

`ClientDataList.xml` 又存在：

```xml
<DataList key="BulletHole" />
<DataList key="effect" />
<DataList key="ui" />
<DataList key="ui_temp" />
```

這支持：

```text
Wiki       = public behavior
Extracted  = resource/data identity
IDA C/LST  = executable data-flow / protocol evidence
```

但不能因資源樹存在就單獨宣布某個 score field 的 semantic。[RES]

## 16. Server Reconstruction 模型

結果／長期統計層應至少抽象為：

```text
PlayerRecord
├─ WinRecord
├─ LoseRecord
├─ KillRecord
├─ DeathRecord
├─ SpecialShotRecords
├─ ConsecutiveKillRecords
└─ UnknownSecondaryValues
```

Quest 應為獨立 consumer：

```text
Result/Record Packet
    ↓
Client record state
    ↓
Quest condition evaluation
```

不能把 `QuestIndex` 直接當成資料庫欄位，也不能把 `ValueB` 未證明地命名成 threshold、timestamp 或 count。

## 17. 尚未閉合的項目

```text
1. EE8D38 / EE8D3C 的正式公開語意
2. EE8DAC 的正式用途
3. 223 的實際時間單位與 producer
4. 237/239/241/243/245 與 381–389 的第二個 u32 語意
5. Quest5/6/11–17 的正式 resource label
6. 225/227/233/235 等 request/send counterpart
7. 381–389 的 Server sender 與完整 result generation
8. dword_F33184 的 writer/source
9. +60150 的真正 gameplay/result writer
10. 223–389 outer framing、sequence、checksum、encryption
```

所有未知欄位維持 raw／`[OPEN]`，不得為 Server 實作方便而填入猜測值。
