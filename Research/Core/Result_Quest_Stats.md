# Result／Score／Quest／Event 整合研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 Result、長期統計、Score／K-D、Quest condition、Assist／Football，以及 `TCP 269 subtype 7` 的 Server→Client player/result hydration。避免結果、Quest、269 state 因不同 packet 範圍而拆成互相重複的主線。

## 1. 整體資料流

```text
Gameplay / Match event
    ↓
Result / Stat event
    ↓
Client result-state
    ├─ long-term account statistics
    ├─ per-player result K/D
    ├─ local result-screen statistics
    └─ special event statistics
    ↓
Quest condition evaluation
    ↓
Result / Quest UI
```

Server→Client 的 `269 subtype 7` 是另一個重要輸入：

```text
269 subtype 7
    → player/channel/game hydration
    → per-player result K/D
    → weapon/action/resource state
    → mode-specific state
    → global/per-player timing state
```

必須與即時 gameplay actor state 分開：

```text
player +240600 / +240604
    = live round / participant K/D-like state

F6DCF8 / F6DCFC
    = Server-provided per-player result K/D

player +60150 / +60151
    = local result-screen My K/D
```

Quest 是多來源 consumer，不是單一 Kill packet 的附屬功能。[C]

## 2. Result／Stat dispatcher

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

`269` 另由：

```text
269 → sub_574B20
```

再依 subtype 分支；`subtype 7` 屬大型 player/channel/game-state hydration family。[C]

## 3. 長期個人統計

Client UI 直接使用：

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

這證明 Result／MyInfo 不是單一平坦 scoreboard。[C]

## 4. Win／Lose／Kill／Death packet

```text
229 body = u32
229 value → EE8D40 = TOTAL_WIN / RECORDWIN

231 body = u32
231 value → EE8D44 = TOTAL_LOSE / RECORDLOSE

233 body = u32
233 value → EE8D48 = absolute / monotonic KILL record
EE8DAC       = delta accumulator

235 body = u32
235 value → EE8D4C = long-term DEATH record
```

`229/231` 的舊 Quest caller 使用 `sub_92EF00(5/6,23,1,0)`，但依實際 `sub_92EF00` 條件匹配規則，不能把第二參數 23 視為 QuestIndex；完整 Quest 證據見後文。[C][OPEN]

## 5. Packet 223：Play-time / timing-like state

```c
sub_592A40(a1, &v2);
sub_92EF00(21, 23, v2 - dword_EE8D34, 0);
dword_EE8D34 = v2;
```

因此：

```text
223 body = u32
223 value = monotonically tracked time-like state
EE8D34 = previous/current baseline
```

Client 嘗試把 delta 送入 generic Quest API，但因第二參數為 23，目前不能單靠這條 call 宣稱條件 21 已直接增加。[C]

Wiki 的 Quest 規則將 Play Time 視為獨立條件，並說明以分鐘計算、捨棄不足一分鐘的餘數；packet raw unit 仍 OPEN。[WIKI][OPEN]

## 6. Packet 225 / 227

```text
225 → u32 → EE8D38
227 → u32 → EE8D3C
```

目前缺乏足夠 consumer evidence，保持 raw state 名稱。[C][OPEN]

## 7. Special-shot / continuous-kill result packets

共同 parser：

```c
sub_556A00(state, packet)
```

直接讀：

```text
u32 ValueA
u32 ValueB
```

因此 `237/239/241/243/245` 都是 8-byte logical body。[C]

### 237

```text
ValueA → EE8D50
ValueB → EE8DB0
UI → HEADSHOT / SOLO_RESULT_R_HEADSHOT
```

### 239

```text
ValueA → EE8D54
ValueB → EE8DB4
UI → AIRCOMBO / SOLO_RESULT_R_AIRCOMBO
```

### 241

```text
ValueA → EE8D5C
ValueB → EE8DBC
UI → CRITICALSHOT / SOLO_RESULT_R_CRITICAL
```

