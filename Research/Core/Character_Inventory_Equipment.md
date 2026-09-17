# 角色、背包、裝備與玩家經濟研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 更新基準：2026-09-17。
> 文件責任：集中 Character／Appearance、Inventory／Owned Item、Weapon Loadout、`SwitchWeaponSlot`、`tItemSlotToClient`、Character Creation，以及 PG／CASH／CP 等玩家資料與經濟 state。ClientData 的 wire protocol 由 [`ClientData_Protocol.md`](ClientData_Protocol.md) 維護。

## 1. 一眼看懂

```text
ClientData_Protocol.md
    = wire 怎麼編碼

本文件
    = 玩家資料在 Runtime 中代表什麼

Resource_Pack_Model.md
    = Resource 如何載入與解析

Wiki
    = 玩家可觀察的歷史行為
```

最重要的分層：

```text
Resource Identity
    ≠ Owned Item Identity
    ≠ Runtime state
    ≠ UI presentation
    ≠ wire field
```

## 2. `CClientData` 的主要資料層

目前直接觀察到至少：

```text
CClientData
├─ 20 × 13-word 複合外觀記錄
├─ 5120 × 7-DWORD 物品記錄（28 bytes）
├─ 4 × 22-word 武器／裝備區塊
└─ tItemSlotToClient
     └─ 9 個索引對映
```

5120 筆物品、四個武器區塊、外觀資料與 9-entry mapping 是不同結構，Server 不應壓成單一 flat inventory。[C]

## 3. Character／Appearance 複合資料

Client 最多維護 20 筆複合外觀記錄，每筆 13 words／26 bytes。主要函式：

```text
sub_524010
sub_5241C0
sub_5244E0
sub_525450
```

目前安全的 runtime model：

```text
CompositeAppearanceState
├─ base resource identity      (+158)
├─ component resource IDs      (+159..+163)
└─ derived/resource fields     (+164..+169)
```

`sub_522580(mask, record)` 以 mask `1/2/4/8/16` 從 base resource 推導五個 component：

```c
base = &unk_12FA660 + (baseId % 100000);

if (mask & 0x01) record[+159] = sub_402FF0(base) + 27008;
if (mask & 0x02) record[+160] = sub_4030A0(base) - 7456;
if (mask & 0x04) record[+161] = sub_403150(base) + 23616;
if (mask & 0x08) record[+162] = sub_403200(base) - 10848;
if (mask & 0x10) record[+163] = sub_4032B0(base) - 10400000;
```

因此這些欄位是由 base resource identity 導出的複合資源表示。[C]

`Extracted` 的 Avatar 結構支持 body／hair／face／set／`acc1..acc4` 等角色外觀概念，但目前不足以把 `+159..+169` 一一命名；維持 `[OPEN]`。[RES][OPEN]

## 4. Resource ID namespace

Client 使用有結構的資源 ID namespace：

```text
19900000 系列 → base character/resource namespace
10000000 系列 → derived/component namespace
```

相關 helper：

```text
sub_533F50(x) = (x - 10000000) / 100000
sub_533F80(x) = (x - 10000000) % 100000
```

`AVATA` UI/resource path 與 `Extracted` 的 avatar／body／hair／face／set／`acc1..acc4`、`SoundFolderName` 等結構互相支持角色外觀 resource domain。[C][RES][X]

## 5. 5120 筆 Inventory／Owned Item

Client 最多配置 5120 筆物品記錄，每筆 7 DWORD／28 bytes；collection 具備搜尋、更新、刪除與壓縮能力，因此是 runtime-owned state，而不是單純 UI cache。[C]

### 5.1 28-byte record

```text
+0   DWORD-like
+4   item/resource identity candidate
+8   DWORD-like
+12  DWORD-like
+16  DWORD-like
+20  u8/type-like
+22  u16
+24  same input as second u16 copy
+26  remaining byte(s), semantic OPEN
```

`sub_524F70()` 建立 28-byte record；`sub_524B70()` 依相同順序讀回資料。[C]

目前可安全確認：

```text
+4        = item/resource identity candidate
+8/+12/+16 = item state fields, semantic OPEN
+20       = type/state byte, semantic OPEN
+22/+24   = duplicated u16 runtime values
+26       = OPEN
```

