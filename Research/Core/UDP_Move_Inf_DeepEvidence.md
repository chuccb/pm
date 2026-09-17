# UDP `Y_UDP_S_MOVE_INF` 深入證據

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是 UDP 8/24 `Y_UDP_S_MOVE_INF` 的唯一深入證據主文件，整合原本的傳輸／Queue／Wire Layout 分析與欄位語意補充。後續不要再建立另一份平行的 `UDP_Move_Inf_*` 深入真相；欄位總表或摘要若需要存在，必須只引用本文件。

## 1. Receive chain：8/24 的 Queue Consumer 已閉合

```text
CUDPManager::sub_595840
    → sub_595A60
    → recvfrom
    → Packet validity checks
    → sub_595E80
    → opcode 8 / 24
    → sub_596940
    → sub_593750
    → queue node
    → sub_593510（每次中央更新處理）
    → sub_602E30(node Packet)
    → 每玩家 movement/state decode
```

`sub_596940()` 有明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

且只有在 `n15 == 13` 時進入 `sub_593750()`；因此 8/24 屬於 gameplay state 下專用的 `S_MOVE_INF` family。[C]

## 2. `sub_593510()` 是每次更新的 Queue Processing，不只是 Shutdown Cleanup

完整 call graph 顯示：

```text
sub_406830(...)
    → sub_58AFD0(...)
        → sub_593510(&byte_1324330)
```

`sub_406830()` 是中央更新路徑之一，另外的 gameplay loop 也會經由 `sub_58AFD0()` 使用它。因此 `sub_593510()` 的實際角色是：

```text
每次中央 update
    → lock UDP movement queue
    → 逐一處理 Packet node
    → sub_602E30(node Packet)
    → 清除已處理 list
```

Shutdown 則另有 `sub_58AF90 → sub_595D50 → DeleteCriticalSection_w`；static object destruction 由 `sub_ADC370 → sub_593410` 處理。因此不能把 `sub_593510()` 簡化命名成 cleanup。[C]

## 3. Queue node 的部分結構

`sub_593750(queue, packet)`：

```text
EnterCriticalSection(queue + 20)
    → v3 = *(queue + 12)
    → sub_5951C0(queue + 8, queue + 8, v3, packet)
LeaveCriticalSection
```

`sub_5951C0()` 建立 node；`sub_593320()`／相關 node builder 最終寫入：

```text
node +0  = iterator/link value
node +4  = list/link value
node +8  = Packet object
```

`Packet::possible_ctor_or_dtor_1(node + 8, a4)` 會複製 packet payload/state metadata，因此 iterator 取得的是 node +8 的 Packet object，並可直接傳至 `sub_602E30()`。[C]

## 4. `sub_602E30()` 是實際 Movement / Actor State Consumer

`sub_602E30()` 開頭會檢查 gameplay state；條件符合後讀取：

```text
u8 count
```

若 count=`N`，便連續解析 `N` 筆 actor record，再把解析值套用至 actor/controller state。[C]

因此目前最強結論是：8/24 並非只進入 queue；Queue 最終確實會把資料送入 gameplay movement/state consumer。[C]

## 5. 單筆 actor record 的目前可證實 Wire Layout

`sub_602E30()` 使用 `sub_592940` / `sub_592A00` / `sub_592A40` 依序讀取：

```text
u8   field_00 = v28
u8   field_01 = v19
u8   field_02 = n16
u32  field_03 = v30
u32  field_04 = v16
u8   field_05 = v25[0]
u16  field_06 = v35
u16  field_07 = v36
u16  field_08 = v37
u8   field_09 = v23
u8   field_0A = v38
u8   field_0B = v14
u8   field_0C = v15[0]
u8   field_0D = n0x1C
u32  field_0E = v29
```

因此單筆 parser footprint 為：

```text
3 × u8
+ 2 × u32
+ 1 × u8
+ 3 × u16
+ 4 × u8
+ 1 × u32
= 27 bytes
```

