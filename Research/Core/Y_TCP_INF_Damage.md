# `Y_TCP_INF_REQ (165)`／`Y_TCP_INF_ACK (166)` Gameplay Event／State 封包族

> 研究目標：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
>
> 本文件是整個 `Y_TCP_INF` 的唯一主文件。原本分開的 Damage、Handler Details 內容已在此整合；`Y_TCP_INF_Transport.md` 只處理更底層的傳輸層，不與本文件平行維護 gameplay 語意。

## 1. 最小正確模型

Client packet registration：

```text
165 → Y_TCP_INF_REQ
166 → Y_TCP_INF_ACK
```

目前最安全的架構模型：

```text
Y_TCP_INF_REQ (165)
    = Client → Server gameplay／actor／effect／state event family

Y_TCP_INF_ACK (166)
    = Server → Client gameplay／actor／effect／state event family
```

不能建模為：

```text
165 = DamagePacket
166 = DamageAck
```

完整 C 已找到多個獨立 165 send path，包括 BotSuicide、dead-position、effect/state、vector/interaction 與 MultiDamage，因此 165 明顯是 subtype-driven family。[C]

## 2. 已確認的 165 send families

| subtype／形態 | Client path | 目前語意 | 信度 |
|---:|---|---|---|
| 2 | `sub_5DF7F0`、`sub_5E6170` | gameplay／action／state event | B |
| 4 | `sub_5E5ED0`、`sub_5E6040` | effect／resource／state event | B |
| 5 | `CViewObj` dead-position path | dead-position／event variant | B |
| 6/7 | gameplay／effect callers | event／state | C |
| 8 | `sub_7452D0` | dead-position／state variant | B |
| 9 | `sub_745D60` | small state event | B |
| 10 | `sub_745E80` | small state event | B |
| 13 | `sub_5E6DF0` | vector／interaction report | B |
| 15 | `sub_55D440` | gameplay event | C |
| 16 | `OnSendPacketMultiDamage`／`sub_55D530` | MultiDamage variant | A |
| 21 | `OnSendPacketBotSuicide`／`sub_5658B0` | BotSuicide variant | A |
| 其他已發現路徑 | `OnSendPacketDamage`／Mine-Bomb | damage-family variant | A |

這是目前搜尋得到的 family inventory，不是假定完整 enum。仍需持續搜尋所有 `Packet(...,165)` 與間接 virtual send path。[C]

## 3. Normal `OnSendPacketDamage`

目前看到的共同前段形狀：

```text
u8  source／actor-like value
u8  event／damage subtype-like value
[特殊條件下額外 u16 ×3]
u8  target／actor-like value
[conditional u8]
u16 resource／weapon-like value
...
```

第二 byte `n20` 被大量 branch 使用：

```c
if ( n20 == 1 || n20 == 3 || n20 == 14 ||
     n20 == 19 || n20 == 17 || n20 == 16 || n20 == 20 )
```

目前可安全描述為：

```text
field1 = gameplay／damage event subtype
```

不能在沒有 reader／consumer 證據時直接改名為公開 `DamageType` enum。[C][OPEN]

## 4. 重要 wire-width 規則：`sub_592B20`

重新檢查完整 C 後，部分 `sub_592B20(...)` 呼叫不能直接視為 1-byte writer。

Caller 可能出現：

```c
sub_592B20(packet, SLOBYTE(value));
```

但 writer implementation 屬 4-byte serialization family，因此：

```text
source expression width
    ≠
actual serializer／wire width
```

所有 `sub_592B20` 欄位都必須追 writer implementation 與 reader pairing 才能封死。[C]

## 5. Normal damage 計算鏈

建包前存在：

```c
v39 = sub_5E72C0(source, target, a5);
v40 = sub_5E72C0(source, target, a6);
```

之後可能套用：

```text
1.0
2.0
```

以及一條 `n20 == 3` 路徑中的：

```text
1.2
```

因此 Server reconstruction 不應只有：

```text
rawDamage → packet
```

而應保留：

