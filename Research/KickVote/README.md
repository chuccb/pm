# Kick Vote 研究總覽

> 研究日期：2026-09-16

本目錄集中保存日本版 PaperMan 客戶端 Kick Vote 的完整逆向結果。研究以 `PaperMan.exe.c`、提取資源與日本 Wiki 三方交叉驗證為原則。

## 已確認的玩家流程

日本 Wiki `操作ガイド` 描述的流程包含：

```text
P
 -> 選擇踢人範圍
 -> 選擇踢人理由
 -> 選擇目標玩家
 -> 啟動投票
 -> 其他符合資格者投票
 -> 結束／結果
```

日文原文的模式、理由與介面名稱保留，不翻譯：

- `個人サバイバル`
- `爆破ミッション`
- `チームサバイバル`
- `スチール`
- `チーム戦術`
- `練習モード`
- `チャットルーム`

Wiki 說明投票時間為 70 秒，未投票者不產生有效票；目標玩家沒有投票權。可選 `チームキック` 或 `全体キック`。兩者皆需要至少 3 名符合條件的參與者。

六個理由的日文原文保持如下：

1. `チート行為`
2. `ゲームプレイ妨害`
3. `悪口、荒らし行為`
4. `キャラクター放置`
5. `アビューズ行為`
6. `その他違反行為`

## 客戶端的主要類別

```text
Voter
└── VoterMgr / IVotingNetwork
    ├── CVoteTargetList
    ├── CVotingTargetUI
    ├── CVotingStateUI
    └── CVotingApprovalUI
```

建立流程會配置：

```text
CVotingApprovalUI  = 0x08 bytes
CVotingStateUI     = 0xE8 bytes
CVotingTargetUI    = 0x28 bytes
CVoteTargetList    = 0x20 bytes
```

這證明投票不是單一 popup，而是由目標列表、投票狀態與表決介面共同組成。

## 目前最重要的狀態

`Voter` 中目前已恢復的關鍵行為包括：

```text
+20  = 投票持續時間／剩餘時間相關欄位
+24  = 本地目標相關的額外計時狀態
+28  = 本局／本次發起狀態
+29  = 當前投票資格／狀態
+30  = 本地是否已投票
+31  = 額外結束／中止狀態
+32  = 投票流程是否 active
+36  = 篩選後候選數
+40  = 全部非申請者數
+44  = 723 結束狀態 byte
```

其中部分語意已由多個函式交叉證明，部分仍維持 `[OPEN]`。

## 目前協定閉合度

```text
718 GR_START_VOTING_REQ   [高]
719 GR_START_VOTING_ACK   [欄位寬度高，enum OPEN]
720 GR_START_VOTING       [高]
721 GR_DO_VOTING          [高]
722 GR_VOTING_RESULT      [高]
723 GR_END_RESULT         [高，enum OPEN]

396 PM_KICKUSER_REQ       [body OPEN]
397 PM_KICKUSER_ACK       [u8 高，enum OPEN]
```

注意：396/397 屬於 Master／房間層，不能與 718–723 合併。

## 最重要的未解問題

- 719 status 的完整 enum。
- 720 第 5 個 byte 的精確原始語意。
- 723 第一個 byte 的完整 enum。
- 投票 timeout 與「有效票」的伺服器最終判定。
- 投票完成後真正踢人的跨層流程。
- 396 request 的實際 body。
- 投票 UI localization 資源 ID 對應的日文原文。

詳見：

- `Protocol.md`
- `UI_State.md`
- `Master_Room.md`
