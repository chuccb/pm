# Kick Vote 完整研究

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：將 Kick Vote 的 UI、資格、718–723 協定、139 lifecycle signal、396/397 Master/Room 分層與 131/132 Force Out 關係集中於同一份主文件。未確認的 Server 最終 action 必須保持 `[OPEN]`。

## 1. 證據與研究範圍

本文件整合原本分散的：

```text
Protocol.md
UI_State.md
Evidence_And_Eligibility.md
Master_Room.md
```

證據標記：

```text
[C]     PaperMan.exe.c / IDA C 直接證據
[RES]   Extracted 資源或資料檔
[WIKI]  日本 PaperMan Wiki 歷史玩家可見資料
[X]     兩種以上獨立來源互相吻合
[OPEN]  尚未充分證明
```

`Hex-Rays` 的函式名稱、參數型別與變數名稱不能單獨視為 protocol truth；wire width 以實際 serializer/parser helper 為準。

## 2. UI 與輸入狀態機

投票不是單一 popup，而是多個 Client object 共同構成：

```text
CVotingApprovalUI = 0x08 bytes
CVotingStateUI    = 0xE8 bytes
CVotingTargetUI   = 0x28 bytes
CVoteTargetList   = 0x20 bytes
```

`sub_A1A090(this, n10)` 依 `CVotingTargetUI` state 分流：

```text
state 0 → 兩個 Scope 選項
state 1 → 六個 Reason 選項
state 2 → Target List
```

Target list 一次最多顯示 8 個 target；超過 8 個可翻頁。Client 內部 target-page command 使用值 `10`，日本 Wiki 的玩家操作則是按 `0` 翻頁；兩者屬不同層，不可混為協定 enum。[C][WIKI]

## 3. Scope、Reason 與資源

Scope UI：

```text
892 → option 1
893 → option 2
```

結合 candidate filtering 與日本 Wiki，可高可信建立：

```text
scope 0 = チームキック
scope 1 = 全体キック
```

但 892/893 的最終 localization literal 尚未直接由 resource store 閉合。[C][RES][WIKI][X][OPEN]

Reason selection 使用：

```text
883, 884, 885, 886, 887, 888
```

Active voting display 使用另一組：

```text
0x373, 0x374, 0x375, 0x376, 0x377, 0x378
```

不得假設兩組 resource ID 一一相等。[C]

Wiki 的六項理由為：

```text
チート行為
ゲームプレイ妨害
悪口、荒らし行為
キャラクター放置
アビューズ行為
その他違反行為
```

這與六項 reason-selection entries 形成跨來源對應。[WIKI][C][X]

Approval UI：

```text
0x369 → option 1
0x36A → option 2
```

並格式化成：

```c
L"1. %s"
L"2. %s"
```

Approval scope 與 892/893 scope selector 必須維持分離。[C]

## 4. Candidate 與 voter eligibility

`CVoteTargetList::sub_A17450(mode)` 重建 36-byte target records。

`sub_A177C0()` 遍歷 player list 時同時追蹤：

```text
全部 non-local candidates
通過 sub_67DDD0() 的 candidates
```

`sub_67DDD0(slot)` 至少要求：

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
+ player/session state comparison
```

`PlayerId`、`SlotIndex`、candidate eligibility、voter eligibility 不能壓縮成同一個 boolean 或整數欄位。[C]

## 5. 718 `GR_START_VOTING_REQ`

`IVotingNetwork::sub_A191D0` 在建立 718 前先執行 preflight：

```text
sub_A17340
    → sub_A17290(Voter, scope)
    → 只有 result == 3 才 serialize
```

serializer：

```c
Packet::possible_ctor_or_dtor_0(v7, 718);
sub_592A20(v7, a2);
sub_592A20(v4, a3);
sub_592A20(v5, a4);
```

因此：

```text
+0x00 u32 scope
+0x04 u32 reason_index
+0x08 u32 target_player_id
```

三個欄位都是 4-byte writer，不可依 Hex-Rays prototype 改成 char。[C]

`sub_A17290()`：

```text
+28 == 1 → reject
+32 == 1 → 特殊 early return，精確語意 OPEN
scope 0 → count field +36 >= 2
scope 1 → count field +40 >= 2
```

`sub_A17340()` preflight 成功時先設：

```text
Voter +28 = 1
```

所以 `+28` 是 request/active-lock-like state，但原始語意名稱仍 `[OPEN]`。[C]

Wiki 說 Team Kick 與 Full Kick 最少需要 3 位參與者；Client 自己比較的是 `>=2`，因此 `+36/+40` 不能直接標成 raw room player count。它們屬 Client 內部衍生 candidate/count domain。[WIKI][C][X]

## 6. 719 `GR_START_VOTING_ACK`

接收：

```c
case 719:
    sub_592940(a2, &v21);
    (*(*this + 12))(this, v21);