```text
DamageInput
    → modifier resolution
    → subtype／mode multiplier
    → quantization
    → Y_TCP_INF_REQ 165
```

## 6. MultiDamage：subtype 16

`GameNetwork::OnSendPacketMultiDamage`：

```c
Packet::possible_ctor_or_dtor_0(v23, 165);
sub_592920(v23, n16);
sub_592920(v23, 16);
sub_592920(v23, n16_1);
```

因此直接確認：

```text
165 field1 == 16
    = MultiDamage send variant
```

後續還有 resource/value、多 target damage components 與 target metadata。[C]

各 `sub_592B20` 寬度仍必須由底層 serializer/reader pairing 決定。[C][OPEN]

## 7. Mine／Bomb damage

`GameNetwork::OnSendPacketMineBombDamage` 同樣使用 165，因此 Mine/Bomb damage 屬於 subtype-driven family，而不是獨立 opcode。[C]

## 8. BotSuicide：subtype 21

`sub_5658B0()`：

```c
Packet::possible_ctor_or_dtor_0(v5, 165);
sub_592920(v5, a1);
sub_592920(v5, 21);
sub_5929E0(v5, a2);
sub_5929E0(v5, a3);
sub_5929E0(v5, a4);
```

可直接閉合：

```text
field0 = a1
field1 = u8 subtype 21
field2 = u16 a2
field3 = u16 a3
field4 = i16 a4
```

`subtype 21 = BotSuicide` 為 A-level family fact；其它欄位公開語意仍 `[OPEN]`。[C]

## 9. subtype 4：effect／resource／state

`sub_5E5ED0()` 與 `sub_5E6040()` 均建立：

```text
165
u8 actor-like
u8 4
u8 local-player-like
u8 variant
u8 state/timing-like
u32 value
```

目前應統稱：

```text
subtype 4 = effect/resource/state family
```

而不是假定某一個固定 gameplay enum。[C][OPEN]

## 10. subtype 5／8：dead-position／state family

`CViewObj::TempSendDeadPosPacket` 明確建：

```text
165
u8 local player
u8 5
...
position／orientation-related values
```

`sub_7452D0` 也建立 165 + subtype 8 並序列化大量 transform-related data。[C]

因此：

```text
5 = dead-position/event variant A
8 = dead-position/state variant B
```

不能直接假定兩者 wire layout 相同。[C][OPEN]

## 11. subtype 9／10：small state event

```text
sub_745D60 → 165 + local-player + 9 + object +152 state/value
sub_745E80 → 165 + local-player + 10
```

兩者使用 `sub_602E00()` 結束 packet path；後續應比較 `sub_58D7D0` 與 `sub_602E00` 的 packet finalization 差異。[C][OPEN]

## 12. subtype 13：vector／interaction report

`sub_5E6DF0()` 產生：

```text
165
u8 actor-like
u8 13
u8 local player
u8 a3
a4
4-byte value
4-byte value
4-byte vector.x
4-byte vector.y
4-byte vector.z
```

其 caller `sub_5E3A50()` 會先進行 target、state、geometry 檢查，因此至少可確認它是經本地計算後送出的 interaction/vector report。[C]

不能因此推論 Client 對最終遊戲結果具有 authority；Server validation 仍待證明。[OPEN]

## 13. `166 Y_TCP_INF_ACK` receive chain

完整接收鏈：

```text
TCP framing
    ↓
sub_58B010
    ↓ case 166
sub_58D820
    ↓
sub_749B90(packet)
    ↓
read u8 n16
read u8 n18
    ↓
second-level handler
```

`sub_58D820()` 本身不重新解析 gameplay body，而是把 packet 交給 `sub_749B90()`。[C]

因此：

```text
n16 = 第一級 actor／subject-like discriminator
n18 = 真正的 second-level gameplay event discriminator
```

## 14. 166 的 discriminator inventory

目前直接確認的 `n18` 包含：

```text
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,
17,18,19,20,21,22,23,24,25,26,27,29,30,31
```

重要已閉合路徑：

