# PaperMan 2016 JP — Gameplay 166 K/D Field Evidence

> 研究日期：2026-09-16  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA Hex-Rays C export + exact field search + cross-function data flow + mode/UI cross-check  
> Purpose：補充 `Gameplay_166_DeepEvidence.md`，專門固定 `+240600/+240604`、`+60150/+60151` 四組結果欄位的證據邊界。

## 1. `sub_7463E0()` 已直接建立「killer-side / victim-side」雙玩家結果更新

`sub_7463E0()` 的參數：

```text
n16 = outer 166 actor/player-like id

a4  = 0 for subtype 2
a4  = 1 for subtype 16
```

payload 另外讀取：

```text
n16_2 = second player id
```

並立即建立兩個 slot mapping：

```text
v85 = sub_67D7D0(n16_1)
v87 = sub_67D7D0(n16_2)
```

後續 UI/effect notification 仍保留兩者的方向性；在 local-player branch 中，`n16_1 == localPlayer` 與 `n16_2 == localPlayer` 分別走不同通知路徑。這表示兩個 ID 不是同義重複欄位，而是事件中的兩個不同 participant。[A]

## 2. 最直接的結果 counter mutation

在 `sub_7463E0()` 後半段：

```c
v68 = sub_67D7D0(n16_1);
v67 = sub_67D7D0(n16_2);

if (v68 < 0 || v67 < 0)
    return;

if (v68 != v67)
{
    if (sub_67D630(v68, v67)
        && ((resource(v90[0]) category == 4)
         || (resource(v90[0]) category == 5)))
    {
        // CViewObj::OnDeadCtrl diagnostic path
    }
    else
    {
        ++byte_F33120[240780 * v68 + 240600];
    }
}

if (a4 == 0)
    ++byte_F33120[240780 * v67 + 240604];
```

因此在正常 `a4 == 0` 路徑：

```text
n16_1 / v68
    → +240600 increment

n16_2 / v67
    → +240604 increment
```

而第二個 increment 明確被 `a4 == 0` 條件控制。

結合同一函式先對 `n16_2` 做：

```text
sub_67DF00(n16_2)
→ controller
→ sub_9BC470(...)
→ controller/runtime dead-state transition
```

目前最穩健的語義是：

```text
+240600 = round / mode-local Kill counter for first participant (killer-side)
+240604 = round / mode-local Death counter for second participant (victim-side), on a4==0 path
```

這比先前的「兩個未命名 result counters」更精確，confidence A（語義來自直接 mutation + participant direction + result UI）。

## 3. `a4 == 1` 是重要例外，不得忽略

dispatcher 明確：

```text
166 subtype 2
    → sub_7463E0(..., a4 = 0)

166 subtype 16
    → sub_7463E0(..., a4 = 1)
```

因此 subtype 16 共享同一 participant/death-state machinery，但：

```text
if (a4 == 0)
    victim +240604 ++
```

在 subtype 16 路徑不成立。

另一方面，當 `n16_2 == localPlayer` 且 `sub_67EE30()` 成立時：

```text
if (a4 == 1)
    this +96 = 4000
else
    this +96 = 0
```

因此 `a4` 明確控制額外的 local gameplay state/timing 行為。

**結論：不要把 subtype 16 直接命名為普通 Kill/Death packet。** 正確表述是：

> subtype 2/16 共用一個大型 participant/gameplay-state event parser；`a4` 改變結果計數與 local timing/state branch。subtype 2 的 `a4=0` 路徑具有完整 killer-side / victim-side round counter mutation；subtype 16 的 `a4=1` 路徑不做 victim `+240604` increment。

[A]

## 4. `+240600` 的 UI cross-check

初始化：

```c
*(this + 240600) = 0;
*(this + 240604) = 0;
```

`CyIndividualSurvivalMode::sub_76FA50()` 的 `RoundStat` 顯示路徑直接取：

```c
v8 = player->field_240600;
```

並以 `Num16x16` renderer 顯示。

這是一個非常強的 mode/result presentation anchor：

```text
sub_7463E0 participant update
        ↓
+240600
        ↓
RoundStat
        ↓
Num16x16
```

因此 +240600 並非暫時運算變數。[A]

## 5. `+240604` 的 UI cross-check