### 243

```text
ValueA → EE8D60
ValueB → EE8DC0
sub_61FE40(..., 5, 0, 0, 110)
sub_92EF00(11, 5, 0, 0)
```

因此 `243` 同時更新 DOUBLEKILL 統計與 Quest 11。[C]

### 245

```text
ValueA → EE8D64
ValueB → EE8DC4
sub_61FE40(..., 6, 0, 0, 110)
sub_92EF00(12, 6, 0, 0)
```

因此 `245` 同時更新 TRIPLEKILL 統計與 Quest 12。[C]

另有 Client→Server opcode 244 request：

```c
Packet::possible_ctor_or_dtor_0(v1, 244);
sub_592A20(v1, a1);
*dword_EE8D64 = a1;
```

所以：

```text
244 = request carrying u32
245 = result/state carrying 2×u32
```

## 8. `381–389` 連續擊殺統計

```text
381 → EE8D68 / EE8DC8 → source 7 → Quest13
383 → EE8D6C / EE8DCC → source 8 → Quest14
385 → EE8D70 / EE8DD0 → source 9 → Quest15
387 → EE8D74 / EE8DD4 → source 10 → Quest16
389 → EE8D78 / EE8DD8 → source 11 → Quest17
```

UI labels：

```text
MULTIKILL
ULTRAKILL
GENOCIDE
KILLINGMACHINE
DIABLO
```

每一個 packet 都先更新 current/secondary state，再透過：

```text
sub_61FE40(..., source 7..11, ..., 110)
sub_92EF00(Quest13..17, source 7..11, 0, 0)
```

形成完整結果統計 → Quest condition 鏈。[C]

## 9. Score／K-D 三層模型

### Server-provided result K/D

`TCP 269 subtype 7`：

```text
v433 → dword_F6DCF8[60195 * slot]
v383 → dword_F6DCFC[60195 * slot]
```

Result UI 直接消費：

```text
F6DCF8 = KILL
F6DCFC = DEATH
```

這是 Server-provided per-player result/stat hydration。[C]

### Live round K/D

`Y_TCP_INF_ACK (166)` subtype 2/16：

```text
participant A → +240600 ++
participant B → +240604 ++（a4=0）
```

這是即時 round／mode-local state。[C]

### Local result-screen K/D

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前 `+60151` 有直接 death-path write；`+60150` 尚未找到同等直接 gameplay increment。[C][OPEN]

因此：

```text
live participant state
    ≠
server result synchronization
    ≠
local result-screen presentation state
```

## 10. Result ranking comparator

`sub_6482C0(a1,a2)`：

```c
if (KillA != KillB)
    return KillA >= KillB;

if (DeathA == DeathB)
    return F33184A < F33184B;

return DeathA < DeathB;
```

直接確認比較鏈：

```text
Kill 高者優先
→ Kill 相同時 Death 低者優先
→ 兩者相同時 dword_F33184 低者優先
```

`dword_F33184` 的寫入來源未閉合，不得猜其 public semantic。[C][OPEN]

`sub_759030()` 掃描 16 個 player slot，使用同一比較鏈尋找高成績玩家，並交給 Individual Survival display。[C]

日本 Wiki 的個人 Survival 規則與 Client 的 per-player K/D result state 可互相驗證；Team Survival 仍需在 mode layer 做隊伍聚合，不應將 per-player K/D 直接當 TeamKills。[WIKI][C][X]

## 11. Quest generic API：`sub_92EF00()`

### 11.1 參數順序的重要修正

Client export signature：

```c
char __stdcall sub_92EF00(int quest_or_event_id, char sub_type, int amount, int filter)
```

第一個整數會與 active Quest 的 `quest + 2324` 比較；第二個 byte 只參與 compound conditions 7–17。

因此：

```text
sub_92EF00(35,23,1,0)
```

不能直接視為 Quest 35 progress。這修正了舊研究中把第二參數 23 誤當 QuestIndex 的問題。

