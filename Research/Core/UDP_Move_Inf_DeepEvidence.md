# UDP `Y_UDP_S_MOVE_INF` — Deep Evidence / Queue Consumer / Wire Layout

> 研究日期：2026-09-16  
> Target：PaperMan 日本版 2016 結束營運時最終版 Client  
> Evidence：IDA Hex-Rays C export + cross-function data flow  
> Confidence：直接 Client code = A；未閉合 semantic 保留 raw field/offset

本文件補充 `Gameplay_Network_Events.md`。重點是把 UDP 8/24 (`Y_UDP_S_MOVE_INF`) 從「只確認 enqueue」進一步追到 **queue consumer、實際 parser、每 actor wire body 長度與 downstream transform/state mutation**。

---

## 1. Receive chain：8/24 已由 consumer 閉合

```text
CUDPManager::sub_595840
    -> sub_595A60
    -> recvfrom
    -> Packet validity checks
    -> sub_595E80
    -> opcode 8 / 24
    -> sub_596940
    -> sub_593750
    -> queue node
    -> sub_593510 (per-tick processing)
    -> sub_602E30(node Packet)
    -> per-player movement/state decode
```

`sub_596940()` 的明文 diagnostic：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

而且僅在 `n15 == 13` 時呼叫 `sub_593750()`；否則進錯誤/reset path。因此 8/24 屬於 gameplay 狀態下專用的 `S_MOVE_INF` family。[A]

---

## 2. 重要修正：`sub_593510()` 不是單純 shutdown cleanup

之前只看局部 control flow 容易把 `sub_593510()` 誤解為 queue cleanup routine。完整 call graph 顯示：

```text
sub_406830(...)
    -> sub_58AFD0(...)
        -> sub_593510(&byte_1324330)
```

而 `sub_406830()` 是遊戲中央更新路徑之一；另外 `sub_7982F0()` 等 gameplay loop 也呼叫 `sub_58AFD0()`。

因此 `sub_593510()` 的實際角色是：

```text
每次中央 update：
    lock UDP movement queue
    iterate queued Packet nodes
    sub_602E30(node Packet)
    clear processed list
```

它同時確實會在最末端重新建立 opcode 697 的 Packet（在特定 timeout/keepalive path），所以不能只用「shutdown cleanup」命名它。[A]

真正 shutdown 時則另有：

```text
sub_58AF90
    -> sub_595D50
    -> DeleteCriticalSection_w
```

以及 static destructor：

```text
sub_ADC370
    -> sub_593410
```

`sub_593410()` 才是 static object destruction / list destruction 路徑。[A]

---

## 3. Queue node 結構已可部分還原

`sub_593750(queue, packet)`：

```text
EnterCriticalSection(queue + 20)
    v3 = *(queue + 12)
    sub_5951C0(queue + 8, queue + 8, v3, packet)
LeaveCriticalSection
```

`sub_5951C0()` 呼叫：

```text
sub_595320(this, a3, *(a3 + 4), a4)
```

`sub_595320()` 建立 node 並寫入：

```text
node + 0  = a2
node + 4  = a3
node + 8  = Packet copy
```

其中 `Packet::possible_ctor_or_dtor_1(node + 8, a4)`：

```text
copy source payload: a4 + 24, length 9600 buffer
copy packet state/length metadata
```

所以 `sub_62FAC0()`：

```c
return *(this + 1) + 8;
```

實際就是取得 list iterator 當前 node 的 `Packet` object。

因此 `sub_593510()`：

```text
node
  +8
   -> Packet object
      -> sub_602E30(Packet)
```

這直接閉合了 enqueue → consume 的資料流。[A]

---

## 4. `sub_602E30()` 是實際 S_MOVE_INF decode / state-apply consumer

`sub_602E30()` 開頭：

```text
if sub_67EAC0() == 0
and sub_67F120() == 0
    continue
```

之後先讀：

```text
u8 count
```

若 count = `N`，便執行 `N` 次 actor record parse。

這是目前最強的「8/24 真正進 gameplay movement/state consumer」證據。[A]

---

## 5. 每個 actor record 的目前可證實 wire layout

依序由 `sub_592940` / `sub_592A00` / `sub_592A40` 讀取：

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

因此單一 actor record 在目前 C export 所呈現的 parser 中為：

```text
3 * u8
+ 2 * u32
+ 1 * u8
+ 3 * u16
+ 4 * u8
+ 1 * u32
= 27 bytes
```

