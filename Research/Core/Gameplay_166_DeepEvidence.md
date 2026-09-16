# Y_TCP_INF_ACK (166) — Deep Evidence / Subtype 2·16 / UDP Cross-check

> 研究日期：2026-09-16
> Target：PaperMan 日本版 2016 結束營運時最終版 Client
> Evidence：IDA Hex-Rays C export + cross-function data flow + Resource/Research/Wiki cross-check
>
> 本文件是 `Gameplay_Network_Events.md` 的深證據補充，不重新定義既有結論；重點是把 166 subtype 2/16、死亡/結果鏈，以及 UDP receive architecture 分開保存。

## 1. 166 不應被抽象成固定死亡 Struct

已確認 receive chain：

```text
TCP ClientSocket
  -> sub_58B010
  -> opcode 166
  -> sub_58D820
  -> sub_749B90
  -> field0 u8 actor/player-like id
  -> field1 u8 subtype
  -> subtype-specific parser
```

`sub_749B90` 在 body 開頭依序讀 `u8 n16` 與 `u8 n18`，而 `n18` 直接進第二級 switch。因此 166 是 multiplexed gameplay-event family，而不是單一固定 payload。[A]

## 2. subtype 2 / 16 的可證實 wire 前綴

`sub_7463E0` 共用於：

```text
subtype 2  -> a4 = 0
subtype 16 -> a4 = 1
```

在進行 state mutation 前，parser 讀取：

```text
u32 v94
u8  n16_2
u16 v90[0]
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

其中已直接觀察到：

```text
v89 -> local player object +164
v95 -> local player object +172
v90[0] -> resource lookup / event subtype-dependent effect
n2 -> downstream event/result branch selector
```

`v94` 會與 `dword_F2A65C` 比較；目前不要把它命名為時間、sequence 或 result code，公開 semantic 仍 Unresolved。[A]

## 3. actor identity 與 target identity 必須分開

`sub_7463E0` 先保留 outer `n16`，之後另讀 `n16_2`。

兩者分別經過：

```text
n16   -> sub_67D7D0(n16)
      -> actor/player-slot lookup

n16_2 -> sub_67D7D0(n16_2)
       -> target/other-player lookup
```

而且：

```text
if (n16_2 == localPlayer)
    -> local-player-specific state/camera/UI branch
else
    -> remote-player branch
```

因此不要把 subtype 2/16 的第一個與第二個 player byte 視為同一語義。[A]

## 4. 最強死亡證據鏈

對 remote target 分支，當 player object/controller 存在且 `sub_9BC1A0` 不成立時：

```c
sub_9BC470(v77, 1, timeLike, 0, 0);
```

`sub_9BC470` 隨後直接修改 controller/runtime：

```text
controller +56 = 1
controller +16 = 0
controller +60 = timeLike
controller +64 = timeGetTime()
```

同時清理 state arrays / timers，最後呼叫 `sub_5B7AF0(controller)`。[A]

因此這條資料流確實是 gameplay state transition，而不是純 HUD rendering。

同一 `sub_7463E0` 後段還存在 `CViewObj::OnDeadCtrl` 明文 diagnostic path；只有當兩個 player slot 不同、且 resource category 為 4/5 的條件滿足時才走該診斷分支。否則 increment 一組 per-player counters。[A]

**但這不足以宣稱：所有 166 subtype 2/16 都代表 death。** 它們使用共同 parser + 多種 downstream effect；目前正確表述是「包含可證實 death/state-transition 分支的 multiplexed gameplay event」。

## 5. K/D counter 與另一組 result counter 不可混淆

已直接 cross-reference：

```text
player stride 240780
+60150 -> SOLO_RESULT_R_MY_KILL
+60151 -> SOLO_RESULT_R_MY_DEATH
```

結果 UI 直接把這兩個欄位拿去顯示 My Kill / My Death，因此 confidence A。[A]

另一組：

```text
+240600
+240604
```

在 subtype 2/16 path 的不同條件下遞增，並另被 scoreboard/result presentation 使用；目前只可穩健稱為 mode/round-local result counters，不能改名成 KILL / DEATH。[A]

這兩組狀態必須在 Server model 分成兩個概念層。

### 5.1 重要反證：`+60150` 沒有在目前完整 C export 中找到直接寫入

目前對 `PaperMan.exe.c` 的全檔 exact search：

```text
60150
```

只找到 result/UI 讀取：

```c
v93 = *(v94 + 60150);
```

用於：

```text
SOLO_RESULT_R_MY_KILL
```

反過來：

```text
60151
```

除了 result/UI 讀取外，可以直接找到 gameplay death path 的寫入：

```c
*(v12 + 60151) = 1;
```

且該寫入緊鄰：

```text
health/controller +16 <= 0
    -> sub_9BC470(...)
    -> +60151 = 1
    -> death UI / result state