### 11.2 Exact condition matching

Direct conditions：

```text
Quest 1  ← first == 1   → += amount
Quest 2  ← first == 2   → += amount
Quest 3  ← first == 3   → += 1
Quest 4  ← first == 4   → += 1
Quest 5  ← first == 5   → += 1
Quest 6  ← first == 6   → += 1
```

Compound：

```text
Quest 7  ← first == 3  && second == 1 → += 1
Quest 8  ← first == 3  && second == 2 → += 1
Quest 9  ← first == 3  && second == 3 → += 1
Quest 10 ← first == 3  && second == 4 → += 1

Quest 11 ← first == 11 && second == 5  → += 1
Quest 12 ← first == 12 && second == 6  → += 1
Quest 13 ← first == 13 && second == 7  → += 1
Quest 14 ← first == 14 && second == 8  → += 1
Quest 15 ← first == 15 && second == 9  → += 1
Quest 16 ← first == 16 && second == 10 → += 1
Quest 17 ← first == 17 && second == 11 → += 1
```

Direct 18–36：

```text
Quest 18 ← first == 18 → += amount
Quest 19 ← first == 19 → += amount
Quest 20 ← first == 20 → += amount
Quest 21 ← first == 21 → += amount
Quest 22 ← first == 22 → += amount
Quest 23 ← first == 23 → += amount
Quest 24 ← first == 24 → += amount
Quest 25 ← first == 25 → += amount
Quest 26 ← first == 26 → += amount
Quest 27 ← first == 27 → += amount
Quest 28 ← first == 28 → = amount
Quest 29 ← first == 29 → = amount
Quest 30 ← first == 30 → = amount
Quest 31 ← first == 31 → = amount
Quest 32 ← first == 32 → += amount
Quest 33 ← first == 33 → = amount
Quest 34 ← first == 34 → = amount
Quest 35 ← first == 35 → += amount
Quest 36 ← first == 36 → += amount
```

這是 Client control flow；不代表每個條件的日文 public label 已閉合。[C]

### 11.3 Quest eligibility

`sub_92EF00()` 在 mutation 前還檢查：

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

所以：

```text
matching ID ≠ unconditional progress
```

需 active quest 與 mode/state eligibility 都成立後才會變更。

## 12. Quest 11–17 的完整閉合

目前最強的完整語意鏈：

```text
Quest 11 = Double Kill
Quest 12 = Triple Kill
Quest 13 = Multi Kill
Quest 14 = Ultra Kill
Quest 15 = Genocide
Quest 16 = Killing Machine
Quest 17 = Diablo
```

原因是：

```text
Client result-stat label
    +
243/245/381/383/385/387/389 packet update
    +
sub_92EF00 compound match
```

三者全部吻合。[C][X]

日本 Wiki 對 consecutive-kill hierarchy 的說明提供外部行為旁證；不取代 Client 的 condition matching 證據。[WIKI]

## 13. Earlier Quest 1/2/5/6/18–36 Claims — 已撤回

以下呼叫：

```text
sub_92EF00(1,23,...)
sub_92EF00(2,23,...)
sub_92EF00(5,23,...)
sub_92EF00(6,23,...)
sub_92EF00(18,23,...)
...
sub_92EF00(36,23,...)
```

不能僅以第一參數編號就宣稱對應 Quest；對應的 compound / direct condition 必須符合實際 `sub_92EF00` body。

這些 caller 仍可證明：

```text
23 是 Client generic Quest/event API 中反覆出現的 source/subtype-like value
```

但 `23` 的真正產品語意保持 `[OPEN]`。

## 14. Assist packet 994

`sub_5676D0()` 處理 opcode 994 的重複 server record：

```text
u8 record_type
u8/record player id
u32 value0
u32 value1
u32 value2
```

local-player path 在特定條件播放：

```text
ui\\sounds\\assist.wav
```

並更新 local assist-related state。

Independent Assist UI mapping：

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

因此：