整個 body 的 parser 形狀因此是：

```text
u8 N
repeat N times:
    27-byte actor record
```

也就是 parser consumed bytes 的理論最小模型：

```text
body_len = 1 + 27*N
```

**注意：這是 `sub_602E30()` 的 decode footprint，不是尚未驗證過的 wire packet 全長公式。** Outer Packet header、padding、尾端資料，以及 8/24 是否在 sender/transport 層還有額外欄位，都仍需獨立確認。[A]

---

## 6. `field_02` 明確是 player/actor identity candidate

`n16` 被直接送入：

```text
sub_67DF00(n16)
sub_67D7D0(n16)
```

後者回傳 slot index 範圍檢查：

```text
sub_67D7D0(n16) >= 0
&& < 16
```

並以：

```text
byte_F33120[240780 * slot + 239823]
```

等 per-player state 作 actor update。

因此 `field_02 = n16` 至少是 **server-sent actor/player identifier candidate**；目前不要強行區分它是 slot、session player id 或 compact network id。其實際 mapping 是：

```text
n16 -> sub_67D7D0(n16) -> local slot
```

[A]

---

## 7. position-like 三個 16-bit fields 的證據鏈

`field_06..08`：

```text
v20 = v35 / 3.0
v21 = v36 / 3.0
v22 = v37 / 3.0
```

這三個 float 接著組成：

```text
v12[1] = v20
v12[2] = v21
v12[3] = v22
```

並進：

```text
sub_9BCB00(v33, v12)
```

`sub_9BCB00()` 將這三個 float 寫入 actor controller 的 sample state：

```text
controller +652 = x-like
controller +656 = y-like
controller +660 = z-like
```

後續 `IPaperCtrl::sub_9BCBD0()` 又拿這些 sample 與上一 sample 做：

```text
1/2 * (old + current)
```

再寫入 `controller +488` 所代表的 current transform/vector。這與空間位置同步高度一致。[A]

因此目前可提升為：

```text
field_06/07/08 = 3D transform vector components, scaled by 1/3
```

其中「是 position 而非 velocity」已有 downstream transform write 支持，但正式 field names / coordinate unit 尚未由 ASM 或 resource schema 完全固定，因此文件仍保留 `x-like/y-like/z-like`。[A]

---

## 8. `field_04` 是另一個會進 actor runtime 的 u32

`v16`：

```text
sub_592AC0 -> u32
```

先被送入：

```text
if (v33 + 74) + v16 <= ...
    ...
```

並保存為：

```text
v12[0] = v16
```

最後 `sub_9BCB00()`：

```text
controller +632 = previous +652
controller +636 = previous +656
controller +640 = previous +660
controller +644 = previous +664
controller +648 = previous +668
controller +649 = previous +669
controller +650 = previous +670
```

但注意：`v16` 本身先成為 `v12[0]`，而 `sub_9BCB00()` 會把 `*a2` 存入 `controller +652`，也就是它在這段呼叫中充當新的 sample 第一欄；然而 `v20/v21/v22` 又被放入 `v12[1..3]`。

**因此不能簡單寫成「field_04 = timestamp」或「field_04 = position x」。** 現在只確定：它是 32-bit runtime sample component，並參與一個 player-specific state/gauge update；正式 semantic Unresolved。[A]

---

## 9. `field_05` / `field_09` / `field_0A..0D` 都有 downstream consumers，但 semantic 尚未全閉合

### field_05 = v25[0]

送入：

```text
sub_5B3180(v33, v25[0])
```

而 `sub_5B3180()` 只是：

```text
player +233 = a2
```

後續 player controller logic 會讀這個 `+233` 欄位。

所以 field_05 不是 discarded byte，而是明確進 actor controller state。[A]

### field_09 = v23

被：

```text
v13 = v23
```

準備給後續 processing。C export 目前在此 function 中沒有再看到把它轉成公開 semantic enum 的直接證據，因此保持 unresolved。[A]

### field_0A = v38
### field_0B = v14
### field_0C = v15[0]
### field_0D = n0x1C

這四個 byte 主要作為：

```text
sub_5E2570(..., v29, &v20, v14, v30)
sub_5B34B0(..., v29, n0x1C, v38, v34, n16)
```

中的 state/mode/control arguments。

其中 `sub_5B34B0()` 最後會：

```text
sub_5B75F0(this, n0x1C, v10)
```

