# `Y_TCP_INF_ACK (166)` 二級 Handler 深入逆向

> 研究日期：2026-09-16
>
> 本文件承接 `Network_Dispatch.md`，只處理 `166 → sub_58D820 → sub_749B90` 之後的 gameplay Handler。重點是把 parser、state mutation、resource lookup 與 K/D 關係分開證明。

## 1. 完整 receive chain

目前已封死：

```text
TCP receive framing
    ↓
sub_58B010
    ↓ case 166
sub_58D820
    ↓
sub_749B90(dword_1D37560, packet)
    ↓
read u8 n16
read u8 n18
    ↓
second-level handler
```

`sub_58D820()` 本身沒有重新解析 payload，只把 packet 原樣交給 `sub_749B90()`。[C]

因此後面的 `n18` 是 `Y_TCP_INF_ACK` 內部真正的 second-level event discriminator。

---

## 2. `n18 == 3 / 20`：進入 `sub_747980` → `sub_747460`

`sub_747980()` 先讀：

```text
u32 v21
u8  n16_1
u16 v19[0..2]
u8  n20
u8  v15
u8  v18
u32 v16
u32 n26
u8  n0x1E
```

並做：

```c
if (sub_67D7D0(n16) >= 0)
    sub_747350(v19[0], slot);

if (dword_F2A65C == v21)
{
    sub_747460(
        this,
        n16,
        n16_1,
        v19[0],
        n20,
        v16,
        n26,
        n0x1E,
        n3);

    if (n16 != sub_67D010())
        sub_747B90(v19[0], n16_1, v15, v18, n16);
}
```

[C]

### `sub_747460` 的真正性質

它首先取得：

```c
v49 = sub_67DF00(n16);
v45 = sub_67DF00(n16_1);
```

並要求兩邊 player/object 都有效，而且 target object `v45[80]` 存在。[C]

對 target 的 local/remote state，它會比較：

```c
*(v45[80] + 16)
```

與 server 傳來的：

```c
a6
```

若不同，就依 `n20` 走不同效果；最後：

```c
if (v45[80] != 0)
    *(v45[80] + 16) = a6;
```

所以 `a6` 是一個 **直接被寫入 target runtime object 的 server-side state value**。[C]

目前從上下文最合理的描述是 HP-like / value-like state，但尚未找到該 `+16` struct field 的正式型別定義，因此文件保持 `target_object_value`，不把它硬命名成 HP。

### `n20` 的特殊分支

當：

```text
n20 == 20
```

會走：

```c
sub_5A6460(...)
```

而 remote target 還會：

```c
sub_5B8F10(v45[80], -1, 0.0, 0.0);
```

一般 `n20 != 20` 則依 `n20 == 1` 與否選擇不同 effect resource；若 target value 發生改變，會呼叫 `sub_5B8EE0()`。[C]

這說明 `n20` 是 gameplay event subtype / effect selector，而不是單純 damage amount。

---

## 3. `sub_747460` 與 resource/action data

`sub_747460()` 最後又：

```c
v44 = sub_5F5450(dword_1CC95A0, a4);
if (v44 != nullptr && sub_7473E0(n3, n26, n0x1E))
{
    n3_1 = sub_5EFE40(v44);
    sub_74CB20(this, n3, a4, n16, n16_1, n0x1E, n26, n3_1);
}
```

以及：

```c
if (v44 != nullptr && sub_5EFE00(v44) == 7)
    ...
```

[C]

也就是該 Handler 不只更新 target state，還會透過 `dword_1CC95A0` 做 resource/object lookup，再進 `sub_74CB20()`。

### `sub_74CB20` 做了什麼

先：

```c
v16 = sub_67DF00(n16a);
v17 = sub_995A00(dword_23164E8, n0x1E);
```

然後以 resource `a3` 查出：

```text
n21 = sub_5EFE40(resource)
```

對 `n21` = 1、2、3、4、5 以及 8..20 有不同 downstream route。[C]

其中：

```text
n21 == 1 → sub_5E6DA0(...)
n21 == 2 → sub_74D720(2,...)
n21 == 3 → sub_74D720(3,...)
n21 == 4 → sub_74D720(4,...)
n21 == 5 → sub_74D720(5,...)
n21 == 8..20 → sub_74D720(n21,6,...)
```

