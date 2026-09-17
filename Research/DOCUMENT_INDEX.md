# PaperMan 研究文件完整索引

> 目的：提供所有研究 Markdown 的單一導覽入口，將同一大方向集中於同一主文件，避免同一主題分散、重複與互相漂移。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

本索引是 `Research/` 的唯一文件導覽。被合併文件的證據必須保留在合併後主文件；索引不得保留已刪除副本的失效入口。

## 使用方式

先找對應大方向主文件，再閱讀其中的章節、證據、協定、欄位與狀態。發現矛盾時回到 `[C]`、`[RES]`、`[WIKI]` 原始證據，不以另一份摘要覆蓋既有證據。

## 一、研究總入口

| 文件 | 定位 |
|---|---|
| [Research/README.md](README.md) | 整體研究目標、版本基準、證據方法與研究方向 |
| [Core/README.md](Core/README.md) | Core 研究範圍與文件導航 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |

## 二、網路、傳輸、封包與 Dispatcher

| 文件 | 定位 |
|---|---|
| [Core/Network_Protocol.md](Core/Network_Protocol.md) | TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration 與 dispatcher；原 `Foundation_TCP_Handshake_Login_Protocol.md`、`Network_Dispatch.md`、`Y_TCP_INF_Transport.md` 已整合至此 |

## 三、登入、ClientData、玩家資料與裝備

| 文件 | 定位 |
|---|---|
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` 登入鄰近協定與 `681` server-list record |
| [Core/MyInfo_198_ClientData_Field_Schema.md](Core/MyInfo_198_ClientData_Field_Schema.md) | `198` composite 順序、MyInfo／Avatar hydration 與未閉合欄位 |
| [Core/ClientData_Shared_Decoder_Field_Evidence.md](Core/ClientData_Shared_Decoder_Field_Evidence.md) | ClientData 共用 wire family、record schema 與 decoder/serializer 證據 |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Inventory、Equipment、Weapon 與 Runtime 資料模型 |
| [Core/Currency_State_Field_Evidence.md](Core/Currency_State_Field_Evidence.md) | PG、CASH、CP 與帳戶經濟欄位證據 |

## 四、Channel、Lobby、Room、Player、Map 與 GameRule

| 文件 | 定位 |
|---|---|
| [Core/Channel_Lobby_193_221_Field_Evidence.md](Core/Channel_Lobby_193_221_Field_Evidence.md) | `193–221` top-level packet、parser、serializer 與欄位證據 |
| [Core/Channel_Lobby_Lifecycle.md](Core/Channel_Lobby_Lifecycle.md) | Channel → Lobby → Room 高階生命週期 |
| [Core/Room_Channel_GameRule_101_192_Field_Evidence.md](Core/Room_Channel_GameRule_101_192_Field_Evidence.md) | `101–192` packet、parser、serializer 與欄位證據 |
| [Core/Room_Settings_Packets.md](Core/Room_Settings_Packets.md) | Room UI selector/value、設定封包與資料流 |
| [Core/Map_And_Room.md](Core/Map_And_Room.md) | Map 專題入口、Map/Room 關係與未閉合問題 |
| [Core/GameRule_Lifecycle.md](Core/GameRule_Lifecycle.md) | CGameRule 狀態機、Ready/Start/End/Leave 與生命週期因果 |
| [Core/Player_Slot_Team.md](Core/Player_Slot_Team.md) | 16-slot、Player ID、Slot、Team/Group 與玩家有效狀態 |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | 跨 Packet／跨子系統的 Server reconstruction 抽象模型 |

## 五、遊戲模式、Gameplay、戰鬥、移動與武器事件

| 文件 | 定位 |
|---|---|
| [Core/Mode_Rules.md](Core/Mode_Rules.md) | 各模式規則、版本差異與 Runtime 待閉合項目 |
| [Core/Mode_Option_Tables.md](Core/Mode_Option_Tables.md) | mode-specific selector index/value 的主文件 |
| [Core/Gameplay_166_DeepEvidence.md](Core/Gameplay_166_DeepEvidence.md) | `166` Gameplay、死亡、K/D、state 與 subtype 深入證據 |
| [Core/Combat_Hit_Detection.md](Core/Combat_Hit_Detection.md) | 命中判定與戰鬥事件 |
| [Core/Damage_Calculation.md](Core/Damage_Calculation.md) | Damage modifier/transform 與 Runtime 計算 |
| [Core/Y_TCP_INF_Damage.md](Core/Y_TCP_INF_Damage.md) | `165/166 Y_TCP_INF` gameplay/event family、sender/receiver 與 state 證據 |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP 8/24、Queue、27-byte actor record 與欄位證據 |
| [Core/DropWeapon_Protocol.md](Core/DropWeapon_Protocol.md) | 丟棄武器封包與流程 |

## 六、Result、Score、Quest、Event 與 Resource

| 文件 | 定位 |
|---|---|
| [Core/Packet_166_Field_Map.md](Core/Packet_166_Field_Map.md) | `166` 欄位快速索引；完整證據回 `Gameplay_166_DeepEvidence.md` |
| [Core/TCP_269_Subtype7_Field_Detail.md](Core/TCP_269_Subtype7_Field_Detail.md) | `269 subtype 7` 完整欄位、玩家同步與 Result/K/D state |
| [Core/Result_Stat_Protocol_223_245_381_389.md](Core/Result_Stat_Protocol_223_245_381_389.md) | `223–245`、`381–389` Result／Stat／Quest 主題 |
| [Core/Quest_Event_ID_Mapping.md](Core/Quest_Event_ID_Mapping.md) | Quest/Event 與 ID mapping |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | Resource pack、資料模型與 loader/runtime 邊界 |

## 七、Kick Vote

| 文件 | 定位 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |
| [KickVote/Research.md](KickVote/Research.md) | Kick Vote 唯一主文件：UI、Scope/Reason/Target、eligibility、718–723、139、131/132、396/397 與 Server reconstruction |

## 八、已完成的內容整合

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

Foundation_TCP_Handshake_Login_Protocol.md
Network_Dispatch.md
Y_TCP_INF_Transport.md
    → Network_Protocol.md

KickVote/Protocol.md
KickVote/UI_State.md
KickVote/Evidence_And_Eligibility.md
KickVote/Master_Room.md
    → KickVote/Research.md
```