或透過 vtable slot `+132` 回呼。

因此這些 bytes 明確影響 actor controller / movement state，而不是單純 padding。[A]

目前不把它們命名成 crouch、fire、stance、weapon、jump 等，因為現有 evidence 尚不足以一一固定。

---

## 10. `field_0E = v29` 是 flags/state word candidate

`v29` 為 u32，會直接進：

```text
sub_5E2570(..., a4=v29, ...)
sub_548E80(player, v29, byte_EE896D, byte_13242D0)
```

而 `sub_548E80` 是 actor/player state update helper；它與 player object 目前狀態、global render/gameplay byte 一起使用。

因此 `field_0E` 應至少視為：

```text
u32 actor state / flags / control word
```

而不是 timestamp 或 player id。[A]

是否 bitfield、以及每一 bit 的語義，需要 ASM / caller / state transition 比對後才能繼續拆。

---

## 11. `sub_5E2570()` 提供額外的 movement validation/state hook

`sub_5E2570()` 的第一個讀取就是：

```text
u8 n2_1
```

若為 0 立即 return 0；否則它修改：

```text
this +664 = packet +12
this +668 = packet +16
this +669 = packet +17
this +670 = packet +18
```

也就是它把 Packet cursor 的某些 byte/word offset 直接保存到 actor/controller 的 transform-related runtime state。

因為 caller 傳入的是：

```text
sub_5E2570(v31, packet, n16, v29, &v20, v14, v30)
```

目前可以確認這不是獨立的 UI layer；它與 movement record 的 transform/state validation/update 緊密相連。[A]

但 `sub_5E2570()` 自身的 Hex-Rays output 出現未完全還原的 local stack / original type 資訊，因此不能從它現階段的局部變數名稱反推 packet semantic。

---

## 12. actor state application 的完整 downstream chain

單筆 record 的實際資料流：

```text
packet
  ↓
field_02 n16
  ↓
sub_67DF00(n16) → actor object
  ↓
sub_5E2570(...)
  ↓
sub_548E80(actor, field_0E, ...)
  ↓
sub_5B3180(actor, field_05)
  ↓
sub_9BCB00(actor, sample)
  ↓
sub_5B34B0(actor, field_0E, field_0D, field_0A, ...)
  ↓
sub_5B71F0(position, n16)
```

這已足以證明 8/24 不是「只把資料放 queue」；資料最終會改動 actor controller / transform-related state。[A]

---

## 13. `sub_5B71F0(&v20, n16)` 的位置重要性

`sub_5B71F0()` 直接接收：

```text
3D vector (&v20)
player id n16
```

這進一步支持 `v20/v21/v22` 是 actor spatial vector，而不是純 UI coordinate。

其具體用途仍需單獨追 `sub_5B71F0()` 的 implementation/callers，不能僅因函式位置就賦予更細語義。[A]

---

## 14. Transport/frame 與 body 必須分層

UDP Packet object 本身：

```text
Packet +24 = payload buffer
Packet +28 = opcode
Packet +32... = parser cursor / boundaries
```

`sub_591F20()` 建立 length / total-frame metadata；`sub_595980()` 最終：

```text
payload pointer = packet +24
send length = sub_591F00(packet) + 8
```

因此本文件的：

```text
1 + 27*N
```

只描述 `sub_602E30()` 消費的 movement body schema，不應直接當作 `sendto()` 的 UDP datagram 總長公式。

Outer 8-byte framing、sequence、checksum/obfuscation 是否另加，仍須從 UDP sender / `sub_591F90` / `sub_592F60` / LST/ASM 確認。[A]

---

## 15. 8 與 24：同一 handler，不等於已證實完全相同 semantic

Dispatcher：

```text
case 8:
case 24:
    sub_596940(packet)
```

兩者再進同一 queue：

```text
sub_593750(...)
```

因此可以肯定它們屬同一 `Y_UDP_S_MOVE_INF` handling family。

但目前 C evidence 沒有證明：

```text
opcode 8 == opcode 24
```

在所有上層 context 下完全等價。

因此 server implementation 應先保留：

```text
UdpMoveInf8
UdpMoveInf24
```

或至少保留原始 opcode，再共用 decoder，直到 sender/receiver role 與版本差異再閉合。[A]

---

## 16. 與 TCP 166 subtype 14 的關係

目前兩條同步層：

### TCP

