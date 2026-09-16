# PaperMan 2016 JP — TCP Opcode 166 Field Map

> 研究日期：2026-09-17  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA `PaperMan.exe.c` exact parser trace + cross-function data flow  
> Confidence：直接 Client parser/consumer = A；semantic 尚未閉合處保留 raw field

本文件不是把 166 強行命名成單一 struct，而是把目前 Client 實際解析到的每個 subtype、欄位寬度、順序與已知 downstream 用途集中保存。

---

## 1. Outer 166 framing

Receive chain：

```text
TCP dispatcher
  → case 166
  → sub_58D820
  → sub_749B90
```

`sub_749B90()` 在 gameplay gate 成立時先解析：

```text
u8 outer_actor_id = n16
u8 subtype        = n18
```

因此：

```text
166 body
  = u8 actor/player-like id
  + u8 subtype
  + subtype-specific payload
```

`outer_actor_id` 常進 `sub_67DF00/sub_67DF70/sub_67D7D0`；目前保持為 compact actor/player identity，而不直接改叫 slot index。

---

## 2. Subtype 1 — `sub_746360`

Payload：

```text
u8 target_id = n16_1
```

Downstream：

```text
sub_67DF00(target_id)
→ player object/controller
→ if outer_actor_id != local player: sub_5B8EE0(controller)
→ sub_5B8F70(controller)
```

可確認用途：server event 觸發 actor controller 的 reset/state callback。

尚未確定：`target_id` 的公開事件名稱。

---

## 3. Subtype 2 / 16 — `sub_7463E0`

### 3.1 Shared payload

依序：

```text
u32 v94
u8  participant_B = n16_2
u16 resource_id   = v90[0]
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

### 3.2 Participant direction

```text
outer n16      = participant_A
payload n16_2  = participant_B
```

兩者分別：

```text
sub_67D7D0(A)
sub_67D7D0(B)
```

並存在 local-vs-remote branch。

### 3.3 `resource_id`

進入：

```text
sub_5F5400(resourceTable, resource_id)
sub_5F5450(resourceTable, resource_id)
sub_5EF5B0 / sub_5EFE00 / sub_5EF5F0
```

因此 `resource_id` 是此 event 的重要 semantic anchor。

### 3.4 `n2`

已直接確認 downstream mapping：

```text
n2 == 1 → sub_61FC20(..., 6, resource_id)
n2 == 2 → sub_61FC20(..., 4, resource_id)
n2 == 3 → sub_61FC20(..., 7, resource_id)
n2 == 4 → sub_61FC20(..., 5, resource_id)
default  → sub_61FC20(..., 1, resource_id)
```

`sub_61FC20` → `sub_6745C0`，建立 0x84-byte local event object。這個 `a4/type` 是 presentation/effect event type，不是 wire subtype 本身。

### 3.5 `n10`, `n10_1`

目前保留 raw byte。兩者參與 `sub_7463E0()` 的 local/remote state/effect branches，但完整公開 semantic 尚未閉合。

### 3.6 `v89`, `v95`

已直接 observation：

```text
v89 → local player object +164
v95 → local player object +172
```

目前不能直接命名成 HP、score、timestamp 或 sequence。

### 3.7 `v94`

與：

```text
dword_F2A65C
```

比較。

`dword_F2A65C` 本身來自 269 subtype 7 的 server state packet；因此 `v94` 很可能是某種 server/gameplay state token，但 exact semantic 未閉合。

### 3.8 Death/state transition

對 payload participant B 的 remote branch：

```text
sub_67DF00(B)
→ controller
→ sub_9BC470(controller-related object, 1, timeLike, 0, 0)
```

`sub_9BC470()` 明確：

```text
controller +56 = 1
controller +16 = 0
controller +60 = supplied time-like value
controller +64 = timeGetTime()
clear state arrays/timers
sub_5B7AF0(controller)
```

另有 `CViewObj::OnDeadCtrl` diagnostic path。

因此 subtype 2/16 **包含** 可證實的 death/state-transition branch；不能因此把兩者整體命名成單一 DeathPacket。

### 3.9 Round Kill/Death counters

在普通 `a4=0` 路徑：

```text
participant A → player +240600 ++
participant B → player +240604 ++
```

這形成：

```text
+240600 = live round/mode-local Kill count for first participant
+240604 = live round/mode-local Death count for second participant on a4=0 path
```

subtype 16 (`a4=1`) 不做 victim `+240604` increment。

### 3.10 Local event presentation

`sub_6745C0()` 建立 event object，保存：

```text
participant A/B ids
wire-derived n2→mapped effect type
resource id
creation timestamp
```

並 queue 到 `sub_617290()`。

### 3.11 Quest hook

`sub_92EF00(3, n2, 0, resource_id)` / `(4, n2, 0, resource_id)` 是 quest/event-progress notification system。

`sub_92EF00()` 會在 quest table 中尋找：

```text
quest entry +2324 == n2
```

並更新 quest progress。

因此不能把 `n2` / `sub_92EF00()` 直接命名成 Kill/Assist packet field；它是 gameplay event → quest progression hook。

---

## 4. Subtype 3 / 20 — `sub_747980`

共用 parser：

```text
u32 v21
u8  participant_B = n16_1
u16 resource_id   = v19[0]
u8  n20
u8  effect_a      = v15
u8  effect_b      = v18
u32 value_1       = v16
u32 value_2       = n26
u8  tail_flag     = n0x1E
```

先驗證：

```text
dword_F2A65C == v21
```

再：

```text
sub_747460(this,
           outer n16,
           n16_1,
           resource_id,
           n20,
           value_1,
           value_2,
           tail_flag,
           subtype)