```text
994 record_type 0x6B ↔ ASSIST_OCCUPY
```

為高信度 Client linkage。[C][X]

但 `sub_92EF00(36,23,1,0)`、`sub_92EF00(32,23,1,0)` 不能因此被解讀成 Quest36／Quest32 的直接進度。[C]

Wiki 另對 Assist Points 的 damage、airshot、healing、bomb、dye、pulp、occupation、soccer 行為提供外部旁證。[WIKI]

## 15. Soccer Goal event

`sub_566200()` 明確對應：

```text
GameNetwork::OnGLUserGoalFootballACK
```

並處理 football goal/player state。

可見：

```text
sub_92EF00(35,23,1,0)
```

但這不符合目前 `sub_92EF00` 對 Quest35 的條件 matching，因此：

```text
Soccer Goal event = proven
Quest35 ← Soccer Goal = NOT proven
```

需要實際 Quest resource row 或另一個匹配 producer 才能閉合。[C][OPEN][WIKI]

## 16. Quest 的三大來源

```text
A. Gameplay event
   166 subtype 2/16
   → event/resource
   → generic Quest API

B. Dedicated result/stat packets
   223–245 / 381–389
   → result/stat state
   → generic Quest API

C. Specialized events
   994 Assist
   353/309 等 player/result event
   35 / Soccer Goal
```

因此 Quest 是跨 gameplay、result、長期紀錄的共同 consumer。[C]

## 17. Resource／Wiki／Client 三方定位

```text
IDA C / LST
    → wire width、packet parser、caller/callee、state mutation、Quest control flow

Extracted
    → Quest/resource IDs、UI/localization、concrete data records

日本 PaperMan Wiki
    → 玩家可見的 Quest、Assist、Kill/Score 與模式行為
```

任何 public Quest label 都應優先走：

```text
Quest condition ID
    → Extracted Quest data
    → localization/resource label
    → Client consumer
    → Wiki behavior
```

而不是用 packet number 或 `sub_92EF00` caller 名稱反推。

## 18. Server reconstruction

結果資料模型：

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

Quest 為獨立 consumer：

```text
GameplayEvent / ResultRecord
    ↓
QuestConditionEvaluation
```

`QuestIndex`、`ValueB`、source/subtype `23` 皆不得在證據不足時直接當成正式 DB semantic。

## 19. `TCP 269` subtype 7：Server→Client player/result hydration

### 19.1 進入點與 Header

`269 → sub_574B20()`；先讀：

```text
u8 subtype
```

`subtype == 7` 是大型 player/channel/game-state synchronization branch。[C]

Header 依序：

```text
u32 v395
u32 n0x1770
u8  v370
u8  jj_1
u8  v431
u8  v358
u16 v374
u8  thisa_1
u8  v343
u16 v371
u8  v388
u8  v437
u16 v432
u8  v347
u8  v364
u8  v378
u8  v382
u8  v392
u8  v360
u8  v439
```

helper width 直接閉合：

```text
sub_592AC0     → 4 bytes
sub_592940/900 → 1 byte
sub_592A00     → 2 bytes
```

目前重要 state application：

```text
v395    → dword_F2A65C
n0x1770 → sub_537670(...)
v431    → sub_537690 / channel lookup
v388    → channel flags bit tests
v358    → channel +129
v370    → sub_540280(channel,...)
thisa_1 → sub_53FBB0(channel,...)
v371    → channel +144
v343    → channel +136
v432    → channel +148
v437    → channel +146
v374    → channel +110
v347    → channel +150
v364    → child +12
v378    → channel +185
v382    → channel +109
v392    → child +13
v360    → channel +128
v439    → child callback/state
```

因此 subtype 7 header 本身會修改 channel/game state，不只是 player count。[C]

### 19.2 Repeated player record 與 identity

```text
for (jj = 0; jj < jj_1; ++jj)
```

因此 `jj_1` 是 player record count。[C]

每筆前綴：