Body 解析形狀為：

```text
u8 N
repeat N:
    27-byte actor record
```

所以 `sub_602E30()` 的 body consumption 模型為：

```text
1 + 27 × N bytes
```

但這**不是**完整 UDP datagram length 公式；outer Packet header、padding、額外尾端資料與 transport framing 必須分開確認。[C]

## 6. `field_02` 是 Actor / Player Identifier Candidate

`n16` 會送入：

```text
sub_67DF00(n16)
sub_67D7D0(n16)
```

`sub_67D7D0()` 會將該值映射到 `<16` 的本地 slot 範圍，並進入 per-player state，例如：

```text
byte_F33120[240780 * slot + ...]
```

因此 `field_02` 至少可安全命名成：

```text
ActorId / PlayerId candidate
```

但目前不能強行區分它是 slot index、session player id 或 compact network id；真正 mapping 是：

```text
n16 → sub_67D7D0(n16) → local slot
```

[C]

## 7. `field_06..08`：3D Spatial Vector

`field_06..08` 會被除以 `3.0`：

```text
x = field_06 / 3.0
 y = field_07 / 3.0
 z = field_08 / 3.0
```

再組成 vector 並進入：

```text
sub_9BCB00()
```

`sub_9BCB00()` 將資料寫入 actor controller 的 sample state；後續 `IPaperCtrl::sub_9BCBD0()` 將新、舊 sample 做插值／平均後寫入 current transform/vector。[C]

因此現在可以把：

```text
field_06
field_07
field_08
```

定義為 **3D transform vector components candidate**。已高度支持它們是位置／空間同步值；但正式的座標軸名稱、單位與精確數值格式仍可待 ASM/LST 補強。[C][OPEN]

## 8. `field_04` 是另一個參與 Actor Runtime 的 u32

`field_04` 經 `sub_592AC0()` 以 u32 讀取，之後進入 movement/controller sample path。它會成為某個 sample 的第一個 component，再與位置資料一起傳給 `sub_9BCB00()`。[C]

但目前沒有足夠證據把它命名成 timestamp、sequence 或 velocity。保留為：

```text
field_04 = u32 runtime movement/sample component
```

並標 `[OPEN]`。

## 9. `field_05` 的 downstream state

`field_05` 會送入：

```text
sub_5B3180(actor, field_05)
```

而 `sub_5B3180()` 把它保存到 actor/player state `+233`；後續 controller logic 會繼續讀取。因此它不是 padding。[C]

目前只能命名為：

```text
field_05 = controller state byte candidate
```

## 10. `field_09..0D` 都參與 Gameplay State，但尚未完成公開命名

這幾個 byte 會被送入例如：

```text
sub_5E2570(..., field_0E, ..., field_0B, field_04)
sub_5B34B0(..., field_0E, field_0D, field_0A, ..., field_02)
```

並最終更新 controller／movement state，包含 vtable callback。[C]

目前不得直接把它們命名成 crouch、fire、stance、weapon、jump 等。這些名字即使看起來符合常見 FPS 結構，也不足以形成 confirmed 結論。[OPEN]

## 11. `field_0E`：Resource / Action Identifier Candidate

原先若將 `field_0E = v29` 命名成一般 `flags`，會忽略強烈的下游語意證據。

`v29` 會進入：

```text
sub_5E2570(..., v29, ...)
sub_548E80(player, v29, byte_EE896D, byte_13242D0)
```

`sub_548E80()` 對 `v29` 做非常具體的 Resource-name lookup：

```text
Resource("BOMBPLANT")
Resource("Pulp_A")
Resource("Pulp_B")
Resource("magic_finger")
Resource("Escape")
```

並另外檢查 actor object 中多組連續的 action/resource-like slots，例如：

```text
+119699..+119702
+119721..+119724
+119743..+119746
+119765..+119768
```

