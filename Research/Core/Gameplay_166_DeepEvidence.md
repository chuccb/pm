# `166` Gameplay 深入證據

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是 `166` Gameplay／結果／死亡／移動事件的深入證據主文件。`Packet_166_Field_Map.md` 負責欄位總表；本文件負責跨函式、跨狀態、跨資源的證據鏈。原本的 `Gameplay_166_KD_Field_Evidence.md` 已整合至本文件，不再維護第二份同主題結果欄位真相。

## 1. `166` 是多型 Gameplay Event Family

已確認接收鏈：

```text
TCP ClientSocket
  → sub_58B010
  → opcode 166
  → sub_58D820
  → sub_749B90
  → field0 u8 actor/player-like id
  → field1 u8 subtype
  → subtype-specific parser
```

`sub_749B90` 開頭依序讀取 `u8 n16` 與 `u8 n18`，其中 `n18` 直接進第二級 switch。因此 166 是多種 gameplay event 共用的 multiplexed family，不是一個固定結構的死亡封包。[C]

## 2. subtype 2／16 的 Participant 結構

`sub_7463E0()` 共用於：

```text
subtype 2  → a4 = 0
subtype 16 → a4 = 1
```

除外層 actor ID 外，payload 還讀取第二個 player-like ID `n16_2`，並建立兩個玩家映射：

```text
n16_1 → sub_67D7D0() → participant A
n16_2 → sub_67D7D0() → participant B
```

後續 local-player branch 對 `n16_1 == localPlayer` 與 `n16_2 == localPlayer` 採取不同處理，因此兩個 ID 不是重複欄位，而是事件中的兩個不同 participant。[C]

## 3. subtype 2／16 的可直接觀察欄位

`sub_7463E0()` 在 state mutation 前讀取：

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

目前可直接確認：

```text
v89    → local player object +164
v95    → local player object +172
v90[0] → resource lookup / event effect
n2     → downstream effect/result branch selector
```

`v94` 會與 `dword_F2A65C` 比較，但目前不能把它直接命名為時間、sequence 或 result code。[C][OPEN]

## 4. 最強的死亡／狀態轉移證據

對 remote target 分支，當 player object/controller 存在且 `sub_9BC1A0` 不成立時，會呼叫：

```c
sub_9BC470(v77, 1, timeLike, 0, 0);
```

該函式隨後直接修改 controller/runtime：

```text
controller +56 = 1
controller +16 = 0
controller +60 = timeLike
controller +64 = timeGetTime()
```

並清理多組 state array／timer，最後呼叫 `sub_5B7AF0(controller)`。[C]

這條資料流是 gameplay state transition，不是純 UI 呈現。[C]

同一 `sub_7463E0()` 後段還出現 `CViewObj::OnDeadCtrl` 明文診斷路徑；特定 resource category 條件成立時走該路徑，否則更新 per-player counter。[C]

**因此正確結論不是「所有 166 subtype 2/16 都是死亡」。** 正確描述是：

> subtype 2/16 共用大型 participant/gameplay-state parser，其中存在可直接確認的 death/state-transition 分支；不同 subtype、resource category、team 關係與 local-player 狀態會改變後續結果。

## 5. `+240600`／`+240604` 的直接結果計數更新

`sub_7463E0()` 後半段可整理為：

```c
v68 = sub_67D7D0(n16_1);
v67 = sub_67D7D0(n16_2);

if (v68 < 0 || v67 < 0)
    return;

if (v68 != v67)
{
    if (sub_67D630(v68, v67)
        && ((resource(v90[0]) category == 4)
         || (resource(v90[0]) category == 5)))
    {
        // CViewObj::OnDeadCtrl diagnostic path
    }
    else
    {
        ++byte_F33120[240780 * v68 + 240600];
    }
}

if (a4 == 0)
    ++byte_F33120[240780 * v67 + 240604];
```

因此正常 `a4 == 0` 路徑具有明確的 participant-directed mutation：

```text
participant A → +240600 ++
participant B → +240604 ++
```

結合同一函式對 participant B 的 death-state transition，目前最穩健的語意是：

```text
+240600 = 回合／模式局部的 Kill counter（participant A）
+240604 = 回合／模式局部的 Death counter（participant B；a4=0）
```

這是直接 mutation + participant direction + UI cross-check 的 A 級證據。[C][X]

## 6. `a4 == 1` 的 subtype 16 例外

Dispatcher 明確指定：

```text
166 subtype 2  → a4 = 0
166 subtype 16 → a4 = 1
```

因此：

```text
if (a4 == 0)
    victim +240604 ++
```

只存在於 subtype 2 的這條路徑；不能把 subtype 16 當成完全相同的 Kill/Death packet。[C]

當 `n16_2 == localPlayer` 且 `sub_67EE30()` 成立時，`a4` 還會控制 local gameplay timing/state：

```text
if (a4 == 1)
    this +96 = 4000
else
    this +96 = 0
```

