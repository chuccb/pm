# Room 設定與規則變更封包研究

> 研究日期：2026-09-16
>
> 本文件專門收斂「Room UI → 設定值 → Request → ACK → Client 狀態」這一層。重點不是只記 opcode，而是把每個欄位一路追到真正讀寫的位置。

## 1. 三方證據規則

本文件使用三種證據：

- **[C] IDA Hex-Rays `PaperMan.exe.c`**：封包建立、解析、函式資料流、物件欄位。
- **[W] PaperMan Wiki**：玩家實際可見的 Room 設定與模式規則。
- **[R] Extracted 資源**：客戶端實際使用的地圖／UI／資料資源。

命名原則：沒有被資料流直接封死的欄位，不強行命名成伺服器 enum；優先使用 `*_value`、`selector_value`、`control_flag` 這類可逆命名。

---

## 2. Room UI 實際存在的設定控制

IDA 中同一套 Room UI 明確會尋找以下 resource key：

```text
GAMEROOM_START
GAMEROOM_READY
GAMEROOM_SCROLL_MAP
GAMEROOM_SCROLL_RULE
GAMEROOM_SCROLL_OBJECT
GAMEROOM_SCROLL_TIME
GAMEROOM_ITEM
GAMEROOM_GIMMICK
GAMEROOM_TEAMBALANCE
GAMEROOM_DAMAGEROOM
GAMEROOM_USERSLOTS
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_CHATMODE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_MASTERROOM
GAMEROOM_LOCALROOM
```

這不是單純從變數名稱猜測：Room UI 的事件 dispatch 會逐一比較這些 key，並依 key 進入對應操作。fileciteturn330file1L141-L253

另一段初始化／刷新流程則直接取得 `GAMEROOM_SCROLL_MAP`、`GAMEROOM_SCROLL_RULE`、`GAMEROOM_SCROLL_TIME`、`GAMEROOM_SCROLL_OBJECT`、`GAMEROOM_ITEM`、`GAMEROOM_TEAMBALANCE` 等物件，並呼叫其 UI virtual method 更新狀態。fileciteturn329file1L245-L318

### Wiki 對這一層的獨立確認

Wiki 的 Room information 明確列出玩家可以看到的：

```text
モード
マップ
勝利条件
制限時間
アイテム/ノーアイテム戦
チームバランス
チームシャッフル
ローカルルール
ナイフ戦
クレイジープレイ
ノースキルモード
```

且模式列表與可選規則會隨版本／模式改變。[W] citeturn606128search0

因此目前可以把 UI 層理解成：

```text
Room
├─ map selector
├─ rule / victory-condition selector
├─ time selector
├─ object / gimmick-related selector
├─ item / no-item
├─ team balance
├─ team shuffle
├─ no-skill variants
└─ other room flags
```

**[W+C] 這個層級的存在已完全對上。**

---

## 3. `GR_MAPCHANGE_REQ/ACK`：Map selector value

### 3.1 Request 121

`sub_56E480` 最終呼叫：

```c
Packet::possible_ctor_or_dtor_0(v2, 121);
sub_592920(v2, a1);
sub_555090(&dword_1321D00, v2);
```

所以：

```text
121 GR_MAPCHANGE_REQ
+0x00 u8 map_value
payload = 1 byte
```

[C]

### 3.2 ACK 122

`sub_56E530` 讀出一個 byte 後直接呼叫：

```c
sub_42FC50(dword_EA10D0, v2);
```

`sub_42FC50()` 取得：

```text
GAMEROOM_SCROLL_MAP
```

然後以 `sub_4387B0()` 逐項比較 `map_value`；命中後選中該項目，再更新 Room state。[C] 此資料流已在 `Map_And_Room.md` 詳述。

### 3.3 列表項目的真正 value

`sub_4387B0()`：

```c
return *(*(this + 33) + 40 * a2 + 36);
```

因此 Room selector list 是以 **40-byte entry** 組成，而其可傳輸／選取 value 在 entry `+36`。fileciteturn336file0L100-L108

