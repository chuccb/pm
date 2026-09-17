# `TCP 269` subtype 7 玩家狀態同步與欄位深入研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件現在同時承擔原本 `TCP_269_Subtype7_Field_Detail.md` 與 `TCP_269_Subtype7_Result_State.md` 的內容：前者負責完整 parser／欄位，後者的 K/D、Result state 與 Server→Client hydration 證據已整合至本文件，不再維護第二份平行結論。

## 1. 封包進入點

TCP dispatcher：

```text
269 → sub_574B20()
```

`sub_574B20()` 先讀取：

```text
u8 subtype
```

其中 subtype 7 是大型 match/channel/player-state synchronization branch。[C]

## 2. subtype 7 Header 欄位

開頭依序讀取：

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

其中：

```text
sub_592AC0     → 4 bytes
sub_592940/900 → 1 byte
sub_592A00     → 2 bytes
```

因此上述 width 是由實際 helper 讀取寬度直接確認，而不是由 Hex-Rays 表面型別猜出來。[C]

### 2.1 Header State Application

目前已看到：

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

之後設定 channel/game state 並把 16 個 player state block 清理，再進入 repeated player list。[C]

因此 subtype 7 顯然不是只有「玩家數量 + 玩家資料」的簡單列表；Header 本身也會修改 channel/gameplay state。[C]

## 3. `jj_1` 是玩家記錄數量

後續直接：

```c
for (jj = 0; jj < jj_1; ++jj)
```

因此 `jj_1` 是 repeated player record 的 count／iteration upper bound。[C]

## 4. Repeated Player Record：前綴

每筆記錄開始讀取：

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

`v399` 由 `sub_592730()` 讀取，因此它是變長字串／資料塊；後續欄位不能用「固定總長 offset」取代。[C]

資料流立即把欄位寫入 player state：

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

## 5. Player Identity

`n16_3` 直接寫入：

```text
dword_F6DCF4[60195 * slot]
```

因此它是 Server 提供、與 slot 綁定的 player/actor identity。[C]

目前仍不要把它直接改名成某一種 SQL user id、session id 或 slot id；只能說它是 server-provided compact player identity，其 local mapping 仍需由其他資料流確認。[C][OPEN]

## 6. Server-Provided Result／K/D State

同一筆 repeated record 直接做：

```text
dword_F6DCF8[60195 * slot] = v433
dword_F6DCFC[60195 * slot] = v383
```

這是非常重要的 authority 證據：K/D 結果狀態至少有一條明確的 Server→Client hydration path，並非全部由本地 gameplay event 即時計算。[C]

### 6.1 Result UI Cross-check

完整結果呈現路徑使用：

```text
TEAM_RESULT_B_TEXT_KILL
    → dword_F6DCF8[60195 * slot]

TEAM_RESULT_B_TEXT_DEATH
    → dword_F6DCFC[60195 * slot]
```

此外 `sub_759030()` 會使用 `F6DCF8` 作排序 key，`F6DCFC` 作第二排序 key，進一步證明它們是正式 result/stat state，而非 transient rendering value。[C]

因此目前可記為：

```text
F6DCF8 = team/result Kill value
F6DCFC = team/result Death value
```

這是直接 Client code + UI cross-reference 的高信度語意。[C][X]

## 7. 與 `166 subtype 2/16` 的結果層級區分

`166` 的 `sub_7463E0()` 另外修改：

```text
+240600
+240604
```

在 normal `a4 == 0` 路徑：

```text
participant A → +240600 Kill++
participant B → +240604 Death++
```

因此：

```text
166 subtype 2/16
    = 即時 gameplay event / participant state mutation

269 subtype 7
    = Server 提供的 player-state hydration / result stat synchronization
```

兩者都可能與 Kill/Death 有關，但不能假定同一欄位、同一封包或同一 update event。[C]

## 8. `+60150/+60151` 是第三層結果狀態

Result screen local fields：

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前 exact C evidence 顯示：

```text
+60151
    → 有直接 death-path write

+60150
    → 目前未找到同等直接 gameplay increment/write
```

因此 Server reconstruction 必須分成至少三層：

```text
F6DCF8/F6DCFC
    = Server-provided per-player team/result Kill/Death

+240600/+240604
    = live round/mode participant Kill/Death

+60150/+60151
    = local player result-screen My Kill/Death
```

它們的數值可能互相相關，但不可僅因 UI label 相似就合併。[C]

## 9. Negative Evidence：不要假設 `+60150` 一定由 166 直接遞增

對完整 `PaperMan.exe.c` 搜尋 `60150`，目前主要找到 result/UI read，例如：

```c
v93 = *(v94 + 60150);
```

送入 `SOLO_RESULT_R_MY_KILL`。[C]

相較之下 `+60151` 可以找到更直接的 death-path write。因此目前不能建立：

```text
166 kill event → ++60150
```

作為已證實規則。[C][OPEN]

## 10. Conditional 13-byte Spawn／State Block

若：

```text
v413 == 0
```

則再讀取：

```text
u32 v396
u16 v390
u16 v348
u16 v429
u16 v425
u8  v384
```

並寫入：

```text
dword_F6DD04
word_F6DD08
word_F6DD0A
word_F6DD0C
word_F6DD0E
byte_F6DD10
```

