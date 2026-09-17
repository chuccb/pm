# 角色、背包與裝備研究

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 更新基準：2026-09-17。

本文件是角色、背包與裝備的唯一主文件。原本分散在摘要文件與深入證據文件中的內容，在此按「結構 → 直接證據 → 交叉驗證 → 未確認事項」整合。後續研究應優先更新本文件，不再建立另一份平行主線。

## 1. 文件責任與證據規則

本文件涵蓋：

- Character／Appearance。
- Inventory／Owned Item。
- Weapon Loadout／Weapon Record。
- `SwitchWeaponSlot`。
- `tItemSlotToClient`。
- Character Creation。
- `GL_MYINFO`／`GL_MYITEM` 對應的角色與物品同步。
- 遊戲資源與 Client state 的關係。

證據優先順序固定為：

```text
實際 serializer / parser
    → 實際讀寫寬度與 offset
    → caller / callee 與資料流
    → state field read / write
    → Extracted 資源
    → Wiki／歷史行為
    → 交叉驗證
```

Hex-Rays 的函式名稱、變數名稱與表面型別不能單獨視為語意證據。對外公開名稱尚未閉合時，保持中性的結構名稱並標記 `[OPEN]`。

證據標記：

- `[C]`：`PaperMan.exe.c` 可直接觀察。
- `[RES]`：`Extracted/` 的資源或資料檔證據。
- `[WIKI]`：日本 PaperMan Wiki 的歷史玩家可見資料。
- `[X]`：兩種以上獨立來源交叉吻合。
- `[OPEN]`：尚未充分證明。

## 2. `CClientData` 的主要資料層

Client 建構與資料流顯示至少存在以下互相獨立的結構：

```text
CClientData
├─ 20 × 13-word 複合外觀記錄
├─ 5120 × 7-DWORD 物品記錄（28 bytes）
├─ 4 × 22-word 武器／裝備區塊
└─ tItemSlotToClient
     └─ 9 個索引對映
```

5120 筆物品集合與四個武器區塊是不同資料結構，不應壓平為單一 Inventory 表。

## 3. 角色／外觀複合資料

Client 維護最多 20 筆複合外觀記錄，每筆 13 words／26 bytes。主要解析、序列化與比較函式包括：

```text
sub_524010()
sub_5241C0()
sub_5244E0(index)
sub_525450()
```

目前安全的結構模型為：

```text
CompositeAppearanceState
├─ 基底資源識別值（+158）
├─ 元件資源識別值（+159..+163）
├─ 其他衍生／資源欄位（+164..+169）
└─ Resource / Runtime resolution
```

### `sub_522580()` 的遮罩式元件重建

`sub_522580(mask, record)` 會依 mask bits `1/2/4/8/16` 產生五個元件欄位。其資料流可直接整理為：

```c
base = &unk_12FA660 + (baseId % 100000);

if (mask & 0x01) record[+159] = sub_402FF0(base) + 27008;
if (mask & 0x02) record[+160] = sub_4030A0(base) - 7456;
if (mask & 0x04) record[+161] = sub_403150(base) + 23616;
if (mask & 0x08) record[+162] = sub_403200(base) - 10848;
if (mask & 0x10) record[+163] = sub_4032B0(base) - 10400000;
```

不同 caller 會分別設定這些欄位，因此可以直接確認它們是由基底資源身份推導而來的複合資源表示，而不是互不相關的任意整數。[C]

目前不要把 `+159..+169` 直接命名成 body、hair、face、set、accessory 等公開欄位。`Extracted` 的 Avatar 資源確實支持這些概念，但資源拓撲本身不足以把每一個 wire word 一一對應到公開名稱。[RES][OPEN]

## 4. 資源 ID 命名空間

Client 使用有結構的數值資源命名空間：

```text
19900000 系列 → 基底角色／資源命名空間
10000000 系列 → 衍生元件／資源命名空間
```

相關 helper：

```text
sub_533F50(x) = (x - 10000000) / 100000
sub_533F80(x) = (x - 10000000) % 100000
```

另有路徑會把絕對身份轉回區域命名空間，再交給資源／渲染流程。這直接證明這些數值是結構化資源身份，不是普通小型列舉值。[C]

`AVATA` UI／資源路徑與 `Extracted` 的 avatar、body、hair、face、set、`acc1..acc4`、`SoundFolderName` 等資源結構互相支持「複合外觀會進入角色外觀呈現系統」的結論；但不應據此逕自完成每個 wire 欄位的公開命名。[C][RES][X]

## 5. 5120 筆物品集合

Client 最多配置 5120 筆物品記錄，每筆 7 DWORD／28 bytes。集合具備搜尋、更新、刪除與壓縮能力，因此它是由 Runtime 持有的玩家物品狀態，而不只是 UI 快取。[C]

### 5.1 28-byte 記錄結構

目前可閉合的相對位移為：

```text
+0   DWORD-like 欄位
+4   物品／資源識別值
+8   DWORD-like 欄位
+12  DWORD-like 欄位
+16  DWORD-like 欄位
+20  可選 u8／型別欄位
+22  物品關聯 u16
+24  同一 u16 的第二份副本
+26  剩餘位元組；公開語意 OPEN
```

