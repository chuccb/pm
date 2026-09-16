# Mode-specific Selector Option 實際數值

> 研究日期：2026-09-16
>
> 本文件收錄目前能從 `PaperMan.exe.c` 直接證明「顯示文字／resource key ↔ selector value」的 mode-specific option。Wiki 用來做玩家可見規則的獨立交叉驗證；`Extracted/` 則確認這些 label/data 由 client resource system 提供。尚未能直接由 extracted binary 反查的 resource key，不虛構其日文內容。

## 1. 核心結論：Selector Index 與 Value 是兩個不同東西

一般 Room selector entry 以 40-byte stride 儲存，value 在 entry `+36`。因此：

```text
UI list index != selector value
```

而 mode-specific lobby builder 又以 `sub_4386A0(..., VALUE, ...)` 直接把 concrete value 放入 option。

完整資料模型：

```text
mode lobby
  ├─ display label
  ├─ selector index
  └─ selector value
          ↓
    generic selector entry
       value @ +36
          ↓
       Room state
          ↓
       packet / rule
```

這是目前 Server reconstruction 最重要的 Room-level invariant 之一。

---

## 2. `CyTeamMatchModeLobbyUI`：`3/5/7/10/12/15 Round`

C function：`CyGameModes::CyTeamMatchModeLobbyUI::sub_74F8B0()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `3 Round` | 3 |
| 1 | `5 Round` | 5 |
| 2 | `7 Round` | 7 |
| 3 | `10 Round` | 10 |
| 4 | `12 Round` | 12 |
| 5 | `15 Round` | 15 |

C 直接建立這六個 value。[C]

Wiki 的 `チーム戦術モード` 也列出 `3/5/7/10/12/15 Round`。[W]

**結論：[C+W] value 完全閉合。**

---

## 3. `CyIndividualSurvivalModeLobbyUI`：`20/30/40/50 Kill`

C function：`CyGameModes::CyIndividualSurvivalModeLobbyUI::sub_750220()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `20 Kill` | 20 |
| 1 | `30 Kill` | 30 |
| 2 | `40 Kill` | 40 |
| 3 | `50 Kill` | 50 |

C 同時存在 `ArgList > 0` 的 generic `%d Kill` path，因此 function 可以接收其它實際 value；預設列表就是上述四個。[C]

Wiki 的 `個人サバイバル` 完全一致。[W]

**結論：[C+W] value 完全閉合。**

---

## 4. `CyTeamSurvivalModeLobbyUI`：`50/100/200 Kill`

C function：`CyGameModes::CyTeamSurvivalModeLobbyUI::sub_751510()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `50 Kill` | 50 |
| 1 | `100 Kill` | 100 |
| 2 | `200 Kill` | 200 |

C 直接建立上述 values。[C]

Wiki 的現行 `チームサバイバル` 完全一致。[W]

**結論：對目前研究的 Client build，`C+W` value closed。**

### 4.1 歷史版本反證：同名 mode 的 rule schema 曾經不同

2010-02-07 的日本 `ver.Gp` Wiki 對 `チームサバイバル` 記錄的是：

```text
染料ポイント：1000/2000/3000cc
時間：10/20/30分
```

而目前日本 Wiki 已經是：

```text
Kill：50/100/200
時間：10/20/30分
```

[W]

因此：

```text
同一 public mode name
    != 永遠固定同一 rule schema