因此目前最強的臨時語意不是 generic flags，而是：

```text
field_0E = ResourceOrActionId（候選）
```

仍不應將其當成最終公開協定名稱；是否為單一 ID、Action ID 或 state word，需要更多證據。[C][OPEN]

## 12. `field_0E` 還會觸發 TCP 714 Report Path

`sub_548E80()` 還顯示：

```text
if player +240640 != 0
    return

if sub_548C80(player, field_0E)
    return

++player +240644

if player +240644 > 40:
    build TCP packet 714
```

714 目前可直接觀察到的建構內容包含：

```text
u8  local player/network id
u8  byte_EE896D
u8  player +240596
string player +64
u32 field_0E
```

再透過 `sub_55D960(packet)` 發送。[C]

因此 `field_0E` 明顯不是只存在於 renderer-local context 的值；它可以影響另一條 Client→Server network report path。[C]

但**不能**因為存在 714 report 就直接把 714 命名成 anti-cheat 或 cheat report。現有證據只證明它是另一條 report/send path；真正用途仍待 714 receive counterpart、Resource、ASM 或行為驗證。[C][OPEN]

## 13. `sub_548C80()` 的 Filter 進一步支持 Resource / Action 語意

`sub_548C80(player, field_0E)` 回傳 true 的條件包含：

```text
field_0E == 0
field_0E == Resource("BOMBPLANT")
field_0E == Resource("Pulp_A")
field_0E == Resource("Pulp_B")
field_0E == Resource("magic_finger")
field_0E == Resource("Escape")
```

或等於 player 內多組 action/resource identities；最後還有 player flag fallback：

```text
player +9 != 0
```

因此目前合理的語意鏈為：

```text
UDP Move field_0E
    ↓
action/resource identity filter
    ↓
可能形成 client-side report/state event
```

這是 `field_0E` 從「unknown u32」提升到「Resource/Action identifier candidate」最強的交叉證據。[C]

## 14. `field_05` 與 `field_0E` 必須分開

目前可保持：

```text
field_05 = controller state byte candidate
field_0E = Resource/Action identifier candidate
```

兩者都會影響 actor state，但 downstream role 完全不同，不應在 Server object model 中合併成一個 `Flags` 欄位。[C]

## 15. Queue / Consumer 的 static lifecycle

初始化：

```text
sub_58ED30(...)
    → sub_595C90(CUDPNetworkManager,...)
    → sub_593460(&byte_1324330)
```

`sub_593460()`：

```text
queue state reset
InitializeCriticalSection(queue +20)
```

static constructor：

```text
sub_5933F0(&byte_1324330)
    → sub_5950E0(this +2)
```

static destructor：

```text
sub_ADC370()
    → sub_593410(&byte_1324330)
```

這支持「receive side enqueue + central update dequeue」的架構。[C]

## 16. Transport / Frame 與 Body Schema 必須分層

Packet object 至少具有：

```text
Packet +24 = payload buffer
Packet +28 = opcode
Packet +32... = parser cursor / boundaries
```

`sub_591F20()` 負責 length／total-frame metadata；sender side 最終會以 payload pointer 與 computed length 進行傳送。[C]

因此：

```text
1 + 27 × N
```

只能描述 `sub_602E30()` 消費的 movement body；不能直接當成 `sendto()` 的 datagram total length。[C]

Outer framing、sequence、checksum／obfuscation 仍需由 UDP sender、相關 parser、LST/ASM 確認。[OPEN]

## 17. Opcode 8 與 24：同一 Family，不等於所有 Context 都完全等價

Dispatcher：

```text
case 8:
case 24:
    sub_596940(packet)
```

兩者進入相同 queue，因此屬同一 `Y_UDP_S_MOVE_INF` handling family。[C]

但目前證據尚不足以宣稱：

```text
opcode 8 == opcode 24
```

在所有 sender、version、state context 下完全等價。因此 Server reconstruction 應至少保留 raw opcode，直到 sender/receiver role 與版本差異再閉合。[OPEN]

