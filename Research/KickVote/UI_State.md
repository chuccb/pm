# Kick Vote UI 與狀態機研究

> 研究日期：2026-09-16

## UI 類別結構

`VoterMgr::sub_A19B10` 建立：

```text
CVotingApprovalUI = 0x08 bytes
CVotingStateUI    = 0xE8 bytes
CVotingTargetUI   = 0x28 bytes
CVoteTargetList   = 0x20 bytes
```

並將 `CVotingTargetUI` 與 `CVoteTargetList` 連接。這是獨立的投票子系統，而不是單一視窗。

## 輸入狀態

`sub_A1A090(this, n10)` 的狀態依 `CVotingTargetUI` 的內部 state 分成：

```text
state 0
  兩個選項：踢人範圍

state 1
  六個選項：踢人理由

state 2
  每頁最多 8 個目標
  額外有翻頁控制
```

範圍選擇接受 `0..1`；理由接受 `0..5`；目標號碼接受 1–8。翻頁在 C 的內部輸入值為 `10`，日本 Wiki 對應實體按鍵為 `0`。

## UI resource ID

### 範圍

```text
892 -> UI 選項 1
893 -> UI 選項 2
```

結合 target-list 行為與日本 Wiki，可得到高可信行為 mapping：

```text
0 = チームキック
1 = 全体キック
```

日文原始字串尚未從 localization store 直接取出，因此不把 resource ID 與日文 literal 假定為固定對應。

### 理由

選擇畫面使用：

```text
883, 884, 885, 886, 887, 888
```

Active voting state 顯示使用另一組：

```text
0x373, 0x374, 0x375, 0x376, 0x377, 0x378
```

兩組是不同 resource key，不能假設 `883 == 0x373` 等價。

Wiki 的六項日文原文維持不翻譯：

```text
チート行為
ゲームプレイ妨害
悪口、荒らし行為
キャラクター放置
アビューズ行為
その他違反行為
```

### YES / NO

`CVotingApprovalUI` 使用：

```text
0x369 -> UI 選項 1
0x36A -> UI 選項 2
```

並格式化為：

```c
L"1. %s"
L"2. %s"
```

它們屬於最後的投票表決，不是前面的 `892/893` 範圍選擇。

### 翻頁

`0x379` 被格式化為：

```c
L"0. %s"
```

並在目標數量超過 8 時使用。這與 Wiki 的實體 `0` 鍵翻頁完全一致。

## VotingAble

`sub_A1A6D0`：

```c
return *(this + 32) == 1
    && *(this + 29) == 1
    && *(this + 30) == 0;
```

`sub_A171F0` 在本地投票後設定：

```c
*(this + 30) = 1;
```

因此 `VotingAble` 並不是單純的「顯示按鈕」，而是反映本地玩家目前仍可投票的狀態。這也直接說明同一玩家在同一次投票中的重複投票會被本地狀態阻止；Server 仍應自行做權威驗證。

## Active voting UI 的角色區分

`sub_A1A830` 的參數經過資料流後形成：

```text
+88 = applicant_id == local_player_id
+91 = 由 720 field4 推導出的 eligibility / display flag
+92 = VotingAble
+93 = voting-state update / active flag
```

因此不可將「我是發起者」、「我是否有資格投票」、「投票 UI 是否啟用」混成同一個 flag。

## 倒數計時

720 的第 4 個 DWORD 進入 `sub_A17130(..., a5)`，保存至 Voter 的 +20。`sub_A17380` 以 elapsed milliseconds 扣減並限制在 0。

之後 `VoterMgr::sub_A19940` 將剩餘時間推送至 UI，`CVotingStateUI::sub_A1BF30` 以：

```c
remaining / 0x3E8u
```

處理顯示，因此此值是毫秒尺度的投票倒數／持續時間。

日本 Wiki 明確記載投票上限為 70 秒；因此相容 Server 使用 `70000` ms 是非常強的跨來源推導，但目前沒有直接在 C 匯出中找到 `70000` literal。

## 3000 ms 必須與投票倒數分開

`sub_A17180` 中存在：

```c
*(this + 24) = 3000;
```

而 `CVotingStateUI::sub_A1B900` 也有本地 `3000` 狀態初值。它們是結果／UI 的局部計時狀態，不能拿來代替 Wiki 的 70 秒投票窗口。

## 目前的狀態流程

```text
初始
  |
  | 選擇範圍
  v
scope state
  |
  | 選擇理由
  v
reason state
  |
  | 選擇目標
  v
target state
  |
  | 718
  v
投票 session 開始
  |
  | 720 + 倒數
  +----------------+
  |                |
  | 721            | elapsed time
  v                v
投票提交         倒數更新
  |                |
  | 722            |
  +------> 計票/UI <+
             |
             | Server 結束
             v
          723 結果
```

## 尚未解決

- 719 各狀態 byte 的原始 enum 與日文提示。
- 720 field4 的原始 symbol。
- 723 第一 byte 的完整 enum。
- localization store 中 `0x369/0x36A/0x373..0x379/0x892/0x893` 的最終日文內容。
