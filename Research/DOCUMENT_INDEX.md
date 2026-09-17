# PaperMan 研究文件完整索引

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-18。
> 本索引回答一件事：**我要找什麼，第一站去哪裡。**

## 最短閱讀路徑

```text
AGENTS.md
   ↓
Research/README.md
   ↓
本索引
   ↓
第一入口
   ↓
需要證據才往下追 C / LST / Extracted / Wiki
```

## 最快定位

| 問題 | 第一入口 |
|---|---|
| TCP/UDP、frame、XOR、checksum、核心 dispatcher、UDP movement | [`Core/Network_Protocol.md`](Core/Network_Protocol.md) |
| TCP dispatcher 完整 opcode → handler、UDP peer/bootstrap、movement/action identity 交叉證據 | [`Core/Network_Dispatcher_Inventory.md`](Core/Network_Dispatcher_Inventory.md) |
| Login、Server List、`680–696`、MyInfo、`197–221` ClientData | [`Core/Login_ClientData_Protocol.md`](Core/Login_ClientData_Protocol.md) |
| Character、Appearance、Inventory、Weapon、PG/CASH/CP | [`Core/Character_Inventory_Equipment.md`](Core/Character_Inventory_Equipment.md) |
| Channel、Lobby、Room、Player、Map、Mode、GameRule、selector | [`Core/Room_GameRule_Mode.md`](Core/Room_GameRule_Mode.md) |
| `101–221` 精確 packet/parser/serializer bytes | [`Core/Room_Channel_GameRule_101_221_Field_Evidence.md`](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) |
| Hit、Damage、`165/166`、`960–963` | [`Core/Gameplay_Combat.md`](Core/Gameplay_Combat.md) |
| Result、Score、K-D、Quest、Event、`269 subtype 7` | [`Core/Result_Quest_Stats.md`](Core/Result_Quest_Stats.md) |
| Resource pack、loader、runtime boundary | [`Core/Resource_Pack_Model.md`](Core/Resource_Pack_Model.md) |
| 跨子系統 Server state abstraction | [`Core/Server_State_Model.md`](Core/Server_State_Model.md) |
| Kick Vote | [`KickVote/Research.md`](KickVote/Research.md) |

## Core 現存文件

| 文件 | 唯一責任 |
|---|---|
| [Core/README.md](Core/README.md) | Core 導航與閱讀規則 |
| [Core/Network_Protocol.md](Core/Network_Protocol.md) | TCP/UDP transport、frame、codec、integrity/XOR、checksum、核心 dispatcher、UDP movement |
| [Core/Network_Dispatcher_Inventory.md](Core/Network_Dispatcher_Inventory.md) | `sub_58B010` 完整 TCP opcode → handler inventory、UDP peer/bootstrap、movement/action identity 跨函式證據 |
| [Core/Login_ClientData_Protocol.md](Core/Login_ClientData_Protocol.md) | `680–696` + `197–221` login / MyInfo / ClientData wire protocol |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Appearance、Inventory、Weapon Loadout、Economy runtime/domain model |
| [Core/Room_GameRule_Mode.md](Core/Room_GameRule_Mode.md) | Channel/Lobby/Room、Player/Slot/Team、Map、selector、Mode、GameRule lifecycle/rules |
| [Core/Room_Channel_GameRule_101_221_Field_Evidence.md](Core/Room_Channel_GameRule_101_221_Field_Evidence.md) | `101–221` exact packet/parser/serializer/field evidence |
| [Core/Gameplay_Combat.md](Core/Gameplay_Combat.md) | Hit/Damage → `165/166` → `960–963` gameplay chain |
| [Core/Result_Quest_Stats.md](Core/Result_Quest_Stats.md) | Result、Score/K-D、Quest、Event、`269 subtype 7` hydration |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | Resource pack、loader、resource/runtime boundary |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | Cross-domain Server abstraction；不重新定義 Packet truth |

## Kick Vote

| 文件 | 唯一責任 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題導航 |
| [KickVote/Research.md](KickVote/Research.md) | Kick Vote 唯一主文件：UI、eligibility、718–723、139、131/132、396/397、Server reconstruction |

## 跨文件閱讀規則

### Packet

```text
第一入口
  ↓
需要 bytes → 該入口文件的 wire/schema section
  ↓
需要 transport → Network_Protocol
需要完整 dispatcher / peer evidence → Network_Dispatcher_Inventory
```

### State

```text
找真正擁有該 state 的領域文件
  ↓
看 writer / reader / transition
  ↓
跨域才看 Server_State_Model
```

### Resource

```text
先看 Resource 被哪個功能使用
  ↓
需要 pack / loader → Resource_Pack_Model
```

### C# Server

```text
Packet truth → Protocol / Field Evidence
Domain truth → Domain 主文件
Cross-domain abstraction → Server_State_Model
```

不要從 Server abstraction 反推 Packet bytes。

## 單一真相規則

```text
同一 Packet → 一份主要 wire truth
同一 State  → 一份主要 semantic truth
同一 Domain → 一份主要 model truth
未知欄位 → [OPEN]
沒有證據 → 不填 0 / 固定常數 / guessed enum
不同版本／地區 → 不可無標記混用
新增文件 → 先證明既有文件無法承載
```

## 文件整理原則

舊研究內容已依責任合併到現存主文件；**舊檔名不再作為閱讀入口，也不應重新建立平行版本。**

當新增證據時：

```text
已有主題？ → 更新既有主文件
只有既有主題的欄位證據？ → 放該主文件對應 section
跨子系統 abstraction？ → Server_State_Model
都不是？ → 先重新檢查本索引與 AGENTS.md
```
