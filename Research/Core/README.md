# PaperMan 核心逆向研究

> 目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 本文件：Core 唯一導航入口。
> 更新基準：2026-09-17。

## 一眼看懂

```text
怎麼傳                         → Network_Protocol.md
登入後玩家資料怎麼傳           → Login_ClientData_Protocol.md
角色／背包／裝備的 Client 狀態 → Character_Inventory_Equipment.md
Room / Mode / GameRule         → Room_GameRule_Mode.md
101–221 精確封包 bytes         → Room_Channel_GameRule_101_221_Field_Evidence.md
命中 → 傷害 → 165/166 → Pickup → Gameplay_Combat.md
Result / K-D / Quest / 269      → Result_Quest_Stats.md
Resource pack / loader         → Resource_Pack_Model.md
Server 最後怎麼建模             → Server_State_Model.md
```

## 整體資料流

```text
Login / ClientData
    ↓
Channel / Lobby / Room
    ↓
Player / Slot / Team
    ↓
GameRule / Mode
    ↓
Gameplay / Combat / Movement
    ↓
Result / Quest
    ↓
PlayerData / Resource
```

證據固定交叉：

```text
IDA C / LST
    ↕
Extracted/
    ↕
日本 PaperMan Wiki
```

固定升級鏈：

```text
原始證據 → wire truth → domain semantic → server abstraction → C# implementation
```

上層模型不能反向補出下層不存在的證據。

## 文件責任

| 文件 | 唯一責任 |
|---|---|
| `Network_Protocol.md` | TCP/UDP transport、frame、codec、integrity/XOR、checksum、dispatcher、UDP movement |
| `Login_ClientData_Protocol.md` | `680–696` + `197–221` login / MyInfo / ClientData wire protocol |
| `Character_Inventory_Equipment.md` | Character、Appearance、Inventory、Weapon Loadout、Economy runtime/domain model |
| `Room_GameRule_Mode.md` | Channel/Lobby/Room、Player/Slot/Team、Map、selector、Mode、GameRule lifecycle/rules |
| `Room_Channel_GameRule_101_221_Field_Evidence.md` | `101–221` precise packet/parser/serializer evidence |
| `Gameplay_Combat.md` | Hit/Damage → `165/166` → `960–963` gameplay chain |
| `Result_Quest_Stats.md` | Result、Score/K-D、Quest、Event、`269 subtype 7` hydration |
| `Resource_Pack_Model.md` | Resource pack、loader、resource/runtime boundary |
| `Server_State_Model.md` | cross-domain Server abstraction only |

Kick Vote 位於 `../KickVote/Research.md`。

## 閱讀規則

### Packet

```text
先找所屬主題
    ↓
需要 bytes → 該主題文件
    ↓
需要 frame / transport → Network_Protocol
```

### State

```text
找真正擁有 state 的主文件
    ↓
看 writer / reader / transition
    ↓
跨域才看 Server_State_Model
```

### Resource

```text
先看使用它的功能
    ↓
需要 pack / loader 細節 → Resource_Pack_Model
```

### C# Server

```text
Packet truth → 對應 Protocol / Field Evidence
Domain truth → 對應 Domain 主文件
Cross-domain abstraction → Server_State_Model
```

## 硬規則

```text
同一 Packet → 一份主要 wire truth
同一 State  → 一份主要 semantic truth
同一 Domain → 一份主要 model truth
未知欄位 → [OPEN]
沒有證據 → 不填 0 / 固定常數 / guessed enum
不同版本／地區 → 不可無標記混用
新增文件 → 先證明既有文件無法承載
```

## 新證據應放哪裡？

```text
已有主線？
 ├─ 是 → 更新原文件
 └─ 否
    ↓
只是既有 packet / field / function 證據？
 ├─ 是 → 放既有主題文件
 └─ 否
    ↓
跨子系統 abstraction？
 ├─ 是 → Server_State_Model
 └─ 否 → 先檢查 DOCUMENT_INDEX / AGENTS.md
```