因此 `a4` 不只是語法上的參數，而是實際控制不同 gameplay state branch 的重要維度。[C]

## 7. `+240600`／`+240604` 的 UI 交叉驗證

初始化可直接看到：

```c
*(this + 240600) = 0;
*(this + 240604) = 0;
```

`CyIndividualSurvivalMode::sub_76FA50()` 的 `RoundStat` 顯示路徑直接讀取：

```c
player->field_240600
```

並送入 `Num16x16` renderer。[C]

另一條 member/result presentation builder `sub_640110()` 也同時讀取：

```text
+240600
+240604
```

兩者一直位於相同的 player stride `240780` 中，支持它們是 per-player round/stat pair。[C][X]

## 8. `+60150`／`+60151` 是另一層 Result-screen 狀態

結果 UI 明確使用：

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

這兩個欄位不是 `+240600/+240604` 的同一物理儲存位置，因此 Server model 應分開：

```text
Live round / mode-local stats
├─ +240600 Kill
└─ +240604 Death

Result-screen MY stats
├─ +60150 My Kill
└─ +60151 My Death
```

兩組數值可能在某些情境同步，但不能因此假定同一 update event 或同一 authority layer。[C]

## 9. `+60150` 的重要 Negative Evidence

對完整 `PaperMan.exe.c` 做 `60150` exact search，目前主要看到 result/UI 讀取：

```c
v93 = *(v94 + 60150);
```

並送入 `SOLO_RESULT_R_MY_KILL`。[C]

相較之下，`+60151` 可以找到更直接的 death-path write：

```c
*(v12 + 60151) = 1;
```

且位置緊鄰 health/controller death-state transition。[C]

因此目前必須保留這個證據區分：

```text
+60151
    = client-visible My Death result field
    = 存在直接 death-path write

+60150
    = client-visible My Kill result field
    = 目前未找到同等直接的 gameplay increment/write
```

不能因 result label 是 `MY_KILL`，就推論 Client 每次正式 PvP kill 都直接 `++60150`。[C][OPEN]

## 10. `n2` 是 effect/result selector，不可直接命名成 Kill/Hit/Death

subtype 2/16 parser 後段：

```text
n2 == 1 → sub_61FC20(..., 6, v90[0])
n2 == 2 → sub_61FC20(..., 4, v90[0])
n2 == 3 → sub_61FC20(..., 7, v90[0])
n2 == 4 → sub_61FC20(..., 5, v90[0])
default  → sub_61FC20(..., 1, v90[0])
```

因此 `n2` 是控制 downstream presentation/effect path 的離散事件值，且與 resource ID `v90[0]` 聯合使用。目前不足以單靠數字把它命名成 hit、kill 或 death。[C][OPEN]

## 11. Resource lookup 是 166 語意的重要錨點

多個 subtype handler 會呼叫：

```text
sub_5F5400(dword_1CC95A0, resourceId)
sub_5F5450(dword_1CC95A0, resourceId)
```

並依 Resource metadata category（例如 `sub_5EF5B0`、`sub_5EFE00`、`sub_5EF5F0`）選擇不同 downstream behavior。[C]

因此解釋 166 numeric fields 時，標準方法應是：

```text
166 field
  → Resource ID
  → Resource table
  → category / metadata
  → effect/state handler
```

不能孤立從一個數值命名遊戲語意。[C]

## 12. 166 subtype 14 與 UDP movement 是兩個同步層

`166 subtype 14 → sub_749AB0`：

```text
u32 time-like
u16 × 4
u8 flag
    → sub_5B3DD0
    → two transform samples
    → IPaperCtrl::sub_9BCBD0
    → position/vector + angle interpolation
```

同時 UDP `8/24 → sub_596940` 存在明文 diagnostic：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF
```

且 `n15 == 13` 時會進入 queue。[C]

因此目前應維持：

```text
TCP 166 subtype 14
    = gameplay actor-state / interpolation event

UDP 8 / 24
    = dedicated S_MOVE_INF family
```

它們同屬 gameplay synchronization，但 wire protocol 不應合併。[C]

## 13. UDP movement queue 目前只能證實 enqueue

`sub_596940()`：

```c
if (n15 == 13)
    sub_593750(&byte_1324330, packet);
```

`sub_593750()`：

```text
EnterCriticalSection
  → sub_5951C0(queue, ..., packet)
LeaveCriticalSection
```

`sub_5951C0()` 建立 list node，保存傳入 packet data／length-like value。[C]

`sub_593510()` 則在 UDP manager shutdown／cleanup 時迭代 queue、呼叫 `sub_602E30` 處理 node payload，再清空 node list，因此它不能直接被命名成 8/24 movement decoder。[C]

目前在 C export 中找不到 `sub_5937D0()` 的直接 callsite；它較可能透過 thread、state machine 或 vtable 間接驅動。其自身只根據 state 選擇 `sub_593830()`、檢查 `sub_5941D0()` 或回傳 ready/terminal-like 條件。[C]

因此 queue consumer 仍 `[OPEN]`。

## 14. UDP Receive Architecture

目前可固定為：

```text
CUDPManager::sub_595840
  → sub_595A60
  → recvfrom / packet framing
  → sub_595E80
  → opcode dispatcher
