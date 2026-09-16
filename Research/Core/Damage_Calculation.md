# Damage 計算層：`sub_5E72C0()` 逆向

> 研究日期：2026-09-16
>
> 本文件只處理 `Y_TCP_INF_REQ (165)` 發送前的 damage value transform。`165` 的完整 receive-side 語意仍另列於 `Y_TCP_INF_Damage.md`。

## 1. `sub_5E72C0()` 的真實角色

函式：

```c
double __stdcall sub_5E72C0(int n16, int n16_1, float a3)
```

`OnSendPacketDamage`、`OnSendPacketMultiDamage`、`OnSendPacketMineBombDamage` 都先呼叫：

```c
sub_5E72C0(source, target, raw_value);
```

再把結果經 multiplier 後量化成 byte 寫入 opcode `165` payload。

Evidence：`PaperMan.exe.c` 約 L154616-L154617、L154780-L154781、L154900。

## 2. 它不是固定倍率；會檢查 source / target 的三個 entry

核心迴圈：

```c
for (i = 0; i < 3; ++i)
{
    v3 = dword_F5653C[60195 * sub_67D7D0(n16) + i];
    ...

    v11 = dword_F5653C[60195 * sub_67D7D0(n16_1) + i];
    ...
}
```

即每個 actor 都有最多 3 個相關 entry；函式會以 `sub_67D7D0()` 把傳入 identifier 轉成實際 player slot，再取該 slot 的三個 `dword_F5653C` entry。

Evidence：`PaperMan.exe.c` 約 L222574-L222639。

## 3. Entry 類型會被轉成內部 category

對每個 entry：

```c
switch (entry - &unk_E98C4B)
{
    case 0:
    case 1:
    case 2:
        type = 2;
        break;

    case 3:
    case 4:
    case 5:
        type = 3;
        break;

    case 6:
        type = 4;
        break;

    case 7:
    case 8:
        type = 6;
        break;

    case 9:
        type = 1;
        break;

    case 10:
    case 11:
        type = 5;
        break;

    case 12:
        type = 7;
        break;

    case 13:
    case 14:
    case 25:
        type = 8;
        break;

    case 19:
    case 20:
    case 21:
        type = 10;
        break;

    case 24:
        type = 12;
        break;

    case 26:
        type = 9;
        break;

    default:
        type = -1;
        break;
}
```

其中：

```text
source entry type == 8
    → v13 = source entry

target entry type == 9
    → v12 = target entry
```

也就是本函式只會把兩類 entry 選入最後 damage transform：

```text
source-side category 8 → damage increase candidate
target-side category 9 → damage decrease candidate
```

Evidence：`PaperMan.exe.c` 約 L222577-L222642。

## 4. 百分比加成與減成的實際公式

最後真正修改 `a3` 的程式是：

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

因此如果：

```text
increase_percent = P
reduce_percent    = Q
```

則實際順序為：

```text
A = raw_damage * (1 + P / 100)
B = A * (1 - Q / 100)
```

注意第二步的減成是作用在「已加成後的 `a3`」，不是原始 damage。

Evidence：`PaperMan.exe.c` 約 L222691-L222710。

## 5. 同一 `sub_5E72C0()` 被多種 165 variant 共用

### Normal damage

```c
v39 = sub_5E72C0(n16, n16a, a5);
v40 = sub_5E72C0(n16, n16a, a6);
```

Evidence：`PaperMan.exe.c` 約 L154616-L154617。

### Mine/Bomb damage

```c
v21 = sub_5E72C0(n16, n16a, a5);
v22 = sub_5E72C0(n16, n16a, a6);
```

Evidence：`PaperMan.exe.c` 約 L154780-L154781。

### MultiDamage

```c
v27 = sub_5E72C0(n16, n16_1, a4);
```

Evidence：`PaperMan.exe.c` 約 L154900。

因此 damage modifier 並不是 Normal Damage 專屬；它是多個 `165` gameplay event variant 共用的低階 transform。

## 6. `165` 的 damage byte 是最後的量化結果

