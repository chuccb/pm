# 玩家 Slot、Player ID 與 Team／Group 機制研究

> 研究日期：2026-09-16

## 1. 固定的 16-slot 玩家模型

目前 `PaperMan.exe.c` 中有大量核心函式以：

```c
for (i = 0; i < 16; ++i)
```

掃描玩家資料表；玩家資訊以大型固定 stride 結構儲存在 `byte_F33120` / `dword_F6DCF4` 等全域資料中。

Kick Vote、Ready、Force Out、Change Slot、Match Start 等多個子系統都共用這個 16-slot 模型。

## 2. 本地玩家 Slot

`sub_67D110()`：

```c
if (n2 == 2)
    n0x10 = -2;
else
    n0x10 = ::n0x10;

if (n0x10 >= 0x10)
    return -1;

for (i = 0; i < 16; ++i)
{
    if (byte_F6D9E4[240780 * i] == 0
        && byte_F6DD11[240780 * i] == 0
        && n0x10 == dword_F6DCF4[60195 * i])
        return i;
}
return -1;
```

因此 `::n0x10` 是一個可拿來映射到 16-slot player table 的本地玩家識別值。

這與 Kick Vote 中：

```c
(slot_record - byte_F33120) / 0x3AC8C
```

取得 slot index 的資料結構可以互相對照。

## 3. Player ID 與 Slot 並不是必然相同

`sub_67D110()` 使用全域 `::n0x10` 去搜尋：

```c
dword_F6DCF4[60195 * i]
```

找到後才返回真正的 slot index `i`。

因此在 Server 重建時應分開保存：

```text
Player
    PlayerId
    SlotIndex
    Team/GroupId
    Active/Occupied state
```

不能因為兩者都以 byte/int 形式出現，就直接假設 `PlayerId == SlotIndex`。

## 4. Player ID → Team／Group

`sub_67D240()` 取得本地玩家的 group/team 值：

```c
v1 = sub_407E80(this_15, byte_EE896D);
...
return (*(**(v1 + 132) + 40))(*(v1 + 132));
```

`sub_67D520(a1)` 則對指定 player/group key 取得另一個 group/team 值：

```c
return (*(**(v2 + 132) + 48))(*(v2 + 132), a1);
```

接著 `sub_67D3F0(slot)`：

```c
if (sub_67EB70())
    return true;

v2 = sub_67D520(slot);
return v2 == sub_67D240();
```

因此在一般路徑中，Team／Group 的判定確實是「指定玩家的 group 值 == 本地玩家的 group 值」。

這就是 Kick Vote Team Kick filter 的直接底層依賴之一。

## 5. Group 相等比較不只用於 Kick Vote

另外存在：

```c
sub_67D600(a,b)
{
    return sub_67D440(a) == sub_67D440(b);
}

sub_67D630(a,b)
{
    return sub_67D520(a) == sub_67D520(b);
}
```

因此客戶端內部至少存在兩種「玩家分類值」比較：

```text
sub_67D440()
    -> 一種 player relation / grouping value

sub_67D520()
    -> Team／Group 相關值
```

不能把所有 `group-like` 欄位都直接命名成 `TeamId`；應依 caller 使用情境分開建立語意。

## 6. Slot active / occupied 判定

`sub_67D310(n16)`：

```c
if (sub_67E940(n16))
    return 1;
if (n16 >= 0x10)
    return 0;
if (byte_F6D9E4[240780 * n16] != 0)
    return 0;
if (byte_F6DD11[240780 * n16] != 0)
    return 0;

v2 = dword_F6DCF4[60195 * n16];
if (sub_67D010() == v2)
    return 2;
else
    return 1;
```

在沒有特殊 `sub_67E940()` override 的一般情況下：

```text
return 0 -> slot 不可視為一般 active participant
return 1 -> active participant，但不是本地玩家
return 2 -> active participant，而且是本地玩家
```

這是非常重要的共用 helper，因為它提供了玩家是否佔用 slot、是否為 local player 的統一判定。

## 7. 所有玩家是否都已進入有效狀態

`sub_67D680()`：

```c
for (i = 0; i < 16; ++i)
{
    if (byte_F6D9E4[240780 * i] == 0
        && byte_F6DD11[240780 * i] == 0)
        return 0;
}
return 1;
```

`sub_67D6F0()` 則進一步要求每一個符合 slot 條件的玩家通過 `sub_67D3B0(playerId)`。

這說明 `PaperMan` 在某些操作中會有「全部有效玩家已完成某個狀態」的全局判定，而不是單純靠人數。

## 8. `CGameRule::NewGameStart` 中的 team balance 條件

`NewGameStart` 會重新掃描 16 個 player record：

```c
v25 = sub_67DE10(0, 3);
while (v25 != nullptr)
{
    if (sub_67DDD0(v25))
        ++n2;
    else
        ++n2_1;
    v25 = sub_67DE10(v25, 3);
}

if (n2 < 2 || n2_1 < 2)
{
    *(this + 82) = 1;
    *(this + 81) = 1;
}
```

結合 `sub_67DDD0 -> sub_67D3F0` 可知這是在依目前 player grouping/team relation 將參與者分成兩群，並檢查兩邊是否至少有 2 人。

因此 `NewGameStart` 本身就會檢查 team distribution，而不是只由房間 UI 決定是否可以開始。

這是之後恢復 `チームサバイバル`、`チーム戦術モード`、`爆破ミッション` 等 team-based mode 的重要入口。

## 9. 對 Server 重建的直接意義

核心資料模型應至少把下列概念分開：

```text
Room
    GameMode
    Map
    Period / Rule
    MasterPlayerId

PlayerSlot[16]
    Occupied
    PlayerId
    TeamId / GroupId
    ReadyState
    InGameState
    ConnectionState
    Character / loadout 等
```

然後由 server authoritative state 決定：

```text
是否可 Ready
是否可 Start
能否換 Slot
玩家屬於哪一隊
誰可看到哪些玩家
哪些玩家可作為 Kick Vote target
誰需要被 Force Out
```

不要將 client 的全域 `dword_F6DCF4`、`byte_F6D9E4` 等直接照搬成 Server API；它們是 client storage implementation。真正要重建的是它們所代表的狀態關係。

## 10. 目前最值得再追的 helper

```text
sub_67E940()
    -> Slot override / special participant 判定

sub_67D440()
    -> 第二種 grouping / relation 值

sub_67D520()
    -> Team / Group value

sub_67DFB0()
    -> player-specific object

sub_67D7D0()
    -> Slot -> player ID mapping

sub_67DE10()
    -> player record iterator
```

將這一組 helper 封閉後，幾乎所有房間／GameRule 功能都會得到共同的 Player 基礎資料模型。
