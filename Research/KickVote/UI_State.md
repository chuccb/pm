# Kick Vote UI 與狀態機研究

> 研究日期：2026-09-16
> 目標版本：日本版 PaperMan 2016 年服務終了時 Client

## UI 類別結構

`VoterMgr::sub_A19B10` 建立並連接：

```text
CVotingApprovalUI = 0x08 bytes
CVotingStateUI    = 0xE8 bytes
CVotingTargetUI   = 0x28 bytes
CVoteTargetList   = 0x20 bytes
```

投票不是單一 popup；target list、target selection、active voting state、approval UI 與 Voter state 共同構成子系統。

## 輸入狀態

`sub_A1A090(this, n10)` 依 `CVotingTargetUI` 內部 state 分流：

```text
state 0
  兩個 scope 選項

state 1
  六個 reason 選項

state 2
  target list
  一次最多顯示 8 個 target
  超過 8 個可翻頁
```

Client 內部 target-page command 使用值 `10`；日本 Wiki 的玩家操作是按 `0` 翻頁。因此 UI key 與內部 command value 是不同層，不可直接混用。

## Scope resource

`CVotingTargetUI::sub_A1C2E0` state 0 使用：

```text
892 -> option 1
893 -> option 2
```

結合 Team/Full candidate filtering 與日本 Wiki，行為 mapping 高可信：

```text
0 = チームキック
1 = 全体キック
```

但目前尚未從 localization store 直接恢復 892/893 的最終日文 literal。

## Reason resource

Reason selection state 使用：

```text
883, 884, 885, 886, 887, 888
```

Active voting display 使用另一組 resource IDs：

```text
0x373, 0x374, 0x375, 0x376, 0x377, 0x378
```

不要假定這兩組 ID 一一相等。

Wiki 的六項理由：

```text
チート行為
ゲームプレイ妨害
悪口、荒らし行為
キャラクター放置
アビューズ行為
その他違反行為
```

## Approval UI

`CVotingApprovalUI::sub_A18B90`：

```text
0x369 -> option 1
0x36A -> option 2
```

並格式化成：

```c
L"1. %s"
L"2. %s"
```

這是 vote approval 層，不是 892/893 的 scope selector。

## Target list 與 eligibility

`CVoteTargetList` 保存 36-byte records。`sub_A17450(mode)` 重建候選列表；`mode=0/1` 對應兩種 scope 的不同候選集合。

`sub_A177C0()` 遍歷 player list 時：

```text
排除 local player
統計全部 non-local candidate
另統計通過 sub_67DDD0() 的 candidate
```

`sub_67DDD0(slot)` 至少要求：

```c
if ( slot >= 0x10 )
    return false;
if ( sub_67EB70() )
    return true;
return sub_67D520(slot) == sub_67D240();
```

所以 candidate eligibility 不是單純 `player exists` 或 `room count`；至少包含 16-slot domain 與 player/session state comparison。

## 718 preflight 與 UI/state 的連接

`IVotingNetwork::sub_A191D0` 在建立 opcode 718 前先呼叫 `sub_A17340`，再進 `sub_A17290`。Client 直接使用：

```text
scope 0 -> Voter +36 >= 2
scope 1 -> Voter +40 >= 2
```

只有 preflight 成功才會真的建立 718，而且 `sub_A17340()` 成功時會先將 `Voter +28 = 1`。因此 `+28` 不只是資訊欄位，而是 request/active-lock-like state；精確原始名稱仍未恢復。

## Voter lifecycle flags

`sub_A17130()` 啟動 active vote state：

```c
*(this + 31) = 0;
*(this + 44) = 0;
*(this + 24) = 0;
*(this + 20) = duration;
*(this + 29) = eligibility;
*(this + 32) = 1;
*(this + 30) = 0;
```

`sub_A17180()` 結束/更新 result state：

```c
*(this + 44) = result;
if ( *(this + 8) == *(this + 12) && result == 1 )
    *(this + 24) = 3000;
*(this + 29) = 0;
*(this + 32) = 0;
```

初始/重置 `sub_A17220`：

```text
+28 = 0
+29 = 0
+30 = 0
+31 = 0
+32 = 0
+8  = -1
```

`sub_A171F0`：

```c
if ( *(this + 29) == 0 )
    return 0;
*(this + 30) = 1;
return 1;
```

因此 `+30` 是本地 already-voted flag，而 `+29` 是該時點的 local voting eligibility/active state。

## Re-press / invalid-state handling

`VoterMgr::sub_A1A4A0()` 額外區分數種狀態：

```text
+31 == 1
    -> reject

Voting environment invalid (`sub_A18F20()`)
    -> reject

VotingAble() == true
    -> local vote / toggle path

+32 == 1 && +29 == 1 && +30 == 1
    -> UI message resource 878
    -> reject repeated vote operation

+32 == 1 && +29 == 0 && +56 != +12
    -> UI message resource 880
    -> reject

+52 == 0 or candidate-list check succeeds
    -> continue via sub_A18F50

otherwise
    -> UI message resource 879
    -> reject
```

這表示「已投票」「當前可投票」「投票流程 active」「候選列表是否可接受」是獨立條件；Server state model 不應壓成單一 boolean。

## 719 status dispatch

`GR_START_VOTING_ACK`：

```text
payload = u8 status
```

接收 virtual dispatch 的單一參數與 `IVotingNetwork::sub_A19380(int)` 對應度很高。`sub_A19380()`：

```text
status 0 -> 清掉 UI pulse，active-flow flag 保留
status 1 -> message 878，active-flow flag 保留
status 2 -> message 880
status 3 -> message 879
```

因此現在可把：

```text
719 -> IVotingNetwork::sub_A19380
```