```text
n18 = 3 / 20
    → sub_747980 → sub_747460
    → target player state + resource/effect

n18 = 21
    → sub_747DD0 → sub_747B90
    → remote action/vector-like propagation

n18 = 13
    → GameRule / NewGameStart / player-state reset

n18 = 24
    → server-driven millisecond-like timing/state

n18 = 1
    → player runtime effect

n18 = 2 / 16
    → large player/runtime state synchronization

n18 = 12
    → two-u16 state/control path
```

不能建立「165 subtype N 對應 166 subtype N」的數字對稱模型。[C]

## 15. n18 == 3 / 20：target runtime value mutation

`sub_747980()` 讀：

```text
u32 v21
u8  n16_1
u16 v19[0..2]
u8  n20
u8  v15
u8  v18
u32 v16
u32 n26
u8  n0x1E
```

之後呼叫 `sub_747460()`。

`sub_747460()` 取得 source/target player objects，並比較：

```text
*(target_object + 16)
```

與 Server 傳入的：

```text
a6
```

不同時依 `n20` 做不同 effect，最後直接：

```c
*(target_object + 16) = a6;
```

因此 `a6` 是 Server → Client 直接寫入 target runtime object 的 value-like state。[C]

最合理的暫名是：

```text
target_runtime_value
```

可疑似 HP-like，但在 object layout 完全閉合前不得直接寫成正式 HP。[C][OPEN]

## 16. `sub_747460` 的 Resource／Action bridge

Handler 之後呼叫：

```text
sub_5F5450(dword_1CC95A0, resourceId)
```

再依 Resource category 進入：

```text
sub_74CB20(...)
```

`sub_74CB20()` 再根據 category 1、2、3、4、5 與 8–20 選擇不同 downstream route，形成：

```text
Y_TCP_INF_ACK
    → Resource lookup
    → Resource category
    → local effect/state application
```

因此部分 166 事件顯然不是單純 damage/result，而是直接驅動 resource/action system。[C]

## 17. `sub_74D720` 的本地／遠端 state application

```c
if (a3 == sub_67D1D0())
    sub_74C880(...);
else if (a3 != 0)
{
    *(a3 + 2*n21 + 672) = a6;
    *(a3 + 4*n21 + 336) = 1;
}
```

這再次證明 166 是 runtime object state application，不是單純 K/D counter update。[C]

## 18. n18 == 21：remote actor action／vector propagation

`sub_747DD0()` 讀取：

```text
u8  actor-like
u16 vector/value ×3
u8  state
u8  state
```

再進 `sub_747B90()`；其中 scalar 會經：

```text
1 / 256
```

之後寫入 target object movement/state。[C]

因此這條 route 是 action/vector-like state propagation，不是 K/D 統計。[C]

## 19. n18 == 1：player object effect

`sub_746360()` 只額外讀一個 u8，找到 player object 後直接操作其 runtime effect state：

```c
if (n16 != sub_67D010())
    sub_5B8EE0(*(v2 + 320));
sub_5B8F70(*(v2 + 320));
```

沒有直接 K/D counter write。[C]

## 20. n18 == 2 / 16：大型 player runtime state

`sub_7463E0()`：

```text
u32 v94
u8  n16_2
u16 v90[0..2]
u8  n2
u8  n10
u8  n10_1
u32 v89
u32 v95
u8  v86
```

之後依 local／remote player 走不同 state application。

Remote 路徑會呼叫：

```text
sub_9BC470(...)
```

並處理 coordinates、runtime controller 與 state；local path 則會刷新多個 gameplay subsystem。[C]

這是完整 runtime state application，不應簡化成單一「位置封包」。[C]

## 21. `+240600/+240604` 的即時 Round K/D-like state

`sub_7463E0()` 中可直接看到：

```c
++byte_F33120[240780 * killerSlot + 240600];

if (a4 == 0)
    ++byte_F33120[240780 * victimSlot + 240604];
```

初始化也會把這兩個欄位清零；`CyIndividualSurvivalMode::sub_76FA50()` 直接將 `+240600` 送入 `RoundStat` UI。[C]

