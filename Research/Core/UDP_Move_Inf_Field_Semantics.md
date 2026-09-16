# UDP `Y_UDP_S_MOVE_INF` — Field Semantic Evidence Addendum

> 研究日期：2026-09-16  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Scope：補充 `Research/Core/UDP_Move_Inf_DeepEvidence.md`

## 1. 最後的 `u32 field_0E` 不應暫時命名成單純 flags

在 `sub_602E30()` 中，每個 actor record 的最後一個欄位：

```text
field_0E = v29 : u32
```

會進入：

```text
sub_5E2570(actor, packet, n16, v29, &position, v14, v30)
sub_548E80(player, v29, byte_EE896D, byte_13242D0)
```

`sub_548E80()` 對 `a2 = v29` 做非常具體的 Resource-name lookup：

```text
sub_5F5500(resourceTable, "BOMBPLANT")
sub_5F5500(resourceTable, "Pulp_A")
sub_5F5500(resourceTable, "Pulp_B")
sub_5F5500(resourceTable, "magic_finger")
sub_5F5500(resourceTable, "Escape")
```

並另外檢查 actor object 中 4 組連續 resource/action-like slots：

```text
+119699
+119700
+119701
+119702

+119721
+119722
+119723
+119724

+119743
+119744
+119745
+119746

+119765
+119766
+119767
+119768
```

因此 `field_0E` 至少是某種 **Resource/Action identifier 或與 action/resource state 直接相關的 32-bit value**。把它直接命名為 generic `flags` 會遺失這條很強的 semantic evidence。[A]

## 2. `sub_548E80()` 還顯示 field_0E 會觸發 client→server report

`sub_548E80()`：

```text
if player +240640 != 0
    return

if sub_548C80(player, field_0E)
    return

++player +240644

if player +240644 > 40:
    build TCP packet 714
```

Packet 714 的目前已證實 payload construction：

```text
u8  local player/network id
u8  byte_EE896D
u8  player +240596
string player +64
u32 field_0E
```

然後：

```text
sub_55D960(packet)
```

送出。

這代表 movement record 裡的 `field_0E` 並非純粹 renderer-local value；它能一路影響到另一個 Client→Server network report path。[A]

**但不能據此把 714 命名成 anti-cheat packet 或 cheat report。** 現有程式只證明它是另一條 report/send path；用途名稱仍需 714 receive counterpart、字串/resource、ASM 或行為測試確認。[A]

## 3. `sub_548C80()` 的 filter 進一步支持 action/resource semantic

`sub_548C80(player, field_0E)` 回傳 true 的條件包含：

```text
field_0E == 0
field_0E == Resource("BOMBPLANT")
field_0E == Resource("Pulp_A")
field_0E == Resource("Pulp_B")
field_0E == Resource("magic_finger")
field_0E == Resource("Escape")
```

或 field_0E 等於 player 內 4 組 action/resource IDs 之一，最後還有一個 player flag fallback：

```text
player +9 != 0
```

因此：

```text
UDP Move field_0E
    ↓
action/resource identity filter
    ↓
可能形成 client-side report/state event
```

這是目前把 field_0E 從「unknown u32」提升到「resource/action related u32 candidate」最強的交叉證據。[A]

## 4. 與 `field_05` 的 distinction

`field_05`：

```text
sub_5B3180(actor, field_05)
→ actor +233 = field_05
```

目前更像 controller-local state byte。

`field_0E`：

```text
sub_548E80(actor, field_0E, ...)
→ Resource-name comparisons
→ potential Packet 714 report
```

因此兩者不要合併：

```text
field_05 = controller state byte candidate
field_0E = resource/action identifier candidate
```

兩者 semantic confidence 都仍低於完全命名；但它們的 downstream roles 已經明顯不同。[A]

## 5. Position fields 的證據仍保持獨立

`field_06..08`：

```text
u16 / 3.0
→ float x-like/y-like/z-like
→ sub_9BCB00
→ controller interpolation/current transform
```

因此目前 record 可以安全維持：

```text
field_02  actor/player id candidate
field_05  controller state byte candidate
field_06..08 spatial vector components
field_0E  Resource/Action identifier candidate
```

這種分層比直接產生一個猜測版 `MovementPacket` class 更符合 evidence-driven reconstruction。[A]

## 6. Server implementation consequence

在沒有更多 ASM/LST/Resource schema 前，server model 應保留：

```text
MoveRecord {
    byte   Raw00;
    byte   Raw01;
    byte   ActorId;
    uint   Raw03;
    uint   Raw04;
    byte   State05;
    ushort PosX3;
    ushort PosY3;
    ushort PosZ3;
    byte   Raw09;
    byte   Raw0A;
    byte   Raw0B;
    byte   Raw0C;
    byte   ActionState0D;
    uint   ResourceOrActionId0E;
}
```

其中 `ResourceOrActionId0E` 是目前最符合 cross-function evidence 的臨時 semantic 名稱；不是最終公開協議名稱。

## 7. Remaining proof targets

```text
sub_5E2570()
    → resolve remaining byte fields with ASM/LST

Packet 714 receive counterpart
    → determine why field_0E is reported

Extracted resource IDs
    → match BOMBPLANT/Pulp_A/Pulp_B/magic_finger/Escape

sub_5B71F0()
    → complete spatial/update side effects

TCP 166 subtype 14
    ↔ UDP 8/24
    → compare precedence when both update the same actor
```