```

因此：

```text
+0x00 u8 status
```

同一 concrete `IVotingNetwork` class 存在：

```text
sub_A19380(int status)
```

其目前可觀察分支：

```text
0 → 清除 message/UI pulse，保留 active-flow marker
1 → message resource 878，保留 active-flow marker
2 → message resource 880
3 → message resource 879
```

因此：

```text
719 → sub_A19380
```

為高 confidence concrete dispatch mapping。`0..3` 的產品層 enum 與 878/879/880 的 localization literal 仍 `[OPEN]`。[C][OPEN]

## 7. 720 `GR_START_VOTING`

接收欄位順序：

```text
+0x00 u32 reason_index
+0x04 u32 applicant_player_id
+0x08 u32 target_player_id
+0x0C u32 duration
+0x10 u8  control
```

`reason`、`applicant_id`、`target_id` 的 Client consumer 路徑已閉合到 reason UI、applicant identity 與 target display。[C]

### 7.1 Voting duration

`duration` 進入 `sub_A17130(..., duration)`，成為 Voter `+20`；`sub_A17380(elapsed)` 會扣減並 clamp 至 0；`VoterMgr::sub_A19940()` 將剩餘值送給 State UI；UI 再使用：

```text
remaining / 0x3E8u
```

形成秒數顯示。

因此：

```text
720 +0x0C = voting duration / remaining timer
unit = millisecond scale
```

Wiki 公開規則為 70 秒，所以相容性實作值可推導為：

```text
70000 ms
```

這是 Wiki + Client 行為的推導，不是目前找到的 `70000` binary literal。[C][WIKI][X]

### 7.2 720 最後 byte 的重要修正

`sub_A19460()`：

```c
*(this - 32) = field4;
v25 = 1;
if ( *(this - 32) == 0 )
{
    v18 = *(this - 40); // applicant
    v25 = (*(**(this + 12) + 28))(*(this + 12), v18);
}
```

之後：

```c
sub_A1A830(..., applicant == local_player, v25);
```

`sub_A1A830()` 才將 `v25` 寫入 `CVotingStateUI +91`。

所以：

```text
720 field4 == 0
    → 執行 applicant-id eligibility predicate
    → v25 = predicate result

720 field4 != 0
    → 跳過 predicate
    → v25 = 1

CVotingStateUI +91
    = predicate result
```

舊結論：

```text
StateUI +91 <- 720 final byte
```

已證明錯誤。[C]

因此 field4 目前最準確的暫名是：

```text
applicant_eligibility_control
```

其完整 server semantic 與 allowed values 仍 `[OPEN]`。

## 8. 721 `GR_DO_VOTING`

serializer：

```c
Packet::possible_ctor_or_dtor_0(v5, 721);
sub_5928E0(v5, a2);
```

因此：

```text
+0x00 u8 vote
```

Client aggregation：

```c
if ( a2 != 0 )
    ++*(this + 20);
else
    ++*(this + 21);
```

所以 Client branch semantic：

```text
0       = NO / 反對
nonzero = YES / 贊成
```

這不代表 Server 應接受任意非零值；Server 必須獨立驗證合法 wire value。[C]

## 9. 722 `GR_VOTING_RESULT`

Parser：

```text
+0x00 u32 voter_player_id
+0x04 u8 vote
```

`IVotingNetwork::sub_A19890` 先將 voter ID 送入 player-side state，再呼叫 `sub_A1A9D0()` 做 YES/NO aggregation。

因此 722 的：

```text
wire width
+ voter identity
+ vote aggregation
```

鏈條已閉合。[C]

若 voter 是 applicant/local player，還有額外 applicant-result UI branch；不得把一般 voter 與 applicant path 壓成同一 state transition。

## 10. 723 `GR_END_RESULT`

Parser：

```text
+0x00 u8 result_state
+0x01 u32 player_id
```

`sub_A19770()`：

```text
player_id → Voter identity
result byte → sub_A17180()
```

`sub_A17180()`：

```text
保存 result byte → Voter +44
若 target/local 且 result == 1 → Voter +24 = 3000
清除 +29 / +32 voting-active state
```

之後只有 player-side virtual lookup 成功時才呼叫 `sub_A1A970()` 做 result UI；再由 `sub_A18F80(..., 0)` cleanup。[C]

因此目前能確認：

```text
723
  → Voter result state mutation
  → optional player lookup / result UI
  → voting UI cleanup
