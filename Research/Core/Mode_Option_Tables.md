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

C 直接建立這六個 value。fileciteturn364file0L65-L125

Wiki 的 `チーム戦術モード` 也列出 `3/5/7/10/12/15 Round`。[W] citeturn606128search0

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

C 同時存在 `ArgList > 0` 的 generic `%d Kill` path，因此 function 可以接收其它實際 value；預設列表就是上述四個。fileciteturn359file4L290-L325

Wiki 的 `個人サバイバル` 完全一致。[W] citeturn606128search0

**結論：[C+W] value 完全閉合。**

---

## 4. `CyTeamSurvivalModeLobbyUI`：`50/100/200 Kill`

C function：`CyGameModes::CyTeamSurvivalModeLobbyUI::sub_751510()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `50 Kill` | 50 |
| 1 | `100 Kill` | 100 |
| 2 | `200 Kill` | 200 |

C 直接建立上述 values。fileciteturn364file1L169-L207

Wiki 的 `チームサバイバル` 完全一致。[W] citeturn606128search0

**結論：[C+W] value 完全閉合。**

---

## 5. `CyPulpnRollModeLobbyUI`：`15/30/45`

C function：`CyGameModes::CyPulpnRollModeLobbyUI::sub_753000()`。

| Index | Resource key for label | Value |
|---:|---:|---:|
| 0 | `0x24` | 15 |
| 1 | `0x2D` | 30 |
| 2 | `0x395` | 45 |

C 沒有寫死 label，而是由 `sub_408080(sub_408140(), key)` 取得；value 明確是 `15/30/45`。fileciteturn366file3L648-L700

Wiki 的 `パルプ＆ロール` 列出 `15/30/45 分`。[W] citeturn606128search0

**結論：[C+W] value 與分鐘選項一致；[R] label 為 resource-backed，但目前未完成 key→原始日文的 binary-level 反查。**

---

## 6. `CyStealModeLobbyUI`：`1000/2000/3000 cc`

C function：`CyGameModes::CyStealModeLobbyUI::sub_751D20()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `1000 cc` | 1000 |
| 1 | `2000 cc` | 2000 |
| 2 | `3000 cc` | 3000 |

C 直接建立三個 concrete values。fileciteturn359file6L424-L451

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

C 直接建立上述 values。fileciteturn366file1L305-L368

Wiki 的 `new占領モード` 列出 `300/500/700/1000 Point`。[W] citeturn606128search0

`Extracted/ClientDataList.xml` 確認 client resource system 至少包含 `ui`、`ui_temp`、`data.pat` 等 data sources；C 中的 display labels 確實走 resource provider。 [R] fileciteturn368file0L1-L2

**結論：[C+W] value 完全閉合；[R] resource-backed 已確認，但 `0x53B..0x53E` 對應原始日文 label 尚 OPEN。**

---

## 8. `CyOccupyModeLobbyUI`：`1/2/3 Round`

C function：`CyGameModes::CyOccupyModeLobbyUI::sub_753BA0()`。

| Index | Display | Value |
|---:|---|---:|
| 0 | `1 Round` | 1 |
| 1 | `2 Round` | 2 |
| 2 | `3 Round` | 3 |

[C] fileciteturn366file0L106-L177

這與 `CyTeamMatchModeLobbyUI` 的 `3/5/7/10/12/15 Round` 是不同 option family；不可建立 global round enum 後假設兩者等價。

**結論：[C] concrete values closed；public semantics 仍需 Wiki mode page + runtime handler 確認。**

---

## 9. `CyPracticeModeLobbyUI` / `CyTutorialModeLobbyUI`：特殊 `999 Kill`

`CyPracticeModeLobbyUI::sub_752540()` 直接建立：

```text
display = `999 Kill`
value   = 999
```

[C] fileciteturn364file2L222-L240

同一系列的 `CyTutorialModeLobbyUI` 也存在 `999 Kill` option。

Wiki 對 `練習モード` 明確說明 `999 kill` 不會依一般 Kill target 正常結束。[W] citeturn606128search0

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
|---:|---:|---:|
| 0 | `0x4C6` | 7 |
| 1 | `0x21` | 10 |
| 2 | `0x24` | 15 |
| 3 | `0x28` | 20 |

這與 Wiki `サッカーモード` 的 `7/10/15/20 分` 完全一致。[C] fileciteturn366file2L408-L486 [W] citeturn606128search0

### 10.2 `sub_754B20()`：Goal `5/7/10/15`

同一個 lobby class 的另一個 builder 直接建立：

