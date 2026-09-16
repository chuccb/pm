# Room 設定與規則變更封包研究

> 研究日期：2026-09-16
>
> 本文件專門收斂「Room UI → selector/value → Request → ACK → Client 狀態」這一層。重點是資料流，而不是只依 packet name 猜 enum。

## 1. 證據等級與命名原則

- **[C]**：IDA Hex-Rays `PaperMan.exe.c` 的封包建立、解析、函式資料流、物件欄位。
- **[W]**：PaperMan Wiki 的玩家可見規則與 Room 設定。
- **[R]**：`Extracted/` 實際資源。
- **[X]**：跨來源推導；若仍未完全封死，必須明確標記 OPEN。

命名原則：先保留 `*_value`、`selector_value`、`packed_flags`、`unknown_*` 等可逆名稱；沒有證據時不把數字直接命名成伺服器 enum。

---

## 2. Room UI 的實際控制面

C 中同一套 Room UI 明確查找並操作：

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

Room UI event dispatch 會依這些 key 選擇對應操作，而不是所有控制共用一條 generic path。**[C]**

Wiki 的 Room information 也明確列出：

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

**[W]** citeturn606128search0

因此「Room UI 的 selector / flag 層」在 C 與 Wiki 兩邊獨立成立。

---

## 3. 所有 selector 的共同資料模型：Index 與 Value 分離

多個 Room scroll control 使用同一種 entry 結構。

`sub_4387B0()`：

```c
return *(*(this + 33) + 40 * a2 + 36);
```

代表：

```text
entry stride = 40 bytes
entry value  = +36
```

**[C]**

因此必須區分：

```text
OptionIndex      // UI list position
OptionValue      // 真正存取／傳輸的 value
```

不能假設：

```text
OptionIndex == OptionValue
```

這個 distinction 是整個 Room protocol reverse engineering 的核心。

---

## 4. `GR_MAPCHANGE_REQ/ACK (121/122)`：Map selector value

### 4.1 Wire format

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 121);
sub_592920(v2, a1);
```

ACK receiver：

```c
sub_592940(a1, &v2);
sub_42FC50(dword_EA10D0, v2);
```

因此：

```text
121 GR_MAPCHANGE_REQ
+0x00 u8 map_value

122 GR_MAPCHANGE_ACK
+0x00 u8 map_value
```

**[C]**

### 4.2 ACK 會回到 `GAMEROOM_SCROLL_MAP`

`sub_42FC50()` 取得：

```text
GAMEROOM_SCROLL_MAP
```

再用 `sub_4387B0()` 找 `entry value == map_value` 的項目，找到後透過 `sub_6B9B10()` 選中。

因此：

```text
121/122 field
    ↓
GAMEROOM_SCROLL_MAP entry value
```

不是任意 status byte。

### 4.3 Object field 與本地 cache

`sub_540260()`：

```c
return *(this + 130);
```

`sub_540280()`：

```c
*(this + 130) = a2;
```

因此目前最安全的命名是：

```text
Room/Player object +130 = current_map_selector_value
```

是否完全等同於 `map_id`，仍不能只靠這一層下結論。

Client 還會把該 byte 寫進：

```text
cfg\\Map.dat
```

而 `Extracted/map/maplist.dat` 確實是實際的二進位 map inventory，可看到例如：

```text
maps\\TU_01_tutorial.pmm
```

因此：

```text
[R] maplist.dat / map resource
        ↓
[C] GAMEROOM_SCROLL_MAP
        ↓
[C] 40-byte entry, value @ +36
        ↓
[C] object +130
        ↓
[C] 121/122 u8
```

這是目前 Room → map 的三方最完整閉環之一。

---

## 5. `GR_START_REQ (129)`：其 byte 也由 Map selector 產生

`sub_4320F0()` 在通過 Start precondition 後呼叫：

```c
n125 = sub_437060(this);
*(this + 112) = 6;
sub_5627C0(n125);
```

`sub_437060()` 明確取得：

```text
GAMEROOM_SCROLL_MAP
```

並在至少 `n124 == 125` 的 path 中：

```c
v4 = (v13[34] - v13[33]) / 40;
v11 = rand() % (v4 - 2);
return sub_4387B0(v13, v11);
```

所以：

```text
129 GR_START_REQ
+0x00 u8 start_map_value / start_parameter
```

其中「payload 由 Map selector value 產生」是 **[C 高可信]**；「server side field 應命名成 map id」仍應保持 OPEN。

因此不能把 129 byte 當成 generic `start_flag`。

---

## 6. `GR_TIMECHANGE_REQ/ACK (173/174)`：Time selector value

Packet registration 明確是：

```text
173 GR_TIMECHANGE_REQ
174 GR_TIMECHANGE_ACK
```

**[C]**

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 173);
sub_592920(v2, a1);
```

