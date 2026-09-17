# PaperMan 核心遊戲機制逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：`Core/` 的入口與研究脈絡導航。
> 更新基準：2026-09-17。

本目錄不追求「每個功能一份 Markdown」，而是追求 **每個問題都有唯一且明確的閱讀入口**。先找到主文件，再沿著它指向的 Field Evidence／Schema／Detail 深入；不要在多份摘要之間來回比對。

## 先建立整體脈絡

```text
Login
  ↓
Channel / Lobby
  ↓
Room / Player / Slot / Team
  ↓
GameRule / Mode / Room Settings
  ↓
Gameplay
  ├─ TCP 165/166
  ├─ UDP Movement
  └─ Combat / Damage
  ↓
Result / Score / Quest
  ↓
Profile / Inventory / Equipment / Resource
```

研究證據固定從三個方向互相校驗：

```text
IDA C / LST
    ↕
Extracted/
    ↕
日本 PaperMan Wiki
```

其中 `C` 與 `LST` 優先回答「程式實際怎麼讀寫」，`Extracted/` 優先回答「資源實際定義了什麼」，Wiki 優先回答「玩家可觀察到什麼」。三者衝突時保留衝突，不用猜測消除差異。

## 先問「我要查什麼」

| 我要查的問題 | 先讀哪份 | 再往哪裡深入 |
|---|---|---|
| TCP/UDP frame、XOR、checksum、Dispatcher 怎麼運作？ | [`Network_Protocol.md`](Network_Protocol.md) | UDP 具體資料 → [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md) |
| `165/166` 到底傳什麼？ | [`Gameplay_Network.md`](Gameplay_Network.md) | Combat 計算 → [`Combat_Damage.md`](Combat_Damage.md)；Result 聚合 → [`Result_Quest_Stats.md`](Result_Quest_Stats.md) |
| 登入、Server List、Login-adjacent packet？ | [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md) | `198` → [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md) |
| Character / Appearance / Inventory / Weapon 是什麼？ | [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md) | 共用 wire record → [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) |
| `198/200/203/218/220/221` 的 ClientData wire layout？ | [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md) | `198` 組合順序 → [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md) |
| PG / CASH / CP？ | [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md) | 相關 packet 回到各 packet schema |
| Channel / Lobby / Room / Player / Team / Map / GameRule 生命週期？ | [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md) | 精確 packet → `101–192` / `193–221` Field Evidence |
| Room selector / map / rule / setting packet？ | [`Room_Settings_Packets.md`](Room_Settings_Packets.md) | 高階生命週期回 [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md) |
| 各模式規則與 selector value？ | [`Mode_Rules_And_Options.md`](Mode_Rules_And_Options.md) | Runtime 狀態回 [`Server_State_Model.md`](Server_State_Model.md) |
| Result / K-D / Score / Quest / Event？ | [`Result_Quest_Stats.md`](Result_Quest_Stats.md) | `269 subtype 7` → [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md) |
| 跨整個 Server 要怎麼建模？ | [`Server_State_Model.md`](Server_State_Model.md) | 再回各領域主文件取得 packet truth |
| Resource pack / loader / runtime boundary？ | [`Resource_Pack_Model.md`](Resource_Pack_Model.md) | 再回使用該 Resource 的功能主文件 |
| 武器丟棄／拾取？ | [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md) | 需要 gameplay/context 時回 [`Gameplay_Network.md`](Gameplay_Network.md) |

## 文件責任邊界

```text
Network_Protocol
    = 怎麼傳

Room_Lobby_GameRule / Mode_Rules_And_Options / Gameplay_Network
    = 系統與事件是什麼、何時發生

*Field_Evidence / *Schema / *Detail
    = 某段 wire layout、欄位、函式與證據到底是什麼

Combat_Damage / UDP_Move_Inf_DeepEvidence / Resource_Pack_Model
    = 特定技術子領域的深入證據

Server_State_Model
    = 把各領域串成 Server abstraction，但不重新定義 packet truth
```

最重要的單一真相規則：**如果你已經在某文件看到一個 Packet／Field／State 的完整定義，不要在另一份文件重新抄一份；後者應只引用前者並補充自己責任範圍內的新證據。**

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

這是閱讀脈絡，不代表每一步都已經完全閉合。尚未證明的轉移、時間條件與欄位必須保留 `[OPEN]`。

## 網路／傳輸／Dispatcher

- [`Network_Protocol.md`](Network_Protocol.md)：TCP/UDP transport、frame、integrity/XOR、checksum、共用 codec、submission、opcode registration 與 dispatcher。