因此目前高信度模型：

```text
+240600 = live round/mode Kill counter
+240604 = live round/mode Death counter
```

但它們不是 `F6DCF8/F6DCFC` 的同一個儲存位置。[C]

## 22. `F6DCF8/F6DCFC` 的 Server-provided Result K/D

完整 source-level 搜尋目前可見：

```c
dword_F6DCF8[60195 * slot] = v433;
dword_F6DCFC[60195 * slot] = v383;
```

這兩個 u32 由 `TCP 269 subtype 7` repeated player records 直接灌入；Result UI 也直接使用：

```text
TEAM_RESULT_B_TEXT_KILL  → F6DCF8
TEAM_RESULT_B_TEXT_DEATH → F6DCFC
```

並由排序函式使用。[C]

此外，目前沒有找到 166 gameplay handler 直接 `++F6DCF8` / `++F6DCFC`。[C]

因此目前應分層：

```text
166 live gameplay
    → +240600/+240604

269 subtype 7
    → F6DCF8/F6DCFC
```

## 23. `+60150/+60151`：第三層結果畫面欄位

Result-screen local fields：

```text
+60150 → SOLO_RESULT_R_MY_KILL
+60151 → SOLO_RESULT_R_MY_DEATH
```

目前 exact source search 顯示：

```text
+60151 → 有直接 death-path write
+60150 → 尚未找到同等直接 gameplay increment/write
```

因此不能自行建立：

```text
166 kill event → ++60150
```

而應保留：

```text
F6DCF8/F6DCFC = Server-provided result K/D
+240600/+240604 = live round K/D-like state
+60150/+60151 = local result-screen My K/D
```

三者可以相關，但不能因 UI 相似而合併。[C][OPEN]

## 24. n18 == 12：two-u16 state/control message

`sub_749A30()`：

```c
sub_592A00(a2, &v7);
sub_592A00(v2, &v6);
sub_67F2F0();
sub_67CD20(n9_0, v7, v6, 2 - !v3);
```

之後刷新多個 UI/runtime subsystem。[C]

目前只能安全命名為：

```text
two-u16 state/control event
```

## 25. n18 == 13：Game/round reset lifecycle

此路徑會：

```text
清 byte_F6DD11[16 slots]
sub_95EC00(slot) × 16
重新建立 local/remote player state
sub_718000
sub_7603A0（特定環境）
sub_67B5C0(..., -1)
sub_62D570
sub_720A10
```

而 `sub_67B5C0` 已與 `CGameRule::NewGameStart` 對上。[C]

目前可以提升為：

```text
166 n18 = 13
    → Server-driven Game/round reset/start path
```

但不要自行賦予 packet table 未證明的正式名稱。[C]

## 26. n18 == 24：Server-driven timing/state

此路徑會將 nested millisecond-like value 分解成：

```c
minutes = value / 1000 / 60;
seconds = value / 1000 % 60;
```

並設定：

```text
dword_1D0A970 = 1
dword_1D0A974 = 0
```

再經 `sub_7498E0()` 傳入 virtual callback 並刷新 HUD/UI。[C]

因此是 Server-driven timing/state dispatch 的高信度證據，但「可見比賽倒數」仍待進一步證明。[C][OPEN]

## 27. Player ID 與 Slot 必須分離

Y_TCP_INF 與 score/death path 同時出現：

```text
sub_67D010()
sub_67D110()
sub_67D7D0()
dword_F6DCF4[slot]
dword_F6DD1C[slot]
```

因此 Server model 必須至少區分：

```text
PlayerId
SlotIndex
Team/Group
RuntimeObject
ConnectionState
```

packet 第一個 byte 不能直接預設成 slot，也不能反過來把 slot 當成 PlayerId。[C]

## 28. Transport boundary：`sub_58D7D0` vs `sub_602E00`

部分 165 sender 走：

```text
sub_58D7D0(byte_13242F8, packet)
```

部分 runtime/state event 走：

