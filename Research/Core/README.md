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
遊戲模式／Gameplay
    ↓
戰鬥／移動／武器
    ↓
Result／Quest／Resource
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
  → Ready
  → Start
  → Match 初始化
  → Gameplay / Round
  → Result
  → Leave / End
  → Room / Lobby
```

## 大方向主文件

### 網路／傳輸／Dispatcher

- [`Network_Protocol.md`](Network_Protocol.md)：TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration 與 dispatcher。原本的 `Foundation_TCP_Handshake_Login_Protocol.md`、`Network_Dispatch.md`、`Y_TCP_INF_Transport.md` 已整合於此。

### 登入／ClientData／玩家資料

- [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md)：`680–696` 登入鄰近協定與 `681` server-list 結構。
- [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md)：`198` composite 順序、MyInfo／Avatar hydration 與未閉合欄位。
- [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)：ClientData 共用 wire family、record schema、decoder/serializer 與 Resource validation。
- [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md)：Character、Inventory、Equipment、Weapon 與 Runtime 資料模型。
- [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md)：PG、CASH、CP 與經濟欄位證據。

### Channel／Lobby／Room／Player／GameRule

- [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md)：Channel → Lobby → Room、Player Slot／Team、Map、Room selector 與 CGameRule 生命週期的大方向主文件。
- [`Room_Channel_GameRule_101_192_Field_Evidence.md`](Room_Channel_GameRule_101_192_Field_Evidence.md)：`101–192` 精確 packet、parser、serializer 與欄位證據。
- [`Channel_Lobby_193_221_Field_Evidence.md`](Channel_Lobby_193_221_Field_Evidence.md)：`193–221` 精確 top-level packet evidence。
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)：Room selector/value、設定封包與 UI data-flow 的詳細證據。
- [`Server_State_Model.md`](Server_State_Model.md)：跨子系統 Server reconstruction 抽象模型。

`GameRule_Lifecycle.md`、`Channel_Lobby_Lifecycle.md`、`Map_And_Room.md`、`Player_Slot_Team.md` 的大方向內容已整合至 `Room_Lobby_GameRule.md`；舊檔已移除或僅保留必要遷移痕跡，不再作為研究主文件。

### Gameplay／戰鬥／移動／武器

- [`Mode_Rules.md`](Mode_Rules.md)：遊戲模式規則與版本差異。
- [`Mode_Option_Tables.md`](Mode_Option_Tables.md)：mode-specific selector index/value。
- [`Gameplay_166_DeepEvidence.md`](Gameplay_166_DeepEvidence.md)：`166` Gameplay event family 深入證據。
- [`Y_TCP_INF_Damage.md`](Y_TCP_INF_Damage.md)：`165/166 Y_TCP_INF` gameplay/event family。
- [`Combat_Damage.md`](Combat_Damage.md)：Hit Detection、Combat geometry、Damage modifier 與 `165` 建包前計算的整合主文件。
- [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)：UDP movement actor record 與欄位證據。
- [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md)：丟棄／拾取武器流程。

`Combat_Hit_Detection.md` 與 `Damage_Calculation.md` 已整合至 `Combat_Damage.md`，不再作為獨立主文件。

### Result／Quest／Resource

- [`Packet_166_Field_Map.md`](Packet_166_Field_Map.md)：`166` 欄位快速索引。
- [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md)：`269 subtype 7` 完整欄位與 Result/K/D state。
- [`Result_Stat_Protocol_223_245_381_389.md`](Result_Stat_Protocol_223_245_381_389.md)：Result、Stat、Quest 相關 packet。
- [`Quest_Event_ID_Mapping.md`](Quest_Event_ID_Mapping.md)：Quest/Event ID mapping。
- [`Resource_Pack_Model.md`](Resource_Pack_Model.md)：Resource pack、資料模型與 loader/runtime 邊界。

## 文件整理原則

同一大方向優先使用同一主文件；只有在資料量、證據性質或責任確實不同時才保留獨立文件。

新增文件前先回答：

```text
這是不是既有大方向主文件應該承載的內容？
```

若答案是「是」，直接更新既有主文件，不建立副本。

完整文件清單以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準；儲存庫級規則以 [`../../AGENTS.md`](../../AGENTS.md) 為準。
