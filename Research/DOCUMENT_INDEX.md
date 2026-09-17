# PaperMan 研究文件完整索引

> 目的：提供所有研究 Markdown 的單一導覽入口，避免同一主題分散、重複與互相漂移。
>
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。

本索引涵蓋目前 `Research/` 下的研究 Markdown。凡是被合併的文件，其證據已移入主文件，不再於索引保留失效連結。

## 使用方式

先找到主題主文件，再閱讀其證據、協定、欄位與狀態章節。若發現矛盾，回到 `[C]`、`[RES]`、`[WIKI]` 的原始證據，而不是用另一份摘要取代主文件。

### 證據標記

| 標記 | 意義 |
|---|---|
| `[C]` | `PaperMan.exe.c` 的直接反編譯證據 |
| `[RES]` | `Extracted/` 遊戲資源或資料檔證據 |
| `[WIKI]` | 日本 PaperMan Wiki 的歷史玩家可見資料 |
| `[X]` | 兩種以上獨立來源交叉吻合 |
| `[OPEN]` | 尚未充分確認 |

---

# 一、研究總入口

| 文件 | 定位 |
|---|---|
| [Research/README.md](README.md) | 整體研究目標、版本基準、證據方法與研究方向 |
| [Core/README.md](Core/README.md) | 核心遊戲機制與文件導航 |
| [KickVote/README.md](KickVote/README.md) | Kick Vote 專題主入口 |

# 二、基礎傳輸、封包與 Dispatcher

| 文件 | 定位 |
|---|---|
| [Core/Foundation_TCP_Handshake_Login_Protocol.md](Core/Foundation_TCP_Handshake_Login_Protocol.md) | TCP、握手、登入與基礎協定骨架 |
| [Core/Network_Dispatch.md](Core/Network_Dispatch.md) | 封包註冊、接收 Dispatcher、handler 路由 |
| [Core/Y_TCP_INF_Transport.md](Core/Y_TCP_INF_Transport.md) | `Y_TCP_INF` 傳輸層行為與資料流 |
| [Core/ClientData_Shared_Decoder_Field_Evidence.md](Core/ClientData_Shared_Decoder_Field_Evidence.md) | 共用 decoder 與欄位讀取證據 |

# 三、登入、玩家資料與房間前置狀態

| 文件 | 定位 |
|---|---|
| [Core/Login_681_Server_Record_Field_Schema.md](Core/Login_681_Server_Record_Field_Schema.md) | `681` 與 Server Record 欄位配置 |
| [Core/Login_Adjacent_680_696_Field_Schema.md](Core/Login_Adjacent_680_696_Field_Schema.md) | `680–696` 鄰近登入封包與欄位 schema |
| [Core/MyInfo_198_ClientData_Field_Schema.md](Core/MyInfo_198_ClientData_Field_Schema.md) | `198` ClientData 欄位 schema |
| [Core/MyInfo_198_Composite_Codec_Evidence.md](Core/MyInfo_198_Composite_Codec_Evidence.md) | `198` composite codec 與資料流證據 |
| [Core/Player_Slot_Team.md](Core/Player_Slot_Team.md) | Player slot、Team、玩家位置與隊伍狀態 |
| [Core/Character_Inventory_Equipment.md](Core/Character_Inventory_Equipment.md) | Character、Inventory、Equipment 主文件與深入證據 |
| [Core/Currency_State_Field_Evidence.md](Core/Currency_State_Field_Evidence.md) | 貨幣與玩家狀態欄位證據 |

# 四、Channel、Lobby、Room 與 GameRule

| 文件 | 定位 |
|---|---|
| [Core/Channel_Lobby_193_221_Field_Evidence.md](Core/Channel_Lobby_193_221_Field_Evidence.md) | `193–221` Channel/Lobby 欄位直接證據 |
| [Core/Channel_Lobby_Lifecycle.md](Core/Channel_Lobby_Lifecycle.md) | Channel/Lobby 生命週期與狀態轉移 |
| [Core/Room_Channel_GameRule_101_192_Field_Evidence.md](Core/Room_Channel_GameRule_101_192_Field_Evidence.md) | `101–192` Room/Channel/GameRule 欄位證據 |
| [Core/Room_Settings_Packets.md](Core/Room_Settings_Packets.md) | 房間設定與相關封包 |
| [Core/Map_And_Room.md](Core/Map_And_Room.md) | Map、Room 以及兩者的關係 |
| [Core/GameRule_Lifecycle.md](Core/GameRule_Lifecycle.md) | GameRule 生命週期與狀態機 |
| [Core/Server_State_Model.md](Core/Server_State_Model.md) | Server-side 狀態模型與同步關係 |

# 五、遊戲模式與模式設定

| 文件 | 定位 |
|---|---|
| [Core/Mode_Rules.md](Core/Mode_Rules.md) | 各遊戲模式的規則與狀態 |
| [Core/Mode_Option_Tables.md](Core/Mode_Option_Tables.md) | 模式選項與欄位對照表 |
| [Core/Gameplay_166_DeepEvidence.md](Core/Gameplay_166_DeepEvidence.md) | `166` Gameplay、死亡、K/D、結果與相關深入證據 |
| [Core/Gameplay_Network_Events.md](Core/Gameplay_Network_Events.md) | Gameplay network event 與事件鏈 |