```

若 outer actor 非 local：

```text
sub_747B90(resource_id, n16_1, effect_a, effect_b, outer n16)
```

`sub_747B90()` 會查 Resource、計算 effect/timing，最後對 target controller 執行 `sub_5B8E90()`。

**目前高可信：**這是 resource/impact/gameplay effect event family。

**尚未確定：**

```text
n20
value_1
value_2
effect_a/effect_b
tail_flag
```

的公開名稱。

---

## 5. Subtype 4 — `sub_748860`

Payload：

```text
u32 value_0     = n0x64
u16 value_1     = n0xA
u32 resource_or_token = v22
u32 value_2
u32 value_3
u32 value_4
u32 value_5
u32 value_6
u32 value_7
```

所有後六個 scalar 經 `sub_592B40()`，helper 本身為 **4-byte reader**。

主要 consumer：

```text
sub_61BA90(...)
```

接著對 resource category `1..7` 有特殊 effect path，部分情況觸發 `sub_885680()`，並建立 Packet `174` 的後續訊息。

**結論：** effect/resource-heavy server event；尚不能把六個 DWORD 猜成固定公開字段。

---

## 6. Subtype 5 — `sub_748A50`

Payload：

```text
u32 value_0
u8  control
u32 resource_id_0
u32 effect_0
u32 effect_1
u32 effect_2
u32 effect_3
u32 effect_4
u32 effect_5
```

前三個後續 DWORD 等經 `sub_592B40()`，確定為 4 bytes each。

Resource：

```text
sub_5F5400(resource_id_0)
sub_5F5450(resource_id_0)
```

特殊 branch 直接進：

```text
sub_84C900
sub_84C7B0
sub_84C670
sub_84C920(0.02)
sub_5B7050
sub_5B6C40
```

其中 local-player / current-player 判斷存在。

**尚未閉合：**每個 effect DWORD 的公開語義。

---

## 7. Subtype 6 — `sub_748CD0`

Payload：

```text
u16 value_0
u16 resource_id
u32 value_2
u32 value_3
u32 value_4
u32 value_5
u32 value_6
u32 value_7
u8  tail
```

Resource metadata：

```text
sub_5F5450(resource_id)
if category == 10 || category == 15:
    sub_5B6C40(...)
