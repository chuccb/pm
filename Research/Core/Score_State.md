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

這與每一場新的 player-state synchronization 需要重新建立 score state 的模型一致。

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

## 4. 排名規則：Kill → Death → 第三欄

`sub_6482C0(a1, a2)`：

```c
if (dword_F6DCF8[60195 * a1] != dword_F6DCF8[60195 * a2])
    return dword_F6DCF8[60195 * a1] >= dword_F6DCF8[60195 * a2];

if (dword_F6DCFC[60195 * a1] == dword_F6DCFC[60195 * a2])
    return dword_F33184[60195 * a1] < dword_F33184[60195 * a2];

return dword_F6DCFC[60195 * a1] < dword_F6DCFC[60195 * a2];
```

因此排序鍵精確是：

```text
1. Kill 降序
2. Kill 相同時 Death 升序
3. Kill / Death 都相同時 dword_F33184 升序
```

Evidence：`PaperMan.exe.c` 約 L265865-L265879。

## 5. High-score selector 也重複相同排序

`sub_759030()` 在 16 個 slot 中尋找最佳成績，核心比較順序同樣是：

```text
higher Kill
    ↓ tie
lower Death
    ↓ tie
lower dword_F33184
```

並將選出的 slot 寫入自己的 state。

這不是單一 Result UI 的偶然排序，而是 mode/runtime 共用的比較邏輯。

Evidence：`PaperMan.exe.c` 約 L759030 起始的 `sub_759030`，其中 L188-L233 可見完整比較鏈。

## 6. 個人サバイバル：Wiki 與 C 的 score 模型吻合

Wiki `MAP・ルール詳細` 對 個人サバイバル 的描述是：

```text
制限時間内に一番多くの敵を倒した人が勝利するモード
```

並列出：

```text
20 / 30 / 40 / 50 Kill
10 / 15 / 20 分
```

C 則直接把 `dword_F6DCF8` 顯示為 `KILL`，並以它選擇 high score；`dword_F6DCFC` 顯示為 `DEATH`。

因此三方目前形成的閉環是：

```text
Wiki
  └─ 個人サバイバル的核心勝負量 = Kill

C / UI
  ├─ F6DCF8 = KILL
  ├─ F6DCFC = DEATH
  └─ high-score = highest Kill, then lowest Death

Result
  └─ 可直接由兩個 player state 建立排名
```

Wiki evidence：PaperMan Wiki `MAP・ルール詳細`（個人サバイバル段落）。

## 7. Team Survival 的公開規則也能對上同一 state

Wiki 對 チームサバイバル 描述為以隊伍累積擊殺數決定勝負，目標可選：

```text
50 / 100 / 200 Kill
10 / 20 / 30 分
```

C 的 team result UI 仍直接以每個 player 的：

```text
F6DCF8 = Kill
F6DCFC = Death
```

組成 TEAM_RESULT_A / B 與 TEAM_GAMEEND 的個人成績顯示。

因此目前最穩健的模型是：

```text
Player score state
    ├─ Kill
    └─ Death

Mode rule
    └─ 再決定如何把 player score 聚合成 team / round / game outcome
```

不要把 `F6DCF8` 直接重命名成 `TeamKills`；它在 C 中是 per-player state，Team Survival 的 team total 應視為更高層聚合。

## 8. 一個非常重要的 network 邊界

目前已找到大型 server-state synchronization parser 對：

```text
F6DCF4
F6DCF8
F6DCFC
F6DD00
F6DD11
...
```

進行整體寫入。

但截至本輪，尚未在 `PaperMan.exe.c` 找到可靠的：

```text
++dword_F6DCF8[slot]
++dword_F6DCFC[slot]
```

write path。

因此目前不能寫成：

```text
Y_TCP_INF_REQ (165)
    → Kill++
    → Death++
```

目前應保持：

```text
Kill / Death state                    = CLOSED
Kill / Death 是 synchronized state    = CLOSED / HIGH
165 是 gameplay information path      = HIGH
165 直接更新 Kill / Death             = OPEN
```

## 9. 與 165 Damage family 的關係

`Y_TCP_INF_REQ (165)` 被以下 send path 共用：

```text
GameNetwork::OnSendPacketDamage
GameNetwork::OnSendPacketMultiDamage
GameNetwork::OnSendPacketMineBombDamage
GameNetwork::OnSendPacketBotSuicide
```

而 packet payload 常帶有 actor/target slot-like 欄位，部分 variant 還會附帶：

```c
dword_F6DD1C[target]
```

因此 165 明顯位於 gameplay event / state propagation 路徑，但目前沒有足夠證據把它直接等同於 score mutation。

這個邊界刻意保留，供後續找到 165/166 receive dispatcher 後再閉合。

## 10. 目前適合 Server 的資料模型

建議先抽象成：

```text
PlayerScore
├─ Kill: int
├─ Death: int
└─ TieBreak: int   // 對應 dword_F33184，public semantic 尚待確認
```

而：

```text
TeamScore
RoundScore
GameResult
```

不要直接與 `PlayerScore.Kill` 混成同一欄位；它們應由 mode-specific rule 聚合。

### Server reconstruction 禁止的過早假設

```text
❌ client 本地收到一次 Damage 就自己 Kill++
❌ client 自己判定 Death++
❌ 165 == Kill event
❌ F6DCF8 == TeamKills
```

只有找到 receive handler、state mutation 或其他更直接證據後才提升 confidence。

## 11. 三方證據矩陣

| 主題 | Wiki | Extracted / RES | IDA C | 狀態 |
|---|---|---|---|---|
| 個人サバイバル以 Kill 決勝 | 有 | UI/resource identity 間接支持 | `F6DCF8` + high-score | CLOSED |
| 個人 K/D | 公開規則涉及勝負與死亡/重生 | `KILL` / `DEATH` resource/UI key | `F6DCF8/F6DCFC` | CLOSED |
| Team Survival Kill target | 有 50/100/200 | Team result UI keys | per-player Kill state | CLOSED（聚合層仍續追） |
| Kill / Death per-player storage | 無直接 internal field | result UI/resource | 16-slot synchronized state | CLOSED |
| 165 → Kill/Death mutation | 無直接 packet 說明 | 未閉合 | 未找到 increment path | OPEN |

## 12. 下一個真正值得閉合的問題

```text
server/player-state sync parser
        ↓
F6DCF8/F6DCFC 的來源
        ↓
是哪一種 incoming packet 寫入？
        ↓
是否由 165、159/160、其他 gameplay opcode 更新？
        ↓
mode-specific aggregation
        ↓
round/game end
```

這一條一旦閉合，才可以把目前的 scoreboard state 提升成可實作的 Server `ScoreManager` 協定。
