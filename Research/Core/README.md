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
→ 對應 Protocol / Schema / Field Evidence

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

## 2. 整體脈絡

```text
Login / ClientData
        ↓
Channel / Lobby / Room
        ↓
Player / Slot / Team
        ↓
GameRule / Mode / Room Settings
        ↓
Gameplay / Combat
        ├─ TCP 165/166
        ├─ TCP 960–963
        └─ UDP Movement
        ↓
Result / Score / Quest
        ↓
Resource / PlayerData
```

## 3. 問題 → 第一入口

| 問題 | 第一入口 | 深入資料 |
|---|---|---|
| TCP/UDP frame、XOR、checksum、Dispatcher、UDP Movement | [`Network_Protocol.md`](Network_Protocol.md) | 該文件 UDP `8/24` 章節 |
| Hit、Damage、`165/166`、`960–963` | [`Gameplay_Combat.md`](Gameplay_Combat.md) | [`Result_Quest_Stats.md`](Result_Quest_Stats.md) |
| Login、Server List、`680–696`、`197–221` ClientData | [`Login_ClientData_Protocol.md`](Login_ClientData_Protocol.md) | [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md) |
| Character、Appearance、Inventory、Weapon、PG/CASH/CP | [`Character_Inventory_Equipment.md`](Character_Inventory_Equipment.md) | [`Login_ClientData_Protocol.md`](Login_ClientData_Protocol.md) |
| `101–221` Room／Channel／GameRule packet bytes | [`Room_Channel_GameRule_101_221_Field_Evidence.md`](Room_Channel_GameRule_101_221_Field_Evidence.md) | [`Room_GameRule_Mode.md`](Room_GameRule_Mode.md) |
| Room／Player／Map／GameRule／Mode lifecycle | [`Room_GameRule_Mode.md`](Room_GameRule_Mode.md) | `101–221` Field Evidence |
| Mode／Rule／Selector／Room settings | [`Room_GameRule_Mode.md`](Room_GameRule_Mode.md) | `101–221` Field Evidence |
| Result／Score／K-D／Quest／Event／`269 subtype 7` | [`Result_Quest_Stats.md`](Result_Quest_Stats.md) | 該文件 `269 subtype 7` 章節 |
| Resource pack／loader | [`Resource_Pack_Model.md`](Resource_Pack_Model.md) | 使用該 Resource 的主文件 |
| 跨子系統 Server model | [`Server_State_Model.md`](Server_State_Model.md) | 再回各領域主文件 |
| Kick Vote | `../KickVote/Research.md` | `../KickVote/README.md` |

## 4. 文件責任

```text
Network_Protocol
    = TCP/UDP transport、frame、codec、dispatcher、UDP movement

Login_ClientData_Protocol
    = 680–696 + 197–221 account/player-data wire protocol

Character_Inventory_Equipment
    = Character / Inventory / Weapon / Economy runtime model

Room_GameRule_Mode
    = Room / Player / Map / selector / Mode / GameRule lifecycle

Room_Channel_GameRule_101_221_Field_Evidence
    = 101–221 exact packet wire evidence

Gameplay_Combat
    = Hit / Damage → 165/166 → 960–963 gameplay events

Result_Quest_Stats
    = result / score / quest / 269 hydration

Resource_Pack_Model
    = resource pack / loader / runtime boundary

Server_State_Model
    = cross-domain Server abstraction only
```

## 5. 單一真相

```text
同一 Packet → 一份主要 wire truth
同一 State  → 一份主要 semantic truth
同一 Domain → 一份主要 model truth
Server abstraction → 不產生第二份 Packet truth
未知欄位 → [OPEN]
```

## 6. 新證據放哪裡？

```text
已有主文件？
    ├─ 是 → 更新該文件
    └─ 否
        ↓
是既有 packet / field / function evidence？
    ├─ 是 → 放進對應主題文件，不建立摘要副本
    └─ 否
        ↓
是跨子系統 abstraction？
    ├─ 是 → Server_State_Model
    └─ 否 → 先檢查 DOCUMENT_INDEX 與 AGENTS.md
```

不要因「這個功能很大」就重新建立第二份主文件；應先判斷它是不是既有主線的另一個 section。

完整文件清單以 [`../DOCUMENT_INDEX.md`](../DOCUMENT_INDEX.md) 為準；格式與維護規則以 [`../../AGENTS.md`](../../AGENTS.md) 為準。
