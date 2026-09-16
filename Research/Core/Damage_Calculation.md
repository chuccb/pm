# Damage 計算層：`sub_5E72C0()` 逆向

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client／服務終了時版本
>
> 本文件只處理 `Y_TCP_INF_REQ (165)` 發送前的 damage value transform。`165` 的完整 polymorphic family 另見 `Y_TCP_INF_Damage.md`。

## 1. `sub_5E72C0()` 的真實角色

函式：

```c
double __stdcall sub_5E72C0(int n16, int n16_1, float a3)
```

`OnSendPacketDamage`、`OnSendPacketMultiDamage`、`OnSendPacketMineBombDamage` 都先呼叫：

```c
sub_5E72C0(source, target, raw_value);
```

再把結果經 variant multiplier 後送入 packet serializer。

Evidence：`PaperMan.exe.c` 約 L154616-L154617、L154780-L154781、L154900；完整 Library C 可直接定位。

---

## 2. 每個 source / target 最多掃描 3 個 modifier entries

核心迴圈：

```c
for ( i = 0; i < 3; ++i )
{
    v3 = dword_F5653C[60195 * sub_67D7D0(n16) + i];
    ...

    v11 = dword_F5653C[60195 * sub_67D7D0(n16_1) + i];
    ...
}
```

也就是：

```text
source slot -> 3 entries
 target slot -> 3 entries
```

`sub_67D7D0()` 負責將 packet/game identifier 映射為實際 player slot index，因此不能直接把 `n16` / `n16_1` 當成固定 SlotIndex。

Evidence：`PaperMan.exe.c` 約 L222574-L222639。

---

## 3. Entry category mapping

每個 entry 是 pointer-like value，以：

```c
entry - &unk_E98C4B
```

分類：

```text
0,1,2       -> category 2
3,4,5       -> category 3
6           -> category 4
7,8         -> category 6
9           -> category 1
10,11       -> category 5
12          -> category 7
13,14,25    -> category 8
19,20,21    -> category 10
24          -> category 12
26          -> category 9
other       -> -1
```

source 端：

```text
category 8 -> selected increase candidate
```

target 端：

```text
category 9 -> selected decrease candidate
```

Evidence：`PaperMan.exe.c` 約 L222574-L222639；完整 Library C 已再次確認 source/target 兩側都有相同 category classification。

---

## 4. 真正的百分比公式

最後 modification：

```c
if (v13 != 0)
{
    v10 = sub_535020(dword_EE3E98, v13);
    if (v10 != 0)
    {
        v9 = *(v10 + 548) / 100.0 * a3;
        a3 = a3 + v9;
    }
}

if (v12 != 0)
{
    v8 = sub_535020(dword_EE3E98, v12);
    if (v8 != 0)
    {
        v7 = *(v8 + 548) / 100.0 * a3;
        a3 = a3 - v7;
    }
}
```

所以若：

```text
P = source increase percent
Q = target reduction percent
R = raw damage
```

則順序是：

```text
A = R * (1 + P/100)
B = A * (1 - Q/100)
```

第二步作用於已加成後的值，而不是原始 damage。

Evidence：`PaperMan.exe.c` 約 L222691-L222710。

---

## 5. 這不是固定倍率，而是 data-driven modifier resolution

完整資料流：

```text
source identifier
    ↓
sub_67D7D0()
    ↓
actual source slot
    ↓
dword_F5653C[slot][0..2]
    ↓
category classification
    ↓
category 8?
    ↓
sub_535020()
    ↓
object +548
    ↓
percentage increase
```

target side 同理，但 category 9 會做 reduction。

因此：

```text
dword_F5653C = modifier-entry table [C]
```

而不是普通 weapon damage table。

---

## 6. 165 variants 共用此 transform

### Normal Damage

```c
v39 = sub_5E72C0(n16, n16a, a5);
v40 = sub_5E72C0(n16, n16a, a6);
```

### Mine/Bomb Damage

```c
v21 = sub_5E72C0(n16, n16a, a5);
v22 = sub_5E72C0(n16, n16a, a6);
```

### MultiDamage

```c
v27 = sub_5E72C0(n16, n16_1, a4);
```

因此這是 **165 gameplay event family 的共同低階 damage transform**，不是某個單一 packet handler 私有公式。

---

## 7. **重要 serializer 修正：`sub_592B20` 是 4-byte writer**

完整 C 直接給出：

```c
void *__thiscall sub_592B20(void *this, char a2)
{
    sub_592580(this, &a2, 4u);
    return this;
}
```

因此：

```text
sub_592B20 = serialize 4 bytes
```

即使 caller 寫：

```c
sub_592B20(packet, SLOBYTE(calculated));
```

