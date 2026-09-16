# `PM_KICKUSER_REQ/ACK` Master／房間層研究

> 研究日期：2026-09-16
> 目標版本：日本版 PaperMan 2016 年服務終了時 Client

## 一、先分清三條不同的「踢人」協定層

目前 Client 證據至少區分：

```text
131 GR_FORCEOUT_REQ / 132 GR_FORCEOUT_ACK
    = GameRoom 層指定 slot 的 force-out

718–723 GR_*VOTING_*
    = 遊戲內玩家投票流程

396 PM_KICKUSER_REQ / 397 PM_KICKUSER_ACK
    = Master／Room protocol family 的 kick-user 操作
```

不能因為三者都與「kick」相關，就直接假設它們是同一 packet chain。

## 二、131 `GR_FORCEOUT_REQ` 已確認為實際 Client sender

Client serializer：

```c
// sub_56EC10
Packet::possible_ctor_or_dtor_0(v2, 131);
sub_592920(v2, n0x10);
sub_555090(&dword_1321D00, v2);
```

因此：

```text
131 payload = 1 byte
```

`n0x10` 在呼叫前會先由 room logic 根據 `dword_F6DCF4[slot]` 尋找目標玩家；`CLobbyGameRoom::sub_432270()` 與 `CLobbyTournamentGameRoom::sub_479190()` 都直接包裝 `sub_56EC10()`。

一般 `CLobbyGameRoom` caller `sub_42F700(target_player_id)` 在：

```text
目標不是 local player
且該 slot 的狀態符合 forceout path (`byte_F6D9EC[slot] == 9`)
```

時發送 131。

因此目前高 confidence 語意為：

```text
131 GR_FORCEOUT_REQ
+0x00 u8 target_slot / forceout slot
```

它不是 `player_id` DWORD；Client 先把 player identity 映射成 0..15 slot，再只序列化該 slot。

## 三、132 `GR_FORCEOUT_ACK` 不只是「ACK」；存在明確的房間 slot mutation

接收 handler：`sub_56ECC0()`。

第一欄：

```c
sub_592900(a1, &v12);
```

當 `v12 != 0` 時又讀：

```c
sub_592940(a1, &n0x10);
```

之後一般 `CLobbyGameRoom` 路徑呼叫：

```c
sub_432EE0(dword_EA10D0, n0x10, 0, 1);
```

Tournament 路徑則呼叫：

```c
sub_479A50(dword_EA0F30, n0x10, 0, 1);
```

這兩個函式都直接取得 `GAMEROOM_USERSLOTS`／`USERSLOTS` 容器中的 slot object，然後：

```c
sub_6FC460(v10);                  // remove/reset user-slot object
```

且在特定條件下重設相關 UI/selection state。

所以：

```text
132 status != 0
    -> 取得 target slot
    -> 從 room user-slot collection 做實際 client-side removal/reset
```

這是目前比單純函式名稱更強的直接證據：**132 的某個非零狀態確實能驅動房間 slot mutation。**

但 `v12=1/2/...` 的產品層 status enum 尚未命名；不能直接說 `1=KICK_SUCCESS`，除非再找到 server/ACK 對應。

## 四、132 status=0 是另一種同步路徑

若 `v12 == 0`，`sub_56ECC0()` 不走上述 forceout removal branch，而是讀取：

```text
slot / player id / 16-entry state data
```

再更新：

```text
byte_F6DCF4[slot]  // player identity mapping
room/tournament state
```

其中大量資料屬於完整 room/player state synchronization。

因此 132 至少包含兩種高階形態：

```text
status != 0
    -> forceout/removal event + slot mutation

status == 0
    -> broader room/player synchronization
```

## 五、131/132 與 396/397 的差異

396/397 是另一個 protocol family：

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

397 dispatcher：

```c
case 397u:
    sub_58E410(a1, a4);
```

`sub_58E410()` 只直接讀一個 byte status，再依 `0/1/2/default` 顯示不同 message/resource：

```text
397 payload = u8 status
```

396 的 request body 在目前完整 `PaperMan.exe.c` 中仍未找到直接 `Packet ctor(...,396)` serializer/caller。

一個重要負面證據是：即使同一 Client 有明確的：

```c
sub_5790B0(...)
    -> opcode 394 MASTER_ROOMINFO_REQ
sub_579270(...)
    -> opcode 398 MASTER_SVRCLASS_REQ
sub_579350(...)
    -> opcode 400 MASTER_CONNTYPE_REQ
```

但目前未發現對應的 396 constructor。這可能代表：

```text
396 是間接/虛擬 dispatch 建立
或特定功能在此 Client build 中沒有普通 UI caller
或該 opcode 主要由另一端使用
```

在證據不足前不猜。

## 六、718–723 與 131/132 的關係目前仍未閉合

目前最可靠的 Client-side evidence graph：

```text
Player Kick Vote
    718
      ↓
    720
      ↓
    721 / 722
      ↓
    723
      ↓
    Voter result/UI cleanup

GameRoom direct forceout
    131
      ↓
    132
      ↓
    USERSLOTS / GAMEROOM_USERSLOTS mutation
```

目前沒有在 `723 -> sub_A19770 -> sub_A1A970/sub_A18F80` 的直接 C call chain 裡看到：

```text
Packet 396
Packet 131
```

因此尚不能宣稱：

```text
723 success -> 131
```

也不能宣稱：

```text
723 success -> 396
```

更合理的目前模型是：**投票結果與實際 room removal 可能由 Server 在不同 packet/lifecycle 路徑通知 Client；Client 對收到的 removal/sync packet 再執行 slot mutation。**

這一點仍需要 server-side traffic 或更多 client-side xref/vtable evidence 最終封閉。

## 七、後續追查優先級

```text
A. 132 status nonzero 的完整 enum
   -> 各 status 對應 message/UI/room mutation

B. 723 final result -> 是否還有另一個未直接顯示的 network/event path

C. 396 request
   -> 搜索所有 opcode metadata / indirect packet construction
   -> 確認是否 Client 實際會主動發送

D. `sub_6FC460`
   -> 完整 user-slot removal/reset semantics

E. `sub_67D520 / sub_67D440 / sub_67D240`
   -> 封閉 player/team/state identity semantics
```
