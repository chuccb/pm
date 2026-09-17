# Kick Vote 協定研究

> 研究日期：2026-09-17
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Kick Vote 的 packet／wire protocol 主文件；UI 狀態與資格證據分別由 `UI_State.md` 與 `Evidence_And_Eligibility.md` 維護。

## 證據規則

`[C]` = `PaperMan.exe.c` 直接證據；`[WIKI]` = 日本 Wiki；`[RES]` = 提取資源；`[X]` = 多條證據交叉吻合；`[OPEN]` = 尚未證明。

## 718–723 封包總表

| ID | 名稱 | 方向 | 已證明 Payload |
|---:|---|---|---|
| 718 | `GR_START_VOTING_REQ` | Client → Server | `u32 scope` + `u32 reason_index` + `u32 target_player_id` = 12 bytes |
| 719 | `GR_START_VOTING_ACK` | Server → Client | `u8 status` = 1 byte |
| 720 | `GR_START_VOTING` | Server → Client | `u32 reason` + `u32 applicant_id` + `u32 target_id` + `u32 duration` + `u8 control` = 17 bytes |
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
if ( sub_A17340(this - 48, a2) != 3 )
    return 0;
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

`scope` 來自兩選項狀態，`reason_index` 來自六選項狀態，目標 ID 來自 `CVoteTargetList`。[C]

行為上的 `scope=0/1` 對應 Team／Full Kick 由 `Evidence_And_Eligibility.md` 統一維護；本文件只保留 wire 層與 serializer 證據，避免重複第二份資格模型。[X]

更深一層：`sub_A17340()` 並非單純查詢；只有 `sub_A17290()` 回傳 `3` 才繼續，而且成功時會先把 Voter `+28 = 1`。因此 `+28` 應視為 request/active-lock-like state，精確原始名稱仍 `[OPEN]`。[C]

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

更進一步，`IVotingNetwork::sub_A19380(int)` 位於同一 voting network concrete class，行為上直接處理 `0..3`：

```text
0 -> 清除 message/UI pulse，保留 active flow
1 -> message resource 878，保留 active flow
2 -> message resource 880
3 -> message resource 879
```

其函式 signature 與 719 dispatcher 的單一 `int` virtual-call 形狀吻合，因此 **719 → `sub_A19380` 已達很高 confidence 的 concrete dispatch mapping**；但 `0/1/2/3` 的產品層 enum 名稱與 878/879/880 的日文 literal 仍 `[OPEN]`，不得直接命名成 `SUCCESS` / `DENIED` 等。[C][OPEN]

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
+0x0C u32 duration
+0x10 u8  control
```

### 前三欄

`sub_A19460` 直接將第一欄送入 `sub_A19090` 作為 reason；第二欄保存為 applicant ID，並與本地 player ID 比較；第三欄保存／解析為目標 ID。這三欄可視為高可信固定語意。[C]

### 第四欄：duration

`duration` 進入 `sub_A17130(..., a5)`，成為 Voter `+20`；`sub_A17380(elapsed)` 再以經過時間扣減並 clamp 至 0；`VoterMgr::sub_A19940` 將剩餘值送到 `CVotingStateUI`，UI 再以 `remaining / 0x3E8u` 形成秒數顯示。[C]

因此：

```text
720 +0x0C = voting duration / remaining timer
unit = millisecond scale
```

日本 Wiki 公開規則為 70 秒。由此得到的 `70000 ms` 是 **Wiki + Client 行為的相容性推導值**，不是目前找到的 `70000` binary literal。[WIKI][C][X]

### 第五欄：control

這裡有一個重要修正。

`sub_A19460` 中：

```c
*(this - 32) = a6;
v19 = *(this - 32);

v25 = 1;
if ( v19 == 0 )
{
    v18 = *(this - 40);      // applicant
    v25 = (*(**(this + 12) + 28))(*(this + 12), v18);
}
```

所以：

```text
field4 == 0
    -> 額外執行 applicant eligibility/predicate virtual call
field4 != 0
    -> 不執行該 predicate，v25 保持 1
