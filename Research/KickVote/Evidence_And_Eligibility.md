# Kick Vote — Eligibility／State／Protocol 證據帳

> 研究日期：2026-09-17
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：Kick Vote 的資格、狀態與跨來源證據主文件；`Protocol.md` 維護 718–723 的 wire protocol，`UI_State.md` 維護 UI 與狀態機，`Master_Room.md` 維護 131/132 與 396/397 的 Master／Room 分層。

## 研究範圍

本文件保存從 `PaperMan.exe.c` 恢復出的 Kick Vote 深入證據鏈，重點是 voter／target eligibility、狀態欄位、跨來源驗證，以及後續 Server reconstruction 所需的邊界。

證據來源：

```text
IDA / Hex-Rays C / LST / ASM
        ↕
Extracted 資源
        ↕
日本 PaperMan Wiki
```

未知資訊保持 `[OPEN]`。不得只依 packet 名稱、Hex-Rays 表面型別或 UI 名稱猜測協定語意。

## 1. 718 request 在序列化前會先經過資格閘門

### 程式路徑

```text
IVotingNetwork::sub_A191D0
    -> sub_A17340(this - 48, scope)
        -> sub_A17290(Voter, scope)
    -> 只有 result == 3 時：
        Packet ctor(opcode=718)
        write DWORD scope
        write DWORD reason
        write DWORD target_player_id
        send
```

### `sub_A17290`

```c
if ( *(this + 28) == 1 )
    return 0;
if ( *(this + 32) == 1 )
    return 1;

v4 = a2 == 0 && *(this + 36) >= 2;
v3 = a2 == 1 && *(this + 40) >= 2;
if ( v4 || v3 )
    return 3;
return 2;
```

### 直接可確認的內容

```text
scope 0 -> 候選／計數欄位 +36 必須 >= 2
scope 1 -> 候選／計數欄位 +40 必須 >= 2
+28 == 1 -> request 因既有狀態被拒絕
+32 == 1 -> 特殊提前返回；精確生命週期語意仍 [OPEN]
```

`sub_A17340()` 並非單純查詢：preflight 成功時，它會在 718 序列化前先設定 `+28 = 1`。因此 `+28` 可安全視為 request／active-lock-like state，但原始語意名稱仍 `[OPEN]`。[C]

不要把 Server 規則簡化成只有 `players >= 3`。Client 先建立候選／計數狀態，再以該衍生狀態作為 request gate；`+36/+40` 不能直接命名成房間總人數。[C]

日本 Wiki 的 Team Kick／Full Kick 最低參與人數規則為 3 人；Client 內部比較為 `>= 2`，表示其計數域至少排除了某個 local／role 維度。[WIKI][C][X]

## 2. Scope mapping 是行為交叉驗證，不只是 enum 猜測

Client UI 有兩個 scope 選項；日本 Wiki 將其命名為：

```text
チームキック
全体キック
```

target-list code 使用相同的兩種邏輯模式，並把各自衍生的候選統計送入 718 preflight。因此目前高信度行為 mapping 為：

```text
scope=0 -> Team Kick
scope=1 -> Full Kick
```

原始內部 enum 名稱仍未恢復。[C][WIKI][X]

## 3. 候選列表與 voter eligibility 是不同集合

`CVoteTargetList::sub_A17450(mode)` 會重建 36-byte target record。

`sub_A177C0()` 遍歷 player list 時同時追蹤：

```text
所有 non-local candidates
符合 sub_67DDD0() 的 candidates
```

並明確排除 local player。

`sub_67DDD0(slot)`：

```c
if ( slot >= 0x10 )
    return false;
if ( sub_67EB70() )
    return true;
v2 = sub_67D520(slot);
return v2 == sub_67D240();
```

因此 candidate eligibility 至少包含：

```text
16-slot domain
+ player/session-state comparison
```

`sub_67D520()`、`sub_67D240()` 尚需與更大的 player/session subsystem 對應，才能建立更具體的公開語意名稱。[C][OPEN]

## 4. 本地重複投票鎖定是真實的 Client state

`sub_A1A6D0()`：

```c
return *(this + 32) == 1
    && *(this + 29) == 1
    && *(this + 30) == 0;
```

`Voter::sub_A171F0()`：

```c
if ( *(this + 29) == 0 )
    return 0;
*(this + 30) = 1;
return 1;
```

因此可確認：

