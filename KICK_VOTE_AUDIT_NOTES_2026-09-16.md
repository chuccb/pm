# PaperMan Kick Vote——逆向稽核筆記（2026-09-16）

## A. Team Scope 的篩選已直接連到玩家分組系統

目標列表的篩選最終會透過 `sub_67DDD0(record)` 呼叫 `sub_67D3F0(slot)`。

相關實作為：

```c
BOOL __cdecl sub_67D3F0(unsigned int slot)
{
    if (slot >= 0x10)
        return false;
    if (sub_67EB70())
        return true;

    v = sub_67D520(slot);
    return v == sub_67D240();
}
```

`sub_67D520(slot)` 取得特定玩家 slot 的分組／隊伍值，而 `sub_67D240()` 取得本地玩家對應的值。

因此，在 `sub_67EB70()` 特殊路徑之外，這個 predicate 實際上就是將玩家的分組／隊伍值與本地玩家值做相等比較。

這比先前「模糊的分組 predicate」描述更精確：

```text
scope 0 篩選 -> 與本地玩家同隊／同分組的候選人
scope 1 篩選 -> 不套用上述同隊限制的候選人
```

日本 Wiki 也獨立描述 Team Kick 僅限申請者同隊玩家，而 Full Kick 可作用於全體參與者。因此兩條證據在行為層面高度一致。

### 重要細節

`sub_67EB70()` 可以強制讓 predicate 回傳 true。這個全域／模式輔助函式在 Kick Vote 中的精確觸發條件仍需另外恢復，因此實作時應保留這個特殊覆寫，而不能簡化成無條件 `teamId == localTeamId`。

## B. 718：不可相信 Hex-Rays 顯示的第二、第三參數 `char` 型別

目前反編譯函式原型看起來像：

```c
IVotingNetwork::sub_A191D0(char *this, int scope, char reason, char target)
```

但實際序列化時三個值全部呼叫 `sub_592A20`：

```c
v4 = sub_592A20(v7, scope);
v5 = sub_592A20(v4, reason);
sub_592A20(v5, target);
```

`sub_592A20` 是這個封包層使用的 4-byte 原始整數寫入函式。

更重要的是，目標選擇 callback 從 36-byte 目標列表項目取得 player ID 的 DWORD 值，再把該值傳入 request callback。

因此安全的重建方式為：

```text
718 邏輯欄位：
  field 0 = scope，序列化 4 bytes
  field 1 = reason index，序列化 4 bytes
  field 2 = target player ID，序列化 4 bytes

payload = 12 bytes
```

Hex-Rays 顯示的 `char` 是不可靠的型別恢復結果，不能拿來當作 wire field 寬度證據。

### 後續逆向的判斷優先順序

對封包 layout，建議依以下證據強度判斷：

1. 實際 serializer 的寫入寬度，例如 `sub_592A20`、`sub_5928E0`；
2. receiver parser 的讀取寬度，例如 `sub_592A40`、`sub_592940`；
3. caller 的資料流與欄位來源；
4. 最後才參考 Hex-Rays 顯示的 C 參數型別。

這可以避免因為間接呼叫而被 Hex-Rays 錯誤縮成 `u8`，尤其是 32-bit player ID。

## C. 目前 718～723 的欄位寬度

```text
718 = u32 + u32 + u32 = 12-byte 邏輯 payload
721 = u8 = 1-byte 邏輯 payload
720 = u32 + u32 + u32 + u32 + u8 = 17-byte 邏輯 payload
722 = u32 + u8 = 5-byte 邏輯 payload
723 = u8 + u32 = 5-byte 邏輯 payload
719 = u8 = 1-byte 邏輯 payload
```

Packet send path 外層還會加入 8-byte framing/header，因此以上數字是邏輯 payload 大小，不是 TCP 上最終封包總長度。

## D. 證據定位

### IDA／C

- `sub_A191D0`／718 serializer：`PaperMan.exe.c` 約第 699767–699787 行。
- `sub_67D3F0`／同分組比較：`PaperMan.exe.c` 約第 287387–287415、287700–287728 行。
- `sub_67D520`／每個 slot 的分組值：`PaperMan.exe.c` 約第 287390 行附近。
- `sub_A190C0`／目標選擇 callback：`PaperMan.exe.c` 約第 699730–699775 行。

### Wiki

日本 PaperMan Wiki 的 `操作ガイド` 描述 Team Kick 僅限申請者同隊使用者，Full Kick 適用於全體參與者，並列出相應的最低參與者條件、70 秒投票時間及六種理由。

## E. 目前仍開放的項目

- scope 0/1 的內部正式 enum／symbol 名稱；
- `sub_67EB70()` 在 Kick Vote 中的特殊覆寫條件；
- 719 status enum 的精確值義；
- 723 result enum 的精確值義；
- 伺服器端實際 timeout／最終計票演算法；
- 396/397 Master／房間協定的完整 body 與跨層關聯。