ACK：

```c
sub_592940(a1, &v2);
sub_430920(dword_EA10D0, v2);
```

所以：

```text
173/174 +0x00 u8 time_value
```

`sub_430920()` 會：

```c
*(i_2 + 136) = a2;
```

接著取得：

```text
GAMEROOM_SCROLL_TIME
```

再以 `sub_4387B0()` 找相同 value 的 entry 並選中。

因此可以封死：

```text
Room/Player object +136 = current_time_selector_value
```

**重要：** `time_value` 目前不能直接命名為 `minutes`。Wiki 雖然確認多模式存在例如 `10/20/30分`、`3/4/5分` 的時間選項，但 packet field 是 selector value，不代表其數字必然就是分鐘數。[W] citeturn606128search0

Server 應保留：

```text
TimeOptionIndex
TimeOptionValue
TimeMinutes
```

三者分離。

---

## 7. `GR_RULECHANGE_REQ/ACK (169/170)`：Rule selector value

Wire：

```text
169 GR_RULECHANGE_REQ
+0x00 u8 rule_value

170 GR_RULECHANGE_ACK
+0x00 u8 rule_value
```

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 169);
sub_592920(v2, a1);
```

ACK：

```c
sub_592940(a1, &n17);
sub_42FE50(dword_EA10D0, n17);
```

**[C]**

### 7.1 `sub_42FE50()` 的資料流

收到 `rule_value` 後，client 不是只更新 UI，而是：

```text
rule_value
  ↓
sub_426930(...)
  ↓
Room/Player object +130
  ↓
GAMEROOM_SCROLL_RULE
  ↓
sub_4387B0() 找 entry value
  ↓
sub_6B9B10() 選中 UI item
```

另外 `GAMEROOM_USERSLOTS` 等 Room state 也會在這條 path 上同步調整。

### 7.2 一個重要的 list-index clue

Start path 中有：

```c
v77 = v123[36];
n11 = sub_4387B0(v123, v77);
```

此處 `v123[36]` 是 current selector value，而 `sub_4387B0()` 接受的是 index，表示 caller 可能在做：

```text
current value → 找回 list index
```

因此 selector value 與 list index 在 client 內部確實是兩個不同概念。

`n11 == 11` 會走特殊 Start path，但 **index 11 的玩家語意目前未封死**，不能直接寫成某個 mode/rule enum。

---

## 8. `GR_WINCHANGE_REQ/ACK (171/172)`：名稱不能直接當成 `kill_limit`

這一段需要修正先前容易產生的錯誤推導。

Registration：

```text
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
```

Wire：

```text
171 +0x00 u16
172 +0x00 u16
```

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 171);
sub_5929E0(v2, a1);
```

ACK：

```c
sub_592A00(a1, &v2);
sub_430720(dword_EA10D0, v2);
```

**[C]**

而 `sub_430720()` 明確處理：

```text
GAMEROOM_SCROLL_OBJECT
```

並把收到的值直接存入：

```c
*(RoomPlayerObject + 144) = a2;
```

然後同樣使用：

```c
sub_4387B0(...)
sub_6B9B10(...)
```

找回 selector entry。

因此目前最安全結論是：

```text
171/172
    = 16-bit value for GAMEROOM_SCROLL_OBJECT
```

而 **不是** 已證明的：

```text
kill_limit
round_limit
win_type
```

### 為什麼 packet name 不能覆蓋資料流證據

`GR_WINCHANGE` 是歷史命名；client 真正的接收函式把它送進 `GAMEROOM_SCROLL_OBJECT`。Server reverse engineering 應優先服從實際 data flow，而不是只看名字。

Wiki 確實有各 mode 不同的勝利條件，例如：

```text
Team Survival: 50/100/200 Kill
Team Tactical: 3/5/7/10/12/15 Round
new占領: 300/500/700/1000 Point
```

[W] citeturn606128search0

這些 rule-specific values 與 `GAMEROOM_SCROLL_OBJECT` 的 16-bit field 是否是一一對應，目前仍需繼續從 `sub_430720()` caller、resource entry 與 mode UI 完整閉合。

---

## 9. `GR_ITEMCHANGE_REQ/ACK (175/176)`：u8 packed flags

Registration：

```text
175 GR_ITEMCHANGE_REQ
176 GR_ITEMCHANGE_ACK
```

Request：

```c
Packet::possible_ctor_or_dtor_0(v2, 175);
sub_592920(v2, a1);
```

**[C]**

### 9.1 建包前的 packed flag 來源

`sub_430AF0()` 建立送出的 byte：

```c
v17 = 0;
if ( v19 != 0 )
    v17 = *(v19 + 76) == 1;

if ( v18 )
    v17 |= 2 * v18;

return sub_56F6E0(v17);
```

