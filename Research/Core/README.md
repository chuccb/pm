# PaperMan 核心遊戲機制逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Core 目錄入口與大方向導航。
> 更新基準：2026-09-17。

本文件只負責說明 `Research/Core/` 的研究範圍、主要大方向與閱讀入口。具體封包欄位、函式、狀態與證據應寫入對應主文件；同一大方向的研究應優先集中，不再為每個微小功能建立平行 Markdown。

## 研究範圍

```text
網路／傳輸／Dispatcher
    ↓
登入／ClientData／玩家資料
    ↓
Channel／Lobby／Room／Player／GameRule
    ↓
遊戲模式／規則／Selector
    ↓
Gameplay／165/166／Combat／Movement
    ↓
Result／Score／Quest／Resource
```

主要研究方法固定為：

```text
IDA C / LST
    ↕
Extracted 資源
    ↕
日本 PaperMan Wiki
```

研究時優先沿 serializer、parser、caller／callee、實際讀寫寬度與 state-field data-flow 追查，不以 Hex-Rays 猜測名稱或欄位位置直接決定語意。

## 目前核心生命週期

```text
Login
  → Channel / Lobby
  → Room
  → Player / Slot / Team
  → Room settings
  → Ready
  → Start
  → Match 初始化
  → Gameplay / Round
  → Result / Quest
  → Leave / End
  → Room / Lobby
```

## 大方向主文件

### 網路／傳輸／Dispatcher

- [`Network_Protocol.md`](Network_Protocol.md)：TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration 與 dispatcher。

### Channel／Lobby／Room／Player／Map／GameRule

- [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md)：同一大方向的主要主文件，集中 Channel → Lobby → Room、16-slot Player、Team/Group、Map、Room selector 與 CGameRule 生命週期。
- [`Room_Channel_GameRule_101_192_Field_Evidence.md`](Room_Channel_GameRule_101_192_Field_Evidence.md)：`101–192` 精確 packet／parser／serializer／field evidence。
- [`Channel_Lobby_193_221_Field_Evidence.md`](Channel_Lobby_193_221_Field_Evidence.md)：`193–221` 精確 top-level packet／parser／serializer／field evidence。
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)：Room selector/value 與設定 packet 的詳細資料流。
- [`Server_State_Model.md`](Server_State_Model.md)：跨整個 Server reconstruction 的 state abstraction。

`Channel_Lobby_Lifecycle.md`、`Player_Slot_Team.md`、`Map_And_Room.md` 已整合；`GameRule_Lifecycle.md` 的研究內容也已集中至 `Room_Lobby_GameRule.md`，舊檔只應視為遷移殘留，不得重新加入第二套研究結論。

### 遊戲模式／規則／Selector

- [`Mode_Rules_And_Options.md`](Mode_Rules_And_Options.md)：各模式玩家可見規則、Client mode builder、OptionIndex／OptionValue、具體 selector values、版本差異與 Runtime 待閉合項目。

### Gameplay／Y_TCP_INF／Combat／Movement

- [`Gameplay_Network.md`](Gameplay_Network.md)：`165/166 Y_TCP_INF` gameplay event family、166 subtype、Resource/state application、sender/receiver 與 165/166 K/D 邊界。
- [`Combat_Damage.md`](Combat_Damage.md)：Hit Detection、2D/3D combat geometry、Damage modifier、165 建包前計算。
- [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)：UDP movement actor record 與欄位證據。
- [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md)：武器丟棄／拾取事件與流程。

`Gameplay_166_DeepEvidence.md`、`Y_TCP_INF_Damage.md`、`Packet_166_Field_Map.md` 已整合至 `Gameplay_Network.md`；`Combat_Hit_Detection.md` 與 `Damage_Calculation.md` 已整合至 `Combat_Damage.md`。

### Result／Score／Quest／Event／Resource

- [`Result_Quest_Stats.md`](Result_Quest_Stats.md)：Result、Score/K-D、長期統計、Quest condition、Assist／Football 等相關事件的整合主文件。
- [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md)：`269 subtype 7` 詳細欄位與 Result/K-D state。
- [`Resource_Pack_Model.md`](Resource_Pack_Model.md)：Resource pack、資料模型與 loader/runtime 邊界。

`Result_Stat_Protocol_223_245_381_389.md`、`Quest_Event_ID_Mapping.md` 已整合至 `Result_Quest_Stats.md`。

## 文件整理原則

同一大方向優先使用同一主文件；只有在資料量、證據性質或責任確實不同，且無法無損放入既有主文件時，才保留獨立文件。

新增文件前先回答：

```text
1. 它屬於哪個大方向？
2. 既有大方向主文件為何不能直接承載？
3. 是否會形成第二份 Packet／State／Semantic 真相？
```

若只是新的證據、欄位、caller、Resource 對照或 OPEN 項目，原則上直接更新既有主文件。

完整文件清單以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準；儲存庫級規則以 [`../../AGENTS.md`](../../AGENTS.md) 為準。