不要因 5120 entry 就自行命名成 SQL inventory slot number；wire 與 runtime identity 必須分離。[C][OPEN]

## 6. Inventory durability Runtime model

解析物品時，u16 inventory value 同時：

```text
寫入 OwnedItem +22/+24
    ↓
sub_534450(resourceIdentity, int16 value)
    ↓
Resource runtime +1200 / +1202
```

另有：

```text
sub_534530(resourceManager, resourceId)
    ↓
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base × 100
```

`sub_534B60()` 對應 resource definition `+1204`。[C]

因此目前最安全模型：

```text
DurabilityState
├─ Current = runtime current value
├─ Base    = Resource definition +1204
└─ Percent = Current / Base × 100
```

「current/base 是耐久度模型」具有高信度；wire 上的正式欄位名稱仍 `[OPEN]`。[C][X][OPEN]

## 7. Wiki 耐久度交叉驗證

日本 Wiki 的 `武器耐久値情報` 描述永久 PG／CASH 主武器與副武器具有可修理耐久度、戰鬥消耗、中途退出額外扣減、約 19% 附近開始劣化、修理回 100%，時間制武器另有不同模型。[WIKI]

這只能作為 Client current/base 架構的外部旁證；確切消耗／修理／劣化封包與 Client 常數仍 `[OPEN]`。

## 8. Weapon Loadout

Client 明確存在四個主要武器類別：

```text
+144206 → PRIMARYSLOT
+144208 → SECONDARYSLOT
+144210 → MELEESLOT
+144212 → THROWSLOT
```

`SwitchWeaponSlot` 對應 `+144338`，是獨立選擇／啟用 state，不是第五個武器槽。[C]

Runtime：

```text
WeaponLoadout
├─ Primary
├─ Secondary
├─ Melee
└─ Throw

SwitchWeaponSlot
└─ 獨立 selection state
```

## 9. Weapon record wire 與 runtime 的關係

單一 weapon/config record：

```text
u8 type
u16 component0
if type != 3:
    3 × u16 components
if component0 != 0:
    8 × 4-byte values
```

`sub_592AA0()` 表面 prototype 不可靠；尾端確定是 8 × 4-byte wire units。[C]

`sub_527DB0()` 對主要元件使用不同 Resource namespace；非法元件會進 error IDs 21–24。這證明不同 component 屬於不同 resource role，但不意味著已知道所有 public names。[C][OPEN]

`220/221` 可以採：

```text
delta → 只送變更槽位
full  → count = 4
```

Server 不應硬編碼「永遠四筆」或「永遠單筆」。[C]

## 10. `tItemSlotToClient`

`tItemSlotToClient` 是獨立 mapping：

```text
9 indices
```

建構子會清除；index `< 9` 才有效；parser／serializer 都完整處理 9 個值。[C]

不要把它與 Inventory index 或四類 Weapon Loadout 合併。

## 11. Character Creation

`214 GM_CREATECHAR_REQ` 為固定 6-byte payload：

```text
u8
u16
u8
u16
```

caller 資料流可看到部分值由 character/resource pointer 推導，例如：

```text
base namespace index
sub_4030A0(pointer) - 7456
sub_402FF0(pointer) + 27008
```

但四個 wire field 的 public semantic 尚未閉合；不要直接命名成 `characterId/gender/name/slot`。[C][OPEN]

`215 GM_CREATECHAR_ACK` 目前可確認讀取一個 byte 並交給角色選擇 state machine；結果語意 `[OPEN]`。[C][OPEN]

## 12. 197–200 玩家資料同步

```text
197 GL_MYINFO_REQ → 0-byte request
198 GL_MYINFO_ACK → composite ClientData/profile bootstrap
199 GL_MYITEM_REQ → 0-byte request
200 GL_MYITEM_ACK → item collection synchronization
```

198 會解析 Profile、Appearance、Loadout 與 validation components；完整 wire 順序／Family A/B/C/D 由 [`ClientData_Protocol.md`](ClientData_Protocol.md) 維護。[C]

200 則填入 5120 筆 item collection。[C]

## 13. Package 與 Item 必須分離