```

之後：

```c
sub_A1A830(..., applicant == local_player, v25);
```

而 `sub_A1A830()` 將最後一個參數寫入 `CVotingStateUI +91`。

因此 **舊研究中「`+91 <- 720 final byte`」是錯的，已修正**：

```text
720 field4 !=直接等於 CVotingStateUI +91
720 field4 -> 決定是否執行 applicant predicate
CVotingStateUI +91 -> predicate result (v25)
```

`field4` 的 wire semantic 仍未完全封閉，目前最準確命名應為：

> **applicant-eligibility control byte / predicate-gating byte** `[OPEN]`

不能把它直接命名成 `isApplicant`、`isVoter` 或 scope enum。

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

因此目前 Client aggregation 語意為：

```text
0       = NO
nonzero = YES
```

這裡的 `nonzero = YES` 是 Client branch semantics；Server 仍應獨立限制允許的 wire values。

## 722 `GR_VOTING_RESULT`

接收 parser：

```c
case 722:
    v7 = sub_592A40(a2, &v15);
    sub_592900(v7, &v14);
    (*(*this + 16))(this, v15, v14);
```

所以：

```text
+0x00 u32 voter_player_id
+0x04 u8 vote
```

`IVotingNetwork::sub_A19890` 先把 voter ID 轉交 player-side state，再呼叫 `sub_A1A9D0`；後者明確累積 YES / NO counter。這使 722 的「wire width + voter identity + vote aggregation」鏈條完整閉合。[C]

若收到的是 applicant/local player，自身 UI 邏輯還有額外分支；不要把一般 voter 與 applicant result path 合併成同一 state transition。

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
+0x00 u8 result_state
+0x01 u32 player_id
```

`IVotingNetwork::sub_A19770`：

```c
*(this - 40) = a3;                  // player_id
*(this - 17) = (a3 == local_id);    // target/local identity flag
sub_A17180(this - 48, a2);          // result byte
```

`sub_A17180` 會：

```text
保存 result byte 到 Voter +44
若 target/local 且 result == 1 -> +24 = 3000
清除 +29 / +32 voting-active state
```

接著只有在 player-side virtual lookup 成功時，才呼叫 `sub_A1A970()` 更新結果 UI；其後 `sub_A18F80(..., 0)` 進行 voting UI cleanup。[C]

因此目前已能更精確地說：

> **723 在此 Client 上的直接可觀察責任是「final result → Voter/UI state transition + cleanup」，不是已證明的「直接修改 room/player occupancy」。**

目前在這條 723 → `sub_A19770` → `sub_A1A970` / `sub_A18F80` chain 中沒有看到直接構造 `396 PM_KICKUSER_REQ` 的證據，所以兩者仍不能直接視為同一 packet。[C][OPEN]

`result_state` 的 literal enum 仍 `[OPEN]`；尤其值 `1` 雖在 local-target path 有特殊 3000ms transition，但不足以單獨命名成 `SUCCESS` / `KICKED`。

## 139 voting lifecycle signal

`VoterMgr::sub_A19A70()` 建立並送出 opcode 139，然後設定：

```c
byte_2317C68 = 1;
```

而 `sub_A17380()` 的部分 countdown/phase update 只有在 `byte_2317C68 == 0` 時才繼續。因此 139 明顯屬於 voting lifecycle/control path，但目前尚不能把它正式命名成 `END_VOTE`、`CANCEL_VOTE` 或其他具體 enum。[C][OPEN]

## 396 / 397 分層

目前 Client registration/dispatcher 證據將：

```text
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
```

放在 Master/Room protocol family：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397 的 receive dispatcher：

```c
case 397u:
    sub_58E410(a1, a4);
```

`sub_58E410()` 讀一個 status byte，對 `0/1/2/default` 走不同 message/resource branch；因此：

```text
397 payload = u8 status
```

396 的 request body 仍未找到直接 serializer/caller，因此不要猜 body。[C][OPEN]

## Vote lifecycle

```text
Client UI
  |
  | 718 scope/reason/target
  v
Server
  |
  +--> 719 status
  +--> 720 reason/applicant/target/duration/control
           |
           +--> local eligibility / UI state
           +--> 721 voter submission
           +<-- 722 voter result
           +--> 723 final result/state
                    |
                    +--> Voter/UI cleanup
                    +--> [actual room/player kick still unresolved]
```

### 尚未封閉

- 719 的 `0..3` 產品層 enum / localization literals。
- 720 field4 的最終 server-side semantic / allowed values。
- 723 result byte 的完整 enum 與 server final-action contract。
- timeout、missing vote、early-end 與 Server 的正式計票演算法。
- 723 後真正的 room/player removal function。
- 396 request 的 body 與 caller。
- 718–723 與 396/397 是否在 server-side convergent action 匯合。
