# PaperMan 核心遊戲機制逆向研究

> 研究日期：2026-09-16
> **Target：日本版 PaperMan 2016 年最終 Client／服務終了時版本**

日本服務於 2016-12-26 12:00 終止；因此本目錄中的 Client 行為、Resource 與 Protocol reconstruction 均以 2016 final Client build 為 primary target。Wiki 則主要作為最終服務期玩家可見規則與歷史差異證據使用。

本文件開始從 Kick Vote 擴展到整個 PaperMan gameplay／room／GameRule 核心。目標不是單純整理 opcode，而是恢復「玩家操作 → client state → packet → receive dispatcher → GameRule → 房間／玩家資料 → UI」的完整生命週期。

## 目前已恢復的 GameRule 協定家族

日本版客戶端的封包註冊表中，可以直接看到一組連續的 `GR_*` 操作：

| ID | 封包名稱 | 目前確認狀態 |
|---:|---|---|
| 121 | `GR_MAPCHANGE_REQ` | Client request；目前已找到 1-byte sender |
| 122 | `GR_MAPCHANGE_ACK` | Receiver 已找到，讀取 1-byte |
| 123 | `GR_LEAVE_REQ` | Client sender，無 payload |
| 124 | `GR_LEAVE_ACK` | Receiver 已找到；詳細語意待續追 |
| 127 | `GR_READY_REQ` | Client sender，無 payload |
| 128 | `GR_READY_ACK` | Receiver 已找到；實際 body 不只是單純 status |
| 129 | `GR_START_REQ` | Client sender，1-byte payload |
| 130 | `GR_START_ACK` | Receiver 已找到；詳細語意待續追 |
| 131 | `GR_FORCEOUT_REQ` | Client sender，1-byte payload |
| 132 | `GR_FORCEOUT_ACK` | Receiver 已找到；詳細語意待續追 |
| 133 | `GR_END_REQ` | Client sender，無 payload |
| 134 | `GR_END_ACK` | Receiver 已找到；詳細語意待續追 |
| 135 | `GR_CHANGESLOT_REQ` | Client sender，2-byte payload |
| 136 | `GR_CHANGESLOT_ACK` | Receiver 已找到；詳細語意待續追 |
| 137 | `GR_STARTTIME_REQ` | 註冊表已確認；sender/receiver 待續追 |
| 138 | `GR_STARTTIME_ACK` | 註冊表已確認；sender/receiver 待續追 |
| 189 | `GR_CHANGEMASTER_REQ` | 註冊表已確認；待續追 |
| 190 | `GR_CHANGEMASTER_ACK` | 註冊表已確認；待續追 |

以上名稱與 ID 來自 2016 final Client packet registration；實際 wire body 仍以 serializer/parser 為準，不以名稱猜測。

## 1. `GR_READY_REQ` / `GR_READY_ACK`

### 127 `GR_READY_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v1, 127);
sub_555090(&dword_1321D00, v1);
```

沒有任何 payload writer，因此目前可證明：

```text
127 GR_READY_REQ
payload = 0 bytes
```

發送前的 gameplay wrapper `sub_4320B0()` 先呼叫 `sub_432040()` 檢查目前是否允許操作；成功後才送 127。`sub_432040()` 會檢查 `sub_67D010()` 對應的 player/game state，以及 `sub_548E20(...) == 1`，若不符合會顯示資源訊息並拒絕送出。這表示 Ready 並非單純「按鍵即送封包」，client 有本地狀態門檻。

### 128 `GR_READY_ACK`

註冊後的接收 handler 是：

```text
case 128:
    sub_5626D0(a4)