### 3.4 Room object 對 Map value 的儲存欄位

`sub_540260()`：

```c
return *(this + 130);
```

`sub_540280()`：

```c
*(this + 130) = a2;
```

所以目前可以安全寫成：

```text
Room/Player object +130 = current selector value
```

而不是直接叫 `map_id`；`map_id` 是否等同於 resource map identifier，仍需再閉合。[C] fileciteturn336file3L661-L665 fileciteturn336file4L892-L896

### 3.5 本地 resource cache

Client 會把目前的 `sub_540260()` 寫到：

```text
cfg\Map.dat
```

且是以 1 byte 寫入。fileciteturn336file3L548-L554

[R+C] `Extracted/map/maplist.dat` 本身是實際二進位地圖清單，內容可看到 UTF-16 map resource path，例如：

```text
maps\TU_01_tutorial.pmm
```

因此 `GAMEROOM_SCROLL_MAP` 並不是憑空建立的 UI list，而是與客戶端實際 map resource inventory 相連。[R]

**目前最穩固的模型：**

```text
maplist.dat / map resources
        ↓
GAMEROOM_SCROLL_MAP
        ↓
40-byte entries, value @ +36
        ↓
current Room value @ object +130
        ↓
121 / 122 carries that value as u8
        ↓
Map selection synchronized to clients
```

---

## 4. `GR_TIMECHANGE_REQ/ACK`：Time selector value

### 4.1 Opcode 已被名稱直接封死

Packet registration 明確為：

```text
173 GR_TIMECHANGE_REQ
174 GR_TIMECHANGE_ACK
```

C registration：fileciteturn344file0L24-L47

### 4.2 Request 173

`sub_56F600(char a1)`：

```c
Packet::possible_ctor_or_dtor_0(v2, 173);
sub_592920(v2, a1);
sub_555090(&dword_1321D00, v2);
```

所以：

```text
173 GR_TIMECHANGE_REQ
+0x00 u8 time_value
payload = 1 byte
```

### 4.3 ACK 174

`sub_56F6B0()`：

```c
sub_592940(a1, &v2);
return sub_430920(dword_EA10D0, v2);
```

[C] 174 的 payload 也是一個 u8。

### 4.4 `sub_430920()` 封死了它是哪個 selector

核心流程：

```c
*(this + 112) = 0;
i_2 = sub_407E80(this_15, *(this + 213));
*(i_2 + 136) = a2;
...
GAMEROOM_SCROLL_TIME
...
sub_6B9B10(v15, 0);
for ( i = 0; ; ++i )
{
    if ( sub_4387B0(v15, i) == a2 )
        return sub_6B9B10(v15, i);
}
```

因此：

```text
173/174 u8
    = GAMEROOM_SCROLL_TIME 的 selector value
    = stored at object +136
```

而不是「剩餘時間」或「時間秒數」本身。[C]

這是很重要的差別：Room UI 選項通常是 **selector value**，真正玩家可見的 `10/20/30 min` 等文字是 selector entry／mode UI 的另一層語意。

Wiki 確實確認多個模式有可選的制限時間，例如 Team Survival `10/20/30分`、Team Tactical `3/4/5分` 等。[W] citeturn606128search0

所以：

```text
u8 time_value ≠ 必然直接等於「分鐘」
```

在伺服器重建中應保留 selector mapping，而不是直接 hardcode `value = minutes`。

---

## 5. `GR_RULECHANGE_REQ/ACK`：Rule / victory-condition selector

### 5.1 Packet 格式

Request 169：

```c
Packet::possible_ctor_or_dtor_0(v2, 169);
sub_592920(v2, a1);
```

ACK 170：

```c
sub_592940(a1, &n17);
sub_42FE50(dword_EA10D0, n17);
```

所以：

```text
169 GR_RULECHANGE_REQ
+0x00 u8 rule_value

170 GR_RULECHANGE_ACK
+0x00 u8 rule_value
```

[C] fileciteturn341file0L24-L47

### 5.2 ACK 的資料流

