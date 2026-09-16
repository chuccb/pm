# Kick Vote 研究總覽

> 研究日期：2026-09-16
> 目標版本：日本版 PaperMan 2016 年服務終了時 Client

本目錄保存日本版 PaperMan Kick Vote 的逆向結果。研究以 `PaperMan.exe.c`、`Extracted/`、日本 Wiki 三方交叉驗證為核心；IDA/LST/ASM 在 Hex-Rays 類型或 CFG 可疑時優先回查。

## 已確認的玩家流程

```text
P
 -> 選擇踢人範圍
 -> 選擇踢人理由
 -> 選擇目標玩家
 -> 啟動投票
 -> 其他符合資格者投票
 -> 結束／結果
```

日本 Wiki `操作ガイド` 記載可用於：

```text
個人サバイバル
爆破ミッション
チームサバイバル
スチール
チーム戦術
```

不可用於 `練習モード`、`チャットルーム`；投票窗口 70 秒；目標玩家不能投票；有效票全部贊成才 kick；一票反對即不能 kick；Team Kick 與 Full Kick 均要求至少 3 名符合條件的參與者；每局每人只能申請一次。

六個理由維持 Wiki 原文：

1. `チート行為`
2. `ゲームプレイ妨害`
3. `悪口、荒らし行為`
4. `キャラクター放置`
5. `アビューズ行為`
6. `その他違反行為`

## Client 類別結構

```text
Voter
└── VoterMgr / IVotingNetwork
    ├── CVoteTargetList
    ├── CVotingTargetUI
    ├── CVotingStateUI
    └── CVotingApprovalUI
```

目前建立流程可觀察到：

```text
CVotingApprovalUI = 0x08 bytes
CVotingStateUI    = 0xE8 bytes
CVotingTargetUI   = 0x28 bytes
CVoteTargetList   = 0x20 bytes
```

投票系統不是單一 popup，而是 target list、active state、approval UI 與 Voter state 共同構成。

## 718–723 協定狀態

```text
718 GR_START_VOTING_REQ   Client -> Server   u32 + u32 + u32
719 GR_START_VOTING_ACK   Server -> Client   u8
720 GR_START_VOTING       Server -> Client   u32 + u32 + u32 + u32 + u8
721 GR_DO_VOTING          Client -> Server   u8
722 GR_VOTING_RESULT      Server -> Client   u32 + u8
723 GR_END_RESULT         Server -> Client   u8 + u32
```

欄位寬度均以實際 serializer/parser 優先，不以 Hex-Rays guessed prototype 為準。

## 本輪新增的重要確認

### 718 有 Client-side preflight gate

`IVotingNetwork::sub_A191D0` 在建立 718 前先呼叫 `sub_A17340`。其底層 `sub_A17290` 明確使用 `scope`：

```text
scope == 0 -> Voter +36 >= 2 才回傳可申請
scope == 1 -> Voter +40 >= 2 才回傳可申請
```

只有判定為可申請後才建立 718。`Voter +28 == 1` 時直接拒絕再次申請。

這與 Wiki 的「Team/Full 至少 3 人」規則吻合，但 `+36/+40` 不是可直接命名成總玩家數的欄位；C 使用 `>=2`，表示其計數口徑至少排除了某個角色／發起者。

### Candidate eligibility 不是單純 online count

`CVoteTargetList` 會排除 local player，並區分全部候選與通過 `sub_67DDD0` 的候選。

`sub_67DDD0(slot)` 至少確認：

```text
slot < 16
以及 sub_67D520(slot) == sub_67D240()
```

所以 Server reconstruction 不應只實作 `room.players.count >= 3`；候選 set 與 voter set 的定義仍需和 Player/Session state 一起還原。

### Vote byte 已閉合

721/722 的 vote 欄位都是 `u8`。`sub_A1A9D0`：

```c
vote != 0 -> YES
vote == 0 -> NO
```

這是 Client 的確定語意；Server 仍應自行驗證 voter 是否具資格、是否已投票、是否為 target。

### 720 duration 已閉合到毫秒尺度

720 第四個 DWORD 進入 Voter timer，之後以 elapsed milliseconds 扣減；UI 使用 `remaining / 1000` 並送到 `Vote_Digit`。

Wiki 給出的投票限制為 70 秒，因此 Server 相容值為 `70000 ms`。這是 Wiki + Client 行為的 cross-source inference，不是目前已找到的 C literal。

### 3000 ms 不是投票窗口

Client 還有 `3000` 的局部 UI/result timer。它與 720 的 70 秒投票 duration 必須分開，不能因為看到 `3000` 就把 vote timeout 寫成 3 秒。

## 396/397 分層

```text
718–723 = Game/Gameplay voting
396/397 = Master/Room kick
```

目前沒有足夠 binary evidence 證明 723 成功後一定直接建立 396；兩條鏈是否在 shared kick implementation 匯合仍為 OPEN。

## 目前仍未封閉

- 719 status enum 與 localization。
- 720 最後 byte 的 concrete meaning。
- 723 result byte enum。
- `sub_67D520/sub_67D240` 的完整 player/session state meaning。
- Server voter set、timeout、missing vote、early-end 與最終 kick 條件的完整實作。
- 396 request body/caller。
- 8-byte outer framing 的 sequence/encryption/checksum 細節。
- localization store 中 0x369/0x36A/0x373..0x379/0x892/0x893 等 ID 的最終日文 literal。

詳細內容：

- `Protocol.md` — 718–723 payload、data flow、資格 gate、跨層關係
- `UI_State.md` — UI/state machine、candidate list、timer、duplicate-vote lock
- `Master_Room.md` — 396/397 Master/Room layer
