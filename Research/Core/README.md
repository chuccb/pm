# PaperMan 核心遊戲機制逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Core 目錄入口與導航。

本文件只負責說明 `Research/Core/` 的研究範圍、文件分工與閱讀順序。具體封包欄位、函式、狀態與證據不得持續堆在這裡；應寫入對應的專題文件，再由本入口或 `Research/DOCUMENT_INDEX.md` 導航。

## 研究範圍

```text
TCP／UDP 傳輸
    ↓
Packet Dispatcher
    ↓
Login / ClientData
    ↓
Channel / Lobby
    ↓
Room / Player / Slot / Team
    ↓
GameRule
    ↓
Mode / Gameplay
    ↓
Combat / Movement / Weapon
    ↓
Quest / Result / Resource
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

## 目前的核心生命週期主線

```text
Login
  → Channel / Lobby
  → Room
  → Player / Slot / Team
  → Ready
  → Start
  → Match 初始化
  → Gameplay
  → Result
  → Leave / Logout
```

`CGameRule`、房間狀態、玩家 slot／team 與網路封包是目前核心研究的主要交會點。詳細生命週期請直接閱讀 [`GameRule_Lifecycle.md`](GameRule_Lifecycle.md)。

## 文件導覽

### 網路與封包基礎

- [`Foundation_TCP_Handshake_Login_Protocol.md`](Foundation_TCP_Handshake_Login_Protocol.md)：TCP、握手、登入與基礎協定。
- [`Network_Dispatch.md`](Network_Dispatch.md)：封包註冊、接收 Dispatcher 與 handler 路由。
- [`Y_TCP_INF_Transport.md`](Y_TCP_INF_Transport.md)：`Y_TCP_INF` 傳輸層資料流。
- [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)：共用 decoder 與欄位讀取證據。

### Login、玩家與房間前置狀態

- [`Login_681_Server_Record_Field_Schema.md`](Login_681_Server_Record_Field_Schema.md)
- [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md)
- [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md)
- [`MyInfo_198_Composite_Codec_Evidence.md`](MyInfo_198_Composite_Codec_Evidence.md)
- [`Player_Slot_Team.md`](Player_Slot_Team.md)
- [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md)
- [`Character_Inventory_Equipment_DeepEvidence.md`](Character_Inventory_Equipment_DeepEvidence.md)
- [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md)

### Channel、Lobby、Room、Map、GameRule

- [`Channel_Lobby_193_221_Field_Evidence.md`](Channel_Lobby_193_221_Field_Evidence.md)
- [`Channel_Lobby_Lifecycle.md`](Channel_Lobby_Lifecycle.md)
- [`Room_Channel_GameRule_101_192_Field_Evidence.md`](Room_Channel_GameRule_101_192_Field_Evidence.md)
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)
- [`Map_And_Room.md`](Map_And_Room.md)
- [`GameRule_Lifecycle.md`](GameRule_Lifecycle.md)
- [`Server_State_Model.md`](Server_State_Model.md)

### 遊戲模式與 Gameplay

- [`Mode_Rules.md`](Mode_Rules.md)
- [`Mode_Option_Tables.md`](Mode_Option_Tables.md)
- [`Gameplay_Network_Events.md`](Gameplay_Network_Events.md)
- [`Gameplay_166_DeepEvidence.md`](Gameplay_166_DeepEvidence.md)
- [`Gameplay_166_KD_Field_Evidence.md`](Gameplay_166_KD_Field_Evidence.md)

### 戰鬥、移動與武器

- [`Combat_Hit_Detection.md`](Combat_Hit_Detection.md)
- [`Damage_Calculation.md`](Damage_Calculation.md)
- [`Y_TCP_INF_Damage.md`](Y_TCP_INF_Damage.md)
- [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)
- [`UDP_Move_Inf_Field_Semantics.md`](UDP_Move_Inf_Field_Semantics.md)
- [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md)

### Packet、Result、Score 與 Quest

- [`Packet_166_Field_Map.md`](Packet_166_Field_Map.md)
- [`Packet_166_Field_Detail_3_15.md`](Packet_166_Field_Detail_3_15.md)
- [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md)
- [`TCP_269_Subtype7_Result_State.md`](TCP_269_Subtype7_Result_State.md)
- [`Quest_Result_Packets_223_245.md`](Quest_Result_Packets_223_245.md)
- [`Result_Stat_Protocol_223_245_381_389.md`](Result_Stat_Protocol_223_245_381_389.md)
- [`Score_State.md`](Score_State.md)

### Quest、Event、Resource

- [`Quest_Event_ID_Mapping.md`](Quest_Event_ID_Mapping.md)
- [`Resource_Pack_Model.md`](Resource_Pack_Model.md)

完整文件清單與角色分類以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準。

## 研究文件撰寫邊界

### 這裡應該放什麼

- Core 研究範圍。
- 文件導航。
- 研究優先順序。
- 跨主題的高階生命週期模型。

### 這裡不應該放什麼

- 大量 Packet 欄位表。
- 單一函式的長篇反編譯分析。
- 同時屬於多份文件的重複結論。
- 尚未確認的欄位硬編碼值。
- 完整 Wiki 條目或完整資源內容。

需要保存深入證據時，請放入既有的 `Field_Evidence`、`DeepEvidence`、`Detail`、`Schema`、`Protocol`、`Lifecycle` 或 `State` 文件；不要再把內容堆回本 README。

## 新增研究前的最低流程

```text
先搜尋既有文件
    ↓
確認是否已有主文件
    ↓
能更新舊文件就不要新增
    ↓
若必須新增，先決定文件角色
    ↓
更新 Research/DOCUMENT_INDEX.md
    ↓
執行 python scripts/check_markdown.py
```

所有文件維護規則以根目錄 [`AGENTS.md`](../../AGENTS.md) 為準。