```text
u32 v407[0]
u8  n16_3
string/blob v399
u8  v381
u8  v427
u32 v433
u32 v383
u32 v389[?]
u8  v413
u8  v344
```

`v399` 使用 `sub_592730()`，所以為 variable/string-like data。[C]

直接 state flow：

```text
v407[0] → dword_F3312C[slot]
v381   → sub_548940(playerState,&v399,v381)
v427   → sub_548B00(playerState,v427)

n16_3  → dword_F6DCF4[slot]
v433   → dword_F6DCF8[slot]
v383   → dword_F6DCFC[slot]
v413   → byte_F6DD00[slot]
v344   → byte_F6DD11[slot]
```

`n16_3` 是 server-provided player/actor identity candidate；不要直接命名為 SQL user id、session id 或 slot id。[C][OPEN]

### 19.3 K/D 結果同步

同一筆 record 直接：

```text
F6DCF8[60195 * slot] = v433
F6DCFC[60195 * slot] = v383
```

Result UI：

```text
TEAM_RESULT_B_TEXT_KILL  → F6DCF8
TEAM_RESULT_B_TEXT_DEATH → F6DCFC
```

`sub_759030()` 亦用這兩個值進行 result ranking。[C]

此章節的 K/D layer 已在「Score／K-D 三層模型」統一定義，不在此建立第二份結論；本節只保存 `269` 的 producer/field evidence。

### 19.4 Conditional spawn／state block

當：

```text
v413 == 0
```

再讀：

```text
u32 v396
u16 v390
u16 v348
u16 v429
u16 v425
u8  v384
```

寫入：

```text
dword_F6DD04
word_F6DD08
word_F6DD0A
word_F6DD0C
word_F6DD0E
byte_F6DD10
```

這是實際 conditional wire block，不是 padding。[C]

### 19.5 Local-player detection

Client 以 `sub_537740(byte_EE8968)` 與 player record 中 string/blob 比較；符合時：

```text
byte_F6DD11[slot] = 1
byte_F6DD60[slot] = 1
byte_F6D9EF[slot] = 1
```

並更新 local network identity / mode state。因此 `v399` 並非純 UI name。[C]

### 19.6 Additional per-player state

每筆 record 還讀：

```text
u8  v414
u16 v359
u16 v366
u16 v434
u32 v438
u32 v375
u32 n0xA_3
string Source_1
```

並：

```text
v414 → n64[slot]
v359 → word_F6DD14[slot]
v366 → n46[slot]
v434 → n445[slot]
v438 → sub_548A90()
v375 → sub_548A40()
n0xA_3 + Source_1 → sub_54A740() emblem/texture state
```

public semantic 仍 `[OPEN]`，但 width／state destination 已閉合。[C]

### 19.7 四組 Weapon／Action Resource blocks

每筆 player record 還包含 4 組 weapon/action group。

每組至少：

```text
u16 itemId
```

若 `kk != 3`：

```text
u16 subValue0
u16 subValue1
u16 subValue2
```

若 `itemId != 0`：

```text
8 × u32
```

並經：

```text
sub_5F5400(resourceTable,itemId)
sub_5F5400(resourceTable,subValue0)
```

若 Resource category 為 `10 / 14 / 15`，會設定狀態並觸發：

```text
sub_9B8D40(player)
```

因此這些 blocks 是 player weapon/action/resource state，不是普通 Inventory snapshot。[C]

### 19.8 Optional 8×u32 state block

之後讀：

```text
u8 v368
```

若非零：

```text
u32 v327[0..7]
```

目的與 mode/player-specific state 有關，保持 raw。[C][OPEN]

### 19.9 Mode-dependent tail

common player record 後依 active mode object/vtable 分支，例如：

```text
mode 12 → additional u8/state path
mode 13 → player/slot state，可能填 dword_F6DDA8[slot]
mode 11 → sub_760BA0(child, packet)
others  → u32/u8/u8/u32，可能再讀 16-slot timing/state array
```