視為高 confidence concrete dispatch mapping。

但 `0/1/2/3` 的產品層 enum 名稱，以及 878/879/880 對應的最終日文訊息仍 `[OPEN]`。

## Vote aggregation

`sub_A1A9D0`：

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

所以 Client aggregation：

```text
0       = NO
nonzero = YES
```

若 caller 代表 local applicant，`sub_A1A970` 另有 applicant-result UI 狀態。這表示 applicant 與一般 voter 的 UI/result state machine 有分支差異。

## Active vote state

720 parser 的欄位：

```text
u32 reason
u32 applicant_id
u32 target_id
u32 duration
u8  control
```

第四個 DWORD 進入 Voter timer；`sub_A17380(elapsed)` 每次扣減並 clamp 0。`VoterMgr::sub_A19940` 再把剩餘值送到 `CVotingStateUI`。

`CVotingStateUI` 顯示 path 以：

```c
remaining / 0x3E8u
```

形成 `Vote_Digit` 的秒數，所以 duration 是 millisecond-scale。

日本 Wiki 為 70 秒，因此 server compatibility 值可推導為：

```text
70000 ms
```

這仍是 Wiki + Client behavior inference，不是目前找到的 C literal。

## 720 control 與 State UI 的修正

舊結論：

```text
+91 <- 720 final byte
```

已證明錯誤。

`sub_A19460()` 的實際鏈條：

```text
720 field4
   |
   +-- == 0 --> call virtual predicate with applicant ID
   |             -> v25 = predicate result
   |
   +-- != 0 --> skip predicate
                 -> v25 remains 1

v25 -----------------> CVotingStateUI::sub_A1A830(..., a7=v25)
                           |
                           +--> UI +91 = v25
```

同一時間 `sub_A1A830()` 另存：

```text
+88 = applicant == local player
+17 = duration
+91 = eligibility predicate result (v25)
```

而 `VoterMgr::sub_A19940()` 在 update path 將：

```text
StateUI +92 = sub_A1A6D0()
StateUI +93 = active/display-update condition
```

所以目前正確模型是：

```text
720 field4
    = applicant-eligibility predicate gating/control byte [OPEN]

StateUI +91
    = predicate result

StateUI +88
    = applicant-is-local
```

不能把 field4 直接命名成 `isApplicant`、`isVoter` 或 `result`。

## 3000 ms 是另一層

`sub_A17180()` 在 local-target/result condition 下將 Voter `+24` 設為 `3000`；`CVotingStateUI::sub_A1B900()` 也有獨立 `+76 = 3000` result/phase timer。

這些 3000ms timers 不可與 720 的 voting duration 混淆。

## 139 lifecycle signal

`VoterMgr::sub_A19A70()`：

```c
Packet::possible_ctor_or_dtor_0(v1, 139);
sub_58D7D0(byte_13242F8, v1);
byte_2317C68 = 1;
```

而 `sub_A17380()` 只有在 `byte_2317C68 == 0` 時才更新某段 result/phase countdown，因此 139 與 voting lifecycle/control 明確相關。

精確 semantic 仍 `[OPEN]`，不先命名成 `END_VOTE` / `CANCEL_VOTE`。

## 723 result

`GR_END_RESULT (723)`：

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770()`：

```text
player_id -> Voter identity
result byte -> sub_A17180()
```

`sub_A1A970()` 只處理 UI-side result presentation data，之後 `sub_A18F80(..., 0)` 做 voting UI cleanup。

因此目前能確定的是：

```text
723
  -> result state mutation in Voter
  -> optional player lookup / result UI
  -> cleanup
```

尚不能從這條 Client chain 宣稱它直接移除 room/player。

## State machine

```text
Idle
 |
 +-- Kick Vote input
 v
Scope Selection (2)
 |
 v
Reason Selection (6)
 |
 v
Target Selection (<=8/page)
 |
 | candidate/session eligibility
 v
718 Request
 |
 +--> 719 requester status
 |
 +--> 720 active vote
          |
          +--> applicant predicate / UI state
          +--> countdown
          +--> 721 vote
          +<-- 722 voter result
          +--> 723 final result
                    |
                    +--> Voter result state
                    +--> UI cleanup
                    +--> [actual room/player kick unresolved]
```

## Evidence status

### Direct / high confidence

- UI class sizes and composition.
- Two scope options and six reasons.
- Target list records are 36-byte entries.
- Candidate enumeration excludes local player.
- Candidate eligibility reaches player/session state.
- 718 request is gated by Voter state and successful preflight sets `+28`.
- 719 status payload is one byte; `sub_A19380` is a high-confidence concrete target for the corresponding single-argument network dispatch.
- 721/722 vote field is a byte; client aggregation uses zero vs nonzero.
- 720 fourth field is millisecond-scale timer.
- 720 final byte gates an applicant predicate; it is not directly copied to StateUI +91.
- applicant identity and voting eligibility are independent state.
- local duplicate-vote state exists.
- 723 direct Client responsibility is result/UI state transition, not yet proven room occupancy mutation.

### Cross-source

- scope `0/1` maps behaviorally to Team/Full Kick.
- 70 seconds maps to `70000 ms` for a compatibility implementation.
- Wiki's six reasons correspond to the six reason-selection entries.
- Wiki's minimum-participant rule matches the Client preflight behavior after accounting for the Client's internal count domain.

### Open

- 719 status `0..3` product semantics / localization.
- 720 control byte final server semantic and allowed values.
- 723 result enum and server-side final-action contract.
- 139 lifecycle semantic.
- `sub_67D520` / `sub_67D240` player/session semantics.
- complete server-side voter set, timeout, missing-vote, early-end and final kick action.
- localization literals for 878/879/880 and 892/893.