```

Server reconstruction 必須至少保留：

```text
ProtocolVersion / ClientBuild
Mode
RuleFamily
RuleValue
```

不能把後期 `50/100/200 Kill` 直接套到早期 ver.Gp client/server。

更重要的是，這個歷史差異也強化了目前對 `GR_WINCHANGE (171/172)` 的保守命名：即使名稱與某個勝利條件有關，也不能只靠 current Wiki 將 `u16` 固定命名成某一種全域 `kill_limit`。

---

## 5. `CyPulpnRollModeLobbyUI`：`15/30/45`

C function：`CyGameModes::CyPulpnRollModeLobbyUI::sub_753000()`。

| Index | Resource key for label | Value |
|---:|---:|---:|
| 0 | `0x24` | 15 |
| 1 | `0x2D` | 30 |
| 2 | `0x395` | 45 |

C 沒有寫死 label，而是由 `sub_408080(sub_408140(), key)` 取得；value 明確是 `15/30/45`。[C]

Wiki 的 `パルプ＆ロール` 列出 `15/30/45 分`。[W]

**結論：[C+W] value 與分鐘選項一致；[R] label 為 resource-backed，但目前未完成 key→原始日文的 binary-level 反查。**

---

## 6. `CyStealModeLobbyUI`：`1000/2000/3000 cc`

C function：`CyGameModes::CyStealModeLobbyUI::sub_751D20()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `1000 cc` | 1000 |
| 1 | `2000 cc` | 2000 |
| 2 | `3000 cc` | 3000 |

C 直接建立三個 concrete values。[C]

這提供了很強的反證：即使 packet 名稱叫 `GR_WINCHANGE`，也不能先驗把其 `u16` 命名成 global `kill_limit`；不同 mode 的 objective/value namespace 明顯存在。

**結論：[C] value 完全確定；public Wiki semantics 還應用 `スチールモード` 專頁繼續獨立閉合。**

---

## 7. `CyOccupyRenewalModeLobbyUI`：`300/500/700/1000`

C function：`CyGameModes::CyOccupyRenewalModeLobbyUI::sub_755420()`。

| Index | Resource key for label | Value |
|---:|---:|---:|
| 0 | `0x53B` | 300 |
| 1 | `0x53C` | 500 |
| 2 | `0x53D` | 700 |
| 3 | `0x53E` | 1000 |

C 直接建立上述 values。[C]

Wiki 的 `new占領モード` 列出 `300/500/700/1000 Point`。[W]

`Extracted/ClientDataList.xml` 確認 client resource system 至少包含 `ui`、`ui_temp`、`data.pat` 等 data sources；C 中的 display labels 確實走 resource provider。[R]

**結論：[C+W] value 完全閉合；[R] resource-backed 已確認，但 `0x53B..0x53E` 對應原始日文 label 尚 OPEN。**

---

## 8. `CyOccupyModeLobbyUI`：`1/2/3 Round`

C function：`CyGameModes::CyOccupyModeLobbyUI::sub_753BA0()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `1 Round` | 1 |
| 1 | `2 Round` | 2 |
| 2 | `3 Round` | 3 |

[C]

這與 `CyTeamMatchModeLobbyUI` 的 `3/5/7/10/12/15 Round` 是不同 option family；不可建立 global round enum 後假設兩者等價。

**結論：[C] concrete values closed；public semantics 仍需 Wiki mode page + runtime handler 確認。**

---

## 9. `CyPracticeModeLobbyUI` / `CyTutorialModeLobbyUI`：特殊 `999 Kill`

`CyPracticeModeLobbyUI::sub_752540()` 直接建立：

```text
display = `999 Kill`
value   = 999
```

[C]

同一系列的 `CyTutorialModeLobbyUI` 也存在 `999 Kill` option。

Wiki 對 `練習モード` 明確說明 `999 kill` 不會依一般 Kill target 正常結束。[W]

因此 Server 不應僅靠：

```text
if currentKill >= ruleValue:
    MatchEnd()
