# Combat／Hit Detection／Damage 逆向研究

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中命中判定、Hit Result、Runtime hit state、Damage modifier、165 發送前計算與 Client→Server combat event 鏈；避免 `Combat_Hit_Detection.md` 與 `Damage_Calculation.md` 分裂維護同一條證據鏈。

## 1. 整體 Combat 證據鏈

目前最完整的 Client-side 工作模型：

```text
screen / aim sampling
    ↓
2D hit-detection map / 3D geometry checks
    ↓
HitDetectionResult
    ├─ hit category
    ├─ raw result
    └─ spatial / geometry context
    ↓
Runtime hit state
    ↓
local hit feedback
    ↓
DamageInput
    ↓
sub_5E72C0() modifier transform
    ↓
variant multiplier / quantization
    ↓
Y_TCP_INF_REQ (165)
    ↓
Server authority / validation
    ↓
Y_TCP_INF_ACK (166)
    ↓
health / state / death / result
```

重要限制：Client 明確執行大量本地命中與互動計算，但目前沒有足夠證據證明 Client 對最終 damage 具有 authority。

## 2. `CDamageDetect::sub_5EB290()`

核心函式：

```c
double __thiscall sub_5EB290(
    void *this,
    float a2,
    float a3,
    _WORD *hitType,
    float *rawResult)
```

關鍵流程：

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

因此 `sub_5EAB60()` 回傳的 16-bit result 同時攜帶：

```text
低位元組 → numeric component
高位元組 → hit-result category
```

Hit category 非 0 時，該 normalized result 還會乘 `1.5`。[C]

## 3. `sub_5EAB60()`：256×512 Hit Detection Map

函式在 `dword_1D0D724` 上進行：

```text
256 × 512
```

的 hit-detection map 掃描。以輸入座標換算後，以局部半徑尋找非零 entry 中距離最近者。

核心範圍：

```text
x ∈ [0, 255]
y ∈ [0, 511]
```

記憶體讀取形狀：

```c
*(a1 + 2 * n256 * i + 2 * j)
```

最後只有在：

```text
nearest distance <= radius²
```

時才回傳 16-bit result，否則回 0。[C]

因此這不是簡單 boolean raycast，而是 **16-bit-valued detection map + nearest hit selection**。[C]

## 4. Hit Detection 輸入座標

`sub_5EB290()` 固定以：

```text
256
512
```

作為 detection map 尺寸；輸入 `a2/a3` 經 `255/511` 之比例換算，因此目前安全名稱為：

```text
normalized 2D hit-detection coordinates
```

不能只依此直接命名成 screen pixel、UV 或其他特定座標系統，除非 caller / ASM 再閉合來源。[C][OPEN]

## 5. Hit Category 的玩家可見語意

`sub_5E63C0()` 直接依 runtime field `+1244` 分支：

```text
0 / 4  → hit
1      → hit_headshot
2      → hit_heartbreak
3      → hit_critical
0x15   → taget_impact_bullet1
0x16   → taget_impact_bullet2
```

因此目前高可信語意：

```text
+1244 = hit-result category / hit-effect selector [HIGH]
```

它不能直接命名成 `HitRegion`，因為目前已觀察到 headshot、critical、heartbreak 等不同層次的分類。[C]

其中 `0` 與 `4` 雖共享 generic effect，但仍應保留為不同 wire/runtime value。[C]

## 6. Hit Category → Damage Packet

命中處理鏈目前可閉合成：

```text
CDamageDetect
    ↓
sub_5EB290
    ↓
hit category
    ↓
combat object +1244
    ↓
sub_9BC420 / sub_5E63C0
    ↓
local visual/audio feedback
    ↓
sub_55CAB0
    ↓
OnSendPacketDamage
    ↓
Y_TCP_INF_REQ 165
```

因此 hit detection result 確實會進入 damage packet 前置路徑。[C]

## 7. 2D Hit Map 與 3D Geometry 是不同證據

另一條 caller path 在送出 `165 subtype 13` 前會進行：

```text
target existence/state
distance
range
frustum
AABB / geometry
forward-direction dot
```

因此至少存在：

```text
2D hit-map detection
vs.
3D world-space geometry / direction checks
```

兩者不能合併成單一 `HitDistance` 或 `HitMultiplier`。[C][OPEN]

## 8. `dword_1D0D724` Resource 邊界

