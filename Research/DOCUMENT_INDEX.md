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
| [Core/README.md](Core/README.md) | Core 研究範圍與大方向導航 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |

## 二、網路、傳輸、封包與 Dispatcher

| 文件 | 定位 |
|---|---|
| [Core/Network_Protocol.md](Core/Network_Protocol.md) | TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration 與 dispatcher |

## 三、登入、ClientData、玩家資料與裝備

| 文件 | 定位 |
|---|---|
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` 登入鄰近協定、`681` server-list record 與 login-adjacent state |
| [Core/MyInfo_198_ClientData_Field_Schema.md](Core/MyInfo_198_ClientData_Field_Schema.md) | `198` MyInfo／Avatar hydration、composite ClientData 與未閉合欄位 |
| [Core/ClientData_Shared_Decoder_Field_Evidence.md](Core/ClientData_Shared_Decoder_Field_Evidence.md) | ClientData 共用 wire family、nested record、decoder/serializer 與 resource validation |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Appearance、Inventory、Weapon Loadout、tItemSlotToClient 與 Runtime 資料模型 |
| [Core/Currency_State_Field_Evidence.md](Core/Currency_State_Field_Evidence.md) | PG、CASH、CP 與 account-economy 欄位證據 |

## 四、Channel、Lobby、Room、Player、Map 與 GameRule

| 文件 | 定位 |
|---|---|
| [Core/Room_Lobby_GameRule.md](Core/Room_Lobby_GameRule.md) | Channel → Lobby → Room、Player Slot／Team、Map、Room selector 與 CGameRule 生命週期的大方向主文件 |
| [Core/Room_Channel_GameRule_101_192_Field_Evidence.md](Core/Room_Channel_GameRule_101_192_Field_Evidence.md) | `101–192` 精確 packet、parser、serializer 與欄位證據 |
| [Core/Channel_Lobby_193_221_Field_Evidence.md](Core/Channel_Lobby_193_221_Field_Evidence.md) | `193–221` 精確 top-level packet、parser、serializer 與欄位證據 |
| [Core/Room_Settings_Packets.md](Core/Room_Settings_Packets.md) | Room selector/value、設定封包與 UI data-flow 的詳細證據 |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | 跨 Packet／跨子系統的 Server reconstruction 抽象模型 |

## 五、遊戲模式、Gameplay、戰鬥、移動與武器事件

| 文件 | 定位 |
|---|---|
| [Core/Mode_Rules_And_Options.md](Core/Mode_Rules_And_Options.md) | 各模式規則、Client mode builder、selector index/value、版本差異與 Runtime 待閉合項目 |
| [Core/Gameplay_Network.md](Core/Gameplay_Network.md) | `165/166 Y_TCP_INF` gameplay event、166 subtype、Resource/state application 與 sender/receiver |
| [Core/Combat_Damage.md](Core/Combat_Damage.md) | Hit Detection、Combat geometry、Damage modifier 與 `165` 建包前計算 |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP 8/24、Queue、27-byte actor record 與 movement/state 欄位證據 |
| [Core/DropWeapon_Protocol.md](Core/DropWeapon_Protocol.md) | 丟棄／拾取武器事件封包與流程 |

## 六、Result、Score、Quest、Event 與 Resource

| 文件 | 定位 |
|---|---|
| [Core/Result_Quest_Stats.md](Core/Result_Quest_Stats.md) | Result、Score/K-D、長期統計、Quest condition、Assist／Football 等相關事件的整合主文件 |
| [Core/TCP_269_Subtype7_Field_Detail.md](Core/TCP_269_Subtype7_Field_Detail.md) | `269 subtype 7` 詳細欄位、玩家同步與 Result/K-D state |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | Resource pack、資料模型與 loader/runtime 邊界 |

## 七、Kick Vote

| 文件 | 定位 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |
| [KickVote/Research.md](KickVote/Research.md) | Kick Vote 唯一主文件：UI、Scope/Reason/Target、eligibility、718–723、139、131/132、396/397 與 Server reconstruction |

## 八、已完成的內容整合

```text
Foundation_TCP_Handshake_Login_Protocol.md
Network_Dispatch.md
Y_TCP_INF_Transport.md
    → Network_Protocol.md

Channel_Lobby_Lifecycle.md
Player_Slot_Team.md
Map_And_Room.md
GameRule_Lifecycle.md
    → Room_Lobby_GameRule.md

Combat_Hit_Detection.md
Damage_Calculation.md
    → Combat_Damage.md

Mode_Rules.md
Mode_Option_Tables.md
    → Mode_Rules_And_Options.md

Gameplay_166_DeepEvidence.md
Y_TCP_INF_Damage.md
Packet_166_Field_Map.md
    → Gameplay_Network.md

Result_Stat_Protocol_223_245_381_389.md
Quest_Event_ID_Mapping.md
    → Result_Quest_Stats.md

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

目前原則是：

```text
網路／傳輸／Dispatcher
    → Network_Protocol.md

登入／ClientData／角色／裝備／經濟
    → 登入與 ClientData／玩家資料系列主文件

Channel／Lobby／Room／Player／Map／GameRule
    → Room_Lobby_GameRule.md
    → packet detail → 101–192 / 193–221 Field Evidence
    → Room_Settings_Packets.md

遊戲模式／規則／selector values
    → Mode_Rules_And_Options.md

Gameplay／165/166／遊戲事件
    → Gameplay_Network.md

Combat／Hit／Damage
    → Combat_Damage.md

Movement
    → UDP_Move_Inf_DeepEvidence.md

Result／Score／Quest／Event
    → Result_Quest_Stats.md
    → TCP_269_Subtype7_Field_Detail.md

Resource
    → Resource_Pack_Model.md

跨全部子系統的 Server abstraction
    → Server_State_Model.md

Kick Vote
    → KickVote/Research.md
```

只有在「責任確實不同且無法無損放入既有大方向主文件」時才保留細部 Field Evidence、Schema、Detail 或 Resource Mapping 文件。新增文件前必須先證明其必要性。

## 十、禁止再次失控

- 同一大方向被拆成多份互相重複的主文件。
- 同一 Packet 出現多份不同欄位真相。
- 建立 `New`、`Final`、`Final2`、`Latest`、`Copy` 等副本。
- 把猜測改成 confirmed 而沒有新證據。
- 把其它版本／地區資料無標記混入 2016 Japan final Client。
- 只更新子文件，不同步主文件、入口與索引。
- 為了方便 Server 實作而把未知欄位直接填成 `0`、固定常數或 guessed enum。