```text
166
  subtype 14
    u32 time-like
    u16 × 4
    u8 flag
      ↓
sub_5B3DD0
      ↓
sub_9BCA50 samples
      ↓
IPaperCtrl::sub_9BCBD0 interpolation
```

### UDP

```text
8 / 24
  u8 count
  N × 27-byte actor records
      ↓
sub_602E30
      ↓
sub_9BCB00 / sub_5B34B0 / sub_5B71F0
      ↓
actor runtime / transform state
```

兩者確實都能影響 actor transform/state，但 wire format、transport、buffering/processing cadence 都不同。

因此不能把 UDP 8/24 直接命名成「166 subtype 14 的快版」；兩者目前應視為 **不同 wire synchronization mechanisms**，可能互補，但 compatibility behavior 仍需繼續驗證。[A]

---

## 17. Cross-check：Packet queue 的 static lifecycle

初始化：

```text
sub_58ED30(...)
    -> sub_595C90(CUDPNetworkManager,...)
    -> sub_593460(&byte_1324330)
```

`sub_593460()`：

```text
queue state reset
InitializeCriticalSection(queue +20)
```

static constructor：

```text
sub_5933F0(&byte_1324330)
```

其呼叫：

```text
sub_5950E0(this +2)
```

static destructor：

```text
sub_ADC370()
    -> sub_593410(&byte_1324330)
```

`sub_593410()`：

```text
sub_595120(this +8)
free queue storage
```

這與「receive thread enqueue / main update dequeue」架構一致。[A]

---

## 18. Current evidence-grade conclusions

### A — 已直接證實

```text
UDP opcode 8 / 24
    = Y_UDP_S_MOVE_INF family

n15 == 13
    = accepted gameplay state for S_MOVE_INF

sub_593750
    = thread-safe enqueue

sub_593510
    = per-update queue processing + list clear

sub_602E30
    = actual movement/state packet consumer

body first byte
    = actor-record count N

one actor record parser footprint
    = 27 bytes

field_02
    = player/actor id candidate, mapped by sub_67D7D0

field_06..08
    = 16-bit values / 3.0 -> 3D vector used by transform state

record data
    = directly mutates actor/controller movement-related state
```

### B — Strong but semantic naming still pending

```text
field_0E
    = actor state/control/flags word candidate

field_05
    = actor controller state field (+233)

field_03 / field_04 / field_09..0D
    = gameplay/movement state/control/timing-related values
```

### C/D — Do not promote yet

```text
field_00 = stance / posture ?
field_01 = movement mode ?
field_03 = sequence / tick ?
field_04 = timestamp / state counter ?
field_09 = animation/state ?
field_0A = direction / angle ?
field_0B = action ?
field_0C = weapon/action flag ?
field_0D = movement mode / input state ?
field_0E bit layout = unknown
```

These require additional caller/xref/ASM/resource evidence.

---

## 19. Immediate next evidence targets

1. `sub_602E30()` 的 caller/usage 是否存在其它 indirect route，確認 8/24 是否只有這一 consumer。
2. `sub_5B71F0()` 完整 implementation，確定 vector 的後續 semantic。
3. `sub_548E80()` 完整 implementation，拆 `field_0E` 的 bit/flag semantics。
4. `sub_5E2570()` 用 ASM/LST 修正 Hex-Rays local/type 問題，確認 field_03/04/09..0D。
5. UDP sender 端是否存在 opcode 8/24 的 direct constructor；目前 exact search 未找到 `Packet::...(...,8/24)` 的直接送出，所以它們目前更像 server→client only，但要保留 evidence caveat。
6. 比對 TCP 166 subtype 14 與 UDP 8/24 寫入的 controller offsets，找共同 state machine 與 precedence。
7. 利用 `Extracted/` 中角色動畫、movement/action、network/resource metadata 搜索對應 numeric ids，避免只靠反編譯猜 field 名稱。

---

## 20. Server reconstruction note

截至本次研究，server compatibility layer 不應只實作一個抽象 `MovePacket`：

```text
Client expects:
    UDP opcode 8 / 24
    -> count
    -> repeated fixed 27-byte actor records
    -> actor id mapping
    -> transform/state update

TCP 166 subtype 14
    -> independent actor state/interpolation path
```

因此實作時保留原始 opcode、raw field ordering、integer width、record count、以及未知 bytes 的位置，比先套上漂亮但未證實的 C# semantic type 更重要。