在 team/member panel builder `sub_640110()` 中，程式同時讀：

```c
*(a5 + 240600)
*(a5 + 240604)
```

並進入 member/result presentation data path。

同一 player object layout 的這兩個欄位始終一起被初始化、一起隨 player stride 240780 保存，符合 per-player round/stat pair。[A]

目前 `+240604` 的「Death」語義最強證據仍來自 `sub_7463E0()` 的 participant-directed increment：第二 participant 進入 death-state transition，接著 `a4==0` 才對該 participant 的 +240604 increment。

因此可以記為：

```text
+240604 = round / mode-local Death counter (normal a4=0 gameplay path)
```

confidence A，並保留 subtype-16 exception。[A]

## 6. 這四個欄位必須分成兩層

### Round / mode-local pair

```text
+240600 → killer-side round/stat Kill
+240604 → victim-side round/stat Death (a4=0)
```

### Result-screen MY pair

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

`+60150/+60151` 是在 result UI 中直接送入：

```text
sub_65FD40(..., field)
```

且其中 `+60150` 明確對應 `SOLO_RESULT_R_MY_KILL`，`+60151` 明確對應 `SOLO_RESULT_R_MY_DEATH`。[A]

這表示 server model 不應用同一個 field 同時承擔：

```text
round live scoreboard state
```

和：

```text
final result-screen MY_K/D state
```

即使兩者數字常常可能同步，也不能在 protocol reconstruction 中假設它們是同一儲存位置或同一更新事件。

## 7. `+60150` 的關鍵 negative evidence

對目前完整 `PaperMan.exe.c` 做 exact search：

```text
60150
```

可見主要是 result/UI read：

```c
v93 = *(v94 + 60150);
```

送進 `SOLO_RESULT_R_MY_KILL`，以及另一組結果畫面路徑。

目前沒有找到與 +60151 類似的直接 gameplay increment/write：

```c
*(player + 60151) = 1;
```

可在 tutorial/training death path 直接觀察到。

因此：

```text
+60151
    = client-visible My Death result field
    = 有直接 client death-path write

+60150
    = client-visible My Kill result field
    = 目前沒有找到同等直接 write/increment evidence
```

**不能**因為結果資源名叫 `MY_KILL`，就反推出 Client 在每次正式 PvP kill 時自己 `++60150`。更可能存在另一條 result/event/network synchronization source，但其 writer 仍需定位。

## 8. Participant direction 與 UI/result direction 的交叉圖

目前最可靠的完整圖：

```text
TCP 166
  ↓
outer n16 = participant A
  ↓
payload n16_2 = participant B
  ↓
sub_67D7D0(A/B)
  ↓
participant-specific event handling
  ├─ B remote/local death-state transition
  │    └─ sub_9BC470(B,...)
  │
  └─ normal a4=0:
       A +240600 (round Kill)
       B +240604 (round Death)
  ↓
RoundStat / member UI

separate result fields:
  +60150 → MY_KILL UI
  +60151 → MY_DEATH UI
```

這條圖把「live round stat」、「death-state transition」、「final result display」三個層次分開，是目前 Server reconstruction 應採用的 abstraction boundary。

## 9. 不應做出的過度結論

目前仍不能單憑這組 evidence 宣稱：

```text
+60150 writer = 166 subtype 2
```

也不能宣稱：

```text
subtype 16 = respawn packet
```

或：

```text
subtype 2 = every possible kill event in every mode
```

原因是 `sub_7463E0()` 本身還有：

```text
resource category branches
team relation branches
magic_finger exception
local-player special handling
mode-specific a4 behavior
```

因此 packet semantics 必須繼續按 mode/resource/event-context 拆解。

## 10. 下一個 proof target

最值得繼續追的不是再命名 offset，而是：

```text
1. locate writer/source of +60150
2. locate exact producer of Assist event types
3. compare +240600/+240604 mutation against Wiki kill-log / survival rules
4. resolve resource IDs used as v90[0] in subtype 2/16
5. determine subtype-16 a4=1 via caller-side mode/state context
6. trace `sub_61FC20()` effect types 1/4/5/6/7
7. trace `sub_92EF00()` event notification paths
```

這些完成後才能把 Kill / Assist / special shot / mode-specific result semantics 真正閉合。