`sub_524F70()` 建立 28-byte 暫存記錄；重要參數會寫入 +4、+8、+12、+16、+20、+22、+24。解析器 `sub_524B70()` 依相同順序讀回資料。[C]

目前可安全確認：

- `+4`：物品／資源身份類欄位。[C]
- `+8/+12/+16`：DWORD 型物品欄位；公開語意 `[OPEN]`。[C][OPEN]
- `+20`：u8／型別類欄位；精確語意 `[OPEN]`。[C][OPEN]
- `+22/+24`：同一解析輸入值形成的兩份 u16 副本。[C]

## 6. 物品耐久度 Runtime 資料流

在解析 5120 筆物品時，Client 讀取該 u16 後，除了寫入物品記錄的 +22／+24，還把它與物品／資源身份一起傳入：

```text
sub_534450(resourceIdentity, int16 value)
```

`sub_534450()` 再把同一值寫入資源 Runtime 項目的 `+1200` 與 `+1202`。[C]

因此應區分：

```text
OwnedItem record
├─ +22 u16
└─ +24 u16

Resource runtime entry
├─ +1200
└─ +1202
```

它們的數值會互相傳播，但不是同一個實體儲存位置，不得在 Server object model 中錯誤合併成單一欄位。

### 6.1 Current / Base 計算

`sub_534530(resourceManager, resourceId)` 建立：

```text
current = sub_534A70(resourceId)
base    = sub_534B60(resourceManager, resourceId)
percent = current / base × 100
```

`sub_534A70()` 從特定 Resource Runtime 命名空間取得目前值；`sub_534B60()` 對應的資源定義欄位為 `+1204`。[C]

因此最強的目前模型是：

```text
CurrentDurability ≈ Runtime current state
BaseDurability    = Resource definition +1204
DurabilityPercent = Current / Base × 100
```

目前信度：

- 存在 current/base 百分比計算：已直接確認。[C]
- 與武器／物品耐久度架構相關：高信度。[C][X]
- 網路協定中正式欄位名稱：`[OPEN]`。

## 7. Wiki 對耐久度規則的交叉驗證

日本 Wiki 的 `武器耐久値情報` 記載：永久 PG／CASH 主武器與副武器具有可修理的耐久度；戰鬥會消耗耐久；中途退出有額外扣減；約 19% 附近開始出現劣化；修理可恢復至 100%；時間制武器則使用不同的模型。[WIKI]

這可作為 Client current/base 架構的歷史外部旁證，但不能拿 Wiki 直接取代封包欄位還原。確切的耐久變更封包、修理封包、消耗條件與約 19% 的 Client 常數仍屬 `[OPEN]`。

## 8. 四類武器 Loadout

Client 直接以名稱與狀態 offset 固定四個主要可持有／選擇武器類別：

```text
+144206 → PRIMARYSLOT
+144208 → SECONDARYSLOT
+144210 → MELEESLOT
+144212 → THROWSLOT
```

這是直接 Client 證據。[C]

日本 Wiki 則使用 Main／Sub／Melee／Throwing 等玩家側名稱；應在最終研究中保留兩套命名並明確指出它們的來源，不要未經證明就把名稱當成 wire enum。[WIKI][X]

## 9. `SwitchWeaponSlot` 是獨立狀態

`SWITCHWEAPONSLOT` 對應 `+144338`。它是獨立的選擇／切換狀態，並不是第五個持久化武器欄位。[C]

目前最安全的模型為：

```text
WeaponLoadout
├─ Primary
├─ Secondary
├─ Melee
└─ Throw

SwitchWeaponSlot
└─ 獨立選擇／啟用狀態
```

其確切遊戲語意仍為 `[OPEN]`；不得建模成第五個武器槽。

## 10. 武器記錄的條件式序列化

`sub_524880()`／`sub_524A50()` 顯示單一武器記錄的結構：

```text
u8 type
u16 component0

if type != 3:
    u16 component1
    u16 component2
    u16 component3

if component0 != 0:
    8 × 4-byte serializer unit
```

這裡有一個重要反編譯陷阱：`sub_592AA0()` 的 Hex-Rays 表面參數可能顯示成 `char`，但其實作會把該值交給底層 copy primitive 並指定 `4` bytes。因此尾端八個值確定是 8 × 4 bytes，共 32 bytes。[C]

目前不要把 `component0..3` 或八個尾端值強行命名成公開欄位；它們的結構已閉合，但語意仍需進一步與資源／遊戲流程交叉確認。[OPEN]

## 11. 220／221 武器同步

```text
220 GI_CHANGEWP_REQ
221 GI_CHANGEWP_ACK
```

Client 具有兩種同步形式：

```text
變更差量 → 只序列化發生變更的槽位
完整快照 → count = 4
```

`sub_573340()` 會掃描四個武器槽，只序列化變更項；另一條路徑會寫入 count `4` 並序列化完整資料。接收端 `sub_5735F0()` 先讀 count，再依每筆條件式記錄解析並套用。[C]