Wiki 歷史資料顯示 Character Package 可以同時授予 Character、Set Avatar、Paper Puzzle；一般 Package 也可組合武器、稱號與 Avatar。[WIKI]

因此：

```text
Package
    = grant / composition layer

OwnedItem
    = owned-instance layer
```

Package 不應直接當成 Inventory Item instance。

## 14. PG／CASH／CP：Profile Economy state

三個 account-economy globals 已由 Client UI 直接閉合：

```text
EE8D18 = PG
ArgList = CASH
EE8D1C = CP
```

UI 同時使用：

```text
EE8D40 → TOTAL_WIN
EE8D44 → TOTAL_LOSE
EE8D48 → MY_KILL
EE8D4C → MY_DEATH
EE8D18 → PG
ArgList → CASH
EE8D1C → CP / COUPON UI
```

`ArgList` 是 Hex-Rays/global-name artifact；Server 端可用語意 alias `g_Cash`，同時保留 raw address 作 provenance。[C]

### 14.1 Dedicated economy write callsites

```text
sub_45FCA0(a2)
    → EE8D18 = PG

sub_45FD80(a2)
    → ArgList = CASH

sub_45FE60(a2)
    → EE8D1C = CP
    → UI label = COUPON
```

因此 `CP` 與 `COUPON` 是同一 Client economy variable 的不同命名層，不應建立兩個 currency。[C]

### 14.2 Packet 205 economy tail

`sub_571910()` 在 repeated collection records 後讀 7 個 `u32`：

```text
u32 trailing_0
u32 PG
u32 trailing_2
u32 CASH
u32 trailing_4
u32 trailing_5
u32 CP
```

Direct assignments：

```c
*dword_EE8D18 = v16;
*ArgList      = v20;
*dword_EE8D1C = v27;
```

因此 packet 205 成功路徑不能省略 PG/CASH/CP。[C]

### 14.3 Packet 207 economy tail

`sub_571B60()` 讀 6 個 trailing u32：

```text
u32 trailing_0
u32 trailing_1
u32 trailing_2
u32 CASH
u32 PG
u32 CP
```

直接：

```c
*dword_EE8D18 = v14;
*ArgList      = v18;
*dword_EE8D1C = v22;
```

因此 207 同樣是 collection + economy synchronization family。[C]

### 14.4 Economy 與其它 profile state

```text
collection/item mutation
        ↓
item/resource record table
        ↓
PG / CASH / CP totals
        ↓
MYINFO / purchase / item UI refresh
```

205/207 的其餘 tail u32 尚未閉合，不能猜成另一種貨幣；必須找到 writer/consumer。[C][OPEN]

## 15. Extracted 與 domain boundary

目前相關資源目錄：

```text
Extracted/character/
Extracted/item/avatar/
Extracted/item/object/
Extracted/item/thumb/
Extracted/item/weapon/
```

保持：

```text
Resource definition
    ≠ OwnedItem
    ≠ WeaponLoadout
    ≠ CharacterAppearance
    ≠ UI presentation
```

## 16. Server domain model

目前可安全採用：

```text
PlayerProfile
├─ CharacterAppearanceState
├─ ItemCollection
│    └─ OwnedItem
│         ├─ Identity
│         ├─ ItemAssociatedValues
│         └─ DurabilityState
│              ├─ Current
│              └─ Base
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
├─ SwitchWeaponSlot
├─ ItemSlotToClient[9]
└─ ProfileEconomy
     ├─ PG
     ├─ CASH
     └─ CP
```

這是 Server domain abstraction；具體 wire codec 必須回 [`ClientData_Protocol.md`](ClientData_Protocol.md) 與各 packet Field Evidence。

## 17. 目前 OPEN 與下一步

```text
Appearance +159..+169 public mapping
Inventory +8/+12/+16/+20/+26 semantics
Durability wire name / change / repair / expiry protocol
19% degradation constant and exact path
Weapon component public semantics
8 × weapon tail DWORD semantics
SwitchWeaponSlot exact gameplay logic
214/215 character creation full semantics
205/207 remaining economy tail fields
```

新增證據應直接補進對應章節，不建立新的 `Character_*`、`Currency_*` 平行主文件；除非未來證明 wire 與 domain 已大到無法無損共存，才重新評估拆分。[OPEN]