| Index | Resource key | Value |
|---:|---:|---:|
| 0 | `0x4F3` | 5 |
| 1 | `0x4F4` | 7 |
| 2 | `0x4F5` | 10 |
| 3 | `0x4FA` | 15 |

[C] fileciteturn370file0L36-L113

而 soccer runtime / HUD 還直接使用：

```text
GOAL_POINT_5
GOAL_POINT_7
GOAL_POINT_10
GOAL_POINT_15
```

作為 Goal-related resource。[C] fileciteturn364file3L442-L477

Wiki 同樣列出 `5/7/10/15 Goal`。[W] citeturn606128search0

**結論：[C+W] soccer 的「時間」與「Goal」兩套 option 已成功拆開，先前看見 `7/10/15/20` 並不是 Wiki mismatch，而是不同 selector。**

這也再次證明：

```text
同一 mode lobby class
    ├─ selector A
    └─ selector B
```

不能用單一 option table 代表所有設定。

---

## 11. Option values 對照總表

| Client class | Option family | Concrete values | Wiki cross-check | 狀態 |
|---|---|---|---|---|
| `CyTeamMatchModeLobbyUI` | Round | 3/5/7/10/12/15 | `チーム戦術モード` | **C+W closed** |
| `CyIndividualSurvivalModeLobbyUI` | Kill | 20/30/40/50 | `個人サバイバル` | **C+W closed** |
| `CyTeamSurvivalModeLobbyUI` | Kill | 50/100/200 | `チームサバイバル` | **C+W closed** |
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

**但最後一段「哪個 option family 對應哪一個 `GR_*`」仍須逐 call path 封死，不能只靠 packet name。**

---

## 13. Extracted resource 三方證據的現況

`Extracted/ClientDataList.xml` 顯示 client 的資料來源包括：

```text
ui
ui_temp
0.xml
convars.pat
data.pat
```

[R] fileciteturn368file0L1-L2

而 C 的 mode lobby builders 對於部分 label 並非使用英文 literal，而是：

```c
sub_408080(sub_408140(), RESOURCE_KEY)
```

例如：

```text
PulpnRoll:       0x24 / 0x2D / 0x395
OccupyRenewal:   0x53B..0x53E
Soccer Time:     0x4C6 / 0x21 / 0x24 / 0x28
Soccer Goal:     0x4F3 / 0x4F4 / 0x4F5 / 0x4FA
```

所以 resource-backed nature 已確定；但目前 extracted binary 未能以可索引文本直接反推出全部 key→Japanese label，因此這些 label mapping 保留 OPEN。

**不要把「C 使用 resource key」誇大成「三方已完全查到 resource bytes」。**

---

## 14. Server reconstruction 規則

### 規則 A：保存 `OptionIndex` 與 `OptionValue`

例如：

```text
Team Match:
  index 0 -> value 3
  index 1 -> value 5

Individual Survival:
  index 0 -> value 20
  index 1 -> value 30
```

### 規則 B：不要建立 global `WinValue`

同樣的 `u8/u16 integer` 表面型態，可以代表：

```text
Kill
Round
Point
CC
Goal
Time
```

必須依 mode + selector family 解釋。

### 規則 C：Practice 是明確反例

`999 Kill` 存在，但 Wiki 明確指出 Practice 不依一般 Kill target 正常結束。

所以 rule engine 應至少提供：

```text
ShouldRespawn()
IsRoundOver()
IsMatchOver()
BuildResult()
```

而不是把所有 mode 合併成一個 `kill >= threshold`。

### 規則 D：未封死的欄位保留 raw

```text
已證明 -> 精確實作
C+W 強一致 -> 高可信語意
C-only -> raw + 明確命名 + OPEN
R 只有 resource key -> 不補猜測的日文
```

---

## 15. 下一個高價值方向

1. `171/172`：完整追 `sub_430720()` 與所有 caller，將 `GAMEROOM_SCROLL_OBJECT` 的各 mode option family 一一映射。
2. `169/170`：追 `sub_42FE50()` → `sub_426930()`，把 `Rule` selector value 與 mode-specific rule branch 封死。
3. `175/176`：沿 bit1 的 `sub_728D90()` → `GAMEROOM_GIMMICK`，找出 exact public label。
4. `177/178`：完整 sender/receiver/state path。
5. `GR_STARTTIME_REQ/ACK (137/138)`：找出真正 handler layer，避免因 registration name 誤判。
6. Room 完整閉環後轉進 `CGameRule` mode runtime，優先 `個人サバイバル`、`チームサバイバル`、`チーム戦術モード` 的 kill/round/timeout/death/respawn/end-result。
