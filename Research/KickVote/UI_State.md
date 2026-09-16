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

只有 preflight 成功才會真的建立 718。這是 UI selection → Voter state → packet serialization 的實際資料流。

## Voter lifecycle flags

`sub_A17180` 可觀察到：

```c
*(this + 44) = a2;
if ( *(this + 8) == *(this + 12) && *(this + 44) == 1 )
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

因此 `+30` 是本地 already-voted flag，而 `+29` 是該時點的 local voting state/eligibility flag。

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

若 caller 代表 local applicant，`sub_A1A970` 還會把非零 vote 保存至另一個 local-result flag，顯示 applicant 與一般 voter 的結果處理存在差別。

## Active vote state

720 parser 的欄位：

```text
u32 reason
u32 applicant_id
u32 target_id
u32 duration_ms
u8  control
```

第四個 DWORD 進入 Voter timer；`sub_A17380(elapsed)` 每次扣減並 clamp 0。`VoterMgr::sub_A19940` 再把剩餘值送到 `CVotingStateUI`。

`CVotingStateUI::sub_A1BF30` 以：

```c
remaining / 0x3E8u
```

送入 `Vote_Digit`，所以它是 millisecond-scale vote duration/remaining time。

日本 Wiki 為 70 秒，因此 server compatibility 值可推導為：

```text
70000 ms
```

這仍是 Wiki + Client behavior inference，不是目前找到的 C literal。

## 3000 ms 是另一層

`sub_A17180` 在特定 local/result transition 將 `+24` 設為 `3000`；`CVotingStateUI::sub_A1B900` 也有 `+76 = 3000` 的 local UI phase。

這些 3000ms timers 不可與 720 的 70-second voting window 混淆。

## 720 control 與 applicant identity 必須分開

`sub_A1A830` 的 data flow：

```text
+88 <- applicant == local_player
+91 <- 720 final byte
+92 <- VotingAble()
+93 <- active/display update state
```

尤其 `+88` 與 `+91` 來源不同，因此不能把 720 最後 byte 直接命名成 `isApplicant` 或 `isVoter`。

## 723 result

`GR_END_RESULT (723)`：

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770` 保存 player identity，再把 result byte 送入 `sub_A17180`。目前只能確定它是 result/state byte；不要把值 1 未經證據直接命名為 `KICKED` 或 `SUCCESS`。

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
          +--> countdown
          +--> eligible voter check
          +--> 721 vote
          +<-- 722 voter result
          +--> 723 final result
 |
 v
Result / cleanup
```

## Evidence status

### Direct / high confidence

- UI class sizes and composition.
- Two scope options and six reasons.
- Target list records are 36-byte entries.
- Candidate enumeration excludes local player.
- Candidate eligibility reaches player/session state.
- 718 request is gated by Voter state before serialization.
- 721/722 vote field is a byte; client aggregation uses zero vs nonzero.
- 720 fourth field is millisecond-scale timer.
- applicant identity and voting eligibility are independent state.
- local duplicate-vote state exists.

### Cross-source

- scope `0/1` maps behaviorally to Team/Full Kick.
- 70 seconds maps to `70000 ms` for a compatibility implementation.
- Wiki's six reasons correspond to the six reason-selection entries.
- Wiki's minimum-participant rule matches the Client preflight behavior after accounting for the Client's internal count domain.

### Open

- 719 status enum and concrete vtable target.
- 720 control byte concrete semantic.
- 723 result enum.
- 0x369/0x36A/0x373..0x379/0x892/0x893 final localization literals.
- `sub_67D520` / `sub_67D240` player/session semantics.
- complete server-side voter set, timeout, missing-vote, early-end and final kick action.