目前 `dword_1D0D724` 是 256×512 hit map 的直接資料來源，但尚未閉合：

```text
allocation size
initialization routine
loader
file/resource origin
```

因此暫時不可直接命名成 `HitboxTexture`、character hitbox resource 或其它具體 public asset。[OPEN]

最高價值追查：

```text
dword_1D0D724 initialization
    ↓
allocation
    ↓
loader
    ↓
Extracted resource source
```

## 9. Damage modifier：`sub_5E72C0()`

`OnSendPacketDamage`、`OnSendPacketMultiDamage`、`OnSendPacketMineBombDamage` 都先呼叫：

```c
sub_5E72C0(source, target, raw_value);
```

因此它是 **165 gameplay family 共用的低階 damage transform**，不是單一 packet 私有公式。[C]

## 10. Source / Target Modifier Entries

`sub_5E72C0()` 最多掃描：

```text
source slot → 3 entries
target slot → 3 entries
```

透過：

```c
sub_67D7D0(identifier)
```

把 source / target identifier 映射成實際 player slot。[C]

Entry category mapping：

```text
0,1,2       → category 2
3,4,5       → category 3
6           → category 4
7,8         → category 6
9           → category 1
10,11       → category 5
12          → category 7
13,14,25    → category 8
19,20,21    → category 10
24          → category 12
26          → category 9
other       → -1
```

目前可直接確認的特別用途：

```text
source category 8 → increase candidate
target category 9 → reduction candidate
```

其它 category 不應只依數字名稱推導 public gameplay enum。[C][OPEN]

## 11. 真正的百分比公式

若：

```text
R = raw damage
P = source increase percentage
Q = target reduction percentage
```

Client 先做：

```text
A = R * (1 + P/100)
B = A * (1 - Q/100)
```

程式直接：

```c
v9 = *(v10 + 548) / 100.0 * a3;
a3 = a3 + v9;

v7 = *(v8 + 548) / 100.0 * a3;
a3 = a3 - v7;
```

因此 target reduction 是作用在 **已完成 source increase 的結果** 上，而不是原始 damage。[C]

## 12. Damage 計算是 data-driven

完整資料流：

```text
source identifier
    ↓
sub_67D7D0()
    ↓
source slot
    ↓
dword_F5653C[slot][0..2]
    ↓
category classification
    ↓
category 8 candidate
    ↓
sub_535020()
    ↓
resource object +548
    ↓
percentage increase
```

Target side 同理，但 category 9 做 reduction。

因此：

```text
dword_F5653C = modifier-entry table [C]
```

不應簡化成普通 weapon damage table。[C]

## 13. 165 Variant 共用 Transform

### Normal Damage

```c
v39 = sub_5E72C0(source, target, raw_a5);
v40 = sub_5E72C0(source, target, raw_a6);
```

### Mine / Bomb

同樣先經 `sub_5E72C0()`。

### MultiDamage

```c
v27 = sub_5E72C0(source, target, raw_value);
```

因此 165 family 中多條 sender path 共用相同 modifier layer。[C]

## 14. Variant Multiplier 與量化

目前 C 路徑可觀察到：

```text
一般路徑          → 1.0
某些 client-state → 2.0
n20 == 3 特殊路徑 → 1.2
```

因此完整鏈條不是：

```text
raw → packet
```

而是：

```text
raw input
   ↓
source increase
   ↓
target reduction
   ↓
variant / client-state multiplier
   ↓
caller-side low-byte truncation
   ↓
serializer
   ↓
Y_TCP_INF_REQ 165
```

其中 `n20` 目前只稱 event/damage subtype-like byte，不直接命名成 public `DamageType`。[C][OPEN]

## 15. 重要 Serializer 陷阱：`sub_592B20()`

完整 C：

```c
void *__thiscall sub_592B20(void *this, char a2)
{
    sub_592580(this, &a2, 4u);
    return this;
}
```

所以：

```text
sub_592B20 = 4-byte serializer
```

即使 caller：

```c
sub_592B20(packet, SLOBYTE(value));
```

仍然是 4-byte wire field。[C]

這個 distinction 對 Damage、MultiDamage 與多條 165 sender path 都直接有相容性影響。

## 16. Hit Distance、Geometry 與 Damage Modifier 不應混成一層

目前至少分開三種 quantity：