```text
+29 = 當前 local voting eligibility/state
+30 = local player 已經投票
```

這證明同一 voting state 存在本地 second-vote lock；並不代表 Server 應信任 Client，Server 仍必須獨立拒絕重複投票。[C]

## 5. 721 與 722 的 vote byte 語意已閉合

721 serializer：

```text
+0x00 u8 vote
```

722 parser：

```text
+0x00 u32 voter_player_id
+0x04 u8 vote
```

`sub_A1A9D0`：

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

因此 Client aggregation 語意為：

```text
0       -> 反對
nonzero -> 贊成
```

這是 Client branch semantics；允許的實際 wire value 範圍仍應由 Server 自行驗證。[C]

## 6. 720 第四個 DWORD 是毫秒尺度計時值

720 解析順序：

```text
u32 reason
u32 applicant_id
u32 target_id
u32 duration
u8  control
```

`duration` 進入 `sub_A17130(..., duration)` 成為 Voter countdown value；`sub_A17380(elapsed)` 扣減經過時間並 clamp 至 0；`VoterMgr::sub_A19940()` 再把剩餘值送入 `CVotingStateUI`。

UI 以：

```text
remaining / 0x3E8u
```

形成秒數顯示。因此：

```text
720 field3 = voting duration / remaining timer
unit = millisecond scale
```

日本 Wiki 公開規則為 70 秒，因此相容 Server 可採用：

```text
70000 ms
```

但這是 Wiki + Client 行為推導，不是目前直接找到的 `70000` binary literal。[C][WIKI][X]

## 7. 720 最後一個 byte 是 applicant predicate 的控制項，不是 StateUI +91

`sub_A19460()`：

```c
*(this - 32) = field4;
v25 = 1;
if ( *(this - 32) == 0 )
{
    v18 = *(this - 40); // applicant id
    v25 = (*(**(this + 12) + 28))(*(this + 12), v18);
}
```

之後：

```c
sub_A1A830(
    StateUI,
    reason,
    target_display,
    applicant_display,
    duration,
    applicant == local_player,
    v25
);
```

`sub_A1A830()` 將最後一個參數寫入 `CVotingStateUI +91`。

因此正確模型為：

```text
720 field4 == 0
    -> 執行 applicant-id eligibility/predicate virtual call
    -> v25 = predicate result

720 field4 != 0
    -> 跳過 predicate
    -> v25 保持 1

StateUI +91
    -> predicate result
```

這修正了舊研究中的錯誤映射：

```text
錯誤：StateUI +91 <- 720 field4
正確：720 field4 -> predicate gate；StateUI +91 <- predicate result
```

`field4` 的精確 Server-side 語意與允許值仍 `[OPEN]`。目前最安全的暫名是 `applicant-eligibility control byte / predicate-gating byte`，不可直接命名為 `isApplicant`、`isVoter` 或 scope enum。[C][OPEN]

## 8. Applicant identity、voter eligibility 與 UI state 是獨立概念

`sub_A1A830()` 保存：

```text
+88 <- applicant == local_player
+91 <- applicant predicate result (v25)
```

同時 `VoterMgr::sub_A19940()` 更新：

```text
StateUI +92 <- sub_A1A6D0()     // local voting-able state
StateUI +93 <- active/display-update condition
```

因此 Client 明確區分：

```text
我是 applicant
Applicant / target 相關 predicate 結果
我目前是否能投票
我是否已投票
目前 voting UI 是否正在更新
```

Server state model 不應把這些條件壓成單一 boolean。[C]

## 9. 719 concrete dispatch 已達高信度

Parser：

```c
case 719:
    sub_592940(a2, &v21);
    (*(*this + 12))(this, v21);
```

同一 `IVotingNetwork` concrete class 定義：

```c
IVotingNetwork::sub_A19380(int status)
```

其行為：

```text
0 -> 清除 UI pulse/state，保留 active-flow marker
1 -> message 878，保留 active-flow marker
2 -> message 880
3 -> message 879
```

單一 `int` 參數與 719 dispatcher 的 virtual-call 形狀一致，且位於同一 concrete implementation 區域，因此：

```text
719 -> sub_A19380
```

可視為高信度 concrete dispatch mapping。[C]

尚未閉合的是 `0..3` 的產品層 enum 與 878/879/880 的日文 localization literal。[OPEN]

## 10. 3000 ms 與 70 秒投票時限是不同層級

Client 中另有：

