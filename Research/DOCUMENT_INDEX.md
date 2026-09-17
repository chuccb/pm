# PaperMan 研究文件完整索引

> 目的：讓人類與 LLM 以最少上下文找到唯一正確入口，再沿證據鏈深入。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

本索引是 `Research/` 的唯一文件導覽。**索引回答「去哪裡」，主文件回答「目前知道什麼」，C／LST／Extracted／Wiki 回答「為什麼知道」。**

## 1. 最快定位

| 問題 | 第一入口 | 深入資料 |
|---|---|---|
| 網路 frame、XOR、checksum、Dispatcher | [`Core/Network_Protocol.md`](Core/Network_Protocol.md) | [`Core/UDP_Move_Inf_DeepEvidence.md`](Core/UDP_Move_Inf_DeepEvidence.md) |
| `165/166`、Hit、Damage、960–963 | [`Core/Gameplay_Combat.md`](Core/Gameplay_Combat.md) | [`Core/Result_Quest_Stats.md`](Core/Result_Quest_Stats.md) |
| UDP Movement | [`Core/UDP_Move_Inf_DeepEvidence.md`](Core/UDP_Move_Inf_DeepEvidence.md) | [`Core/Network_Protocol.md`](Core/Network_Protocol.md) |
| Login／Server List／`680–696` | [`Core/Login_Adjacent_680_696_Field_Schema.md`](Core/Login_Adjacent_680_696_Field_Schema.md) | [`Core/ClientData_Protocol.md`](Core/ClientData_Protocol.md) |
| `198/200/203/218/220/221` wire layout | [`Core/ClientData_Protocol.md`](Core/ClientData_Protocol.md) | [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md) |
| Character／Appearance／Inventory／Weapon／PG／CASH／CP | [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md) | [`Core/ClientData_Protocol.md`](Core/ClientData_Protocol.md) |
| `101–221` Room／Channel／GameRule packet bytes | [`Core/Room_Channel_GameRule_101_221_Field_Evidence.md`](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) | [`Core/Room_GameRule_Mode.md`](Core/Room_GameRule_Mode.md) |
| Channel／Lobby／Room／Player／Map／GameRule／Mode lifecycle | [`Core/Room_GameRule_Mode.md`](Core/Room_GameRule_Mode.md) | `101–221` Field Evidence |
| Mode／Rule／Selector value／Room settings | [`Core/Room_GameRule_Mode.md`](Core/Room_GameRule_Mode.md) | `101–221` Field Evidence |
| Result／Score／K-D／Quest／Event／269 subtype 7 | [`Core/Result_Quest_Stats.md`](Core/Result_Quest_Stats.md) | 該文件 `269 subtype 7` 章節 |
| Resource pack／loader／runtime | [`Core/Resource_Pack_Model.md`](Core/Resource_Pack_Model.md) | 使用該 Resource 的主文件 |
| 跨子系統 Server abstraction | [`Core/Server_State_Model.md`](Core/Server_State_Model.md) | 再回各領域主文件 |
| Kick Vote | [`KickVote/README.md`](KickVote/README.md) | [`KickVote/Research.md`](KickVote/Research.md) |

## 2. 研究入口

| 文件 | 唯一責任 |
|---|---|
| [Research/README.md](README.md) | 研究目標、版本基準、證據方法與整體工作流 |
| [Core/README.md](Core/README.md) | Core 內部問題 → 主文件 → 證據文件導航 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題導航 |

## 3. Core 主文件

