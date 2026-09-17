# PaperMan 研究文件完整索引

> 目的：提供所有研究 Markdown 的單一導覽入口，避免同一主題分散、重複與互相漂移。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

本索引是 `Research/` 的唯一文件導覽。被合併文件的證據必須留在現有主文件；索引不得保留已刪除副本的失效入口。

## 使用方式

先找對應主文件，再閱讀其證據、協定、欄位與狀態章節。發現矛盾時回到 `[C]`、`[RES]`、`[WIKI]` 原始證據，不以另一份摘要覆蓋既有證據。

## 一、研究總入口

| 文件 | 定位 |
|---|---|
| [Research/README.md](README.md) | 整體研究目標、版本基準、證據方法與研究方向 |
| [Core/README.md](Core/README.md) | Core 研究範圍與文件導航，不承載單一主題詳細證據 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口與文件分工 |

## 二、基礎傳輸、封包與 Dispatcher

| 文件 | 定位 |
|---|---|
| [Core/Foundation_TCP_Handshake_Login_Protocol.md](Core/Foundation_TCP_Handshake_Login_Protocol.md) | TCP frame、完整性/XOR transform 與共用 fixed-width codec 基礎；不重複登入 payload |
| [Core/Network_Dispatch.md](Core/Network_Dispatch.md) | 封包註冊、接收 Dispatcher、handler 路由 |
| [Core/Y_TCP_INF_Transport.md](Core/Y_TCP_INF_Transport.md) | `Y_TCP_INF` 傳輸層與資料流；不重複 gameplay 欄位語意 |
| [Core/ClientData_Shared_Decoder_Field_Evidence.md](Core/ClientData_Shared_Decoder_Field_Evidence.md) | 共用 ClientData wire family 的唯一欄位／decoder 真相 |

## 三、登入、玩家資料與房間前置狀態

| 文件 | 定位 |
|---|---|
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` 登入鄰近協定、`681` server-list record 與登入鏈 |
| [Core/MyInfo_198_ClientData_Field_Schema.md](Core/MyInfo_198_ClientData_Field_Schema.md) | `198` 唯一主文件：top-level composite 順序、MyInfo／Avatar hydration 與未閉合欄位 |
| [Core/Player_Slot_Team.md](Core/Player_Slot_Team.md) | Player slot、Player ID、Team／Group、玩家有效狀態 |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Inventory、Equipment、Weapon 與 Runtime 語意主文件 |
| [Core/Currency_State_Field_Evidence.md](Core/Currency_State_Field_Evidence.md) | PG、CASH、CP 與帳戶經濟欄位證據 |

## 四、Channel、Lobby、Room 與 GameRule

| 文件 | 定位 |
|---|---|
| [Core/Channel_Lobby_193_221_Field_Evidence.md](Core/Channel_Lobby_193_221_Field_Evidence.md) | `193–221` top-level packet、parser、serializer 與欄位真相；198 nested codec 另見專屬主文件 |
| [Core/Channel_Lobby_Lifecycle.md](Core/Channel_Lobby_Lifecycle.md) | Channel → Lobby → Room 高階生命週期 |
| [Core/Room_Channel_GameRule_101_192_Field_Evidence.md](Core/Room_Channel_GameRule_101_192_Field_Evidence.md) | `101–192` packet、parser、serializer 與欄位真相 |
| [Core/Room_Settings_Packets.md](Core/Room_Settings_Packets.md) | Room UI selector/value、設定封包與設定資料流主文件 |
| [Core/Map_And_Room.md](Core/Map_And_Room.md) | Map 專題入口；詳細 selector/value 回 `Room_Settings_Packets.md` |
| [Core/GameRule_Lifecycle.md](Core/GameRule_Lifecycle.md) | CGameRule 狀態機、生命週期與跨物件因果 |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | 跨子系統 Server state abstraction，不重複 packet schema |

## 五、遊戲模式與 Gameplay

| 文件 | 定位 |
|---|---|
| [Core/Mode_Rules.md](Core/Mode_Rules.md) | 各模式玩家可見規則、版本差異與 Runtime 待閉合項目；不重複 selector value |
| [Core/Mode_Option_Tables.md](Core/Mode_Option_Tables.md) | mode-specific selector index/value 的唯一主文件 |
| [Core/Gameplay_166_DeepEvidence.md](Core/Gameplay_166_DeepEvidence.md) | `166` Gameplay、死亡、K/D、Quest hook 與深入證據 |

## 六、戰鬥、移動與武器

| 文件 | 定位 |
|---|---|
| [Core/Combat_Hit_Detection.md](Core/Combat_Hit_Detection.md) | 命中判定與戰鬥事件 |
| [Core/Damage_Calculation.md](Core/Damage_Calculation.md) | Damage modifier／transform 與 Runtime 計算；不重複 165 packet family |
| [Core/Y_TCP_INF_Damage.md](Core/Y_TCP_INF_Damage.md) | `Y_TCP_INF` 165/166 family、handler 與 state 證據 |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP 8/24、Queue、27-byte actor record 與欄位證據 |
| [Core/DropWeapon_Protocol.md](Core/DropWeapon_Protocol.md) | 丟棄武器封包與流程 |

## 七、Packet、Result、Score 與 Quest

| 文件 | 定位 |
|---|---|
| [Core/Packet_166_Field_Map.md](Core/Packet_166_Field_Map.md) | `166` 欄位快速索引；完整證據回 `Gameplay_166_DeepEvidence.md` |
| [Core/TCP_269_Subtype7_Field_Detail.md](Core/TCP_269_Subtype7_Field_Detail.md) | `269 subtype 7` 完整欄位、玩家同步與 Result/K/D 狀態 |
| [Core/Result_Stat_Protocol_223_245_381_389.md](Core/Result_Stat_Protocol_223_245_381_389.md) | `223–245`、`381–389` Result／Stat／Quest 主文件 |

## 八、Quest、Event 與資源模型

| 文件 | 定位 |
|---|---|
| [Core/Quest_Event_ID_Mapping.md](Core/Quest_Event_ID_Mapping.md) | Quest/Event 與 ID mapping 字典 |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | 遊戲資源封裝、資料來源與 loader/runtime 邊界 |

## 九、Kick Vote

| 文件 | 定位 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口與目前文件分工 |
| [KickVote/Evidence_And_Eligibility.md](KickVote/Evidence_And_Eligibility.md) | Wiki、C、資源與 voter／target 資格證據 |
| [KickVote/Protocol.md](KickVote/Protocol.md) | `718–723` 協定與資料流 |
| [KickVote/UI_State.md](KickVote/UI_State.md) | 投票 UI、狀態機、計時器與候選清單 |
| [KickVote/Master_Room.md](KickVote/Master_Room.md) | `396/397` Master／Room 層協定 |

## 十、已完成的內容整合

```text
Character_Inventory_Equipment_DeepEvidence.md
    → Character_Inventory_Equipment.md

