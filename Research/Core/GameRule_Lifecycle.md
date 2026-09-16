# `CGameRule` 與主要遊戲生命週期研究

> 研究日期：2026-09-16

## 研究目標

本文件開始恢復 PaperMan 最核心的遊戲生命週期，而不是只整理單一封包。重點是找出：

```text
房間／Lobby
    -> Ready
    -> Start
    -> Match 初始化
    -> 遊戲進行
    -> End
    -> Leave／返回房間
```

並將每個階段連回實際 `CGameRule` state、player slot、map、team、round 與封包。

## 1. GameRule 封包註冊骨架

目前從 `PaperMan.exe.c` 的封包註冊表確認：

```text
121 GR_MAPCHANGE_REQ
122 GR_MAPCHANGE_ACK
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK
127 GR_READY_REQ
128 GR_READY_ACK
129 GR_START_REQ
130 GR_START_ACK
131 GR_FORCEOUT_REQ
132 GR_FORCEOUT_ACK
133 GR_END_REQ
134 GR_END_ACK
135 GR_CHANGESLOT_REQ
136 GR_CHANGESLOT_ACK
137 GR_STARTTIME_REQ
138 GR_STARTTIME_ACK
189 GR_CHANGEMASTER_REQ
190 GR_CHANGEMASTER_ACK
```

這組封包顯示 GameRule／房間控制層具有非常明確的生命週期操作。

## 2. Ready

### 127 `GR_READY_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v1, 127);
this_3 += sub_555090(&dword_1321D00, v1);
```

沒有 payload writer，因此：

```text
127 GR_READY_REQ
payload = 0 bytes
```

在一個實際 caller `sub_4320B0()` 中，發送前先呼叫 `sub_432040()`；該函式會檢查 player／room 狀態，失敗時顯示訊息並阻止 Ready。若通過且 `n2 != 2`，才發送 127。fileciteturn269file0L34-L61

因此 Ready 是「有本地資格檢查的狀態操作」，而不是任意時刻都能直接送出的無條件封包。

### 128 `GR_READY_ACK`

接收：

```text
case 128:
    sub_5626D0(a4)
```

`sub_5626D0()` 依序讀：

```c
sub_592900(a1, &v6);       // u8
sub_592940(v1, &n0x10_1);  // u8
```

之後在 16 個 player slot 中找到第二個 byte 對應的玩家，並將第一個 byte 寫入該玩家的狀態；同時觸發 lobby player UI/state 更新。fileciteturn260file0L102-L140

所以目前可以安全寫成：

```text
128 GR_READY_ACK
+0x00 u8 player_state
+0x01 u8 player_id_or_slot_key
```

精確 byte 語意仍需追 `sub_548B00()` 與 player table 欄位，但這已證明 128 是玩家狀態同步，而不是單純 `success: u8`。

## 3. Start

### 129 `GR_START_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 129);
sub_592920(v2, n125);
this_3 += sub_555090(&dword_1321D00, v2);
```

因此：

```text
129 GR_START_REQ
+0x00 u8 start_parameter
payload = 1 byte
```

重要 caller `sub_4320F0()`：

```c
if ( sub_432040() == 0 || n2 == 2 )
    return 0;
if ( sub_67EB70() && sub_42F540(this) == 0 )
    return 0;
n125 = sub_437060(this);
*(this + 112) = 6;
sub_5627C0(n125);
```

因此 `n125` 是由 `sub_437060()` 動態取得，而不是固定值。`sub_67EB70()` 也可能對某些特殊環境增加額外條件。fileciteturn269file0L65-L77

### 130 `GR_START_ACK`

接收：

```text
case 130:
    sub_562870(a4)
```

`sub_562870()` 是目前核心生命週期中最重要的大型同步 parser 之一。

當第一個 byte `n2 == 1` 時，它會：

1. 讀取玩家相關的 scalar 與字串資料；
2. 更新對應 player object 的多個欄位；
3. 更新玩家附加狀態；
4. 最後迴圈讀取 **16 個 DWORD**，寫入：

```c
dword_F6DD1C[60195 * i] = v46;
```

5. 再依房間／遊戲模式更新 lobby/game-room UI。

這代表 130 很可能是「開始後的玩家／遊戲狀態同步入口」，而不是一般意義上的單一 ACK code。fileciteturn260file0L210-L289

真正語意仍需進一步把每個欄位連到 `player slot / team / character / state`。

## 4. Match 初始化：`CGameRule::NewGameStart`

目前已知 `CGameRule::NewGameStart` 會集中清理並初始化大量核心 state，例如：

```text
+56 = 5000
+48 = 0
+8  = 0
+12 = 0
+20 = 0
+24 = 0
```

並進一步呼叫數個核心初始化函式，包括：

```text
sub_709330
sub_89B200
sub_720820
sub_67E560
```

另會執行 mode/map 相關初始化；若部分 player count 條件不足，還會修改：

```text
+82 = 1
+81 = 1
```

因此 `NewGameStart` 應視為真正的 match initialization 根節點。

目前還不能將 `+56 = 5000` 直接命名成「5 秒開局倒數」；它也可能是其他與 GameRule 相關的初始計時／state 值。要由 caller、tick routine、UI 與 `GR_STARTTIME` 再交叉確認。

## 5. Leave 與 End 必須分開

### 123 `GR_LEAVE_REQ`

Client sender 無 payload：

```text
123 GR_LEAVE_REQ
payload = 0 bytes
```

重要 caller：

```text
sub_431580()
    -> sub_562D70()