```

不能從這條 Client chain 直接宣稱它修改 room occupancy，也沒有看到直接構造 396 的證據。[C][OPEN]

`result_state` literal enum 尚未閉合；值 `1` 雖然在 local-target path 觸發 3000ms phase，但不足以單獨命名為 `SUCCESS` 或 `KICKED`。[OPEN]

## 11. 139 voting lifecycle signal

`VoterMgr::sub_A19A70()` 建立並送出 opcode 139：

```c
Packet::possible_ctor_or_dtor_0(v1, 139);
sub_58D7D0(byte_13242F8, v1);
byte_2317C68 = 1;
```

`sub_A17380()` 的部分 result/phase countdown update 只有在：

```text
byte_2317C68 == 0
```

時才繼續。

因此 139 明確屬 voting lifecycle/control path，但尚不能命名成 `END_VOTE`、`CANCEL_VOTE` 或其它產品 enum。[C][OPEN]

## 12. 3000ms phase 與 70 秒 timeout 必須分離

Client 有多條獨立 3000ms path：

```text
Voter +24 = 3000
CVotingStateUI +76 = 3000
```

這些屬 result/approval/UI phase，不是 720 的 70 秒 voting duration。[C]

## 13. 396 / 397 Master／Room family

目前 opcode registration / dispatcher family：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397 receiver：

```c
case 397u:
    sub_58E410(a1, a4);
```

`sub_58E410()` 只直接讀一個 status byte，再對 `0/1/2/default` 走不同 message/resource branch，因此：

```text
397 +0x00 = u8 status
```

目前完整 Client C 未找到 396 的直接 `Packet ctor(...,396)` serializer/caller；request body 保持 `[OPEN]`。

即使同一 Client 可以直接找到：

```text
394 MASTER_ROOMINFO_REQ
398 MASTER_SVRCLASS_REQ
400 MASTER_CONNTYPE_REQ
```

也不能因 opcode 相鄰而猜 396 body。[C][OPEN]

## 14. 131 / 132 Force Out

Kick Vote 不應和 Force Out 或 Master Kick 直接合併。

### 14.1 131 `GR_FORCEOUT_REQ`

`sub_56EC10()`：

```c
Packet::possible_ctor_or_dtor_0(v2, 131);
sub_592920(v2, n0x10);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
131 +0x00 = u8 target_slot
```

Client caller 會先由 player identity 對映到 0..15 slot；不是直接序列化 DWORD player ID。[C]

### 14.2 132 `GR_FORCEOUT_ACK`

`sub_56ECC0()` 第一欄為：

```text
u8 status
```

非零 path 再讀：

```text
u8 target_slot
```

之後一般 `CLobbyGameRoom` 路徑呼叫 `sub_432EE0(...)`，Tournament 路徑呼叫 `sub_479A50(...)`；兩者都取得 `GAMEROOM_USERSLOTS` / `USERSLOTS` 的 slot object 並進入：

```text
sub_6FC460(slot)
```

即實際 client-side slot removal/reset path。[C]

因此：

```text
132 status != 0
    → target slot
    → room user-slot collection mutation
```

但 status `1/2/...` 的產品 enum 尚未閉合。[C][OPEN]

`status == 0` 則走較廣泛的 room/player state synchronization，與非零 removal branch 分開。[C]

## 15. Player slot / team 基礎

Client 有固定：

```text
16 player slots
```

`sub_67D110()` 先使用全域 local-player identity 尋找真正 slot index；因此：

```text
PlayerId != SlotIndex
```

`sub_67D240()` 與 `sub_67D520(slot)` 用於本地與指定玩家的 group/team value 比較；一般路徑為：

```text
sub_67D520(slot) == sub_67D240()
```

這是 Team Kick candidate filter 的重要底層依賴。[C]

`sub_67D310(slot)` 的一般結果為：

```text
0 → inactive / unusable
1 → active participant, non-local
2 → active participant, local
```

因此 Kick Vote Server model 至少應分離：

```text
PlayerId
SlotIndex
Team/Group
Occupied/Active
ConnectionState
VoteEligibility
TargetEligibility
```

## 16. 完整 Client-side state machine

```text
Idle
  ↓