其中：

```text
bit 0 = GAMEROOM_ITEM state
bit 1 = sub_728D90(current_map, ...) 的結果
```

所以 bit 1 **確實與 map-dependent / gimmick-related state 有直接 data flow**；再加上同一 Room UI 存在 `GAMEROOM_GIMMICK`，目前最適合命名為：

```text
bit1_map_gimmick_or_related_flag
```

而不是直接猜成 `crazy`、`knife`。

### 9.2 ACK 的 decode

`sub_430D50()`：

```c
v16 = a2 & 1;
v17 = (a2 >> 1) & 1;
sub_74F450(component, a2 & 1);
sub_74F430(component, (a2 >> 1) & 1);
...
*(GAMEROOM_ITEM + 76) = (a2 & 1) != 0;
```

因此完全可以封死：

```text
175/176 +0x00 u8 packed_flags

bit 0 = Item on/off
bit 1 = map-dependent / gimmick-related flag [X high]
bits 2..7 = unresolved
```

Wiki 確認 Room information 有 `アイテム/ノーアイテム戦`，與 bit0 的 C data flow 完整對應。[W] citeturn606128search0

---

## 10. `GAMEROOM_DAMAGEROOM` 是獨立 Room state，不要混入 Item packet

另有：

```text
sub_430FA0()
    -> sub_56F950(a2)

sub_430FD0()
    -> GAMEROOM_DAMAGEROOM +76 = (a2 != 0)
```

也就是 `GAMEROOM_DAMAGEROOM` 有自己的控制 path。[C]

因此不要因為它同樣是單 byte，就與 175/176 的 packed item byte 共用 enum。

---

## 11. Team balance / Team shuffle / No-skill：存在於同一 Room state machine

C 的 Room UI path 同時實際使用：

```text
GAMEROOM_TEAMBALANCE
GAMEROOM_TEAMSHUFFLE
GAMEROOM_CLAN_NOSKILL
GAMEROOM_NORMAL_NOSKILL
GAMEROOM_USERSLOTS
```

Wiki 的 Room information 也明列：

```text
チームバランス
チームシャッフル
NO SKILL
```

[W] citeturn606128search0

其中 no-skill 更有一個重要 client-side context split：

```text
current player/object +188 == 2
    → GAMEROOM_CLAN_NOSKILL
else
    → GAMEROOM_NORMAL_NOSKILL
```

所以 no-skill **不是單一 global boolean**；至少 client UI 層有 clan / normal 兩條控制路徑。[C]

完整 wire opcode/value mapping 仍應從相應 sender/receiver 繼續封閉，不能只憑 UI key 命名 packet。

---

## 12. `GR_AUTOCHANGE_REQ/ACK (177/178)` 先保留為獨立 family

Registration 明確：

```text
177 GR_AUTOCHANGE_REQ
178 GR_AUTOCHANGE_ACK
```

目前不把它硬併入 Map/Rule/Time family，因為尚未完成其完整 handler data flow。

正確做法是先保留：

```text
AUTOCHANGE = independent room-state family [OPEN]
```

等 sender → receiver → state/resource 三方閉合後再命名。

---

## 13. Mode code 與 Room selector value 必須嚴格分 namespace

C 中存在一組真正的 mode-specific lobby UI factory：

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

這與 Wiki 可見 mode 名稱可以對上大部分 public modes。[C][W] citeturn606128search0

但必須禁止以下錯誤等價：

```text
LobbyUI mode code
    != GR_RULECHANGE selector value
    != GR_TIMECHANGE selector value
    != GR_WINCHANGE / GAMEROOM_SCROLL_OBJECT value
    != CGameRule helper 的 type predicate value
```

目前 C 已經證明系統中同時存在多組 numeric namespace。

---

## 14. Room selector packet summary

