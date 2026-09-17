# PaperMan 研究文件完整索引

> 目的：讓人類與 LLM 能以最少的上下文找到唯一正確的研究入口，再沿證據鏈深入。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

本索引是 `Research/` 的唯一文件導覽。**索引描述「去哪裡找」，主文件描述「目前知道什麼」，原始 C／LST／Extracted／Wiki 描述「為什麼知道」。**

## 讀法

```text
我要回答一個問題
    ↓
先找「第一入口」
    ↓
必要時進入同列的「深入資料」
    ↓
遇到矛盾 → 回 C / LST / Extracted / Wiki
    ↓
不要從另一份摘要重新拼出第三套真相
```

## 最快定位

| 問題 | 第一入口 | 深入資料 |
|---|---|---|
| 網路 frame、XOR、checksum、Dispatcher | [`Core/Network_Protocol.md`](Core/Network_Protocol.md) | [`Core/UDP_Move_Inf_DeepEvidence.md`](Core/UDP_Move_Inf_DeepEvidence.md) |
| `165/166 Y_TCP_INF` | [`Core/Gameplay_Network.md`](Core/Gameplay_Network.md) | [`Core/Combat_Damage.md`](Core/Combat_Damage.md)、[`Core/Result_Quest_Stats.md`](Core/Result_Quest_Stats.md) |
| `960–963` 武器丟棄／拾取 | [`Core/Gameplay_Network.md`](Core/Gameplay_Network.md) | 該文件 `960–963` 章節 |
| Login／Server List／`680–696` | [`Core/Login_Adjacent_680_696_Field_Schema.md`](Core/Login_Adjacent_680_696_Field_Schema.md) | [`Core/ClientData_Shared_Decoder_Field_Evidence.md`](Core/ClientData_Shared_Decoder_Field_Evidence.md) |
| `198` MyInfo／Avatar bootstrap | [`Core/MyInfo_198_ClientData_Field_Schema.md`](Core/MyInfo_198_ClientData_Field_Schema.md) | Shared ClientData wire family |
| Character／Appearance／Inventory／Weapon | [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md) | [`Core/ClientData_Shared_Decoder_Field_Evidence.md`](Core/ClientData_Shared_Decoder_Field_Evidence.md) |
| `198/200/203/218/220/221` wire layout | [`Core/ClientData_Shared_Decoder_Field_Evidence.md`](Core/ClientData_Shared_Decoder_Field_Evidence.md) | [`Core/MyInfo_198_ClientData_Field_Schema.md`](Core/MyInfo_198_ClientData_Field_Schema.md) |
| PG／CASH／CP | [`Core/Currency_State_Field_Evidence.md`](Core/Currency_State_Field_Evidence.md) | 回 [`Core/Room_Channel_GameRule_101_221_Field_Evidence.md`](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) 看 packet context |
| `101–221` Room／Channel／GameRule packet bytes | [`Core/Room_Channel_GameRule_101_221_Field_Evidence.md`](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) | [`Core/Room_Lobby_GameRule.md`](Core/Room_Lobby_GameRule.md)、[`Core/Room_Settings_Packets.md`](Core/Room_Settings_Packets.md) |
| Channel／Lobby／Room／Player／Map／GameRule 生命週期 | [`Core/Room_Lobby_GameRule.md`](Core/Room_Lobby_GameRule.md) | `101–221` Field Evidence |
| Mode／Rule／Selector value | [`Core/Mode_Rules_And_Options.md`](Core/Mode_Rules_And_Options.md) | [`Core/Server_State_Model.md`](Core/Server_State_Model.md) |
| Combat／Hit／Damage | [`Core/Combat_Damage.md`](Core/Combat_Damage.md) | 回 [`Core/Gameplay_Network.md`](Core/Gameplay_Network.md) 看 `165` 建包上下文 |
| UDP Movement | [`Core/UDP_Move_Inf_DeepEvidence.md`](Core/UDP_Move_Inf_DeepEvidence.md) | 回 [`Core/Network_Protocol.md`](Core/Network_Protocol.md) 看 transport |
| Result／Score／K-D／Quest／Event | [`Core/Result_Quest_Stats.md`](Core/Result_Quest_Stats.md) | 內含 `269 subtype 7` 證據 |
| Resource pack／loader／runtime | [`Core/Resource_Pack_Model.md`](Core/Resource_Pack_Model.md) | 回使用該 Resource 的主文件 |
| 跨子系統 Server state abstraction | [`Core/Server_State_Model.md`](Core/Server_State_Model.md) | 再回各領域主文件取得 packet truth |
| Kick Vote | [`KickVote/README.md`](KickVote/README.md) | [`KickVote/Research.md`](KickVote/Research.md) |

## 一、研究入口

| 文件 | 唯一責任 |
|---|---|
| [Research/README.md](README.md) | 研究目標、版本基準、證據方法與整體工作流 |
| [Core/README.md](Core/README.md) | Core 內部「問題 → 主文件 → 證據文件」導航 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題導航 |

## 二、網路、封包與 Dispatcher

| 文件 | 唯一責任 |
|---|---|
| [Core/Network_Protocol.md](Core/Network_Protocol.md) | TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration、Dispatcher |

## 三、登入、ClientData、角色、裝備與經濟

