# 地圖選擇、房間狀態與 GameRule 交叉索引

> 研究日期：2026-09-17。
> 文件角色：地圖主題入口與未閉合問題清單。`121/122/129` 的完整 parser、serializer、Room selector 與 Resource 證據統一維護於 `Room_Settings_Packets.md`，本文件不再複製同一份欄位分析。

## 1. 已閉合的核心資料流

```text
GAMEROOM_SCROLL_MAP
    ↓
OptionIndex ↔ OptionValue
    ↓
121 GR_MAPCHANGE_REQ
    ↓
Server / Room
    ↓
122 GR_MAPCHANGE_ACK
    ↓
GAMEROOM_SCROLL_MAP
    ↓
Room / Map state
```

Start 路徑另有：

```text
Start precondition
    ↓
sub_437060()
    ↓
GAMEROOM_SCROLL_MAP
    ↓
selected / derived OptionValue
    ↓
129 GR_START_REQ
    ↓
130 / GameRule initialization
```

上述所有精確證據、欄位寬度與目前語意等級，唯一主文件為：

```text
Room_Settings_Packets.md
```

## 2. Resource 三方交叉點

目前最重要的 map evidence chain：

```text
Extracted/map/maplist.dat
        ↓
GAMEROOM_SCROLL_MAP
        ↓
40-byte UI entry
        ↓
entry value @ +36
        ↓
121/122 u8 selector value
        ↓
Room/Game state
```

`Map_And_Room.md` 不再另行維護這條結論，避免與 `Room_Settings_Packets.md` 漂移。

## 3. 尚未閉合的地圖問題

```text
P0  sub_4387B0()
    → entry value 是否為 map ID / resource ID / abstract selector

P0  sub_6B9B10()
    → 122 ACK 後到底更新哪些 Room/GameRule state

P1  sub_439600()
    → 特殊地圖列表／選擇型態的完整意義

P1  130 sub_562870()
    → Start 後同步資料是否再次攜帶相同 map value

P1  CGameRule::NewGameStart
    → map selector 最終如何進入真正的 map loading / mode initialization
```

## 4. 不應做的推論

目前不可只依 opcode 名稱或 UI 名稱把：

```text
map_value
start_parameter
OptionValue
```

直接改名成固定 `map_id`。

同樣不可因 `rand()` 出現在 `sub_437060()` 就直接把某條路徑命名成 `random_map`；必須先完成 Resource、UI selector、GameRule 與實際 map loading 的 data-flow 閉環。

## 5. 文件責任

```text
Map_And_Room.md
    = 地圖主題入口、交叉索引、未閉合研究問題

Room_Settings_Packets.md
    = Room selector/value 與 121/122/129/169/171/173/175 等設定封包的完整證據

GameRule_Lifecycle.md
    = Map state 如何進入 Ready → Start → Match lifecycle

Resource_Pack_Model.md
    = Map resource / Pack / ClientData 的資料模型
```

任何新的 map packet evidence 應先更新 `Room_Settings_Packets.md`；本文件只在研究入口或跨文件關係改變時更新。