| Opcode | Packet | Payload | C-side destination | 目前語意 |
|---:|---|---|---|---|
| 121 | `GR_MAPCHANGE_REQ` | `u8` | Map selector | `map_value` **[C]** |
| 122 | `GR_MAPCHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_MAP` | `map_value` **[C]** |
| 127 | `GR_READY_REQ` | none | Ready path | ready request **[C]** |
| 129 | `GR_START_REQ` | `u8` | Start path | map-derived `start_parameter` **[C high]** |
| 169 | `GR_RULECHANGE_REQ` | `u8` | `GAMEROOM_SCROLL_RULE` | `rule_selector_value` **[C]** |
| 170 | `GR_RULECHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_RULE` | `rule_selector_value` **[C]** |
| 171 | `GR_WINCHANGE_REQ` | `u16` | `GAMEROOM_SCROLL_OBJECT` | `object_selector_value` **[C]** |
| 172 | `GR_WINCHANGE_ACK` | `u16` | `GAMEROOM_SCROLL_OBJECT` | `object_selector_value` **[C]** |
| 173 | `GR_TIMECHANGE_REQ` | `u8` | `GAMEROOM_SCROLL_TIME` | `time_selector_value` **[C]** |
| 174 | `GR_TIMECHANGE_ACK` | `u8` | `GAMEROOM_SCROLL_TIME` | `time_selector_value` **[C]** |
| 175 | `GR_ITEMCHANGE_REQ` | `u8` packed | `GAMEROOM_ITEM` + component state | bit0 Item; bit1 map/gimmick-related **[C/X]** |
| 176 | `GR_ITEMCHANGE_ACK` | `u8` packed | same | same decode **[C/X]** |
| 177 | `GR_AUTOCHANGE_REQ` | OPEN | OPEN | 尚未閉合 |
| 178 | `GR_AUTOCHANGE_ACK` | OPEN | OPEN | 尚未閉合 |
|
注意：`GR_WINCHANGE_*` 名稱不能覆蓋 `sub_430720()` 已證明的 `GAMEROOM_SCROLL_OBJECT` data flow。

---

## 15. Server 重建時應使用的 domain model

不要直接把 client packet byte 映射成裸 integer field。推薦保留：

```text
RoomState
├─ Mode
├─ Map
│  ├─ OptionIndex
│  └─ OptionValue
├─ Rule
│  ├─ OptionIndex
│  └─ OptionValue
├─ Time
│  ├─ OptionIndex
│  ├─ OptionValue
│  └─ Duration
├─ ObjectSelector
│  ├─ OptionIndex
│  └─ OptionValue (u16)
├─ ItemEnabled
├─ MapGimmickOrRelatedFlag   // 若尚未完全命名，保留 raw flag
├─ TeamBalance
├─ TeamShuffle
├─ NoSkillNormal
├─ NoSkillClan
└─ DamageRoom
```

Protocol layer 再明確建立：

```text
GR_MAPCHANGE  -> Map.OptionValue
GR_RULECHANGE -> Rule.OptionValue
GR_TIMECHANGE -> Time.OptionValue
GR_WINCHANGE  -> ObjectSelector.OptionValue
GR_ITEMCHANGE -> PackedFlags
```

這比在 Server 中直接寫：

```text
byte rule
byte time
ushort win
```

更容易維護，也更適合之後加入 packet oracle / compatibility test。

---

## 16. 三方交叉驗證結論

### 已高可信閉合

```text
Map
C: GAMEROOM_SCROLL_MAP + entry +36 + object +130 + 121/122
W: Room information / map selection
R: maplist.dat + actual .pmm resource paths
```

### 已高可信但 enum 尚未完全閉合

```text
Time
C: GAMEROOM_SCROLL_TIME + object +136 + 173/174
W: mode-specific time options
R: selector/resource system
```

```text
Rule
C: GAMEROOM_SCROLL_RULE + 169/170
W: mode-specific victory-condition options
R: selector/resource system
```

### Wire 已閉合、語意仍 OPEN

```text
171/172
    u16
    ↓
GAMEROOM_SCROLL_OBJECT
    ↓
object +144
```

```text
175/176
    u8 packed
    bit0 = Item
    bit1 = map/gimmick-related [X high]
```

### 尚未應寫死

```text
rule value → exact Kill/Round/Point/CC enum
object value → exact public meaning
173/174 value → exact minutes mapping
175 bit1 → exact public label
177/178 semantics
team-balance / team-shuffle complete wire mapping
```

---

## 17. 下一個最有價值的閉環

完成 Room selector family 後，優先順序：

1. `sub_430720()` 的所有 caller + `GAMEROOM_SCROLL_OBJECT` entries，找出 171/172 的真正 public semantics。
2. `sub_42FE50()` 的 `sub_426930()`，把 Rule selector value 映射到實際 mode/rule options。
3. `GR_ITEMCHANGE` 的 bit1 沿 `sub_728D90()` → `GAMEROOM_GIMMICK` 繼續追，直到 public label 封死。
4. `GR_STARTTIME_REQ/ACK` 137/138 的真正 handler layer，確認它與 173/174、GameRule start sequence 的關係。
5. Room layer 完成後立即轉進 `CGameRule::sub_67CF90()` 的 mode dispatcher，再追 combat / spawn / death / score packet families。

目前最重要的原則仍是：

```text
Wiki 告訴我們「玩家看到什麼」
IDA C 告訴我們「client 實際怎麼運作」
Extracted 告訴我們「client 手上真正有哪些資料」

三者一致 → 才提升為高可信 Server specification
只有單一路徑 → 保留 raw / unknown
```