Scope Selection (2)
  ↓
Reason Selection (6)
  ↓
Target Selection (≤8/page)
  ↓
candidate/session eligibility
  ↓
718 Request
  ├─ 719 requester status
  └─ 720 active vote
        ├─ applicant predicate / UI state
        ├─ countdown
        └─ 721 vote
             └─ 722 voter result
                    ↓
                   723 final result
                    ├─ Voter result state
                    ├─ result UI
                    └─ cleanup

Separate paths:
131 → 132 Force Out
396 → 397 Master/Room Kick
139 → voting lifecycle/control signal
```

## 17. Voter state machine

`sub_A17130()` 啟動 active vote：

```text
+31 = 0
+44 = 0
+24 = 0
+20 = duration
+29 = eligibility
+32 = 1
+30 = 0
```

`sub_A17220()` reset：

```text
+28 = 0
+29 = 0
+30 = 0
+31 = 0
+32 = 0
+8  = -1
```

`sub_A171F0()`：

```c
if ( *(this + 29) == 0 )
    return 0;
*(this + 30) = 1;
return 1;
```

因此：

```text
+29 = local voting eligibility/state
+30 = already-voted
+32 = voting-active-like state
+31 = additional phase/lock state
```

精確原始 class field names 仍未恢復。[C][OPEN]

## 18. Re-press / invalid-state handling

`VoterMgr::sub_A1A4A0()` 會區分：

```text
+31 == 1
    → reject

Voting environment invalid
    → reject

VotingAble() == true
    → local vote/toggle path

+32 == 1 && +29 == 1 && +30 == 1
    → resource 878
    → reject repeated vote operation

+32 == 1 && +29 == 0 && +56 != +12
    → resource 880
    → reject

+52 == 0 or candidate-list check succeeds
    → continue via sub_A18F50

otherwise
    → resource 879
    → reject
```

這再次證明：

```text
already voted
current ability to vote
vote flow active
candidate acceptance
```

是不同狀態，不應壓成單一 boolean。[C]

## 19. 伺服器重建應分離的概念

最小概念模型：

```text
KickVoteSession
├─ Scope
├─ ReasonIndex
├─ ApplicantPlayerId
├─ TargetPlayerId
├─ DurationMs
├─ Control
├─ EligibleVoterSet
├─ SubmittedVotes
├─ YesCount
├─ NoCount
├─ StartedAt
├─ EndedAt
└─ ResultState
```

並獨立保留：

```text
Room / Master Kick Operation
├─ RequestBody        [OPEN]
├─ Requester/MasterId
├─ TargetId
└─ AckStatus
```

也必須獨立保留：

```text
ForceOut
├─ target_slot
├─ status
└─ room slot mutation
```

在 Client 證據證明前，不要把：

```text
723 → 131
723 → 396
718–723 → 396/397
```

任何一條直接寫死成 Server contract。[OPEN]

## 20. 三方交叉驗證目前已閉合的部分

```text
Wiki
  → 兩種 Scope、六項 Reason、70 秒、最少參與者規則

C / LST
  → UI state、candidate filtering、serializer/parser、state mutation

Resource
  → 892/893、883–888、0x369/0x36A、0x373–0x378、878/879/880

三方相互補強：
  Scope / Reason / Timer / UI state / packet flow
```

但仍有多個重要 OPEN：

```text
719 status 0..3 的產品 enum
720 field4 的 server semantic / allowed values
723 result enum / final action contract
139 的產品 semantic
396 request body / caller
真正的 server voter set
timeout / missing vote / early-end 演算法
723 後真正 room/player removal function
sub_67D520 / sub_67D240 的完整 player/session semantic
878/879/880 等 localization literal
```

## 21. 未來研究原則

發現新的 C/LST/ASM、Resource 或 Wiki 證據時：

```text
先更新本文件的對應章節
    ↓
若證據影響 Core Player/Room state
    → 同步更新對應 Core 主文件
    ↓
若只影響 UI/resource literal
    → 保持 OPEN 邊界並更新資源證據
```

不可因 Server implementation 需要而把未知欄位改成 `0`、固定常數或 guessed enum。