| 文件 | 唯一責任 |
|---|---|
| [Core/Network_Protocol.md](Core/Network_Protocol.md) | TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、Dispatcher |
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` login/account-adjacent packet／parser／serializer |
| [Core/ClientData_Protocol.md](Core/ClientData_Protocol.md) | `198` composite bootstrap、Family A/B/C/D、`200/203/218/220/221` ClientData wire schema 與 validation |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character／Appearance／Inventory／Weapon Loadout／Economy runtime model |
| [Core/Room_GameRule_Mode.md](Core/Room_GameRule_Mode.md) | Channel／Lobby／Room／Player／Map／selector／Mode／GameRule lifecycle 與 mode rules |
| [Core/Room_Channel_GameRule_101_221_Field_Evidence.md](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) | `101–221` exact packet wire／parser／serializer／field evidence |
| [Core/Gameplay_Combat.md](Core/Gameplay_Combat.md) | Hit／Damage → `165/166` → `960–963` gameplay event families |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP `8/24`、queue、27-byte actor record、movement/state fields |
| [Core/Result_Quest_Stats.md](Core/Result_Quest_Stats.md) | Result、Score/K-D、Quest、Event，以及 `269 subtype 7` hydration |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | Resource pack、資料模型與 loader/runtime boundary |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | 跨子系統 Server abstraction；不重新定義 Packet truth |

**目前核心主線只有這些文件。新增文件前，先證明既有文件不能承載。**

## 4. Kick Vote

| 文件 | 唯一責任 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |
| [KickVote/Research.md](KickVote/Research.md) | Kick Vote 唯一主文件：UI、eligibility、718–723、139、131/132、396/397 與 Server reconstruction |

## 5. 跨文件閱讀規則

### Packet

```text
先找所屬主題
    ↓
需要 bytes → 該主題的 Protocol / Schema / Field Evidence
    ↓
需要 transport → Network_Protocol
```

### State

```text
先找真正擁有 state 的主文件
    ↓
看 writer / reader / transition
    ↓
只有跨域才看 Server_State_Model
```

### Resource

```text
先找使用它的功能
    ↓
再看 Resource_Pack_Model 的 loader / pack 證據
```

### C# Server

```text
Packet truth
    → Protocol / Schema / Field Evidence

Domain truth
    → Domain 主文件

Cross-domain abstraction
    → Server_State_Model
```

不要從 Server abstraction 反推 Packet bytes。

## 6. 歷史整合紀錄

以下名稱只為回答「舊研究現在去哪裡」，不是現行閱讀入口：

```text
Foundation_TCP_Handshake_Login_Protocol.md
Network_Dispatch.md
Y_TCP_INF_Transport.md
    → Core/Network_Protocol.md

Channel_Lobby_Lifecycle.md
Player_Slot_Team.md
Map_And_Room.md
GameRule_Lifecycle.md
    → Core/Room_GameRule_Mode.md

Combat_Hit_Detection.md
Damage_Calculation.md
    → Core/Gameplay_Combat.md

Mode_Rules.md
Mode_Option_Tables.md
Room_Settings_Packets.md
    → Core/Room_GameRule_Mode.md

Gameplay_166_DeepEvidence.md
Y_TCP_INF_Damage.md
Packet_166_Field_Map.md
DropWeapon_Protocol.md
    → Core/Gameplay_Combat.md

Result_Stat_Protocol_223_245_381_389.md
Quest_Event_ID_Mapping.md
TCP_269_Subtype7_Field_Detail.md
    → Core/Result_Quest_Stats.md

Room_Channel_GameRule_101_192_Field_Evidence.md
Channel_Lobby_193_221_Field_Evidence.md
    → Core/Room_Channel_GameRule_101_221_Field_Evidence.md

MyInfo_198_ClientData_Field_Schema.md
ClientData_Shared_Decoder_Field_Evidence.md
    → Core/ClientData_Protocol.md

Currency_State_Field_Evidence.md
    → Core/Character_Inventory_Equipment.md

KickVote/Protocol.md
KickVote/UI_State.md
KickVote/Evidence_And_Eligibility.md
KickVote/Master_Room.md
    → KickVote/Research.md
```

## 7. 整理硬規則

```text
同一 Packet → 一份主要 wire truth
同一 State  → 一份主要 semantic truth
同一 Domain → 一份主要 model truth
Server abstraction → 不產生第二套 Packet truth
未知欄位 → [OPEN]
未獲證據 → 不填 0／固定常數／猜測 enum
不同版本／地區 → 不可無標記混用
新增文件前 → 先證明既有文件無法承載
```