`sub_42FE50()` 不是單純改一個 byte：它會把收到的 rule value 套到 Room/player state，並重新選擇：

```text
GAMEROOM_SCROLL_RULE
```

其中 selector entry value 同樣透過：

```c
sub_4387B0(...)
```

找回 UI list item，再呼叫 `sub_6B9B10()` 選中。[C]

因此目前最安全命名：

```text
rule_value
rule_selector_value
```

而不是：

```text
mode_id
win_type
kill_limit
```

後三者都可能只是 selector value 的下游解釋。

### 5.3 一個關鍵 semantic clue：`n11 == 11`

Start UI flow 中會取：

```c
v77 = v123[36];
n11 = sub_4387B0(v123, v77);
if ( n11 == 11 )
    sub_4355D0(this);
else if ( teamshuffle enabled ... )
    sub_435520(this);
else
    sub_42F5E0(this);
```

這證明 `sub_4387B0(v123, current_value)` 可以把 current selector value 映射回其 list position/index。

因此：

```text
current selector value
    ↔ list entry value
    ↔ list index
```

是這套 Room UI 的核心資料模型。

但 **`index == 11` 的實際玩家語意目前仍未完全封死**，因此不要在 Server 中把 11 直接命名成某個 mode/rule enum。[C]

---

## 6. `GR_WINCHANGE_REQ/ACK`：另一個 16-bit Room selector

Packet registration：

```text
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
```

[C] fileciteturn344file0L1-L23

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 171);
sub_5929E0(v2, a1);
```

ACK：

```c
sub_592A00(a1, &v2);
return sub_430720(dword_EA10D0, v2);
```

因此：

```text
171/172 payload = u16
```

[C] fileciteturn341file0L50-L74

`sub_430720()` 所處理的是 Room 設定物件，但目前未完成它與 `GAMEROOM_SCROLL_RULE` / `GAMEROOM_SCROLL_TIME` 的完全對應。因此現階段不要直接把它叫 `kill_limit`。

這一點尤其重要，因為 Wiki 顯示不同 mode 的「勝利條件」數值型態確實不同：例如 Team Survival 是 `50/100/200 Kill`，Team Tactical 是 `3/5/7/10/12/15 Round`。 [W] citeturn606128search0

所以 **u16 很可能是某個 rule-specific selector/value，而不是固定單一單位。**

---

## 7. `GR_ITEMCHANGE_REQ/ACK`：Item + packed flag

Registration：

```text
175 GR_ITEMCHANGE_REQ
176 GR_ITEMCHANGE_ACK
```

[C] fileciteturn344file0L50-L69

Request `sub_56F6E0()`：

```c
Packet::possible_ctor_or_dtor_0(v2, 175);
sub_592920(v2, a1);
```

Receiver `sub_56F790()` 最終把這個 byte 傳入 `sub_430D50()`。

### `sub_430D50()` 精確 bit layout

```c
v16 = a2 & 1;
v17 = (a2 >> 1) & 1;
sub_74F450(component, a2 & 1);
sub_74F430(component, (a2 >> 1) & 1);
...
GAMEROOM_ITEM + 76 = (a2 & 1) != 0;
```

[C] fileciteturn330file2L278-L323

所以目前可以完全確定：

```text
175/176 +0x00 u8 packed_flags