這是實際 conditional wire block，不是 padding。[C]

## 11. Local-player Detection

Client 會以 `sub_537740(byte_EE8968)` 與 player record 中的 string/blob 比較。符合時，會設定：

```text
byte_F6DD11[slot] = 1
byte_F6DD60[slot] = 1
byte_F6D9EF[slot] = 1
```

並更新 local network identity / mode state。[C]

因此 `v399` 並非純 UI 名稱；它參與 local-player identity 判定。[C]

## 12. Additional Per-player State

後續每筆 record 還會讀：

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

並寫入／呼叫：

```text
v414 → n64[slot]
v359 → word_F6DD14[slot]
v366 → n46[slot]
v434 → n445[slot]
v438 → sub_548A90()
v375 → sub_548A40()
n0xA_3 + Source_1 → sub_54A740() emblem/texture state
```

這些欄位的精確公開語意仍 `[OPEN]`，但其 width 與 state destination 是直接證據。[C]

## 13. 四組 Weapon／Action Resource Blocks

每筆 player record 之後還包含 4 組 weapon/action group。

每組至少：

```text
u16 itemId
```

若 `kk != 3`，再讀三個 u16：

```text
u16 subValue0
u16 subValue1
u16 subValue2
```

若 `itemId != 0`，再讀：

```text
8 × u32
```

並解析 Resource：

```text
sub_5F5400(resourceTable,itemId)
sub_5F5400(resourceTable,subValue0)
```

若 Resource category 為 `10 / 14 / 15`，會設定狀態，之後觸發：

```text
sub_9B8D40(player)
```

因此這些 blocks 是實際 player weapon/action/resource state，不是普通 Inventory snapshot。[C]

不要把這四組直接與其它 action/resource manager 的不同物件 layout 壓平。[C]

## 14. Optional 8×u32 State Block

之後讀：

```text
u8 v368
```

若非零，則再讀 8 個 u32：

```text
v327[0..7]
```

其目的與 mode/player-specific state 有關，目前保持 raw 形式。[C][OPEN]

## 15. Mode-dependent Tail

Common player record 後可能依 active mode object/vtable 分支：

```text
mode 12
    → additional u8/state path

mode 13
    → player/slot-dependent state
    → 可能填入 dword_F6DDA8[slot]

mode 11
    → sub_760BA0(child, packet)

其他 mode-specific path
    → u32/u8/u8/u32
    → 可能再讀 16-slot timing/state array
```

這些 tails 不可併入固定的 common record schema，因為 parser shape 隨 mode 改變。[C]

## 16. Common Global Tail 與 16-player Sync State

repeated player records 完成後，還會讀取：

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

這組 16 個 DWORD 與 player slot 直接綁定，並會被其它 gameplay/result path 使用；公開語意尚未完全閉合，因此採 `PerPlayerSyncDword` 暫名。[C][OPEN]

## 17. Timer／State Application

Header 中的 `n0x1770` 與 common tail 的 `n0x3E8` 會進入 timer/state helper，例如：

```text
sub_7180C0(...)
```

不同 mode/path 可能對 `n0x1770` 進行 `-6000` 或 `-7000` 類調整。[C]

這直接證明 Server packet 提供 timing/state 整數，但尚不能僅由這個值命名成「可見比賽倒數時間」。[OPEN]

## 18. subtype 7 的整體語意

目前最合理的 server-side abstraction 是：

```text
269 subtype 7
    = server-provided player/channel/game state hydration
      + per-player result/stat state
      + equipment/resource state
      + mode-specific state
      + global/per-player timing state
```

這與：

```text
166
    = realtime gameplay event family

UDP 8/24
    = realtime movement/state synchronization family
```

應保持不同層級。[C]

## 19. 目前已閉合的結論

```text
269 subtype 7
    → 先解析 global/channel header
    → jj_1 決定 player record 數量
    → 逐 player hydration
    → 條件式 spawn/state block
    → weapon/action/resource blocks
    → optional 8×u32 block
    → mode-specific tail
    → global + 16-player sync tail

n16_3
    = server-provided player identity candidate

v433 → F6DCF8
    = team/result Kill value

v383 → F6DCFC
    = team/result Death value

+240600/+240604
    = 與 166 live participant event 分開的 round-local state

+60150/+60151
    = local result-screen My K/D，第三層
```

## 20. 尚未閉合的項目

```text
1. Header 各欄位的官方／公開語意
2. v407[0] 的正式語意
3. n16_3 的具體 ID namespace
4. v381/v427/v414 等 player flags/state 的正式名稱
5. v359/v366/v434/v438/v375 的公開語意
6. emblem/texture block 的完整 schema
7. 四組 weapon/action resource block 的每個 u16/u32 語意
8. optional 8×u32 block 的用途
9. 所有 mode-specific tail 的完整 wire schema
10. 16 × dword_F6DD1C 的正式語意
11. +60150 的真正 writer/source
12. 269 subtype 7 的 Server sender 與上游 state source
13. outer sequence/checksum/encryption/frame details
```

未知欄位保持 `[OPEN]`；不得因為 Server 實作方便而命名成 guessed semantics 或填入固定值。