| 文件 | 唯一責任 |
|---|---|
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` packet／parser／serializer／login-adjacent state |
| [Core/MyInfo_198_ClientData_Field_Schema.md](Core/MyInfo_198_ClientData_Field_Schema.md) | `198` 的組合順序、封包邊界、198-specific hydration；不維護共用 record schema |
| [Core/ClientData_Shared_Decoder_Field_Evidence.md](Core/ClientData_Shared_Decoder_Field_Evidence.md) | 共用 ClientData wire family、nested record、decoder／serializer／resource validation |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Appearance、Inventory、Weapon Loadout、`tItemSlotToClient` 與 runtime 資料模型 |
| [Core/Currency_State_Field_Evidence.md](Core/Currency_State_Field_Evidence.md) | PG、CASH、CP 與 account-economy 欄位證據 |

**避免混淆：** `198` 是「怎麼組合多個 component」；Shared Decoder 是「component 的 wire truth」；Character 是「runtime/domain model」；Currency 是「貨幣欄位 truth」；Login 是「680–696 packet 區域」。

## 四、Channel、Lobby、Room、Player、Map、GameRule

| 文件 | 唯一責任 |
|---|---|
| [Core/Room_Lobby_GameRule.md](Core/Room_Lobby_GameRule.md) | Channel → Lobby → Room、16-slot Player、Team/Group、Map、Room 與 GameRule 的高階生命週期與關係 |
| [Core/Room_Channel_GameRule_101_221_Field_Evidence.md](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) | `101–221` 精確 packet、parser、serializer、欄位與直接資料流證據 |
| [Core/Room_Settings_Packets.md](Core/Room_Settings_Packets.md) | Room selector/value、設定 packet 與 UI data-flow |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | 跨子系統 Server abstraction；不重新定義 Packet／Field truth |

## 五、Mode、Gameplay、Combat、Movement

| 文件 | 唯一責任 |
|---|---|
| [Core/Mode_Rules_And_Options.md](Core/Mode_Rules_And_Options.md) | ModeId、OptionIndex、OptionValue、模式規則、selector values、版本差異 |
| [Core/Gameplay_Network.md](Core/Gameplay_Network.md) | `165/166 Y_TCP_INF` gameplay event family、166 subtype、Resource/state application，以及 `960–963` 武器丟棄／拾取 protocol |
| [Core/Combat_Damage.md](Core/Combat_Damage.md) | Hit Detection、combat geometry、damage modifier、`165` 建包前計算 |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP `8/24`、queue、27-byte actor record、movement/state fields |

## 六、Result、Score、Quest、Event、Resource

| 文件 | 唯一責任 |
|---|---|
| [Core/Result_Quest_Stats.md](Core/Result_Quest_Stats.md) | Result、Score/K-D、長期統計、Quest condition、Assist／Football 等事件的主線真相；含 `269 subtype 7` 詳細欄位 |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | Resource pack、資料模型與 loader/runtime boundary |

## 七、Kick Vote

| 文件 | 唯一責任 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題入口 |
| [KickVote/Research.md](KickVote/Research.md) | Kick Vote 唯一主文件：UI、Scope/Reason/Target、eligibility、718–723、139、131/132、396/397、Server reconstruction |

## 八、跨文件閱讀規則

### `Packet` 問題

```text
先找 Opcode 所屬的主題／封包文件
    ↓
需要 byte layout → Field Evidence / Schema
    ↓
需要 transport → Network_Protocol
```

### `State` 問題

```text
先找真正擁有該 state 的領域主文件
    ↓
確認誰寫入、誰讀取、何時變更
    ↓
只有跨領域時才看 Server_State_Model
```

### `Resource` 問題

```text
先找 Resource 被哪個功能使用
    ↓
讀該功能的 semantic context
    ↓
需要 loader／pack → Resource_Pack_Model
```

### `C# Server` 問題

```text
不要從 Server_State_Model 反推 Packet

Packet truth
    → Protocol / Schema / Field Evidence

Domain truth
    → 對應主題主文件

Server abstraction
    → Server_State_Model
```

## 九、已整合的舊文件

以下名稱只保留作歷史追溯；它們不是閱讀入口，也不應重新建立：

```text
Foundation_TCP_Handshake_Login_Protocol.md
Network_Dispatch.md
Y_TCP_INF_Transport.md
    → Core/Network_Protocol.md

Channel_Lobby_Lifecycle.md
Player_Slot_Team.md
Map_And_Room.md
GameRule_Lifecycle.md
    → Core/Room_Lobby_GameRule.md

Combat_Hit_Detection.md
Damage_Calculation.md
    → Core/Combat_Damage.md

Mode_Rules.md
Mode_Option_Tables.md
    → Core/Mode_Rules_And_Options.md

Gameplay_166_DeepEvidence.md
Y_TCP_INF_Damage.md
Packet_166_Field_Map.md
    → Core/Gameplay_Network.md

Result_Stat_Protocol_223_245_381_389.md
Quest_Event_ID_Mapping.md
TCP_269_Subtype7_Field_Detail.md
    → Core/Result_Quest_Stats.md

DropWeapon_Protocol.md
    → Core/Gameplay_Network.md

Room_Channel_GameRule_101_192_Field_Evidence.md
Channel_Lobby_193_221_Field_Evidence.md
    → Core/Room_Channel_GameRule_101_221_Field_Evidence.md

KickVote/Protocol.md
KickVote/UI_State.md
KickVote/Evidence_And_Eligibility.md
KickVote/Master_Room.md
    → KickVote/Research.md
```

這些名稱的存在只用來回答「以前的研究內容現在去哪裡」，不是要求讀者重新閱讀多份舊摘要。

## 十、整理硬規則

```text
同一 Packet 只有一份主要欄位真相
同一 State 只有一份主要語意真相
Server abstraction 不產生第二套 Packet truth
未知欄位維持 [OPEN]
未獲證據不得填 0／固定常數／猜測 enum
不同年份／地區／Client 不可無標記混用
新增文件前先證明既有文件無法承載
```

新增、刪除、合併或重新命名研究文件後，必須同步檢查 `Research/README.md`、`Research/Core/README.md`、本索引與所有受影響交叉連結。