## 18. 與 TCP 166 subtype 14 的關係

TCP 166 subtype 14：

```text
u32 time-like
u16 × 4
u8 flag
    → sub_5B3DD0
    → transform samples
    → IPaperCtrl::sub_9BCBD0
```

UDP 8/24：

```text
u8 count
N × 27-byte actor records
    → sub_602E30
    → sub_9BCB00 / sub_5B34B0 / sub_5B71F0
    → actor runtime / transform state
```

兩者都能更新 actor transform/state，但 transport、wire layout、queueing 與處理 cadence 不同。因此不能將 UDP 8/24 直接寫成「166 subtype 14 的快版」。它們目前應保持為兩個不同的 wire synchronization mechanisms。[C]

## 19. Server Reconstruction 的暫時 Raw Schema

在公開語意尚未完全閉合前，Server compatibility layer 應保留 raw layout：

```text
MoveRecord
├─ byte   Raw00
├─ byte   Raw01
├─ byte   ActorId
├─ uint   Raw03
├─ uint   Raw04
├─ byte   State05
├─ ushort PosX3
├─ ushort PosY3
├─ ushort PosZ3
├─ byte   Raw09
├─ byte   Raw0A
├─ byte   Raw0B
├─ byte   Raw0C
├─ byte   ActionState0D
└─ uint   ResourceOrActionId0E
```

其中 `ResourceOrActionId0E` 是目前最符合跨函式證據的臨時名稱，而不是已閉合的官方欄位名稱。[C][OPEN]

## 20. Current Evidence Grade

### A：直接確認

```text
UDP 8 / 24 = Y_UDP_S_MOVE_INF family
n15 == 13 = 接受 gameplay state
sub_593750 = thread-safe enqueue
sub_593510 = per-update queue processing
sub_602E30 = actual movement/state consumer
body first byte = actor-record count
actor record parser footprint = 27 bytes
field_02 = actor/player identity candidate
field_06..08 = 3D spatial vector components candidate
record data = 直接修改 actor/controller movement-related state
field_0E = 確實進入 Resource-name lookup 與 TCP 714 report path
```

### B：高度可信但公開名稱尚未完全閉合

```text
field_04 = movement/runtime sample component
field_05 = controller state byte candidate
field_0E = Resource/Action identifier candidate
field_09..0D = gameplay/movement state/control values
```

### OPEN：不可提前升級

```text
field_00 = stance/posture ?
field_01 = movement mode ?
field_03 = sequence/tick ?
field_04 = timestamp ?
field_09 = animation/state ?
field_0A = direction/angle ?
field_0B = action ?
field_0C = weapon/action flag ?
field_0D = movement mode/input state ?
field_0E = exact bit layout / official semantic
714 = anti-cheat / cheat report ?
8 vs 24 = complete semantic equivalence ?
```

## 21. 下一個證據目標

```text
1. 用 ASM/LST 完整驗證 sub_5E2570 的 field_03/04/09..0D width 與 cursor offset。
2. 找到 UDP 8/24 sender constructor，確認 opcode role。
3. 完整追 sub_5B71F0() 的 transform/state side effect。
4. 完整拆 sub_548E80()/sub_548C80()，確定 field_0E 的 resource/action bit semantics。
5. 找出 TCP 714 receive counterpart，確定 field_0E report 的實際用途。
6. 將 Extracted 中 BOMBPLANT/Pulp_A/Pulp_B/magic_finger/Escape 對應的 resource metadata 與 0E 對照。
7. 比對 TCP 166 subtype 14 與 UDP 8/24 對同一 actor controller offset 的寫入先後。
8. 追查 checksum、sequence、obfuscation 是否位於 UDP outer frame。
```

在這些證據閉合前，不為未知欄位建立猜測式正式語意，也不因 Server 編譯需要而任意填 `0` 或固定值。