```

`sub_5626D0()`：

```c
sub_592900(a1, &v6);
sub_592940(v1, &n0x10_1);
```

之後搜尋 16 個 player slot，將 `n0x10_1` 對應至 slot，再：

```c
sub_548B00(&byte_F33120[240780 * i_1], v6);
```

並根據本地玩家與房間模式更新 lobby/player state。這代表 128 的 payload 至少包含：

```text
+0x00  u8
+0x01  u8
```

第二個 byte 可定位 player；第一個 byte 是該玩家狀態值。精確欄位名稱仍待進一步從 `sub_548B00`／caller data-flow 恢復。

因此不能把 `GR_READY_ACK` 簡化成「只有一個成功 byte」。

## 2. `GR_START_REQ` / `GR_START_ACK`

### 129 `GR_START_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 129);
sub_592920(v2, n125);
sub_555090(&dword_1321D00, v2);
```

所以目前確定：

```text
129 GR_START_REQ
+0x00  u8 start_parameter
payload = 1 byte
```

`sub_4320F0()` 是其中一個重要 caller：先確認 `sub_432040()` 成功，再檢查 `sub_67EB70()` 特殊條件，然後透過 `sub_437060(this)` 取得 `n125`，最後送 129。

這表示 `n125` 並非任意常數，而是由目前 lobby/game state 計算出來。接下來應追 `sub_437060()`，這很可能是開始遊戲條件、模式或玩家準備狀態的重要入口。

### 130 `GR_START_ACK`

Receiver：

```text
case 130:
    sub_562870(a4)
```

`sub_562870()` 是一個大型狀態同步 handler，第一個 byte `n2` 決定是否進入主要同步流程；當 `n2 == 1` 時，它會繼續讀取多個 scalar／string／array 欄位，並更新 16 個玩家 slot 的狀態。換言之，130 是一個重要的「開始／遊戲狀態同步」入口，而不是簡單一個 success byte。

在 `n2 == 1` 的分支中，handler 會讀取 player ID、字串資料與其他多個欄位，最後還讀取 16 個 DWORD 並寫入：

```c
dword_F6DD1C[60195 * i] = v46;
```

這顯示開始流程會重新同步整個玩家 slot 狀態。

## 3. `GR_LEAVE_REQ` / `GR_LEAVE_ACK`

### 123 `GR_LEAVE_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v1, 123);
sub_555090(&dword_1321D00, v1);
```

因此：

```text
123 GR_LEAVE_REQ
payload = 0 bytes
```

caller 很有價值：

```text
sub_431580()
 -> sub_562D70()
```

以及其他離開流程也直接呼叫 123。某些路徑會先設定 client UI state 再發送 123。

另有明確分支：

```c
if (*(this + 12) != 0) {
    if (n2_0 == 3)
        sub_562D70();
    else
        sub_562E00();
}
```

也就是在不同 room/game 模式下，client 對「離開／結束」可能使用不同封包：

```text
n2_0 == 3 -> 123 GR_LEAVE_REQ
其他       -> 133 GR_END_REQ
```

這是很重要的架構線索：離開 room 與結束 game 並不是所有情境都使用同一個封包。

### 124 `GR_LEAVE_ACK`

Receiver：

```text
case 124:
    sub_5607C0(a4)
```

目前已確認存在獨立 handler；其完整 state transition 尚待深入。

## 4. `GR_END_REQ` / `GR_END_ACK`

### 133 `GR_END_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v1, 133);
sub_555090(&dword_1321D00, v1);
```

因此：

```text
133 GR_END_REQ
payload = 0 bytes
```

它與 123 的差異不是 body，而是它所處的高階 game state／操作語意。

### 134 `GR_END_ACK`

Receiver：

```text
case 134:
    sub_562EA0(a4)
```

handler 尚待完整追查。

## 5. `GR_FORCEOUT_REQ` / `GR_FORCEOUT_ACK`

### 131 `GR_FORCEOUT_REQ`

Client sender：

```c
Packet::possible_ctor_or_dtor_0(v2, 131);
sub_592920(v2, n0x10);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
131 GR_FORCEOUT_REQ
+0x00 u8 player_or_slot_value
payload = 1 byte
```

這與「指定某個 player/slot 強制移除」的命名一致，但 `n0x10` 究竟是 player ID、slot index 還是經過轉換的值，仍需從 `sub_432270` / `sub_479190` caller 與 player table data-flow 證明。

### 132 `GR_FORCEOUT_ACK`

Receiver：

```text
case 132:
    sub_56ECC0(a4)
```

`sub_56ECC0()` 很值得深入：其 payload 第一個 byte 決定是否繼續，後面有 player ID、字串與其他同步欄位，且會更新 lobby player object。這看起來不像簡單的 request result，而更像「強制移除／玩家資料同步」事件。