```text
Hit-map result / category
World-space geometry / distance / direction
Damage modifier / multiplier
```

例如：

```text
sub_5EB290
    → hit-map result / category

sub_5E3A50
    → geometry / range / frustum / AABB / dot

sub_5E72C0
    → source increase / target reduction
```

Server reconstruction 時不得用單一 `HitMultiplier` 欄位取代這三種不同語意。[C]

## 17. Client authority 邊界

目前可安全建立：

```text
Client local detection
    → Client damage event construction
    → 165 Client → Server
```

但不能因此宣布 Client 是最終 authority。原因是 `166` receive family 明確存在 Server → Client runtime state mutation，例如：

```text
166 n18 = 3 / 20
    → target object value mutation
    → Resource/effect application
```

因此目前最佳 intermediate model 仍是：

```text
Client computes / reports
Server validates / resolves
Server sends authoritative state
Client applies state
```

是否所有 damage mode 都採完全相同 authority 流程，仍屬 `[OPEN]`。

## 18. Extracted Resource 三方驗證

目前可用的 Resource 對照：

```text
Extracted/0.xml
    → character / item / map / pmClient package references

Extracted/ClientDataList.xml
    → effect / ui resource domains
```

另一方面，combat/effect code 會經：

```text
sub_5F5400
sub_5F5450
sub_5FC510
sub_5EF590
sub_5EF5B0
sub_5EFE00
sub_5F0FB0
```

其中：

```text
sub_5EF590(resource) → *resource
sub_5EF5B0(resource) → resource + 4
sub_5EFE00(resource) → resource + 64
sub_5F0FB0(resource) → resource + 252
```

這條 runtime resource object path 已成立，但 modifier category 與 `&unk_E98C4B` 尚未完全對上 Extracted concrete record。[C][RES][OPEN]

## 19. Server Reconstruction 中間模型

目前 Server 不應只實作：

```csharp
finalDamage = weapon.BaseDamage;
```

應至少保留：

```text
DamageInput
    ↓
ResolveActorModifiers(source)
    ↓
ResolveActorModifiers(target)
    ↓
Select category 8 / 9 candidates
    ↓
Apply source increase
    ↓
Apply target reduction
    ↓
Apply event / variant multiplier
    ↓
Quantize / truncate exactly as Client
    ↓
Serialize exact wire width
    ↓
YTcpInfReq(165)
```

同時 Combat Detection 至少保持：

```text
HitDetectionResult
├─ detection value
├─ hit category
└─ spatial / geometry context
```

兩者在 reconstruction architecture 中仍應視為相鄰但不同層。

## 20. 證據矩陣

| 項目 | Evidence | 狀態 |
|---|---|---|
| 256×512 hit-detection map | C | CLOSED |
| nearest nonzero selection | C | CLOSED |
| 16-bit result carries category | C | CLOSED |
| nonzero category → ×1.5 | C | CLOSED |
| `+1244` receives hit category | C | HIGH |
| 1=headshot | C/string | HIGH |
| 2=heartbreak | C/string | HIGH |
| 3=critical | C/string | HIGH |
| 0/4=generic hit effect | C/string | HIGH |
| 0x15/0x16=bullet impact variants | C/string | HIGH |
| hit category reaches 165 damage path | C | HIGH |
| 3D geometry checks before subtype 13 | C | HIGH |
| `sub_5E72C0` shared by 165 variants | C | CLOSED |
| source category 8 increase | C | CLOSED |
| target category 9 reduction | C | CLOSED |
| reduction after increase | C | CLOSED |
| `sub_592B20` = 4-byte writer | C | CLOSED |
| 1.0 / 2.0 / 1.2 multiplier paths | C | HIGH |
| exact public modifier names | — | OPEN |
| `dword_1D0D724` concrete resource origin | — | OPEN |
| final damage server authority contract | — | OPEN |

## 21. 最高價值後續追查

```text
A. dword_1D0D724
   → initialization / allocation / loader / Extracted source

B. sub_5EAB60 callers
   → exact coordinate source

C. sub_5EB290 return uses
   → determine all consumers of normalized hit result

D. +1244 producer/consumer closure
   → values 0,1,2,3,4,0x15,0x16

E. sub_55CAB0
   → map hit category into 165 subtype/field grammar

F. 165 → 166 → health/state → death/result
   → close final combat authority chain
```
