# Combat Hit Detection：`CDamageDetect` / Hit Result / Damage Packet 前置鏈

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client／服務終了時版本

本文件專門整理目前從完整 `PaperMan.exe.c` 還原出的 hit-detection 前置鏈。重點不是把名稱直接當語意，而是追：

```text
screen/aim sampling
  -> damage-detect lookup
  -> hit result value/category
  -> runtime target object fields
  -> client visual/audio feedback
  -> Y_TCP_INF 165 / damage path
```

## 1. `CDamageDetect::sub_5EB290()` 是明確的 hit-detection API

```c
double __thiscall sub_5EB290(
    void *this,
    float a2,
    float a3,
    _WORD *hitType,
    float *rawResult)
```

核心：

```c
v7 = sub_5EAB60(this + 4, 256, 512, dword_1D0D724, a2, a3);
if ( v7 == 0 )
    return 0.0;

*hitType = HIBYTE(v7);
*rawResult = v7;
v6 = *rawResult / 100.0;

if (*hitType != 0)
    return v6 * 1.5;
return v6;
```

這證明 `sub_5EAB60()` 回傳的 16-bit 值同時攜帶：

```text
low byte / numeric component
high byte / hit-result category
```

而 hit category 非 0 時，`sub_5EB190` / `sub_5EB290` 會對數值再乘 `1.5`。

Evidence：完整 `PaperMan.exe.c` `sub_5EAB60` / `CDamageDetect::sub_5EB190` / `sub_5EB290` 約 L224128-L224373。

---

## 2. `sub_5EAB60()` 實際掃描的是 256×512 hit-detection map

```c
v13 = ((n256 - 1) * a5);
v7  = ((n512 - 1) * a6);

j1 = v13 - (a4 >> 1);
i1 = v7  - (a4 >> 1);
j2 = a4 + j1;
i2 = a4 + i1;
```

之後限制在：

```text
x ∈ [0, n256-1]
y ∈ [0, n512-1]
```

並掃描：

```c
*(a1 + 2 * n256 * i + 2 * j)
```

尋找非零 entry 中距離 `(i-v7)^2 + (j-v13)^2` 最小者。

最後：

```c
if (v8 <= a4*a4)
    return v16;
return 0;
```

因此這不是單純 boolean raycast；它是從一個 **16-bit-valued hit mask / detection map** 中，以局部半徑搜尋最近命中的值。

Evidence：`sub_5EAB60` 完整實作約 L224128-L224186。

---

## 3. Hit map 與 caller 座標輸入

`sub_5EB290()` 固定使用：

```text
n256 = 256
n512 = 512
map = dword_1D0D724
```

而輸入 `a2/a3` 是 `[0,1]` 類座標，因為 `sub_5EAB60` 直接乘：

```text
255
511
```

這與 HUD / aiming / screen-space 類輸入高度吻合；但目前應稱：

```text
normalized 2D hit-detection coordinates
```

而不是直接把它叫「螢幕 pixel」或「UV」，除非後續 caller / ASM 封閉來源。

---

## 4. Hit type 與玩家可見效果已有直接對應

`sub_5E63C0(a1,a2)` 直接讀：

```c
switch (*(a1 + 1244))
{
    case 0:
    case 4:
        "hit"
        break;
    case 1:
        "hit_headshot"
        break;
    case 2:
        "hit_heartbreak"
        break;
    case 3:
        "hit_critical"
        break;
    case 0x15:
        "taget_impact_bullet1"
        break;
    case 0x16:
        "taget_impact_bullet2"
        break;
}
```

這是目前最強的 hit-result semantic 證據之一：

```text
hit type 0/4  -> generic hit effect/audio
hit type 1    -> headshot
hit type 2    -> heartbreak
hit type 3    -> critical
0x15          -> bullet impact variant 1
0x16          -> bullet impact variant 2
```

其中 0/4 目前仍不應硬合併成同一 enum member，因為 code 明確分開列值但共享效果。

Evidence：`sub_5E63C0` 約 L222050-L222060。

---

## 5. `+1244` 是 hit-result category / effect selector 的強候選

Hit detection path 直接：

```c
v77 = sub_5EB290(..., n0x15, ...);
...
*(a4 + 1244) = n0x15[0];
```

隨後其他 path：

```c
sub_9BC420(*(a2 + 1244), ...);
```

以及：

```c
sub_5E63C0(a2, ...);
```

所以可以建立：

```text
CombatRuntimeObject +1244
    = hit-result category / hit-effect selector [HIGH]
```

尚未稱呼它為正式 `HitRegion`，因為 `headshot / critical / heartbreak` 等分類顯示它不單純等同於 body region。

---

## 6. Hit result 直接進 Damage packet 前置鏈

在 `sub_5E5...` 的命中處理路徑：

```text
CDamageDetect
    ↓
sub_5EB290
    ↓
n0x15[0] = hit category
    ↓
combat object +1244 = hit category
    ↓
sub_9BC420(...)  // hit visual/audio family
    ↓
sub_5E63C0(...)  // hit/headshot/critical audio family
    ↓
sub_55CAB0(1, ...)
```

`sub_55CAB0` 即 `OnSendPacketDamage` 建立 opcode 165，因此：