```

因此目前更保守、也更符合 authority 分層的結論是：

```text
+60151 = client-visible death/result state；Client 有直接 death-path write evidence

+60150 = client-visible kill/result field；目前沒有在 C export 找到同等直接 increment/write evidence
```

這表示不能僅因欄位名稱 `MY_KILL` 就推定 Client 自己計算並維護 Kill Counter。Kill counter 很可能來自另一條 event/network/result synchronization path，仍需繼續定位。

這是目前 Server reconstruction 非常重要的 evidence distinction。[A]

## 6. `n2` 的下游語義目前比 opcode 名稱更值得追

在 subtype 2/16 parser 後段：

```text
n2 == 1 -> sub_61FC20(..., 6, v90[0])
n2 == 2 -> sub_61FC20(..., 4, v90[0])
n2 == 3 -> sub_61FC20(..., 7, v90[0])
n2 == 4 -> sub_61FC20(..., 5, v90[0])
default -> sub_61FC20(..., 1, v90[0])
```

因此 `n2` 是一個會控制 presentation/effect path 的離散事件值，而非單純 boolean。這個值應與 resource id `v90[0]` 聯合分析；不能只靠數字直接命名成 hit/kill/death。[A]

## 7. Resource lookup 在 166 event 中是真正的 semantic anchor

多條 subtype 2/16、3/20、10 等 handler 都會呼叫：

```text
sub_5F5400(dword_1CC95A0, resourceId)
sub_5F5450(dword_1CC95A0, resourceId)
```

並依 resource metadata category (`sub_5EF5B0`, `sub_5EFE00`, `sub_5EF5F0`) 選擇 downstream behavior。

這表示 166 中的 numeric field 不能孤立解釋；至少應建立：

```text
166 field
  -> resource ID
  -> Resource table
  -> category / metadata
  -> effect/state handler
```

這條鏈目前比「把 subtype 3 叫 hit」之類的命名可靠。[A]

## 8. subtype 14 與 movement 是兩個不同同步層

`166 subtype 14 -> sub_749AB0`：

```text
u32 time-like
u16 × 4
u8 flag
    -> sub_5B3DD0
    -> two transform samples
    -> IPaperCtrl::sub_9BCBD0
    -> position/vector + angle interpolation
```

同時 UDP `8/24 -> sub_596940` 的明文 diagnostic：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF
```

且只在 `n15 == 13` 時進入 queue。[A]

所以目前模型應保持：

```text
TCP 166 subtype 14
    = server gameplay actor-state / interpolation event

UDP 8 / 24
    = dedicated S_MOVE_INF family
```

兩者都是 gameplay synchronization，但不能合併成同一 wire protocol。[A]

## 9. UDP movement queue：目前只能證實「enqueue」，不能假裝已解析

`sub_596940`：

```c
if (n15 == 13)
    sub_593750(&byte_1324330, packet);
```

`sub_593750`：

```text
EnterCriticalSection
  -> sub_5951C0(queue, ..., packet)
LeaveCriticalSection
```

`sub_5951C0` 建立一個 list node；node 內容保存傳入的 packet data/length-like value。[A]

而 `sub_593510` 在 UDP manager shutdown/cleanup 時迭代 queue、呼叫 `sub_602E30` 處理 node payload，再 `sub_595120` 清空 node list。因此 `sub_593510` 是 cleanup/state-management path，不是 8/24 movement decoder。[A]

目前 exact C export 找不到對 `sub_5937D0` 的直接 callsite；它更可能是被 thread/state-machine/vtable 間接驅動。`sub_5937D0` 本身只會：

```text
state == 0 -> sub_593830(this)
state == 4 -> check sub_5941D0()
state == 7 -> return ready/terminal-like condition
```

其中 `sub_593830` 會定時產生 UDP opcode 1 或在 special state 產生 opcode 15，並依 state 修改自身 status byte。[A]

因此 queue consumer 仍 Unresolved；下一輪應從 `sub_5933F0` / `sub_5950E0` 建構的 object、vtable、thread/state dispatch 反查，而不是假定 `sub_5937D0` 就是 consumer。