[C]

所以 `sub_74CB20` 是很明確的 **resource-category → local effect/state application bridge**。

這也解釋為何 `Y_TCP_INF_ACK` 的某些 subtype 不能單純命名為「damage ack」：它們其實會驅動 item/effect/action resource 系統。

---

## 4. `sub_74D720`：本地與遠端 target 的 state application

```c
if (a3 == sub_67D1D0())
    sub_74C880(...);
else if (a3 != 0)
{
    *(a3 + 2*n21 + 672) = a6;
    *(a3 + 4*n21 + 336) = 1;
}
```

[C]

這裡再一次看到：

```text
remote target
    → 寫入 target object 大型狀態陣列
```

而不是寫 `F6DCF8/F6DCFC`。

因此目前所有直接證據更支持：

```text
166
 ↓
gameplay runtime/object state
```

而非：

```text
166
 ↓
score counter++
```

---

## 5. `n18 == 21`：`sub_747DD0` → `sub_747B90`

`sub_747DD0()` 先確認 `n16 != local player`，然後讀：

```text
u8  n16_1
u16 v8[3]
u8  v9
u8  v7
```

最後：

```c
sub_747B90(v8[0], n16_1, v9, v7, n16);
```

[C]

`sub_747B90()` 又會：

```c
sub_5F5450(dword_1CC95A0, a1)
sub_5F0360(...)
sub_5F5B70(...)
sub_603230(...)
sub_5B8E90(...)
```

其中 `a3`、`a4` 最後會被乘：

```text
1 / 256
```

再交給：

```c
sub_5B8E90(target_object, a3/256, a4/256, 1)
```

[C]

因此這條 route 是很明確的 **remote actor action / vector-like data propagation**，而非 K/D 統計。

---

## 6. `n18 == 1`：直接驅動 player object effect

`sub_746360()`：

```c
sub_592940(a2, &n16_1);
v2 = sub_67DF00(n16_1);
if (v2 != 0 && *(v2 + 320) != 0)
{
    if (n16 != sub_67D010())
        sub_5B8EE0(*(v2 + 320));
    sub_5B8F70(*(v2 + 320));
}
```

[C]

因此它只有一個額外 u8，再直接操作 player runtime object；沒有 K/D counter write。

---

## 7. `n18 == 2 / 16`：大幅更新 player runtime state

`sub_7463E0()` 讀取：

```text
u32 v94
u8  n16_2
u16 v90[0..2]
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

接著：

```text
sub_67D7D0(n16_2)
sub_67DF00(n16_2)
```

做 source/target player state 解析。

若 `n16_2 == local player`，還會：

```c
sub_61FAC0(&dword_1D09130);
...
sub_74D690();
sub_5AA510(...);
...
sub_7226F0(...);
...
sub_62DCF0(...);
sub_62C180(...);
```

若是 remote player，則會：

```c
sub_9BC470(v77, 1, n0x64_0, 0, 0);
...
```

並使用 remote object coordinates / VirtualProcessor mask。[C]

因此這條 route 明顯是完整的 player/runtime state application；不應簡化成單一「位置封包」而未先閉合欄位。

---

## 8. `n18 == 12`：兩個 `u16` 的 state/control message

`sub_749A30()`：

```c
v2 = sub_592A00(a2, &v7);
sub_592A00(v2, &v6);
sub_67F2F0();
sub_67CD20(n9_0, v7, v6, 2 - !v3);
```

之後重建 UI/runtime state：

```text
sub_9F94C0
sub_62DCF0
sub_62E9E0
sub_62C180
sub_5A06B0
```

[C]

精確 public semantic 尚未閉合，但它顯然是兩個 16-bit scalar 所構成的 state/control event。

---

## 9. `n18 == 13`：完整 GameStart / round-state reset

此路徑會：

```text
清 byte_F6DD11[16 slots]
sub_95EC00(slot) × 16
重新建立 local/remote player state
sub_718000
sub_7603A0 (特定環境)
sub_67B5C0(..., -1)
sub_62D570
sub_720A10
```

[C]

其中 `sub_67B5C0` 正是先前已識別的 `NewGameStart`。

因此目前可提高 confidence：

```text
Y_TCP_INF_ACK field1 == 13
    → server-driven game/round restart lifecycle