也不能把 wire field 記成 `u8`。

此 distinction 對 Damage protocol 尤其重要：

```text
source expression type
    !=
wire field width
```

Evidence：`PaperMan.exe.c` `sub_592B20` 約 L180559；Library 完整 C 已直接確認 implementation。

---

## 8. Damage 計算後還有 variant multiplier

Normal Damage：

```text
一般路徑          -> 1.0
client 狀態條件    -> 2.0
n20 == 3 特殊路徑 -> 1.2
```

MultiDamage 與 Mine/Bomb path 至少都有：

```text
1.0 / 2.0
```

所以完整鏈條不是單純：

```text
raw -> modifier -> packet
```

而是：

```text
raw input
   ↓
sub_5E72C0()
   ├─ source category 8 increase
   └─ target category 9 reduction
   ↓
variant / client-state multiplier
   ↓
low-byte truncation at caller
   ↓
sub_592B20()  // 4-byte wire serialization
   ↓
Y_TCP_INF_REQ 165
```

Evidence：Normal / MultiDamage / Mine-Bomb serializers in `PaperMan.exe.c`。

---

## 9. `n20 == 3` 的位置要特別注意

Normal Damage：

```c
if ( n20 == 3 )
{
    v27 = v39 * v34;
    ...
}
```

其 multiplier 在目前 C path 為 `1.2`；其他一般 path 在同一 client-state branch 可為 `2.0`。

這個 `n20` 仍是 Y_TCP_INF 的 event/damage subtype-like byte，不應直接命名為 public damage type。

---

## 10. Extracted / resource closure 的目前狀態

`Extracted/0.xml` 可確認：

```text
character -> Data\\character.dat
item      -> Data\\item.dat
map       -> Data\\map.dat
pmClient  -> Data\\pmClient.dat
```

`ClientDataList.xml` 可確認：

```text
effect
ui
```

另一方面，damage/effect client code 使用：

```text
sub_5F5400()
sub_5F5450()
sub_5FC510()
sub_5EF590()
sub_5EF5B0()
sub_5EFE00()
sub_5F0FB0()
```

其中：

```c
sub_5EF590(resource) -> *resource
sub_5EF5B0(resource) -> resource + 4
sub_5EFE00(resource) -> resource + 64
sub_5F0FB0(resource) -> resource + 252
```

這已形成一條重要的 runtime resource object path，但 `&unk_E98C4B` 及 category 8/9 尚未完全對應到 Extracted 的具體 record，因此仍不能聲稱 public resource name 已閉合。

---

## 11. Wiki 的角色

Wiki 不提供：

```text
dword_F5653C
modifier category 8/9
object +548
```

所以 Wiki 不應被用來猜 internal modifier category。

合理三方定位：

```text
Wiki
  -> 驗證玩家可見的 damage / mode 結果

IDA C / ASM
  -> 恢復公式、field flow、state mutation

Extracted
  -> 追 concrete item / effect / character record
```

---

## 12. Server reconstruction intermediate model

目前 Server 尚不能只用：

```csharp
finalDamage = weapon.BaseDamage;
```

正確中間抽象應近似：

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
Quantize/truncate exactly as client
    ↓
Serialize using exact 4-byte writer semantics
    ↓
YTcpInfReq(165)
```

其中 `ResolveActorModifiers` 的 public resource schema 仍 OPEN。

---

## 13. Evidence / unresolved

| 項目 | Evidence | 狀態 |
|---|---|---|
| `sub_5E72C0` 是 165 Damage/Multi/Bomb 共用 transform | C | CLOSED |
| source 3 entries / target 3 entries | C | CLOSED |
| category mapping | C | CLOSED |
| category 8 = increase candidate | C | CLOSED |
| category 9 = reduction candidate | C | CLOSED |
| `+548 / 100.0` percentage formula | C | CLOSED |
| reduction applies after increase | C | CLOSED |
| `sub_592B20` = 4-byte writer | C | CLOSED |
| low-byte truncation at caller | C | CLOSED |
| 1.0 / 2.0 / subtype-3 1.2 multipliers | C | HIGH |
| exact public identity of modifier categories | — | OPEN |
| `&unk_E98C4B` -> Extracted concrete record | C + RES | OPEN |
| final damage field public semantic | C | OPEN |

---

## 14. Evidence anchors

```text
[IDA / full Library C]
sub_5E72C0      ~ L222570+
modifier apply  ~ L222690+
Normal Damage   ~ L154600+
MultiDamage     ~ L154890+
Mine/Bomb       ~ L154770+
sub_592B20      ~ L180559

[RES]
Extracted/0.xml
Extracted/ClientDataList.xml

[WIKI]
MAP・ルール詳細：公開 gameplay / mode rules
```