```text
hit detection result
    -> runtime hit category
    -> damage packet construction
```

這條鏈是 C 直接連起來的高價值證據。

Evidence：
- `sub_5E63C0` callers around L219648-L219952
- `sub_55CAB0` around L154525-L154707

---

## 7. Distance / falloff 另外存在，不要與 hit category 混成一個概念

Hit processing 會同時處理：

```text
n0x15[0] = hit category
n0x15[2] = nearest hit distance / magnitude-like value
```

`sub_5EB290()` 的 return 又是：

```text
rawResult / 100
(or × 1.5 when hit category != 0)
```

另一條 `sub_5E3A50` 幾何 path 又會計算：

```text
Euclidean distance
range threshold
frustum
AABB/collision
forward-direction dot
```

所以目前至少存在兩種不同 quantity：

```text
hit-map result/category
vs.
world-space geometry / distance / direction factors
```

不要統一命名為 `HitDistance` 或 `HitMultiplier`。

---

## 8. `sub_5E63C0()` 的作用比較像 presentation / feedback，不是 authority

`sub_5E63C0` 只是依 `+1244` 選擇：

```text
hit.wav
hit_headshot.wav
hit_heartbreak.wav
hit_critical.wav
taget_impact_bullet1.wav
taget_impact_bullet2.wav
```

因此：

```text
+1244 -> local feedback
```

非常明確。

它本身不是 server authority，也沒有證明 kill/score。

---

## 9. Client-side hit detection：目前證據應怎麼表述

現在有兩條獨立但會匯合的證據：

### A. 2D hit map

```text
normalized a2/a3
  -> 256×512 detection map
  -> nearest nonzero 16-bit hit result
  -> hit category
```

### B. 3D world geometry validation

另一條 caller path 在送出 `165 subtype 13` 前檢查：

```text
target existence/state
distance
range
frustum
AABB / geometry
forward dot
```

因此目前安全結論是：

> Client definitely performs substantial local hit/interaction detection work.

但仍不能由此直接推出：

> Client is authoritative for damage.

因為 `166 n18=3/20` 明確存在 server→client runtime health/state mutation。

---

## 10. Resource 方向

`sub_5EAB60` 使用：

```text
dword_1D0D724
```

目前它最值得追的不是音效檔，而是：

```text
dword_1D0D724 initialization
loader
allocation size = 256*512*2 candidate
file / resource source
```

若最後確認來源是 character/item/animation/skin/resource 資料，便可完成：

```text
Extracted resource
    -> damage-detection map
    -> hit category values
    -> character body/hit region
    -> client hit feedback
```

現在尚不能把 `dword_1D0D724` 直接命名為 `HitboxTexture`，但其 memory access pattern 強烈值得優先調查。

---

## 11. Server reconstruction intermediate model

現階段合理模型：

```text
Client local combat sampling
    ↓
HitDetectionResult
    ├─ DetectionValue
    ├─ HitCategory
    └─ spatial / geometry context
    ↓
client feedback
    ├─ hit sound/effect
    └─ local target feedback
    ↓
DamageInput
    ├─ source
    ├─ target
    ├─ weapon/resource
    ├─ hit category
    └─ computed damage inputs
    ↓
Damage modifier transform (`sub_5E72C0`)
    ↓
YTcpInfReq(165)
    ↓
Server authority / validation
    ↓
YTcpInfAck(166)
    ↓
health/state / death / result state
```

這是目前的 **intermediate specification**，不是已完成的 server protocol。

---

## 12. Evidence matrix

| 項目 | Evidence | 狀態 |
|---|---|---|
| 256×512 hit-detection map | C | CLOSED |
| nearest-nonzero selection | C | CLOSED |
| 16-bit result carries hit category in high byte | C | CLOSED |
| nonzero hit category causes ×1.5 in CDamageDetect result | C | CLOSED |
| `+1244` receives hit category | C | CLOSED |
| 1 = headshot | C/string | HIGH |
| 2 = heartbreak | C/string | HIGH |
| 3 = critical | C/string | HIGH |
| 0/4 = generic hit effect | C/string | HIGH |
| 0x15/0x16 = bullet impact variants | C/string | HIGH |
| hit category reaches damage packet path | C | HIGH |
| client performs 3D geometry checks before subtype 13 | C | HIGH |
| Client is authoritative for final damage | — | OPEN |
| `dword_1D0D724` exact resource origin | — | OPEN |

## 13. Highest-priority next tracing

```text
A. dword_1D0D724 initialization
   -> allocation size
   -> file/resource loader

B. sub_5EAB60 callers
   -> a2/a3 source
   -> exact screen/aim coordinate semantics

C. sub_5EB290 return value
   -> all uses of returned float
   -> determine whether it is damage multiplier, hit confidence, or another normalized coefficient

D. +1244
   -> full producer chain for values 0,1,2,3,4,0x15,0x16
   -> relation to body region / weapon / hitbox

E. sub_55CAB0(n20=1/3/...)
   -> connect hit category to Y_TCP_INF subtype / fields

F. 165 -> 166 -> health -> OnDeadCtrl
   -> final combat authority chain
```
