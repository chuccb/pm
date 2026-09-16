# 地圖選擇、房間狀態與 GameRule 封包研究

> 研究日期：2026-09-16

本文件專門整理目前已從 `PaperMan.exe.c` 還原出的「房間地圖選擇 → 開局 → Map Change」資料流。

## 1. `GR_MAPCHANGE_REQ (121)`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 121);
sub_592920(v2, a1);
sub_555090(&dword_1321D00, v2);
```

因此目前可確定：

```text
121 GR_MAPCHANGE_REQ
+0x00 u8 map_value
payload = 1 byte
```

重要 caller `sub_56E480(a2)` 會先：

```c
*(this + 112) = 1;
sub_56E480(a2);
```

而 `sub_56E480()` 本身就是建立 121 並送出的函式。其上層 state value `+112 = 1` 顯示這條 path 明確屬於房間內地圖選擇／變更流程。

## 2. `GR_MAPCHANGE_ACK (122)`

Receiver：

```text
122 -> sub_56E530
```

`sub_56E530()` 讀一個 byte 後呼叫：

```c
return sub_42FC50(dword_EA10D0, v2);
```

因此 ACK 的第一欄同樣是：

```text
+0x00 u8 map_value
```

`sub_42FC50()` 直接尋找 UI／資源 key：

```text
GAMEROOM_SCROLL_MAP
```

並在地圖列表中尋找其值等於封包 byte 的項目；找到後呼叫：

```c
sub_6B9B10(v11, i);
```

最後更新玩家／房間 UI state。fileciteturn276file0L17-L63

這提供很強的證據：

```text
121/122 的 1-byte 欄位
    <-> 房間地圖列表中的 map value
```

因此不是任意 status byte。

## 3. `GR_START_REQ (129)` 也與地圖選擇值直接相連

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 129);
sub_592920(v2, n125);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
129 GR_START_REQ
+0x00 u8 start_parameter
payload = 1 byte
```

真正關鍵是 caller `sub_4320F0()`：

```c
if ( sub_432040() == 0 || n2 == 2 )
    return 0;
if ( sub_67EB70() && sub_42F540(this) == 0 )
    return 0;
n125 = sub_437060(this);
*(this + 112) = 6;
sub_5627C0(n125);
```

因此 129 的 byte 不是直接常數，而是由 `sub_437060()` 計算取得。

## 4. `sub_437060()` 的資料來源是 `GAMEROOM_SCROLL_MAP`

`sub_437060()`：

```c
Destination = wcslen(L"GAMEROOM_SCROLL_MAP");
...
v13 = sub_40DDA0((*(this + 4) + 4), v10);
```

也就是直接取得房間的 `GAMEROOM_SCROLL_MAP` UI／資料物件。

之後依其型態 `n124` 處理：

```c
if (n124 == 125)
{
    v4 = (v13[34] - v13[33]) / 40;
    v11 = rand() % (v4 - 2);
    return sub_4387B0(v13, v11);
}
else if (n124 == 124)
{
    ...
    return sub_9B73E0(*(this + 384), n17);
}
```

特別是 `125` 路徑直接從 `GAMEROOM_SCROLL_MAP` 的項目列表取出一個值再返回，因此 129 的 `n125` 與房間地圖資料存在直接 caller-level data flow。fileciteturn275file0L45-L93

### 目前最安全的命名

不要把 129 byte 直接命名為：

```text
start_flag
start_type
ready_count
```

更適合保留成：

```text
start_map_value / start_parameter
```

其中：

```text
「它來自房間地圖列表值」 = 高可信 [C]
「它代表開局時選定地圖」  = 高可信推導 [X/OPEN]
```

最後一步仍建議透過 130、GameRule map state 與真正地圖載入函式再封死。

## 5. `GR_MAPCHANGE` 與 `GR_START` 的關係

目前能建立非常合理、且已有 C 資料流支持的模型：

```text
Room UI
  |
  | 地圖列表 GAMEROOM_SCROLL_MAP
  v
選擇／變更地圖
  |
  | 121 map_value
  v
Server / Room
  |
  | 122 map_value
  v
所有 Client 更新房間地圖選擇

-----------------------------

玩家按 Start
  |
  | sub_437060()
  | 從 GAMEROOM_SCROLL_MAP 取得值
  v
129 GR_START_REQ
  | +u8 start_map_value / parameter
  v
Server / GameRule
  |
  | 130
  v
Match 初始化
```

這表示 map selection 很可能在「Start」前就是房間狀態的一部分，而 129 將當時地圖選擇結果帶入開局流程。

## 6. 房間模式下的特殊地圖選擇

`sub_437060()` 並非只處理單純的固定索引：

```c
if (n124 == 125)
    return sub_4387B0(v13, rand() % (count - 2));

if (n124 == 124)
    return sub_9B73E0(..., n17);
```

因此至少存在不同的房間地圖選擇資料型態／UI 行為。

這很值得繼續追 `sub_439600(v13)` 與 `sub_4387B0()`，因為它們可能把：

```text
固定地圖
隨機地圖
特殊模式地圖
地圖清單索引
地圖 ID
```

做最後轉換。

目前不應只依 `rand()` 就把該路徑命名成 `random_map`；它需要與 Wiki 的地圖選擇規則和實際 resource map ID 再交叉確認。

## 7. Ready / Start 與 room state 的另一個線索

`sub_432040()` 在送 Ready 前會取得：

```text
GAMEROOM_USER...
```

相關 player/object state，成功後 `sub_562640()` 才真正發出 127。

`sub_4320F0()` 送 Start 前又重複經過：

```text
sub_432040()
sub_67EB70() / sub_42F540()
sub_437060()
```

所以 Ready 與 Start 都具有「room state + 本地條件檢查 + 真正送包」三層結構，而不是直接將按鍵事件映射成 opcode。

## 8. 後續高價值追查

### `sub_4387B0()`

確認 `GAMEROOM_SCROLL_MAP` 的列表項目到底存的是：

```text
map ID
map index
resource ID
```

### `sub_439600()`

確認 `124/125` 分支代表什麼資料型態或房間規則。

### `sub_6B9B10()`

確認 map change ACK 後真正更新哪些 room/game state。

### 130 `sub_562870()`

找出 start 後同步資料裡是否再次包含 map ID；若存在相同值，即可把 129 與 match map state 做更高強度的閉環。

### `CGameRule::NewGameStart`

將 map selection 最終連接到真正的 game map loading／mode initialization。

## 9. 目前結論

目前已經不是單純知道「121/122/129 各有一個 byte」，而是得到：

```text
121 byte
    -> GAMEROOM_SCROLL_MAP map value
    -> room map selection update

122 byte
    -> GAMEROOM_SCROLL_MAP 中尋找相同 value
    -> client room map UI/state update

129 byte
    -> Start caller 呼叫 sub_437060()
    -> sub_437060() 直接讀 GAMEROOM_SCROLL_MAP
    -> 其返回值成為 129 payload
```

因此 **地圖是 Ready → Start → GameRule 初始化鏈中的一級核心狀態，而不是單純 UI 裝飾資料**。這是目前核心 GameRule 逆向中相當重要的一個結構性發現。