## 10. UDP receive architecture 已固定

```text
CUDPManager::sub_595840
  -> sub_595A60
  -> recvfrom / packet framing
  -> sub_595E80
  -> opcode dispatcher
```

已證實：

```text
2,4,5,6,8,24,10,12,13,14,15,18,20,22,26,28,29,31,33,34,154,158
```

各自進入獨立 handlers。[A]

8/24 是目前明文可確認 `S_MOVE_INF` 的 movement pair；其它 UDP opcode 不應僅因 timing/state 結構相似而命名為 movement。

## 11. UDP sender / peer endpoint

CUDPSocket constructor 把 default port 初始化成 `27000`。建立 `SOCK_DGRAM`。

`sub_596DA0` 與 `sub_596E60` 都直接使用：

```text
inet_addr(ip)
htons(port)
```

`sub_596EB0` / `sub_596F00` 使用 `sendto`；`sub_596F90` 使用 `recvfrom`。[A]

這證實 PaperMan gameplay network 有明確 UDP transport，而不是在 TCP 層假裝「UDP-like」事件。

## 12. Client → Server damage 與 Server → Client result 必須分層

165 的 client send path 已直接存在：

```text
sub_55CAB0 / sub_55D090 / sub_55D530
    -> Packet opcode 165
```

165 payload 依 damage subtype/resource/mode 可有不同尾段；其中兩個 `sub_592B20` 並非 1-byte wire value，而 helper 本身寫 4 bytes，因此不能把它們標成 u8。[A]

165 的存在只能證明 Client→Server damage/report path；真正的 server authority / HP mutation 必須由 166 receive-side state mutation、death/result chain，以及後續 respawn/result packets 一起確定。

## 13. Wiki cross-check

PaperMan Wiki 的玩家行為資料提供外部 semantic anchor：

- 個人サバイバル描述為「倒した人」決定結果，且達到規定 Kill 或時間到結束。
- 重生後有 5 秒無敵。
- Kill log 另有通常 kill、特殊 shot，以及 assist。
- 2014-09-17 起存在 Assist Point；例如對手受到至少最大 HP 55% 傷害後由其他玩家擊倒可獲 assist point；治療隊友至少 20% HP 亦可累積 assist point。

這些是 Wiki/歷史行為證據，不是 166 欄位的直接 wire proof。它們目前只能用來驗證 Client state/event chain 是否與玩家可觀察行為一致。[C]

## 14. Current server-model implications

目前至少應區分以下 server concepts：

```text
PlayerIdentity
PlayerSlot
ActorGameplayState
ActorTransformState
Hit/DamageReport
DeathStateTransition
KillCounter
DeathCounter
Mode/round-local result counters
AssistState / AssistPointState
RespawnState
ResourceEffectId / ResourceCategory
```

尤其：

```text
166 actor + subtype
```

不應直接變成一個 C# `DeathPacket` class。較正確的 reconstruction abstraction 應是：

```text
GameplayEventEnvelope
{
    ActorId,
    Subtype,
    Payload
}
```

再依 evidence-confirmed subtype 解包。

## 15. Unresolved / 下一個必追

1. 找出 UDP queue 的真正 consumer，完整解析 8/24 的 `S_MOVE_INF` payload。
2. 完成 `sub_7463E0` 全 xref / downstream：確認 subtype 2/16 的所有情境與 `n2` values。
3. 追 `sub_61FC20 -> sub_6745C0`，將 n2/effect type 與 resource metadata 連起來。
4. 追 `+60150` 的真正寫入來源；目前只有 result/UI read evidence。
5. 追 `166 subtype 2/16 -> death -> kill/assist -> respawn` 完整事件鏈。
6. 追 `165 -> 166` 是否存在固定 server validation / sequence coupling，而不是僅靠 opcode pairing 推定。
7. 用 LST/ASM 驗證 `sub_592B20` 與所有 suspect field width，尤其 damage values。
8. 將 Wiki 的 assist/respawn rules 與 Client assist strings、`+60151` death writes、respawn timers 做三方對照。

## Evidence quality

- **A**：IDA C 直接讀取/寫入、call graph、resource lookup、state mutation。
- **C**：Wiki / player-visible behavior 用於外部 semantic cross-check。
- **未定義**：尚未由 ASM/LST 完成的欄位 width/正式 enum 名稱，不升級成 fact。