```

已觀察到的 UDP opcode 包含：

```text
2,4,5,6,8,24,10,12,13,14,15,18,20,22,26,28,29,31,33,34,154,158
```

各自進入獨立 handler。[C]

目前只有 8/24 可以由明文 `S_MOVE_INF` 路徑直接標記為 movement pair；其餘 UDP opcode 不得因為格式相似就猜成 movement。[C]

## 15. UDP Endpoint 與 Transport

CUDPSocket constructor 會初始化 default port `27000`，建立 `SOCK_DGRAM`。[C]

`sub_596DA0()`、`sub_596E60()` 直接使用：

```text
inet_addr(ip)
htons(port)
```

`sub_596EB0()` / `sub_596F00()` 使用 `sendto`，`sub_596F90()` 使用 `recvfrom`。[C]

因此 Client 存在明確 UDP gameplay transport。

## 16. Client → Server Damage 與 Server → Client Result 必須分層

Client send path 可直接找到：

```text
sub_55CAB0 / sub_55D090 / sub_55D530
    → packet opcode 165
```

165 payload 會依 damage subtype、resource、mode 產生不同尾段。[C]

其中有些 `sub_592B20` 呼叫不能把參數看成 1-byte wire value；helper 實作實際可能寫入 4 bytes，因此必須檢查底層 serializer，而不是相信 Hex-Rays 表面 prototype。[C]

目前最安全的 authority 分層是：

```text
165
= Client → Server damage / report path

166
= Server → Client gameplay event / state synchronization family
```

但不能只因 opcode 前後配對，就自行假設一對一 request/response 關係；仍需繼續追 sequence 與 server validation。[C][OPEN]

## 17. Wiki 行為與 166 的交叉驗證

日本 Wiki 提供以下歷史玩家可見規則，可作為外部語意錨點：

- 個人サバイバル的結果與擊倒人數、時間條件相關。
- 重生後存在 5 秒無敵時間。
- Kill Log 區分一般擊殺、特殊射擊與 Assist。
- 2014-09-17 起有 Assist Point；例如造成至少最大 HP 55% 傷害後由其他玩家擊倒可產生 Assist Point，治療隊友達到一定 HP 比例也可產生 Assist Point。[WIKI]

這些資料用於驗證 Client event／state chain 是否符合玩家可觀察行為，但不能直接當作 166 wire field proof。

## 18. Server Model 的必要抽象層

Server reconstruction 至少應拆成：

```text
PlayerIdentity
PlayerSlot
ActorGameplayState
ActorTransformState
Hit/DamageReport
DeathStateTransition
RoundKillCounter
RoundDeathCounter
ResultMyKill
ResultMyDeath
Mode/round-local result counters
AssistState / AssistPointState
RespawnState
ResourceEffectId
ResourceCategory
```

尤其不要把 166 直接抽象成單一：

```text
DeathPacket
```

更符合目前證據的形式是：

```text
GameplayEventEnvelope
{
    ActorId,
    Subtype,
    Payload
}
```

再依證據閉合程度解包各 subtype。[C]

## 19. 研究中最重要的證據邊界

目前必須嚴格保持以下區別：

```text
+240600
    = round / mode-local Kill side state

+240604
    = round / mode-local Death side state（a4=0）

+60150
    = result-screen My Kill field

+60151
    = result-screen My Death field
```

以及：

```text
166 subtype 2/16
    ≠ 固定 Death Packet

166 subtype 14
    ≠ UDP S_MOVE_INF

165
    ≠ 已證明的單一 166 response
```

這些邊界是目前 Server reconstruction 最容易因過度抽象而出錯的地方。

## 20. 尚未閉合的 Proof Targets

```text
1. 找出 +60150 的真正 writer/source。
2. 找出 Assist event 的 producer 與 packet/type chain。
3. 完整解出 subtype 2/16 的所有 mode/resource 分支。
4. 解出 n2 → effect type 1/4/5/6/7 → resource metadata 的關係。
5. 完整追 166 death → kill/assist → respawn → result 的事件鏈。
6. 完整解析 UDP 8/24 S_MOVE_INF payload 與 queue consumer。
7. 找出 165 damage payload 每一欄位的真實寬度與 server validation。
8. 用 LST/ASM 補強 Hex-Rays 可疑 serializer prototype。
9. 將 Wiki 的 kill/assist/respawn 規則與 Client resource/effect state 三方交叉閉合。
```

除非新證據真正封閉上述項目，否則相關欄位維持 `[OPEN]`，不可為方便 Server 實作而硬編碼。
