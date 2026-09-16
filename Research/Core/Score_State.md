# Kill / Death / Score State 逆向

> 研究日期：2026-09-16
>
> 本文件只記錄目前能由 `PaperMan.exe.c` 直接閉合、並可與 Wiki 的公開模式規則互相驗證的 score state。尚未證實的 network write path 不提前命名或硬編碼。

## 1. 每個玩家都有獨立的 Kill / Death state

client 以 16 個 player slot 的固定 stride 儲存核心成績：

```text
slot_stride = 60195 DWORD-equivalent units

slot[n].dword_F6DCF8 = Kill
slot[n].dword_F6DCFC = Death
```

最直接的證據來自 player-state synchronization parser：

```c
n16_6 = n16_3;
dword_F6DCF4[60195 * n0x10] = n16_3;

dword_F6DCF8[60195 * n0x10] = v433;
dword_F6DCFC[60195 * n0x10] = v383;
```

同一段還同步 `byte_F6DD00`、`byte_F6DD11`、`byte_F6D9EC` 等其他 player state。`PaperMan.exe.c` 約 L167562-L167574。

這證明 Kill / Death 是玩家 state synchronization 的一部分，而不是只有結算畫面臨時計算的值。

## 2. 初始化會清空 Kill / Death

玩家 slot 被判定為空/無效時，client 直接：

```c
dword_F6DCF8[60195 * i] = 0;
dword_F6DCFC[60195 * i] = 0;
```

Evidence：`PaperMan.exe.c` 約 L4782-L4792。

## 3. Result UI 對兩個欄位的語意已直接命名

Solo result：

```text
SOLO_RESULT_L_HIGHSCORE_KILL
SOLO_RESULT_L_TEXT_KILL
SOLO_RESULT_L_HIGHSCORE_DEATH
SOLO_RESULT_L_TEXT_DEATH
SOLO_GAMEEND_TEXT_HIGHSCORE_KILL
SOLO_GAMEEND_TEXT_HIGHSCORE_DEATH
```

Team result / game end：

```text
TEAM_RESULT_A_HIGHSCORE_KILL
TEAM_RESULT_A_HIGHSCORE_DEATH
TEAM_RESULT_B_HIGHSCORE_KILL
TEAM_RESULT_B_HIGHSCORE_DEATH
TEAM_GAMEEND_HIGHSCORE_KILL
TEAM_GAMEEND_HIGHSCORE_DEATH
```

這些 UI 位置直接讀：

```c
dword_F6DCF8[60195 * n16]
dword_F6DCFC[60195 * n16]
```

因此：

```text
dword_F6DCF8 = Kill count       [C: CLOSED]
dword_F6DCFC = Death count      [C: CLOSED]
```

Evidence：`PaperMan.exe.c` 約 L266539-L266549、L268522-L268548、L272752-L273079、L274293-L274658。

## 4. 一般 Result ranking 的 comparator 已閉合

`sub_6482C0(a1, a2)`：

```c
if (dword_F6DCF8[60195 * a1] != dword_F6DCF8[60195 * a2])
    return dword_F6DCF8[60195 * a1] >= dword_F6DCF8[60195 * a2];

if (dword_F6DCFC[60195 * a1] == dword_F6DCFC[60195 * a2])
    return dword_F33184[60195 * a1] < dword_F33184[60195 * a2];

return dword_F6DCFC[60195 * a1] < dword_F6DCFC[60195 * a2];
```

所以 **C 實際 comparator** 的排序鍵是：

```text
1. Kill 降序
2. Kill 相同 → Death 升序
3. Kill / Death 都相同 → dword_F33184 升序
```

Evidence：`PaperMan.exe.c` 約 L265865-L265879。

### `dword_F33184` 暫時不能命名

針對 `dword_F33184` 做進一步全檔搜尋後，目前 C export 能可靠定位到的使用主要是 comparator / high-score selection 中的讀取，沒有找到足夠可靠的對應寫入點。

因此目前禁止把它寫成：

```text
❌ participant count
❌ special-shot count
❌ score
```

也不能因 Wiki 的 tournament 特別規則寫著「キル数＞デス数＞参加人数＞特殊ショット」就直接認定 `dword_F33184` 是 `参加人数`；兩者目前缺乏一條直接 data-flow 證據。

這是一個刻意保留的 OPEN 欄位。

## 5. High-score selector 也重複相同比較鏈

`sub_759030()` 在 16 個 slot 中尋找最佳成績，實際比較流程同樣是：

```text
higher Kill
    ↓ tie
lower Death
    ↓ tie
lower dword_F33184
```

Evidence：`PaperMan.exe.c` 約 L759030 起始的 `sub_759030`。

這表示 Kill / Death comparator 不只是單一 Result UI 的畫面排序；同一比較鏈也用於 mode/runtime 尋找 high-score slot。

## 6. 個人サバイバル：Wiki ↔ C 的 score 模型閉環

Wiki `MAP・ルール詳細` 對 個人サバイバル 定義為：

```text
制限時間内に一番多くの敵を倒した人が勝利するモード
```

並列出：

```text
20 / 30 / 40 / 50 Kill
10 / 15 / 20 分
```

C 則直接以 `dword_F6DCF8` 顯示 `KILL`，並透過 high-score comparator 尋找最高 Kill；`dword_F6DCFC` 明確對應 `DEATH`。

因此目前閉環：

```text
Wiki
  └─ 個人サバイバル核心勝負量 = Kill

IDA C
  ├─ F6DCF8 = KILL
  ├─ F6DCFC = DEATH
  └─ high-score = highest Kill, then lowest Death, then unresolved third key
```

Wiki evidence：PaperMan Wiki `MAP・ルール詳細` 的 個人サバイバル 段落。