```

而應由 mode-specific rule policy 決定 `IsMatchOver()`。

---

## 10. `CyTeamSoccerModeLobbyUI`：目前已把「時間」與「Goal」兩組拆開

這一段最值得注意，因為初看會誤以為 C 與 Wiki 不一致。

### 10.1 `sub_754750()`：時間 `7/10/15/20`

C 中建立：

| Index | Resource key | Value |
|---:|---|---:|
| 0 | `0x4C6` | 7 |
| 1 | `0x21` | 10 |
| 2 | `0x24` | 15 |
| 3 | `0x28` | 20 |

這與 Wiki `サッカーモード` 的 `7/10/15/20 分` 完全一致。[C][W]

### 10.2 `sub_754B20()`：Goal `5/7/10/15`

同一個 lobby class 的另一個 builder 直接建立：

| Index | Resource key | Value |
|---:|---|---:|
| 0 | `0x4F3` | 5 |
| 1 | `0x4F4` | 7 |
| 2 | `0x4F5` | 10 |
| 3 | `0x4FA` | 15 |

而 soccer runtime / HUD 還直接使用：

```text
GOAL_POINT_5
GOAL_POINT_7
GOAL_POINT_10
GOAL_POINT_15
```

作為 Goal-related resource。[C]

Wiki 同樣列出 `5/7/10/15 Goal`。[W]

**結論：[C+W] soccer 的「時間」與「Goal」兩套 option 已成功拆開。**

---

## 11. Option values 對照總表

| Client class | Option family | Concrete values | Wiki cross-check | 狀態 |
|---|---|---|---|---|
| `CyTeamMatchModeLobbyUI` | Round | 3/5/7/10/12/15 | `チーム戦術モード` | **C+W closed** |
| `CyIndividualSurvivalModeLobbyUI` | Kill | 20/30/40/50 | `個人サバイバル` | **C+W closed** |
| `CyTeamSurvivalModeLobbyUI` | Kill | 50/100/200 | `チームサバイバル` | **C+W closed for current build** |
| `CyPulpnRollModeLobbyUI` | Time | 15/30/45 | `パルプ＆ロール` | **C+W closed** |
| `CyStealModeLobbyUI` | Objective/CC | 1000/2000/3000 | `スチールモード` | **C closed; Wiki semantics pending** |
| `CyOccupyModeLobbyUI` | Round | 1/2/3 | `占領` family | **C closed; public semantics pending** |
| `CyOccupyRenewalModeLobbyUI` | Point | 300/500/700/1000 | `new占領モード` | **C+W closed** |
| `CyPracticeModeLobbyUI` | Kill | 999 | `練習モード` | **C+W closed** |
| `CyTeamSoccerModeLobbyUI` | Time | 7/10/15/20 | `サッカーモード` | **C+W closed** |
| `CyTeamSoccerModeLobbyUI` | Goal | 5/7/10/15 | `サッカーモード` | **C+W closed** |

---

## 12. 與 `Room_Settings_Packets.md` 的交叉閉環

先前已由 generic Room path 封死：

```text
sub_4387B0()
    -> entry value @ +36
```

以及：

```text
169/170 -> GAMEROOM_SCROLL_RULE
173/174 -> GAMEROOM_SCROLL_TIME
171/172 -> GAMEROOM_SCROLL_OBJECT
```

現在 mode-specific builder 又封死了具體 option values：

```text
Individual Survival -> 20/30/40/50
Team Survival       -> 50/100/200
Team Match          -> 3/5/7/10/12/15
PulpnRoll            -> 15/30/45
Occupy Renewal      -> 300/500/700/1000
Soccer Time         -> 7/10/15/20
Soccer Goal         -> 5/7/10/15
Steal               -> 1000/2000/3000
Practice            -> 999
Occupy               -> 1/2/3
```

所以可以建立：

```text
mode-specific option builder
        ↓
concrete selector value
        ↓
selector entry +36
        ↓
Room current value
        ↓
corresponding GR_* setting packet
```

但這個鏈的最後一段對不同 family 的實際 packet mapping 仍需逐一閉合；目前已完成的是 selector/value layer，不是所有 mode rule 的 final server semantics。

## 13. 歷史版本注意事項

本文件的 concrete values 是針對目前研究的 Client build 所記錄；Wiki 歷史頁可以展示同名 mode 在更早版本使用不同 rule family。例如 2010-02-07 `ver.Gp` 的 `チームサバイバル` 使用 `1000/2000/3000cc` 染料條件，而現行 Wiki 為 `50/100/200 Kill`。

因此任何 Server implementation 都應避免：

```text
ModeName -> 永久固定 rule enum/value
```

較安全的是：

```text
ClientBuild / ProtocolRevision
    + ModeId
    + RuleFamily
    + RuleValue
    + TimeOption
    + CapabilitySet
```

這一層屬於版本化 domain model，而不是單純 UI enum。