Gameplay_166_KD_Field_Evidence.md
    → Gameplay_166_DeepEvidence.md

Packet_166_Field_Detail_3_15.md
    → Gameplay_166_DeepEvidence.md

UDP_Move_Inf_Field_Semantics.md
    → UDP_Move_Inf_DeepEvidence.md

TCP_269_Subtype7_Result_State.md
    → TCP_269_Subtype7_Field_Detail.md

MyInfo_198_Composite_Codec_Evidence.md
    → MyInfo_198_ClientData_Field_Schema.md

Login_681_Server_Record_Field_Schema.md
    → Login_Adjacent_680_696_Field_Schema.md

Y_TCP_INF_Handler_Details.md
    → Y_TCP_INF_Damage.md

Quest_Result_Packets_223_245.md
    → Result_Stat_Protocol_223_245_381_389.md

Score_State.md
    → Result_Stat_Protocol_223_245_381_389.md

Gameplay_Network_Events.md
    → Gameplay_166_DeepEvidence.md
    → Y_TCP_INF_Damage.md
    → UDP_Move_Inf_DeepEvidence.md
    → Result_Stat_Protocol_223_245_381_389.md

Map_And_Room.md
    → 保留為 Map 專題入口，精確內容主從 `Room_Settings_Packets.md`
```

整合必須保留：

```text
證據、反證、欄位寬度、函式路徑、state mutation、[OPEN] 邊界
```

禁止以摘要取代完整研究。

## 十一、文件角色與單一真相

同一主題原則上只保留一份主文件。只有責任確實不同才拆分：

```text
主題結論／深入證據 → 主題主文件
欄位速查            → Field Map／Schema
共用 wire family    → ClientData_Shared_Decoder_Field_Evidence
生命週期            → Lifecycle
傳輸底層            → Transport
模式規則            → Mode_Rules
模式 selector value → Mode_Option_Tables
專題導航            → README／專題入口
跨主題 ID           → Mapping
Server abstraction  → Server_State_Model
```

新增文件前必須先回答：

```text
為什麼不能直接更新現有主文件？
```

沒有合理答案就不要新增。

## 十二、禁止再次失控

- 同一 Packet 出現多份不同欄位真相。
- 建立 `New`、`Final`、`Final2`、`Latest`、`Copy` 等副本。
- 把猜測改成 confirmed 而沒有新證據。
- 把其它版本／地區資料無標記混入 2016 Japan final Client。
- 只更新子文件，不同步主文件、入口與索引。
- 在新 Markdown 一般說明中使用簡體中文或未經必要的英文敘述。
- 為了方便 Server 實作而把未知欄位直接填成 `0`、固定常數或 guessed enum。