```

因此此 subtype 至少是 server→client resource/gameplay state/effect family。

---

## 8. Subtype 7 — `sub_748E40`

Payload：

```text
ASCII-Z string
```

由 `sub_592730()` 解析，然後：

```text
sub_61FCB0(&dword_1D09130, outer_actor_id, string, nullptr)
```

目前 semantic 是 text/event notification family；不是 numeric gameplay state。

---

## 9. Subtypes 8 / 9 / 18 / 25 — `sub_748EB0`

這些 subtype 共用 event callback routine。

目前 parser 不再讀自己的固定 scalar payload；主要作用是：

```text
object/game controller callback
sub_9F94C0(this +1612)
UI render/cleanup
```

部分 dispatcher context 在 subtype 8/9/18/25 後還會再解析 `u32` time-like field，交 `sub_7498E0()`。

因此要注意：

```text
subtype 8/9/18/25
```

的完整 wire body 可能依 dispatcher context 包含附加時間欄位；不能只看 `sub_748EB0()` 本體就斷言 body length。

---

## 10. Subtype 10 — `sub_749230` / `sub_749520`

Dispatcher 先讀：

```text
u8 participant_id
u8 n13
```

之後根據 `n13` 選：

```text
n13 == 1 → sub_749230(...)
else     → sub_749520(...)
```

兩者後續共用：

```text
u8 tail_flag = n0x1E
u32 resource/value = v22 or v21
u32 value_2 = n26
u32 value_3/time-like = v18/v16
```

並明確查找：

```text
Resource("FIRE_BOMB")
```

且 n13 `9/10/13` 有不同 runtime state path。

`n13 == 13` 時會直接寫 player state：

```text
player +79 = 1
player +316 = 1
```

並建立 resource-derived timer/effect。

**目前可確認：** FIRE_BOMB-related gameplay event family。

**尚未確定：** n13 9/10/13 的公開 enum 名稱，以及其全部 resource semantics。

---

## 11. Subtype 11 — `sub_7494B0` / `sub_749810`

Dispatcher 先讀：

```text
u8 n7
```

若 `n7 == 1`：

```text
sub_7494B0(player)
```

直接：

```text
player/controller state +85 = 0
player +106 = timeGetTime()
player +80 object +24 = 0
```

否則：

```text
sub_749810(player, n7, outer_actor_id)
```

會：

```text
sub_9BB9F0(player, 0, 1)
```

以及 local-player special branch。

**結論：** compact player-state reset/update event；完整 `n7` enum unresolved。

---

## 12. Subtype 12 — `sub_749A30`

Payload：

```text
u16 value_A
u16 value_B
```

Downstream：

```text
sub_67CD20(n9_0, value_A, value_B, 2 - !sub_67F2F0())
```

接著刷新 `1612` / UI renderer / sound state。

目前 `value_A/B` semantic 未閉合。

---

## 13. Subtype 13 — inline lifecycle/reset path

目前 inline path 不經獨立 parser function。

主要動作：

```text
sub_568540
sub_71F830
for slot 0..15:
    byte_F6DD11[slot] = 0
    sub_95EC00(slot)
    sub_9942D0(...)