bit 0 = Item state
bit 1 = another Room/gameplay component flag
bits 2..7 = currently unresolved
```

**bit 0 已封死為 Item 開關。**

Wiki 同樣確認 Room information 顯示 `アイテム/ノーアイテム戦`。 [W] citeturn606128search0

bit 1 雖然 C 已證明會影響另一個 component，但在目前證據下不應直接命名成 `crazy`、`knife` 或 `gimmick`；先保留 `bit1_control`。

---

## 8. `GR_AUTOCHANGE_REQ/ACK` 與其它設定：目前不與 121/173 混為一談

Packet registration 還存在：

```text
177 GR_AUTOCHANGE_REQ
178 GR_AUTOCHANGE_ACK
```

以及：

```text
GAMEROOM_DAMAGEROOM
GAMEROOM_TEAMBALANCE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_USERSLOTS
```

目前已能直接看到的 local handlers 包括：

```text
sub_430FD0 -> GAMEROOM_DAMAGEROOM
sub_433BE0 -> GAMEROOM_USERSLOTS
```

`sub_430FD0()` 對 `GAMEROOM_DAMAGEROOM +76` 寫入 boolean：

```c
*(v9 + 76) = a2 != 0;
```

[C] fileciteturn330file2L328-L385

這表示 `GAMEROOM_DAMAGEROOM` 是真正具體的 Room control，不只是字串資源名。

`sub_433BE0()` 則透過 `GAMEROOM_USERSLOTS` 找指定 slot control 並更新其 UI state。fileciteturn330file3L485-L513

---

## 9. Mode / Rule 的 C-side 對應：不能把所有 numeric value 都當同一套 enum

C 中已經存在真正的 mode-specific lobby UI factory：

```text
0  CyTeamMatchModeLobbyUI
1  CyIndividualSurvivalModeLobbyUI
2  CyDefuseBombModeLobbyUI
3  CyTeamSurvivalModeLobbyUI
4  CyStealModeLobbyUI
5  CyPracticeModeLobbyUI
6  CyTutorialModeLobbyUI
7  CyChattingRoomModeLobbyUI
8  CyPulpnRollModeLobbyUI
9  CyGunShootingModeLobbyUI
10 CyOccupyModeLobbyUI
11 CyAIMultiModeLobbyUI
12 CyTeamSoccerModeLobbyUI
13 CyOccupyRenewalModeLobbyUI
15 CyWeaponTestModeLobbyUI
```

[C] `CyGameModes` factory 對 `0..13` 的 mapping 可直接由 `PaperMan.exe.c` 讀到。fileciteturn338file4L197-L333

這與 Wiki 的玩家模式名稱有很好的獨立對應，例如：

```text
個人サバイバル
爆破ミッション
チームサバイバル
スチールモード
練習モード
パルプ＆ロール
new占領モード
PVE
サッカーモード
チーム戦術モード
チャットルーム
```

[W] citeturn606128search0

但要特別注意：

```text
LobbyUI factory mode code
≠
GR_RULECHANGE 的 rule selector value
≠
一定等於 CGameRule object-type helper 的 numeric value
```

目前逆向中已經同時存在數種不同 namespace / enum-like number。Server 重建時必須保持分離。

---

## 10. 目前已收斂的 Room 設定資料模型

```text
                  ┌──────────────────────────┐
                  │  Room UI / Resource      │
                  │                          │
                  │ GAMEROOM_SCROLL_MAP      │
                  │ GAMEROOM_SCROLL_RULE     │
                  │ GAMEROOM_SCROLL_TIME     │
                  │ GAMEROOM_ITEM            │
                  │ GAMEROOM_USERSLOTS       │
                  │ ...                      │
                  └────────────┬─────────────┘
                               │
                  selector list entries
                  stride = 40 bytes
                  value   = entry + 36
                               │
             ┌─────────────────┼─────────────────┐
             │                 │                 │
       current map       current rule       current time
       object +130       selector value      object +136
             │                 │                 │
             │                 │                 │
          121/122          169/170          173/174
           u8/u8            u8/u8            u8/u8

