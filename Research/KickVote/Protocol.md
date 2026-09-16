# Kick Vote 協定研究

> 研究日期：2026-09-16

## 證據規則

`[C]` = `PaperMan.exe.c` 直接證據；`[WIKI]` = 日本 Wiki；`[RES]` = 提取資源；`[X]` = 多條證據交叉吻合；`[OPEN]` = 尚未證明。

## 718–723 封包總表

| ID | 名稱 | 方向 | 已證明 Payload |
|---:|---|---|---|
| 718 | `GR_START_VOTING_REQ` | Client → Server | `u32 scope` + `u32 reason_index` + `u32 target_player_id` = 12 bytes |
| 719 | `GR_START_VOTING_ACK` | Server → Client | `u8 status` = 1 byte |
| 720 | `GR_START_VOTING` | Server → Client | `u32 reason` + `u32 applicant_id` + `u32 target_id` + `u32 field3` + `u8 field4` = 17 bytes |
| 721 | `GR_DO_VOTING` | Client → Server | `u8 vote` = 1 byte |
| 722 | `GR_VOTING_RESULT` | Server → Client | `u32 voter_id` + `u8 vote` = 5 bytes |
| 723 | `GR_END_RESULT` | Server → Client | `u8 result` + `u32 player_id` = 5 bytes |

### 外層 framing

送信路徑使用：

```c
Buffers.buf = a2 + 24;
Buffers.len = sub_591F00(a2) + 8;
```

所以以上是邏輯 Payload 大小，不是最終 TCP 封包長度；外層另有 8-byte framing/header。

## 718 `GR_START_VOTING_REQ`

`IVotingNetwork::sub_A191D0`：

```c
Packet::possible_ctor_or_dtor_0(v7, 718);
v4 = sub_592A20(v7, a2);
v5 = sub_592A20(v4, a3);
sub_592A20(v5, a4);
```

三個欄位都透過 4-byte writer `sub_592A20` 寫入，因此不能採信 Hex-Rays 將後兩個參數恢復成 `char` 的 prototype。

```text
+0x00 u32 scope
+0x04 u32 reason_index
+0x08 u32 target_player_id
```

`scope` 來自兩選項狀態，`reason_index` 來自六選項狀態，目標 ID 來自 `CVoteTargetList`。

目前行為層面的 mapping：

```text
0 = チームキック
1 = 全体キック
```

這個 mapping 有 Wiki + C + target-list filtering 的強交叉證據，但原始內部 enum 名稱仍未恢復。

## 719 `GR_START_VOTING_ACK`

接收端：

```c
case 719:
    sub_592940(a2, &v21);
    (*(*this + 12))(this, v21);
```

因此 payload 嚴格是：

```text
+0x00 u8 status
```

目前發現同一 voting code 區域存在 `sub_A19380(int)`，會處理 `0..3` 並產生不同 UI 狀態，但其是否就是 vtable `+12` 的 concrete implementation 尚未直接從匯出的 vtable table 封死，因此 enum 語意維持 `[OPEN]`。

## 720 `GR_START_VOTING`

接收：

```c
case 720:
    v3 = sub_592A40(a2, &v17);
    v4 = sub_592A40(v3, &v19);
    v5 = sub_592A40(v4, &v20);
    v6 = sub_592AC0(v5, &v18);
    sub_592940(v6, &v16);
    (*(*this + 8))(this, v17, v20, v19, v18, v16);
```

因此：

```text
+0x00 u32 reason_index
+0x04 u32 applicant_player_id
+0x08 u32 target_player_id
+0x0C u32 field3
+0x10 u8  field4
```

### 前三欄

`sub_A19460` 直接將第一欄送入 `sub_A19090` 作為 reason；第二欄保存為 applicant ID，並與本地 player ID 比較；第三欄保存／解析為目標 ID。這三欄可視為高可信固定語意。

### 第四欄

`field3` 進入 `sub_A17130(..., a5)`，寫入 Voter 的 +20；`sub_A17380` 再以經過時間扣減該值，UI 又將相同剩餘值傳給 `Vote_Digit` 並除以 1000 顯示。因此它實際上是 **毫秒級投票倒數／持續時間**。

Wiki 的公開規則是 70 秒，所以相容 Server 的自然值為：

```text
70000 ms
```

但目前沒有從 C literal 直接恢復 `70000`，所以應標記為 Wiki + C 推導值，而不是 binary literal。

### 第五欄

`field4` 是 scope/eligibility 相關的控制 byte：當它為 0 時，client 會經過 `CVoteTargetList` 相關 virtual path 取得額外 eligibility 結果，再送進 `CVotingStateUI`。精確 enum／原始 symbol 尚未封閉，維持 `[OPEN]`。

## 721 `GR_DO_VOTING`

`IVotingNetwork::sub_A192B0`：

```c
Packet::possible_ctor_or_dtor_0(v5, 721);
sub_5928E0(v5, a2);
```

因此：

```text
+0x00 u8 vote
```

`sub_A1A9D0` 對相同 byte 做計票：

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

因此目前 client 端語意為：

```text
0       = NO
nonzero = YES
```

## 722 `GR_VOTING_RESULT`

接收 parser：

```c
case 722:
    v7 = sub_592A40(a2, &v15);
    sub_592900(v7, &v14);
    (*(*this + 16))(this, v15, v14);
```

進入 `sub_A1A9D0` 後：

```text
+0x00 u32 voter_player_id
+0x04 u8 vote
```

而 `0 / nonzero` 分別累積 NO / YES。這是目前最乾淨的「封包寬度 + 欄位來源 + 實際使用」三重證據之一。

## 723 `GR_END_RESULT`

接收 parser：

```c
case 723:
    v9 = sub_592900(a2, &v12);
    sub_592A40(v9, &v13);
    (*(*this + 20))(this, v12, v13);
```

所以：

```text
+0x00 u8 result/state
+0x01 u32 player_id
```

`player_id` 被 `IVotingNetwork::sub_A19770` 當作玩家身份資料繼續解析；第一 byte 被送入 `sub_A17180`。值 `1` 在 local-target 路徑有特殊處理，但目前仍不能單憑此命名為 `KICKED` 或 `SUCCESS`。

## Vote lifecycle

```text
Client
  |
  | 718
  v
Server
  |
  | 719 status
  | 720 reason/applicant/target/duration/control
  v
All clients
  |
  | 721 vote
  v
Server
  |
  | 722 voter_id + vote
  v
All clients
  |
  | ...直到 Server 決定結束...
  |
  | 723 result + player_id
```

### 尚未封閉

- 719 的完整 status enum。
- 720 field4 的原始語意。
- 723 result byte 的完整 enum。
- timeout 與「未投票」的 Server 計票演算法。
- 成功後實際踢除與 396/397 的跨層關聯。