不能併入固定 common record schema，因 parser shape 隨 mode 改變。[C]

### 19.10 Global tail 與 16-player sync

player records 後讀：

```text
u8  v373
u8  v424
u8  v379
u8  v385
u8  v356
u8  v394
u8  v440
u32 n0x3E8
u8  v410
```

再讀：

```text
u8  v386
u32 v361
u16 v357
u16 v412
u8  v426
```

最後重複 16 次：

```text
u32 v387
    → dword_F6DD1C[slot]
```

目前以 `PerPlayerSyncDword` 暫名；它與其它 gameplay/result path 有直接依賴，但正式 public semantic `[OPEN]`。[C][OPEN]

### 19.11 Timer／state application

Header `n0x1770` 與 common tail `n0x3E8` 會進 timer/state helper，例如：

```text
sub_7180C0(...)
```

不同 mode/path 對 `n0x1770` 可出現 `-6000` / `-7000` 類調整。[C]

這證明 Server packet 提供 timing/state integer，但不能僅由數值命名成可見比賽倒數。[C][OPEN]

### 19.12 `269 subtype 7` 完整資料流

```text
269
 ↓
sub_574B20
 ↓ subtype 7
global/channel header
 ↓
player count
 ↓
player identity / name-like data
 ↓
result K/D + flags
 ↓
conditional spawn/state
 ↓
weapon/action/resource blocks
 ↓
optional 8×u32 state
 ↓
mode-specific tail
 ↓
global + 16-player sync tail
```

因此適合的 Server abstraction 是：

```text
ServerPlayerStateHydration
```

而不是把整包硬壓成 `PlayerResultPacket`。

## 20. Result／269 Server reconstruction

跨 packet 的 Server data model 應維持：

```text
PlayerRecord
├─ Identity
├─ Win/Lose records
├─ ResultKill / ResultDeath
├─ LiveRoundKill / LiveRoundDeath
├─ SpecialShotRecords
├─ ConsecutiveKillRecords
├─ Weapon/Action/ResourceState
├─ ModeSpecificState
└─ UnknownSecondaryValues
```

其中：

```text
269 subtype 7
    → Server-provided result/player hydration

166 subtype 2/16
    → live gameplay participant event

223–245 / 381–389
    → result/stat event family

994 / 353 / 309 / football events
    → specialized event family
```

不同 packet 可以共同修改同一 PlayerRecord，但不能因此把它們的 wire schema 合併成同一 packet。

## 21. Resource／Wiki／Client 三方定位

```text
IDA C / LST
    → wire width、packet parser、caller/callee、state mutation、Quest control flow

Extracted
    → Quest/resource IDs、UI/localization、concrete data records

日本 PaperMan Wiki
    → 玩家可見的 Quest、Assist、Kill/Score 與模式行為
```

任何 public label 都應優先走：

```text
Client state / condition ID
    → Extracted data
    → localization/resource label
    → Client consumer
    → Wiki behavior
```

而不是用 packet number、Hex-Rays 變數名稱或函式 caller 名稱直接反推。

## 22. 重要 OPEN

```text
EE8D38 / EE8D3C 正式語意
EE8DAC 正式用途
223 實際時間單位與 producer
237/239/241/243/245 與 381–389 第二個 u32 語意
Quest 1–10、18–36 public resource label
225/227/233/235 request/send counterpart
381–389 Server sender 與完整 result generation
F33184 writer/source
+60150 真正 gameplay/result writer
994 / 353 / 309 / football event 與 Quest condition 完整對應
269 header 各欄位正式語意
269 n16_3 具體 ID namespace
269 player flags/state formal names
269 weapon/action 每個 field semantics
269 optional 8×u32 用途
269 mode-specific tail 完整 wire schema
269 dword_F6DD1C formal semantic
269 Server sender / upstream state source
```

所有未知值保持 raw／`[OPEN]`，不得因 Server 實作方便而填入猜測值。