sub_718000
sub_7603A0(..., packet)
sub_67B5C0(...)
sub_62D570
sub_720A10
```

因此 subtype 13 是大型 gameplay lifecycle/state reset family。

**不能目前直接命名成 Respawn / RoundEnd；必須再與 GameRule 133/134/137/138、269 state、resource mode context 串起來。**

---

## 14. Subtype 14 — `sub_749AB0`

固定 payload：

```text
u32 time_like
u16 sample_0
u16 sample_1
u16 sample_2
u16 sample_3
u8  flag
```

`sub_5B3DD0()` 保存兩筆 transform/state samples；後續 `IPaperCtrl::sub_9BCBD0()` 使用新舊 sample 做插值。

目前高可信：

```text
server → client actor transform/interpolation update
```

但：

```text
sample_0..3
flag
time unit
```

的公開 semantic/coordinate packing 尚需 ASM/LST。

---

## 15. Subtype 15 — `sub_748420`

Payload：

```text
u8  participant_B
u16 resource_id
u8  control_0
u8  control_1
u8  control_2
u32 value_0
u32 value_1
u8  tail
```

Resource / participant context：

```text
sub_67DF00(outer actor)
sub_67DF00(participant_B)
sub_995A00(..., tail)
sub_9BB9F0(...)
sub_747E50(...)
```

並建立多種 timed visual/effect records，部分 resource branch 直接進 `sub_74CB20()`。

**目前：** resource/state transition family；尚未閉合每個 scalar。

---

## 16. Subtype 17 — `sub_748FF0`

與 `sub_748EB0()` 結構相似，但最後 callback/cleanup slightly different：

```text
sub_7093A0() (mode-dependent)
sub_9F94C0(this +1612)
sub_62DCF0
sub_62E9E0
sub_62C180
sub_5A06B0
```

目前保留為 event callback family。

---

## 17. Subtype 19 / 23 / 30 / 31 / 32

目前 direct parser/handler 已定位：

```text
19 → sub_74D150
23 → sub_74D410
30 → sub_74D510
31 → sub_74D5D0
32 → sub_74D5D0
```

這些 handlers 尚未完全還原；目前不從函式編號、相鄰 subtype 或名字推導公開 semantics。

後續必須以：

```text
parser read widths
caller context
resource/xref
state mutation
UI string
ASM
```

逐項閉合。

---

## 18. Subtype 20

`sub_747980()` shared parser，同 subtype 3。

因此 wire fields 與 subtype 3 相同，但 dispatcher passes `n3 = 20`，會進相同 core effect function：

```text
sub_747460(..., n3=20)
```

不能因此假設 subtype 20 和 subtype 3 完全語義相同；`n3` 仍會影響 `sub_747460()` 的 mode/effect path。

---

## 19. Subtype 21 — `sub_747DD0`

先驗證：

```text
outer actor_id != local player
```

Payload：

```text
u8 participant
u16 resource_id
u8 effect_a
u8 effect_b
```

直接：

```text
sub_747B90(resource_id, participant, effect_a, effect_b, outer actor_id)
```

與 subtype 3/20 的 tail effect path 共用 `sub_747B90()`。

**高可信：** compact server resource/effect event。

---

## 20. Subtype 22 — `sub_747AB0`

Payload：

```text
u32 state_token
u8 participant_B
u16 resource_id
u8 n20
u32 value_0
u32 value_1
u8 tail_flag
```

需：

```text
dword_F2A65C == state_token
```

後進：

```text
sub_747460(...)
```

因此它與 subtype 3/20 共用 effect/impact machinery，但沒有 subtype 3 parser 的第二個 post-handler `sub_747B90()` 路徑。

---

## 21. Subtype 24

Dispatcher inline：

```text
u16 field_A
u16 field_B
u32 elapsed_like
u8  flag
```

其中 `elapsed_like` 進：

```text
minutes = elapsed_like / 1000 / 60
seconds = elapsed_like / 1000 % 60
sub_7498E0(...)
```

因此已確認為 server-driven gameplay time presentation/update family。

不要直接將 1000 命名為 protocol millisecond unit；它只是此 client presentation calculation 的 divisor。

---

## 22. Subtype 26 / 27 / 29

目前：

```text
26 → sub_745F50
27 → sub_746060
29 → sub_746060
```

### subtype 26 parser

```text
u32
u16
u16
u16
u8
u8
u8
u8
u8
u32
```

→ `sub_604AC0(...)`

### subtype 27/29 parser

```text
u32
u16
u16
u16
u16
u8
u32
u32
u8
u32
u8
u32
```

`sub_746060()` 有明確 `CViewObj::OnBotDeadCtrl` diagnostics 與 `n27 == 27` special branch。

因此至少屬於 bot/player AI death/state family，但 exact per-field semantics 尚未閉合。

---

## 23. Current rule for upgrading field names

只有以下證據之一成立才升級公開 semantic name：

```text
1. Client 直接把欄位拿去明文命名/Resource lookup
2. 同一欄位在多個 function 中一致使用
3. Resource/Widget/Quest/Wiki 與 code data flow 互相吻合
4. ASM/LST 修正 Hex-Rays 型別或寬度後仍一致
```

否則保持：

```text
RawXX / field_XX / value_N
```

不要用猜測名稱污染後續 Server implementation。

---

## 24. Current high-value cross-links

```text
166 subtype 2/16
    ↔ 269 subtype 7 server player state
    ↔ +240600/+240604 live round K/D
    ↔ +60150/+60151 result-screen MY K/D
    ↔ Resource(v90[0])
    ↔ Quest(sub_92EF00)

166 subtype 3/20/21/22
    ↔ sub_747460
    ↔ Resource metadata
    ↔ sub_747B90

166 subtype 14
    ↔ sub_5B3DD0
    ↔ IPaperCtrl::sub_9BCBD0
    ↔ UDP 8/24 movement state

166 subtype 10
    ↔ Resource("FIRE_BOMB")
    ↔ sub_74CB20
    ↔ timed player state

166 subtype 13
    ↔ GameRule / gameplay lifecycle
    ↔ 16-slot state reset
```

這些 cross-links 應視為後續逐欄位研究的索引，而不是把尚未閉合的 semantic 當成定論。