整合必須保留：

```text
證據、反證、欄位寬度、函式路徑、state mutation、[OPEN] 邊界
```

禁止以摘要取代完整研究。

## 九、文件角色與單一大方向主文件

目前以「大方向」而非單一 packet 拆分主文件：

```text
網路／傳輸／Dispatcher
    → Network_Protocol.md

登入／ClientData／玩家帳號資料
    → 登入與 ClientData 系列主文件

Channel／Lobby／Room／Player／GameRule
    → Room／Channel／GameRule 系列主文件

Gameplay／Combat／Movement
    → Gameplay／Combat 系列主文件

Result／Quest／Resource
    → Result／Quest／Resource 系列主文件

Kick Vote
    → KickVote/Research.md
```

仍可保留真正需要獨立維護的細部欄位文件，但新增文件前必須證明它不是既有大方向主文件可以直接容納的內容。

## 十、禁止再次失控

- 同一大方向被拆成多份互相重複的主文件。
- 同一 Packet 出現多份不同欄位真相。
- 建立 `New`、`Final`、`Final2`、`Latest`、`Copy` 等副本。
- 把猜測改成 confirmed 而沒有新證據。
- 把其它版本／地區資料無標記混入 2016 Japan final Client。
- 只更新子文件，不同步主文件、入口與索引。
- 為了方便 Server 實作而把未知欄位直接填成 `0`、固定常數或 guessed enum。
