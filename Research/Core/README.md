# PaperMan 核心遊戲機制逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Core 目錄入口與導航。

本文件只負責說明 `Research/Core/` 的研究範圍、文件分工與閱讀順序。具體封包欄位、函式、狀態與證據應寫入對應的主題文件，再由本入口或 `Research/DOCUMENT_INDEX.md` 導航。

## 研究範圍

```text
TCP／UDP 傳輸
    ↓
封包 Dispatcher
    ↓
登入／ClientData
    ↓
Channel／Lobby
    ↓
Room／Player／Slot／Team
    ↓
GameRule
    ↓
遊戲模式／Gameplay
    ↓
戰鬥／移動／武器
    ↓
Quest／Result／Resource
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
登入
  → Channel／Lobby
  → Room
  → Player／Slot／Team
  → Ready
  → Start
  → Match 初始化
  → Gameplay
  → Result
  → Leave／Logout
```

`CGameRule`、房間狀態、玩家 slot／team 與網路封包是目前核心研究的主要交會點。詳細生命週期請直接閱讀 [`GameRule_Lifecycle.md`](GameRule_Lifecycle.md)。

## 文件導覽

### 網路與封包基礎

- [`Foundation_TCP_Handshake_Login_Protocol.md`](Foundation_TCP_Handshake_Login_Protocol.md)：TCP、握手、登入與基礎協定。
- [`Network_Dispatch.md`](Network_Dispatch.md)：封包註冊、接收 Dispatcher 與 handler 路由。
- [`Y_TCP_INF_Transport.md`](Y_TCP_INF_Transport.md)：`Y_TCP_INF` 傳輸層資料流。
- [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)：共用 decoder 與欄位讀取證據。

### 登入、玩家與房間前置狀態

- [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md)：`680–696` 與 `681` server-list／登入鏈完整結構。
- [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md)：`198` composite ClientData 完整結構。
- [`Player_Slot_Team.md`](Player_Slot_Team.md)：Player slot、Team、玩家位置與隊伍狀態。
- [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md)：Character、Inventory、Equipment、Weapon 與 Resource 關係。
- [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md)：貨幣與玩家狀態欄位證據。

### Channel、Lobby、Room、Map、GameRule

- [`Channel_Lobby_193_221_Field_Evidence.md`](Channel_Lobby_193_221_Field_Evidence.md)：`193–221` Channel/Lobby 欄位直接證據。
- [`Channel_Lobby_Lifecycle.md`](Channel_Lobby_Lifecycle.md)：Channel/Lobby 生命週期與狀態轉移。
- [`Room_Channel_GameRule_101_192_Field_Evidence.md`](Room_Channel_GameRule_101_192_Field_Evidence.md)：`101–192` Room/Channel/GameRule 欄位證據。
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)：房間設定與相關封包。
- [`Map_And_Room.md`](Map_And_Room.md)：Map、Room 以及兩者的關係。
- [`GameRule_Lifecycle.md`](GameRule_Lifecycle.md)：GameRule 生命週期與狀態機。
- [`Server_State_Model.md`](Server_State_Model.md)：Server-side 狀態模型與同步關係。

### 遊戲模式與 Gameplay

- [`Mode_Rules.md`](Mode_Rules.md)：各遊戲模式的規則與狀態。
- [`Mode_Option_Tables.md`](Mode_Option_Tables.md)：模式選項與欄位對照表。
- [`Gameplay_166_DeepEvidence.md`](Gameplay_166_DeepEvidence.md)：`166` Gameplay、死亡、K/D、結果、欄位與跨函式證據。

### 戰鬥、移動、武器與 Y_TCP_INF

- [`Combat_Hit_Detection.md`](Combat_Hit_Detection.md)：命中判定與戰鬥事件。
- [`Damage_Calculation.md`](Damage_Calculation.md)：傷害計算與相關狀態。
- [`Y_TCP_INF_Damage.md`](Y_TCP_INF_Damage.md)：`Y_TCP_INF` 165/166 全 family、handler 與 state 證據。
- [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)：UDP 8/24、Queue、27-byte actor record 與欄位證據。
- [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md)：丟棄武器封包與流程。

### Packet、Result、Score 與 Quest

- [`Packet_166_Field_Map.md`](Packet_166_Field_Map.md)：`166` 欄位速查；完整證據回到 `Gameplay_166_DeepEvidence.md`。
- [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md)：`269 subtype 7` 完整欄位、玩家同步與 Result/K/D 狀態。
- [`Result_Stat_Protocol_223_245_381_389.md`](Result_Stat_Protocol_223_245_381_389.md)：`223–245`、`381–389` Result／Stat／Quest 主文件。

### Quest、Event、Resource

- [`Quest_Event_ID_Mapping.md`](Quest_Event_ID_Mapping.md)：Quest/Event 與 ID mapping 字典。
- [`Resource_Pack_Model.md`](Resource_Pack_Model.md)：遊戲資源封裝與資料模型。

完整文件清單與角色分類以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準。

## 本 README 的內容邊界

### 這裡應該放

- Core 研究範圍。
- 文件導航。
- 研究優先順序。
- 跨主題的高階生命週期模型。

### 這裡不應該放

- 大量 Packet 欄位表。
- 單一函式的長篇反編譯分析。
- 與其他文件重複的完整結論。
- 未確認欄位的硬編碼值。
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