## 7. Team Survival：player score 與 team aggregation 必須分層

Wiki 對 チームサバイバル 描述為隊伍累積擊殺數，目標可選：

```text
50 / 100 / 200 Kill
10 / 20 / 30 分
```

C 的 Team Result / Game End UI 仍然逐玩家讀：

```text
F6DCF8 = Kill
F6DCFC = Death
```

所以較安全的 server model 是：

```text
PlayerScore
    ├─ Kill
    └─ Death

TeamRule
    └─ 依 mode 規則聚合 PlayerScore
```

不要直接把 `F6DCF8` 改名為 `TeamKills`；它在 client state 中是 per-player storage。

## 8. `sub_759030()` 的另一個證據：它真的在選「最高成績玩家」

`CyGameModes::CyIndividualSurvivalMode::sub_76FBE0()` 呼叫：

```c
if (sub_759030(this, &n0x10) != 0)
{
    ...
    (*(**(this + 12) + 4))(
        *(this + 12),
        *(this + 8),
        v8,
        dword_F6DCF4[60195 * n0x10],
        v9,
        1);
}
```

這條鏈把 `sub_759030()` 選出的 slot 帶入 mode UI / player-related display，與其 high-score 用途吻合。

Evidence：`PaperMan.exe.c` 約 L76FBE0 起始區域；`sub_759030()` 約 L759030。

## 9. Network boundary：score state 有 synchronization，但 mutation source 尚未閉合

目前能看到一個大型 player-state synchronization parser 對：

```text
F6DCF4
F6DCF8
F6DCFC
F6DD00
F6DD11
...
```

進行整體寫入。

同時，針對：

```text
++dword_F6DCF8[slot]
++dword_F6DCFC[slot]
```

做過直接 increment 搜尋，沒有找到可靠結果。

因此目前不能寫成：

```text
Y_TCP_INF_REQ (165)
    → Kill++
    → Death++
```

目前狀態：

```text
Kill / Death storage                 = CLOSED
Kill / Death 是 synchronized state  = CLOSED / HIGH
165 是 gameplay event/info path     = HIGH
165 直接更新 Kill / Death           = OPEN
```

## 10. 與 `Y_TCP_INF_REQ (165)` 的關係

165 至少由以下 send path 共用：

```text
GameNetwork::OnSendPacketDamage
GameNetwork::OnSendPacketMultiDamage
GameNetwork::OnSendPacketMineBombDamage
GameNetwork::OnSendPacketBotSuicide
```

而多種 payload 都含 actor/target slot-like 欄位，部分 variant 還帶：

```c
dword_F6DD1C[target]
```

因此 165 明顯位於 gameplay network / event propagation 一側，但「event → score mutation」仍需 receive-side proof。

## 11. Extracted RES：資源樹本身已證明 client data 是分層封裝的

`Extracted/0.xml` 明確把 client data 分成：

```xml
<PackFile key="character" filename="Data\\character.dat" folderpath="character\\" />
<PackFile key="item" filename="Data\\item.dat" folderpath="item\\" />
<PackFile key="map" filename="Data\\map.dat" folderpath="map\\" />
<PackFile key="pmClient" filename="Data\\pmClient.dat" folderpath="" />
```

同時 `ClientDataList.xml` 又明確列出：

```xml
<DataList key="BulletHole" />
<DataList key="effect" />
<DataList key="ui" />
<DataList key="ui_temp" />
```

這支持本研究採用的三層分工：

```text
Wiki       = public gameplay semantics
Extracted  = concrete client resource / data identity
IDA C/LST  = executable data-flow / protocol evidence
```

它不代表某個特定 score field 已經由 RES 單獨證明；不要過度外推。

Evidence：`Extracted/0.xml`、`Extracted/ClientDataList.xml`。

## 12. 三方證據矩陣

| 主題 | Wiki | Extracted / RES | IDA C | 狀態 |
|---|---|---|---|---|
| 個人サバイバル以 Kill 決勝 | 有 | UI/resource 架構存在 | `F6DCF8` + high-score | **CLOSED** |
| 個人 K/D | 公開規則與結果行為 | `ui` / result 資源體系 | `F6DCF8/F6DCFC` | **CLOSED** |
| Team Survival Kill target | 有 50/100/200 | `ui` resource tree | per-player Kill state | **CLOSED（aggregation 未完）** |
| per-player Kill / Death storage | 無 internal field | client data tree 分層 | 16-slot state sync | **CLOSED** |
| `dword_F33184` 公開語意 | Tournament Wiki 有不同的 tie-break 規則 | 未找到對應 concrete resource identity | C 僅可靠觀察到 comparator read | **OPEN** |
| 165 → Kill/Death mutation | 無直接 packet 說明 | 未閉合 | 未找到可靠 increment path | **OPEN** |

## 13. Server reconstruction 建議

先定義：

```text
PlayerScore
├─ Kill: int
├─ Death: int
└─ UnknownTieBreak: int
```

之後由 mode 層處理：

```text
PlayerScore
    ↓
ModeRule aggregation
    ↓
RoundResult / TeamResult / GameResult
```

而 `Y_TCP_INF_REQ (165)` 先以：

```text
Opcode = 165
Subtype = payload[1]
VariantPayload = subtype-specific
```

處理，不要先把它硬編成 `DamagePacket` 或 `KillPacket`。

## 14. 下一個閉合目標

```text
165 outgoing variants
        ↓
GameNetwork receive dispatcher
        ↓
165/166 concrete handler
        ↓
player-state mutation
        ↓
F6DCF8 / F6DCFC
        ↓
mode aggregation
        ↓
round / timeout / game end
```

只有把這條鏈做出可靠 evidence graph，才適合把目前的 `PlayerScore` 變成真正可實作的 Server protocol contract。