## 登入／ClientData／角色／裝備／經濟

- [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md)：`680–696` 登入鄰近協定。
- [`MyInfo_198_ClientData_Field_Schema.md`](MyInfo_198_ClientData_Field_Schema.md)：只負責 `198` 的組合式 bootstrap、組合順序與 `198` 特有 hydration。
- [`ClientData_Shared_Decoder_Field_Evidence.md`](ClientData_Shared_Decoder_Field_Evidence.md)：共用 ClientData wire family、nested record、decoder/serializer 與 Resource validation。
- [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md)：Character、Appearance、Inventory、Weapon Loadout、`tItemSlotToClient` 與 runtime model。
- [`Currency_State_Field_Evidence.md`](Currency_State_Field_Evidence.md)：PG、CASH、CP 與 account-economy 欄位證據。

這五份文件不是五套 `ClientData` 真相：`198` 負責組合，Shared Decoder 負責共用 wire family，Character 文件負責玩家資料模型，Currency 文件負責貨幣欄位，Login 文件負責 `680–696` packet 區域。

## Channel／Lobby／Room／Player／Map／GameRule

- [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md)：高階 lifecycle、Player Slot、Team/Group、Map、Room 與 GameRule。
- [`Room_Channel_GameRule_101_192_Field_Evidence.md`](Room_Channel_GameRule_101_192_Field_Evidence.md)：`101–192` 精確 packet／parser／serializer／field evidence。
- [`Channel_Lobby_193_221_Field_Evidence.md`](Channel_Lobby_193_221_Field_Evidence.md)：`193–221` 精確 packet／parser／serializer／field evidence。
- [`Room_Settings_Packets.md`](Room_Settings_Packets.md)：Room selector/value、設定封包與 UI data-flow。
- [`Server_State_Model.md`](Server_State_Model.md)：跨子系統 Server abstraction；不取代上述 packet truth。

## 模式／Gameplay／Combat／Movement

- [`Mode_Rules_And_Options.md`](Mode_Rules_And_Options.md)：ModeId、OptionIndex、OptionValue、規則與版本差異。
- [`Gameplay_Network.md`](Gameplay_Network.md)：`165/166 Y_TCP_INF` gameplay event family、166 subtype、Resource/state application。
- [`Combat_Damage.md`](Combat_Damage.md)：Hit Detection、Combat geometry、Damage modifier 與 `165` 建包前計算。
- [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)：UDP `8/24`、Queue、27-byte actor record 與 movement/state 欄位。
- [`DropWeapon_Protocol.md`](DropWeapon_Protocol.md)：武器丟棄／拾取事件。

## Result／Quest／Resource

- [`Result_Quest_Stats.md`](Result_Quest_Stats.md)：Result、Score/K-D、長期統計、Quest condition、Assist／Football 等事件。
- [`TCP_269_Subtype7_Field_Detail.md`](TCP_269_Subtype7_Field_Detail.md)：`269 subtype 7` 詳細欄位與 Result/K-D state。
- [`Resource_Pack_Model.md`](Resource_Pack_Model.md)：Resource pack、資料模型與 loader/runtime boundary。

## 研究與 Server 實作的共同原則

### 不把 Hex-Rays 猜測當成協定真相

實際 serializer／parser 的讀寫寬度高於表面變數型別；函式名稱、猜測名稱、相鄰 offset、常見協定習慣都不足以單獨命名欄位。

### 不用 `0` 填平未知欄位

未知欄位維持 `[OPEN]`。如果 Server 實作因相容性需要暫時填值，必須明確標示為：

```text
相容性假設，不是逆向確認
```

### 不讓 Server abstraction 反過來污染逆向結論

`Server_State_Model.md` 是實作上的共同抽象；真正的 packet width、field semantics、event ordering 仍應回到對應主文件與原始 C／LST。

## 新證據應該放哪裡？

```text
已有主文件描述這個概念？
    ├─ 是 → 直接更新該文件
    └─ 否
         ↓
只是既有 packet 的欄位／函式證據？
    ├─ 是 → 放進對應 Field Evidence / Schema / Detail
    └─ 否
         ↓
跨多個子系統的 abstraction？
    ├─ 是 → 放進 Server_State_Model
    └─ 否 → 先重新檢查 DOCUMENT_INDEX 與 AGENTS.md，再決定是否真的需要新文件
```

完整清單以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準；儲存庫級規則以 [`../../AGENTS.md`](../../AGENTS.md) 為準。
