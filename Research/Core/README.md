# PaperMan 核心遊戲機制逆向研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：`Core/` 唯一入口與研究脈絡導航。
> 更新基準：2026-09-17。

本目錄的目標不是「功能一份 Markdown」，而是讓每個問題只有一條最短閱讀路徑。

## 1. 一眼看懂

```text
我想知道封包怎麼走
→ Network_Protocol.md

我想知道 Packet 的 bytes
→ 對應 Field Evidence / Schema

我想知道 bytes 在遊戲中代表什麼
→ 對應 Domain 主文件

我想知道 Server 最後保存什麼
→ Server_State_Model.md
```

固定層次：

```text
C / LST / Extracted / Wiki
        ↓
Wire truth
        ↓
Domain semantic
        ↓
Server abstraction
        ↓
C# implementation
```

上層 abstraction 不得反向補出下層不存在的證據。

## 2. 整體脈絡

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
  ├─ TCP 960–963
  ├─ UDP Movement
  └─ Combat / Damage
  ↓
Result / Score / Quest
  ↓
PlayerData / Resource
```

研究證據固定交叉：

```text
IDA C / LST
    ↕
Extracted/
    ↕
日本 PaperMan Wiki
```

## 3. 問題 → 第一入口

| 問題 | 第一入口 | 深入資料 |
|---|---|---|
| TCP/UDP frame、XOR、checksum、Dispatcher | [`Network_Protocol.md`](Network_Protocol.md) | [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md) |
| `165/166` gameplay | [`Gameplay_Network.md`](Gameplay_Network.md) | [`Combat_Damage.md`](Combat_Damage.md)、[`Result_Quest_Stats.md`](Result_Quest_Stats.md) |
| `960–963` dropped weapon／pickup | [`Gameplay_Network.md`](Gameplay_Network.md) | 該文件 `960–963` 章節 |
| Login／Server List／`680–696` | [`Login_Adjacent_680_696_Field_Schema.md`](Login_Adjacent_680_696_Field_Schema.md) | [`ClientData_Protocol.md`](ClientData_Protocol.md) |
| `198/200/203/218/220/221` wire layout | [`ClientData_Protocol.md`](ClientData_Protocol.md) | [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md) |
| Character／Appearance／Inventory／Weapon／PG／CASH／CP | [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md) | [`ClientData_Protocol.md`](ClientData_Protocol.md) |
| `101–221` Room／Channel／GameRule packet bytes | [`Room_Channel_GameRule_101_221_Field_Evidence.md`](Room_Channel_GameRule_101_221_Field_Evidence.md) | [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md) |
| Channel／Lobby／Room／Player／Map／GameRule lifecycle | [`Room_Lobby_GameRule.md`](Room_Lobby_GameRule.md) | `101–221` Field Evidence、[`Room_Settings_Packets.md`](Room_Settings_Packets.md) |
| Mode／Rule／Selector values | [`Mode_Rules_And_Options.md`](Mode_Rules_And_Options.md) | [`Server_State_Model.md`](Server_State_Model.md) |
| Combat／Hit／Damage | [`Combat_Damage.md`](Combat_Damage.md) | [`Gameplay_Network.md`](Gameplay_Network.md) |
| UDP Movement | [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md) | [`Network_Protocol.md`](Network_Protocol.md) |
| Result／Score／K-D／Quest／Event／269 subtype 7 | [`Result_Quest_Stats.md`](Result_Quest_Stats.md) | 該文件 `269 subtype 7` 章節 |
| Resource pack／loader | [`Resource_Pack_Model.md`](Resource_Pack_Model.md) | 使用該 Resource 的主文件 |
| 跨子系統 Server model | [`Server_State_Model.md`](Server_State_Model.md) | 再回各領域主文件 |
| Kick Vote | `../KickVote/Research.md` | `../KickVote/README.md` |

## 4. 文件責任

```text
Network_Protocol
    = transport / frame / transform / dispatcher

Login_Adjacent_680_696_Field_Schema
    = 680–696 login-adjacent packet

ClientData_Protocol
    = 198 + 200/203/218/220/221 ClientData wire families

Character_Inventory_Equipment
    = Character / Inventory / Weapon / Economy runtime model

Room_Lobby_GameRule
    = Room / Player / Map / GameRule lifecycle

Room_Channel_GameRule_101_221_Field_Evidence
    = 101–221 exact packet wire evidence

Room_Settings_Packets
    = selector / setting data-flow

Mode_Rules_And_Options
    = mode rule / selector value semantics

Gameplay_Network
    = 165/166 + 960–963 gameplay event families

Combat_Damage
    = hit / geometry / damage calculation

UDP_Move_Inf_DeepEvidence
    = UDP movement / actor record

Result_Quest_Stats
    = result / score / quest / 269 hydration

Resource_Pack_Model
    = resource pack / loader / runtime boundary

Server_State_Model
    = cross-domain server abstraction only
```

## 5. 核心單一真相規則

```text
同一 Packet → 一份主要 wire truth
同一 State  → 一份主要 semantic truth
Server abstraction → 不產生第二份 Packet truth
未知欄位 → [OPEN]
```

不能因為 Server 需要編譯而把未知欄位改成 `0`、固定常數或 guessed enum。

## 6. 新證據放哪裡？

```text
已有主文件？
    ├─ 是 → 更新該文件
    └─ 否
        ↓
只是既有 packet / field / function evidence？
    ├─ 是 → 放對應 Field Evidence / Schema / Detail
    └─ 否
        ↓
跨子系統 abstraction？
    ├─ 是 → Server_State_Model
    └─ 否 → 先檢查 DOCUMENT_INDEX 與 AGENTS.md
```

完整文件清單以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準；格式與維護規則以 [`../../AGENTS.md`](../../AGENTS.md) 為準。