```c
Voter::sub_A17180:
    *(this + 24) = 3000;

CVotingStateUI result/phase path:
    *(this + 76) = 3000;
```

這些屬於 local result／approval／UI phase，而非 720 的 voting-duration DWORD。不能將 3000 ms 視為 70 秒投票逾時的一部分。[C]

## 11. 723 result byte 目前必須保持未命名

Parser：

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770()`：

```text
player_id -> Voter identity
result byte -> sub_A17180()
```

`sub_A17180()` 保存 result byte、清除 voting-active state，並在 local-target + `result == 1` 條件下啟動獨立的 3000 ms Voter phase。

之後 `sub_A19770()` 只有在 player-side lookup 成功時才呼叫 `sub_A1A970()` 做結果呈現，再由 `sub_A18F80(..., 0)` 做 voting UI cleanup。

所以目前能確定的是：

```text
723
  -> Voter result state mutation
  -> optional player lookup / result UI
  -> cleanup
```

尚不能從這條 Client chain 宣稱它直接修改 room occupancy 或移除 player。[C]

## 12. 139 是 voting lifecycle/control signal，但具體語意仍開放

`VoterMgr::sub_A19A70()`：

```c
Packet::possible_ctor_or_dtor_0(v1, 139);
sub_58D7D0(byte_13242F8, v1);
byte_2317C68 = 1;
```

`sub_A17380()` 只有在 `byte_2317C68 == 0` 時才繼續某段 result／phase countdown update。

因此 139 確實屬於 voting lifecycle/control path，但目前證據不足以命名成 `END_VOTE`、`CANCEL_VOTE` 或其他具體 enum。[C][OPEN]

## 13. 396 / 397 是獨立的 Master／Room protocol family

Client registration／dispatcher 顯示：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397：

```c
case 397u:
    sub_58E410(a1, a4);
```

`sub_58E410()` 讀取一個 status byte，並依 `0/1/2/default` 進入不同 message/resource branch，因此：

```text
397 payload = u8 status
```

目前完整 `PaperMan.exe.c` 中仍未找到 396 的直接 serializer/caller，因此其 request body 保持未知。[C][OPEN]

723 → `sub_A19770` → `sub_A1A970` / `sub_A18F80` 的 chain 中，也沒有直接構造 396 的證據。[C]

## 14. 目前證據圖

```text
Wiki
  |
  | mode / reasons / 70 sec / min participants
  v
Client UI
  |
  | scope / reason / target selection
  v
CVoteTargetList
  |
  | candidate records + player/session eligibility
  v
Voter
  |
  | request preflight + active-vote state
  v
718
  |
  v
Server
  |
  +--> 719 status
  +--> 720 reason/applicant/target/duration/control
           |
           +--> applicant predicate gate
           +--> timer / UI state
           +--> 721 vote
           +<-- 722 voter result
           +--> 723 final result
                    |
                    +--> Voter result state
                    +--> UI result/cleanup
                    +--> [actual kick/removal unresolved]

Separate:
Room/Master
   |
   +--> 396 PM_KICKUSER_REQ
   +<-- 397 PM_KICKUSER_ACK
```

## 15. Server reconstruction 所需的最低概念模型

Kick Vote 至少應分離：

```text
KickVoteSession
  scope
  reason_index
  applicant_player_id
  target_player_id
  duration_ms
  control
  eligible_voter_set
  submitted_votes
  yes_count
  no_count
  started_at
  ended_at
  result_state
```

另外獨立保存：

```text
Room / Master kick operation
  request body
  requester/master identity
  target identity
  ACK status
```

在 Client call graph 未證明兩者匯合前，不應把所有行為壓成單一 `Kick()` 操作。

## 16. 目前最高價值的後續追查

```text
A. 719
   localization 878/879/880
   -> 完整使用者可見狀態語意

B. 720 field4
   -> Server 來源
   -> 所有可能值
   -> concrete virtual predicate 的真實語意

C. 723
   -> result enum
   -> voting subsystem 外的 target state mutation
   -> 實際 kick / removal side effect

D. 396
   -> 所有 opcode metadata / indirect packet construction
   -> 確認 Client 是否實際主動送出

E. sub_67D520 / sub_67D240
   -> 完整 player/session state comparison
   -> candidate / voter eligibility 語意

F. localization / resource store
   -> 878 / 879 / 880
   -> 892 / 893
   -> 0x369 / 0x36A
   -> 0x373..0x379
```