# 六、戰鬥、傷害、移動與武器

| 文件 | 定位 |
|---|---|
| [Core/Combat_Hit_Detection.md](Core/Combat_Hit_Detection.md) | 命中判定與戰鬥事件 |
| [Core/Damage_Calculation.md](Core/Damage_Calculation.md) | 傷害計算與相關狀態 |
| [Core/Y_TCP_INF_Damage.md](Core/Y_TCP_INF_Damage.md) | `Y_TCP_INF` 傷害鏈與資料流 |
| [Core/UDP_Move_Inf_DeepEvidence.md](Core/UDP_Move_Inf_DeepEvidence.md) | UDP 8/24、Queue、27-byte actor record 與欄位證據 |
| [Core/DropWeapon_Protocol.md](Core/DropWeapon_Protocol.md) | 丟棄武器封包與流程 |

# 七、Packet 欄位細節與結果協定

| 文件 | 定位 |
|---|---|
| [Core/Packet_166_Field_Map.md](Core/Packet_166_Field_Map.md) | `166` 欄位總表與位置對照 |
| [Core/Packet_166_Field_Detail_3_15.md](Core/Packet_166_Field_Detail_3_15.md) | `166` 3–15 欄位深入細節 |
| [Core/TCP_269_Subtype7_Field_Detail.md](Core/TCP_269_Subtype7_Field_Detail.md) | `269 subtype 7` 完整欄位、玩家同步與 Result/K/D 狀態 |
| [Core/Quest_Result_Packets_223_245.md](Core/Quest_Result_Packets_223_245.md) | `223–245` Quest/Result 封包 |
| [Core/Result_Stat_Protocol_223_245_381_389.md](Core/Result_Stat_Protocol_223_245_381_389.md) | `223/245/381/389` Result/Stat 協定 |
| [Core/Score_State.md](Core/Score_State.md) | Score 與計分狀態 |

# 八、Quest、Event 與資源模型

| 文件 | 定位 |
|---|---|
| [Core/Quest_Event_ID_Mapping.md](Core/Quest_Event_ID_Mapping.md) | Quest/Event 與 ID mapping |
| [Core/Resource_Pack_Model.md](Core/Resource_Pack_Model.md) | 遊戲資源封裝與資料模型 |

# 九、Kick Vote

| 文件 | 定位 |
|---|---|
| [KickVote/README.md](KickVote/README.md) | Kick Vote 主入口與目前結論摘要 |
| [KickVote/Evidence_And_Eligibility.md](KickVote/Evidence_And_Eligibility.md) | Wiki、C、資源與候選資格證據 |
| [KickVote/Protocol.md](KickVote/Protocol.md) | `718–723` 協定與資料流 |
| [KickVote/UI_State.md](KickVote/UI_State.md) | 投票 UI、狀態機、計時器與候選清單 |
| [KickVote/Master_Room.md](KickVote/Master_Room.md) | `396/397` Master/Room 層協定 |

---

# 十、文件角色與整合規則

| 問題 | 首選位置 |
|---|---|
| 完整生命週期與狀態轉移 | `*Lifecycle.md` |
| 封包建立、傳送、接收與整體格式 | `*Protocol.md` |
| 欄位型別、寬度、位置與資料結構 | `*Schema.md` |
| 欄位直接證據 | `*Field_Evidence.md`／主文件相關章節 |
| 跨函式、跨資源、跨來源證據鏈 | `*DeepEvidence.md` 或主題深入章節 |
| 單一狹窄封包的深入拆解 | `*Detail.md` |
| 目前保存的狀態 | `*State.md` |
| 目錄入口 | `README.md` |

同一主題若已存在主文件，後續應直接擴充主文件。只有內容在證據來源、協定層級或生命週期上真正不同時才拆分。

## 十一、已完成的文件整合

以下重複文件已將內容併入主文件，原文件不再維護：

```text
Character_Inventory_Equipment_DeepEvidence.md
    → Character_Inventory_Equipment.md

Gameplay_166_KD_Field_Evidence.md
    → Gameplay_166_DeepEvidence.md

UDP_Move_Inf_Field_Semantics.md
    → UDP_Move_Inf_DeepEvidence.md

TCP_269_Subtype7_Result_State.md
    → TCP_269_Subtype7_Field_Detail.md
```

整合原則是保留證據、反證與 `[OPEN]` 邊界，而不是用較短的摘要覆蓋較完整的研究。

## 十二、禁止的文件演化方式

- 同一封包在多份文件各自維護不同欄位表。
- 建立 `New`、`Final`、`Final2`、`Latest`、`Copy` 等平行副本。
- 把 `[OPEN]` 猜測改寫為 confirmed 卻沒有新增證據。
- 把不同年份或地區版本無標記地混入 2016 Japan final Client。
- 只更新細節文件而不更新主文件、入口與索引。
- 使用簡體中文撰寫新的 Markdown 說明。

文件的目的應該是增加可追溯知識，而不是增加副本。