```

此外還有 path 在 player/game state 改變後直接發送 123。fileciteturn263file2L81-L100

### 133 `GR_END_REQ`

同樣是無 payload：

```text
133 GR_END_REQ
payload = 0 bytes
```

Client code 中有明確分支：

```c
if ( *(this + 12) != 0 )
{
    if ( n2_0 == 3 )
        sub_562D70();    // 123
    else
        sub_562E00();    // 133
}
```

所以不同上層模式下，「離開」與「結束」的協定操作不同，不能只建立一個 `Leave()` 封包代替全部情況。fileciteturn263file2L132-L151

### 124 / 134

目前 receiver 分別為：

```text
124 -> sub_5607C0
134 -> sub_562EA0
```

它們的完整 state transition 還需要繼續逆向。

## 6. Map Change

### 121 `GR_MAPCHANGE_REQ`

已找到 sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 121);
sub_592920(v2, a1);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
121 GR_MAPCHANGE_REQ
+0x00 u8 map_change_value
payload = 1 byte
```

Caller `sub_56E480(a2)` 會先設定：

```c
*(this + 112) = 1;
```

再發送封包，代表 map change request 同時驅動 lobby/client state。fileciteturn268file0L1-L27

### 122 `GR_MAPCHANGE_ACK`

Receiver：

```c
sub_592940(a1, &v2);
return sub_42FC50(dword_EA10D0, v2);
```

目前至少確定 ACK 起始欄位是 1 byte；精確意義要追 `sub_42FC50()`。fileciteturn266file0L27-L35

## 7. Force Out

### 131 `GR_FORCEOUT_REQ`

Sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 131);
sub_592920(v2, n0x10);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
131 GR_FORCEOUT_REQ
+0x00 u8 target_value
payload = 1 byte
```

目前還不能將 `target_value` 直接命名為 `player_id`；caller 需要進一步追 `n0x10` 是 player ID、slot index 或經過 room mapping 的值。

### 132 `GR_FORCEOUT_ACK`

Receiver：

```text
case 132:
    sub_56ECC0(a4)
```

`sub_56ECC0()` 的第一 byte 決定是否進入後續同步；成功路徑還會解析 player、字串及其他資料，並修改 lobby player object。因此 132 同樣不是簡單的 ACK code，而是一個帶有 player-state update 的事件。fileciteturn266file0L253-L305

## 8. Change Slot

### 135 `GR_CHANGESLOT_REQ`

Sender：

```c
Packet::possible_ctor_or_dtor_0(v4, 135);
v2 = sub_592920(v4, n254);
sub_592920(v2, n0x10);
sub_555090(&dword_1321D00, v4);
```

所以 payload 固定是兩個 byte：

```text
135 GR_CHANGESLOT_REQ
+0x00 u8 field0
+0x01 u8 field1
payload = 2 bytes
```

一般房間與 Tournament room 都存在 wrapper：

```text
CLobbyGameRoom::sub_432530()
CLobbyTournamentGameRoom::sub_4793F0()
```

並傳入相同的兩個 byte。fileciteturn268file1L28-L64

這顯示換位是共用 GameRule packet，但兩種 room 類型各自有上層處理。

### 136 `GR_CHANGESLOT_ACK`

Receiver：

```text
case 136:
    sub_56EF40(a4)
```

目前 parser 顯示它會讀取多個 byte、DWORD 及最多 16 個 slot mapping，然後更新 lobby/game-room 中的玩家位置與 team/layout，因此很可能是「換位後整體玩家配置同步」。fileciteturn267file0L21-L97

## 9. `GR_STARTTIME_REQ/ACK` 是下一個高價值節點

`137/138` 已經在 registration table 中確認：

```text
137 GR_STARTTIME_REQ
138 GR_STARTTIME_ACK
```

尚未找到可靠的 sender/parser implementation。

這一對很可能是連接以下幾個概念的關鍵：

```text
GR_START_REQ
    -> CGameRule::NewGameStart
    -> start-time / countdown state
    -> 正式 gameplay
```

但目前不把這個關係當成已證明事實。

## 10. 目前的核心生命週期模型

```text
Lobby / Room
    |
    | Ready
    | 127
    v
玩家 ready 狀態
    |
    | Start
    | 129 + u8
    v
Server / GameRule
    |
    | 130
    v
Match 初始化／玩家狀態同步
    |
    | CGameRule::NewGameStart
    v
開始倒數／正式遊戲
    |
    +--> 121 Map Change
    +--> 135 Change Slot
    +--> 131 Force Out
    |
    v
Match End / Leave
    |
    +--> 133 End
    +--> 123 Leave
    |
    v
124 / 134 ACK 與房間狀態回復
```

這張圖是目前的「證據支持模型」，不是最終完成版；真正的 Server-side state machine、回合與 mode-specific logic 尚待繼續閉合。

## 11. 下一輪優先追查

```text
1. sub_437060()
   -> 完整解出 129 的 start_parameter

2. sub_562870()
   -> 完整解出 130 所同步的玩家欄位

3. sub_56EA80 / sub_56E530
   -> 完整解出 121/122 map change

4. sub_5607C0 / sub_562EA0
   -> 完整解出 124/134 的 end/leave state

5. GR_STARTTIME 137/138
   -> 連接 5000 / countdown / NewGameStart

6. CGameRule::NewGameStart
   -> 將所有 state 欄位映射到 mode/map/player/round

7. GameRule mode handlers
   -> 恢復 FFA / 爆破 / 團隊模式的實際勝負與回合規則

8. Battle event
   -> damage / death / kill / respawn
```
