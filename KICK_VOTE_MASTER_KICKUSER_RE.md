# PaperMan 踢人／PM_KICKUSER——Master／房間協定分離研究

> 研究快照：**2026-09-16**
>
> 本文件記錄沿著封包註冊表追查後確認的重要架構差異：`PM_KICKUSER_REQ/ACK`（396/397）屬於獨立的 Master／房間管理協定，不能與遊戲內投票生命週期的 718–723 混為同一套協定。

## 1. 封包註冊

客戶端封包註冊表明確包含：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

因此 396/397 位於 `MASTER_*` 協定家族中，與房間／Master 管理操作相鄰。

## 2. 397 確實由 Master／房間封包處理器分派

通用的 Master 側接收分派器包含：

```c
switch (sub_591EE0(a4))
{
    ...
    case 395u:
        sub_579160(a4);
        break;
    case 397u:
        sub_58E410(a1, a4);
        break;
    case 403u:
        sub_579500(a4);
        break;
}
```

因此 `397` 並不是由 `IVotingNetwork::sub_9BF430` 處理，而是有自己獨立的 Master／房間 handler：`sub_58E410`。

## 3. 397 的封包本體已證明以 1 byte 開始

`sub_58E410` 直接執行：

```c
char status;
sub_592940(packet, &status);
sub_58AF90(this);
```

接著依這個 1-byte 值分支：

```c
case 0:
    goto default;

case 1:
    message resource 0xF9;
    sub_9A7DE0(..., 68, 1);
    return;

case 2:
    message resource 0xA5;
    sub_9A7DE0(..., 69, 1);
    break;

default:
    message resource 0x38;
    sub_9A7DE0(..., 67, 1);
    break;
```

因此目前已證明的 wire 形狀為：

```text
397 PM_KICKUSER_ACK
    +0x00  u8 status
    payload size = 1 byte
```

至少 `0`、`1`、`2` 三個值具有不同的客戶端處理路徑；其中 `0` 落入 default 路徑。

但是，這些值的實際協定語意仍然是 **OPEN**。不能只靠控制流程自行命名為 `SUCCESS`、`NOT_FOUND`、`DENIED` 等。

## 4. 目前的 PaperMan.exe.c 匯出中沒有直接找到 396 request 建構器

目前在反編譯 C 匯出中，沒有找到直接形式：

```c
Packet::possible_ctor_or_dtor_0(..., 396);
```

而字面量 `PM_KICKUSER_REQ` 只在封包註冊表出現。

因此目前不足以僅憑這份客戶端 C 匯出，確定 396 request 的封包本體配置。

目前合理但尚未證實的可能性包括：

- request 透過目前 C 匯出未完整恢復的間接／virtual 路徑產生；
- 對應 request 路徑位於其他 executable／server component，而不是目前的 gameplay client；
- request 屬於房間／Master 操作，其觸發程式碼位於 voting UI cluster 之外。

以上全部屬於假說，不應當成已證明事實。

## 5. 與遊戲內 Kick Vote 協定分離

真正的遊戲內投票生命週期另外由下列封包構成：

```text
718  client -> server  start vote request
719  server -> client  start/request status
720  server -> client  voting session state
721  client -> server  individual vote
722  server -> client  per-voter vote result/broadcast
723  server -> client  end/result notification
```

這些封包由 `IVotingNetwork::sub_9BF430` 處理，其中 719/720/722/723 是明確的 switch case。

因此相容伺服器應將兩個概念分開建模：

```text
遊戲規則投票
    718–723

Master／房間踢人操作
    396–397
```

兩者可能在使用者可見的「踢人」功能中處於不同層級，但目前客戶端二進位碼沒有足夠證據支持把它們的封包本體合併成同一套協定。

## 6. 為什麼這個區分很重要

日本 PaperMan Wiki 將遊戲內的玩家投票踢人，以及等待房間中由房主執行的踢人操作區分開來。

目前從二進位結構觀察到的分層也與這個區分一致：

```text
遊戲內投票 UI／遊戲規則狀態機
        -> 718–723

Master／房間管理層
        -> PM_KICKUSER_REQ/ACK 396/397
```

但成功投票後究竟是：

```text
成功投票
    -> 396 PM_KICKUSER_REQ
    -> 397 PM_KICKUSER_ACK
```

還是由 game server 直接完成玩家踢除，目前仍未從現有的客戶端 C 匯出中證實。

## 7. 證據定位

### 封包註冊

`PaperMan.exe.c` 約第 675991–676018 行：

```text
PM_KICKUSER_REQ = 396
PM_KICKUSER_ACK = 397
```

### Master／房間分派器

`PaperMan.exe.c` 約第 177329–177349 行：

```text
case 397u:
    sub_58E410(a1, a4);
```

### 397 解析器／處理器

`PaperMan.exe.c` 約第 178307–178344 行：

```text
sub_592940(packet, &status)
switch(status)
```

### 尚未解決

- 396 request 的實際 wire body；
- 397 status enum 的精確語意；
- 718–723 成功投票與 396/397 之間是否存在實際的跨層串接。
