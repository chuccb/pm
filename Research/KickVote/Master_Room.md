# `PM_KICKUSER_REQ/ACK` Master／房間層研究

> 研究日期：2026-09-16

## 協定分層

封包註冊表明確列出：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

因此 `396/397` 位於 `MASTER_*` 協定家族附近，不能直接當成遊戲內 718–723 投票封包。

## 397 的接收路徑

Master／房間層 dispatcher：

```c
case 397u:
    sub_58E410(a1, a4);
    break;
```

它不是 `IVotingNetwork::sub_9BF430` 的 case。

## 397 Payload

`sub_58E410` 開頭直接讀取一個 byte：

```c
char status;
sub_592940(a2, &status);
```

接著依值分支：

```text
status = 0
    -> default 路徑

status = 1
    -> message resource 0xF9
    -> sub_9A7DE0(..., 68, 1)

status = 2
    -> message resource 0xA5
    -> sub_9A7DE0(..., 69, 1)

default
    -> message resource 0x38
    -> sub_9A7DE0(..., 67, 1)
```

所以目前可證明：

```text
397 PM_KICKUSER_ACK
+0x00 u8 status
payload = 1 byte
```

`0/1/2` 至少存在不同處理，但精確 enum 仍為 `[OPEN]`。在找出 localization 與 request/server 對應之前，不命名成 `SUCCESS`、`DENIED` 等。

## 396 目前狀態

在 `PaperMan.exe.c` 中尚未找到：

```c
Packet::possible_ctor_or_dtor_0(..., 396);
```

目前只能確定：

```text
396 = PM_KICKUSER_REQ
397 = PM_KICKUSER_ACK
```

396 的實際 body、產生位置與是否由間接 virtual path 建立，仍未封閉。

## 與 718–723 的關係

目前二進位證據支持分層：

```text
遊戲內 Kick Vote
    718–723

Master／房間踢人
    396–397
```

尚未證明「718–723 投票成功」會直接呼叫 `396 PM_KICKUSER_REQ`。也可能是 game server 在投票完成後直接執行踢除，而 396/397 負責另一層 Master／房間操作。

日本 Wiki 也區分遊戲中的玩家投票踢人與等待房間中的房主踢人機制。

## 後續最重要的追查

```text
396 發送 caller
    -> request body
    -> server response 397
    -> status 對應訊息

718–723 結束
    -> 真正 kick 執行函式
    -> 玩家從 room/game state 移除
```

兩條鏈最後是否會在某個 shared kick function 匯合，是確認 PaperMan 完整踢人架構的關鍵。