```

但「RoundStart」還不是 packet table 的正式名字，文件仍應使用：

```text
server-driven game/round state reset/start path
```

---

## 10. `n18 == 24`：server-driven time state

該 route 讀一個 nested millisecond-like integer，接著：

```c
minutes = v24 / 1000 / 60;
seconds = v24 / 1000 % 60;
```

並：

```c
dword_1D0A970 = 1;
dword_1D0A974 = 0;
sub_7498E0(this, 24, 0, ...);
```

[C]

`sub_7498E0()` 再把 `(n18,n16,a4,a5,a6)` 傳入一個 virtual callback：

```c
(*(*v10 + 64))(v10, n18, n16, a4, a5, &a6);
```

並刷新 HUD/UI 等 subsystem。[C]

因此這條路是 server authoritative timing/state dispatch 的高 confidence 證據。

---

## 11. `sub_747460` 與 `Kill/Death`：目前最重要的反證

對 `dword_F6DCF8/F6DCFC` 做完整 source-level 搜尋後，目前直接寫入只有：

### 初始化

```c
dword_F6DCF8[60195 * i] = 0;
dword_F6DCFC[60195 * i] = 0;
```

### 玩家狀態同步 parser

```c
dword_F6DCF8[60195 * n0x10] = v433;
dword_F6DCFC[60195 * n0x10] = v383;
```

[C]

其它出現點主要是：

```text
result UI
comparator
score display
```

目前沒有找到：

```c
++dword_F6DCF8[...]
++dword_F6DCFC[...]
```

也沒有找到 `sub_747460` / `sub_747B90` / `sub_74CB20` 寫入這兩個 counter。[C]

### 因此目前結論必須修正成

```text
F6DCF8 = Kill count       [C confirmed]
F6DCFC = Death count      [C confirmed]

166 gameplay handlers
    → runtime/player/object state [C confirmed]
    → F6DCF8/F6DCFC mutation [NOT FOUND]
```

所以更合理的 architecture candidate 是：

```text
Server authoritative combat/game result
        │
        ├── Y_TCP_INF_ACK (166)
        │      └── real-time player/object state
        │
        └── another player-score/state synchronization path
               └── writes F6DCF8/F6DCFC
```

而不是先驗假設 166 自己改 score。

---

## 12. 與 Wiki 的對接

Wiki 的 public rule 可以確認：

```text
個人サバイバル：kill count 及 target kill / time 結束條件
チームサバイバル：team cumulative kill
チーム戦術：round / no-respawn-until-round-end
練習モード：K/D 不計算
```

因此 `F6DCF8/F6DCFC` 作為 client score display state 與 Wiki 的可見 K/D 行為是一致的。

但 Wiki 不提供 internal `Y_TCP_INF_ACK` subtype，因此不能用 Wiki 直接命名 `n18=3/20/21`。

---

## 13. Server implementation 嚴禁的過早簡化

現在不能寫：

```csharp
case 166:
    ReadDamageAck();
```

也不能寫：

```csharp
case 165:
    Score.Kill++;
```

更合理的是：

```text
Y_TCP_INF_ACK
  field0: player/actor-like u8
  field1: gameplay event subtype u8
  field1-specific payload
```

其中：

```text
n18=3/20  → player state/value + effect/resource processing
n18=21    → remote action/vector-like state
n18=13    → game/round lifecycle reset/start path
n18=24    → server-driven timer/state path
n18=1     → player runtime effect
n18=2/16  → player runtime state synchronization
n18=12    → two-u16 control/state message
```

這個 abstraction 比固定一個 `DamageAck` class 更貼近實際 client。

---

## 14. 下一步真正值得追的線

目前最有價值的三條：

```text
A. player-state synchronization parser
   ↓
   找出 `v433/v383` 來源
   ↓
   封死 F6DCF8/F6DCFC server packet format

B. `sub_67B5C0(NewGameStart)` 誰呼叫、如何收到 server 指示
   ↓
   連起 n18=13 與 round/end lifecycle

C. 159/160 `TCP_UDP_DEAD_*` + UDP 8/24
   ↓
   把 death / respawn / movement
   與 166 runtime state 做最後閉環
```

這三條比再猜 `n18` 名稱重要。