另外：
171/172 -> u16 rule-specific value
175/176 -> packed u8, bit0 = Item
```

這個模型目前可以把 **「UI 選項」與「wire value」** 分開，對 Server 重建非常重要：Server 不應假設所有 UI 選項都是連續 integer 或直接把 UI index 當 packet value。

---

## 11. 三方交叉驗證總表

| 區域 | C / IDA | Wiki | Extracted resource | 目前結論 |
|---|---|---|---|---|
| Map selector | `GAMEROOM_SCROLL_MAP`、entry `+36`、121/122 u8 | Wiki 明確有 map selection / room info | `maplist.dat` 含實際 `.pmm` map resource path | **高可信閉合** |
| Time selector | `GAMEROOM_SCROLL_TIME`、object `+136`、173/174 u8 | 各 mode 有多個時間選項 | UI/resource selector entry 機制與 C 同源；具體 value↔分鐘仍未完全解析 | **高可信 selector；enum OPEN** |
| Rule selector | `GAMEROOM_SCROLL_RULE`、169/170 u8 | 各 mode 有不同 victory condition | selector list 本身由 C resource system 提供 | **高可信 selector；實際 enum OPEN** |
| Win value | 171/172 u16 | 各 mode victory condition 型態不同 | 尚未把全部 value table 映射完成 | **格式已定；語意 OPEN** |
| Item | 175/176 u8，bit0 直接寫 `GAMEROOM_ITEM` | Wiki 明確有 アイテム/ノーアイテム | `GAMEROOM_ITEM` 為實際 UI control | **bit0 完全閉合** |
| Team balance | `GAMEROOM_TEAMBALANCE` | Wiki 明確列 team balance | 實際 Room control | **控制存在閉合；完整 wire enum 待追** |
| Team shuffle | `GAMEROOM_TEAMSHUFFLE`、Start path 使用 | Wiki 明確列 team shuffle | 實際 Room control | **控制存在閉合；完整 wire enum 待追** |
| No-skill | `GAMEROOM_CLAN_NOSKILL` / `GAMEROOM_NORMAL_NOSKILL` | Wiki 明確列 NO SKILL | 實際 Room controls | **mode/context split 已閉合** |

---

## 12. 對 Server 重建最重要的實作規則

### 規則 A：傳 selector value，不要擅自傳 UI index

C 清楚顯示：

```text
UI list index
        ↕
sub_4387B0()
        ↕
entry value @ +36
        ↕
packet field
```

因此 Server protocol model 應區分：

```text
RuleOptionIndex
RuleOptionValue
TimeOptionIndex
TimeOptionValue
MapOptionIndex
MapOptionValue
```

不要把它們合成一個 `int option`。

### 規則 B：不要把 `u8` 自動轉成 public enum

目前至少已出現：

```text
map_value
rule_value
 time_value
packed item flags
```

它們雖然都是 u8，但 namespace 完全不同。

### 規則 C：不要把 171/172 的 u16 直接寫成 `kill_limit`

Wiki 顯示不同 mode 的 victory condition 單位不同，而 C 尚未證明 171/172 只服務單一模式。因此暫時應保留：

```text
win_condition_value
```

或更保守：

```text
rule_specific_u16_value
```

### 規則 D：保留未知欄位，不要用 0 填滿

對 Server reverse engineering 而言：

```text
已證明 -> 精確實作
高可信推導 -> 明確命名 + 註記
未證明 -> 保留 unknown / raw
```

比「為了讓程式先跑就硬塞 0」更能保持未來與 client compatibility oracle 的可逆性。

---

## 13. 後續閉環目標

這一份 Room-setting family 已經把主要 UI / selector / packet skeleton 收斂下來。下一輪最有價值的工作是：

1. 把 `sub_430720()` 完整解析，封死 `171/172` 的 u16 語意。
2. 完成 `sub_42FE50()` 全部 rule value mapping，找出 Wiki 的 `Kill/Round/CC/Point` 等選項如何映射到 C-side value。
3. 完成 `sub_431160` / `GR_*` 對 `GAMEROOM_TEAMBALANCE`、`GAMEROOM_TEAMSHUFFLE`、`GAMEROOM_NORMAL_NOSKILL` 的 wire path。
4. 找到 `GR_STARTTIME_REQ/ACK` 的真正 handler；registration 已確認 137/138，但目前不能因名稱就假設它是一般 GameRule switch 的一部分。
5. 進一步把 `maplist.dat` 每個固定 record 的 field offset 完整解出來，與 `sub_4387B0()` 的 `+36` value 做 binary-level 對照。

這五項完成後，Room → GameRule 的設定層才算真正封閉，之後再進入 combat / spawn / death / score packet family 會更可靠。