因此 Server 不應硬編碼「每個封包永遠四筆」或「每次只有一筆」。

## 12. 武器資源驗證

`sub_527DB0()` 對主要武器元件使用不同 Resource namespace 進行驗證；非法元件會進入不同錯誤 ID 21–24。[C]

這直接支持「四個武器元件具有不同資源角色」，但尚不足以命名所有公開欄位。[C][OPEN]

## 13. `tItemSlotToClient`

`tItemSlotToClient` 是獨立結構，包含 9 個索引值：

- 建構子會清除映射。
- 索引有效條件為 `< 9`。
- 解析器會完整讀取 9 個值。
- 序列化器會完整輸出 9 個值。[C]

不得把它與物品 Inventory slot 或四類 Weapon Loadout 混成同一層。

## 14. Character Creation

`214 GM_CREATECHAR_REQ` 具有固定 6-byte payload：

```text
u8
u16
u8
u16
```

目前 caller 資料流證明其中兩個值直接由選定角色／資源指標推導，例如：

```text
character/resource pointer
├─ base namespace index
├─ sub_4030A0(pointer) - 7456
└─ sub_402FF0(pointer) + 27008
```

因此不可直接把四個欄位命名成一般化的 `characterId / gender / name / slot`。四個 wire 欄位的公開語意目前仍需持續確認。[C][OPEN]

`215 GM_CREATECHAR_ACK` 目前可確認解析一個 byte 並交給角色選擇狀態機；結果語意 `[OPEN]`。[C][OPEN]

## 15. `197–200` 角色與物品同步

```text
197 GL_MYINFO_REQ   → 0-byte request
198 GL_MYINFO_ACK   → 複合 CClientData / profile sync
199 GL_MYITEM_REQ   → 0-byte request
200 GL_MYITEM_ACK   → 物品集合同步
```

198 並非單純成功碼。Client 會建立暫時 `CClientData`，解析多個 Profile、外觀與裝備結構，再把結果套用至 Runtime。[C]

200 則會填入 5120 筆物品集合。[C]

## 16. Package 與 Item 必須分離

歷史 Wiki 研究支持將 Package grant 與個別 Item instance 分開建模。例如 Character Package 可同時提供 Character、Set Avatar、Paper Puzzle；一般 Package 也可組合武器、稱號與 Avatar。[WIKI]

因此 Server 資料模型不應把 Package 直接當成另一個 Inventory Item instance。Package 是授予／組合層概念；Item 則是持有狀態層概念。

## 17. 資源目錄與領域邊界

`Extracted` 中存在：

```text
Extracted/character/
Extracted/item/avatar/
Extracted/item/object/
Extracted/item/thumb/
Extracted/item/weapon/
```

Client 也會明確載入 item/avatar 類資源。[RES][C]

必須保持以下概念分離，除非存在明確 mapping：

```text
Resource Identity
≠ Render Asset Identity
≠ Owned Item Identity
≠ UI Presentation Identity
```

## 18. Server 重建模型

目前最適合的 Server domain abstraction 為：

```text
PlayerProfile
├─ CharacterAppearanceState
├─ ItemCollection
│    └─ OwnedItem
│         ├─ Identity
│         ├─ ItemAssociatedValues
│         └─ DurabilityState
│              ├─ Current
│              └─ Base（由 Resource definition 推導）
├─ WeaponLoadout
│    ├─ Primary
│    ├─ Secondary
│    ├─ Melee
│    └─ Throw
├─ SwitchWeaponSlot
└─ ItemSlotToClient[9]
```

不要因 Client 在多層資料結構間傳遞同一個 numeric identity，就把 Resource definition、Owned Item、UI presentation 與網路資料合併成一個類別；目前逆向結果明確顯示這些是彼此橋接的不同層。

## 19. 尚未閉合的重點

```text
1. 物品 +8/+12/+16 的正式語意
2. 物品 +20 的正式語意
3. 耐久度 u16 的正式協定欄位名稱
4. 耐久度降低／修理／過期的完整封包鏈
5. 約 19% 劣化規則的 Client 直接常數與判定路徑
6. 四個 weapon component 的公開語意
7. 八個 weapon 尾端 4-byte 值的語意
8. SwitchWeaponSlot 的實際遊戲邏輯
9. +159..+169 與 Avatar 公開欄位的一一 mapping
10. 222/223 字元遊戲流程的完整 sender 與 semantic
```

以上項目在沒有新 C/LST、Resource 或 Wiki 證據前，維持 `[OPEN]`，不得為方便 Server 實作而偷偷填入猜測值。

## 20. 整合後的研究規則

本主題後續新增證據應直接更新本文件相應章節：

```text
欄位 → 欄位結構區
封包 → 對應同步區
生命週期 → 對應流程區
跨函式證據 → 本文件證據段落
Wiki 行為 → 交叉驗證段落
```

不要再次建立 `Character_Inventory_Equipment_Final.md`、`Character_Inventory_Equipment_New.md` 或其他平行副本。若未來深入研究量大到真的需要拆分，必須先在 `Research/DOCUMENT_INDEX.md` 明確定義主文件與子文件責任，再拆分。