Normal Damage 後續會依 client state 使用：

```text
1.0
2.0
```

在特定 subtype `n20 == 3` 時，還有：

```text
1.2
```

再呼叫：

```c
sub_592B20(..., SLOBYTE(calculated_value));
```

因此完整概念鏈是：

```text
raw float
   ↓
sub_5E72C0()
   ├─ source category 8 → +percentage
   └─ target category 9 → -percentage
   ↓
variant / mode multiplier
   ↓
byte quantization
   ↓
Y_TCP_INF_REQ (165)
```

這是目前比「packet 內有一個 damage byte」更接近真實遊戲計算的模型。

## 7. `dword_F5653C` 現在仍不能直接改名成某個資源 ID

`dword_F5653C` 的 entries 是 pointer-like values，並以：

```c
entry - &unk_E98C4B
```

分類，再交給：

```c
sub_535020(dword_EE3E98, entry)
```

取得另一個 data object，最後讀：

```c
*(object + 548)
```

這說明它確實是「data-driven modifier」結構，但目前沒有足夠證據把 category 8/9 直接命名成某個公開 `Item`、`Skill` 或 `Buff` 名稱。

因此保留：

```text
dword_F5653C = modifier-entry table [C: confirmed]
category 8 / 9 = selected increase/decrease candidates [C: confirmed]
public resource name = OPEN
```

## 8. 與 Extracted 資源的三方定位

`Extracted/0.xml` 明確指出 client data package 包括：

```xml
<PackFile key="character" filename="Data\\character.dat" folderpath="character\\" />
<PackFile key="item" filename="Data\\item.dat" folderpath="item\\" />
<PackFile key="map" filename="Data\\map.dat" folderpath="map\\" />
<PackFile key="pmClient" filename="Data\\pmClient.dat" folderpath="" />
```

而 `ClientDataList.xml` 明確列有：

```xml
<DataList key="effect" />
<DataList key="ui" />
```

目前可以確定「entry → data object → +548」是一條 data-driven client path，但尚未把 `&unk_E98C4B` 對應到某個 Extracted 檔案中的具體 record，因此這部分不提前聲稱三方完全閉合。

## 9. Wiki 只適合驗證『效果』，不應拿來猜 internal category

Wiki 可以支持某些 gameplay 現象，例如 個人サバイバル 的擊殺／重生規則、チームサバイバル 的 team score 規則，以及其他 mode-specific 行為；但 Wiki 沒有列出 `dword_F5653C` category 8/9 或 `+548` 欄位。

因此正確的三方使用方式是：

```text
Wiki
    → 驗證玩家可見結果

IDA C
    → 恢復真正計算公式與資料流

Extracted RES
    → 再去定位 category 對應的具體 record
```

不能反過來用 Wiki 名詞硬套 C category。

## 10. Server RE 的實作結論

目前不要把：

```text
165 damage byte
```

直接當成：

```text
weapon base damage
```

比較準確的是：

```text
DamageInput
    ↓
modifier resolution
    ├─ source slot
    ├─ target slot
    ├─ up to 3 modifier entries per side
    ├─ category filtering
    └─ percentage mutation
    ↓
variant-specific multiplier
    ↓
wire quantization
    ↓
YTcpInfReq
```

這個模型之後可再接 `item.dat` / `character.dat` / `effect` / skill resource，一旦找到 `+548` 的具體 record schema，就能進一步把目前的 anonymous modifier 完整命名。

## 11. Evidence anchors

```text
[IDA]
PaperMan.exe.c:
  L154616-L154617   Normal Damage → sub_5E72C0
  L154780-L154781   Mine/Bomb Damage → sub_5E72C0
  L154900          MultiDamage → sub_5E72C0
  L222574-L222642   modifier entry classification
  L222691-L222710   percentage increase/decrease

[RES]
Extracted/0.xml
Extracted/ClientDataList.xml

[Wiki]
MAP・ルール詳細：個人サバイバル／チームサバイバル等公開規則
```