```text
sub_602E00(packet)
```

目前不能假定兩者等價。仍需分別追：

```text
packet finalization
→ length/header
→ queue/send
→ encryption/checksum
→ socket
```

## 29. TCP logical payload 與 final frame 分離

所有本文件的欄位表描述的是 logical packet body；不能把它直接當成 final TCP frame length。

目前其他 network research 顯示 receive framing 使用 outer length/header；因此：

```text
logical payload
    ≠
final TCP frame
```

Server implementation 必須分兩層處理。[C]

## 30. 目前 Evidence matrix

| 項目 | 狀態 |
|---|---|
| 165 = `Y_TCP_INF_REQ` | CLOSED |
| 166 = `Y_TCP_INF_ACK` | CLOSED |
| 165 為 polymorphic family | CLOSED |
| 165 subtype 16 = MultiDamage | CLOSED |
| 165 subtype 21 = BotSuicide | CLOSED |
| 165 subtype 5/8 = dead-position/state variants | HIGH |
| 165 subtype 13 = vector/interaction report | HIGH |
| 166 n18 = second-level discriminator | CLOSED |
| 166 n18=13 = Game/round reset path | HIGH |
| 166 n18=24 = timing/state path | HIGH |
| 166 n18=3/20 = target runtime value mutation | HIGH |
| 166 n18=2/16 = large runtime-state path | HIGH |
| +240600/+240604 = live round K/D-like state | HIGH |
| F6DCF8/F6DCFC = Server-provided result K/D | CLOSED |
| 166 直接修改 F6DCF8/F6DCFC | NOT FOUND |
| 每一個 `sub_592B20` caller 的 wire width | OPEN |
| `sub_58D7D0` / `sub_602E00` 完整 transport boundary | OPEN |
| 所有 subtype public semantic | OPEN |

## 31. Server reconstruction 中禁止的過早簡化

不要寫：

```text
165 = DamagePacket
166 = DamageAck
166 → Score.Kill++
```

應保持：

```text
YTcpInfReq
    Opcode = 165
    EventSubtype = subtype-specific
    Payload = exact serializer-defined grammar

YTcpInfAck
    Opcode = 166
    ActorOrSubject = first discriminator
    EventSubtype = second discriminator
    Payload = subtype-specific
```

並保留：

```text
raw unknown fields
source function
reader/writer width
state mutation
resource lookup
caller/callee
```

直到 C／LST／Resource／Wiki 證據真正閉合。[C][RES][WIKI][X]

## 32. 下一輪最高優先級

```text
A. 完整追 sub_592B20
   → writer implementation
   → 全 caller
   → reader pairing

B. 完整追 sub_58D7D0 / sub_602E00
   → TCP framing
   → queue
   → encryption/checksum
   → socket boundary

C. 建立 165 subtype 2/4/5/8/9/10/13/15 的 caller→state graph

D. 完整閉合 166 n18=3/20
   → resource
   → target state
   → death
   → score/stat
   → result synchronization

E. 追 166 ↔ 269 K/D aggregation / replacement

F. 用 LST/ASM 驗證可疑 serializer prototype

G. 將 Y_TCP_INF resource IDs 對到 Extracted 的 item/effect/map/ui/sound
```

## 33. 最小可信描述

```text
165 = Y_TCP_INF_REQ
     polymorphic Client→Server gameplay/event/state family

166 = Y_TCP_INF_ACK
     polymorphic Server→Client gameplay/event/state family

165 subtype 16 = MultiDamage
165 subtype 21 = BotSuicide

166 n18=3/20 = target runtime state mutation
166 n18=13   = Game/round reset/start path
166 n18=24   = timing/state path
166 n18=21   = remote action/vector-like propagation
166 n18=2/16 = player runtime synchronization

+240600/+240604 = live round K/D-like counters
F6DCF8/F6DCFC = Server-provided result K/D
+60150/+60151 = local result-screen My K/D

未知欄位、完整 serializer 寬度、transport boundary、
Server-side validation 與 K/D aggregation：持續研究。
```
