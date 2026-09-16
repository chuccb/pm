# `Y_TCP_INF_REQ (165)` / `Y_TCP_INF_ACK (166)`：Gameplay Event / State Packet Family

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client／服務終了時版本

本文件原本以 Damage family 為中心；在重新掃描 Library 中與 GitHub 相同的完整 `PaperMan.exe.c`（約 800,880 lines）後，已證明 `165` 被大量非 Damage gameplay path 共用，因此本文件正式提升為 **Y_TCP_INF family** 研究。

## 1. 最小正確模型

Client packet registration：

```text
165 -> Y_TCP_INF_REQ
166 -> Y_TCP_INF_ACK
```

目前最安全的架構模型：

```text
Y_TCP_INF_REQ (165)
    = client -> server gameplay / actor / effect / state event family

Y_TCP_INF_ACK (166)
    = server -> client gameplay / actor / effect / state event family
```

**不能**建模為：

```text
165 = DamagePacket
166 = DamageAck
```

因為完整 C 已直接找到 subtype 2/4/5/6/7/8/9/10/13/15/16/21 等多個獨立 send path；其中至少有 BotSuicide、dead-position、effect/state、vector/interaction 等非單一 Damage 語意。

---

## 2. 完整 C 掃描後已確認的 165 send families

目前直接找到的高價值建包點：

| Subtype / 形態 | Client path | 目前語意 | Confidence |
|---:|---|---|---|
| 2 | `sub_5DF7F0`, `sub_5E6170` | gameplay/action/state event | B |
| 4 | `sub_5E5ED0`, `sub_5E6040` | effect/resource/state event | B |
| 5 | `CViewObj` dead-position path | dead-position/event variant | B |
| 6/7 | 其他 gameplay/effect callers | event/state | C |
| 8 | `sub_7452D0` | dead-position/state variant | B |
| 9 | `sub_745D60` | small state event | B |
| 10 | `sub_745E80` | small state event | B |
| 13 | `sub_5E6DF0` | vector/interaction report | B |
| 15 | `sub_55D440` | gameplay event | C |
| 16 | `OnSendPacketMultiDamage` / `sub_55D530` | MultiDamage variant | A |
| 21 | `OnSendPacketBotSuicide` / `sub_5658B0` | BotSuicide variant | A |
| other normal values | `OnSendPacketDamage` / Mine-Bomb paths | damage-family variants | A |

這張表是 **目前已發現的 family inventory，不是假定 exhaustive enum**；仍需繼續搜尋所有 `Packet(...,165)` 與間接 virtual send path。

---

## 3. Normal `OnSendPacketDamage`

`OnSendPacketDamage` 建立 opcode 165，前段依序包含：

```text
u8  source/actor-like value
u8  damage/event subtype-like value
[特殊環境才存在的額外 u16 x3]
u8  target/actor-like value
[conditional u8]
u16 resource/weapon-like value (semantic OPEN)
...
```

其中第二 byte `n20` 會被大量 branch 使用：

```c
if ( n20 == 1 || n20 == 3 || n20 == 14 ||
     n20 == 19 || n20 == 17 || n20 == 16 || n20 == 20 )
```

因此目前只能稱：

```text
field1 = event/damage subtype [C high]
```

不能只依名稱把它定義成 public `DamageType` enum。

---

## 4. **重要 wire-width 修正：`sub_592B20` 不能直接視為 1-byte writer**

完整 C 重新檢查後，先前把部分 `sub_592B20(...)` 欄位直接記成 `u8` 是不可靠的。

原因：caller 經常傳：

```c
sub_592B20(packet, SLOBYTE(value));
```

但 `sub_592B20` 本身屬於 4-byte serialization family；caller 的 `SLOBYTE()` 只是把輸入值截成低 byte 後交給 serializer，**不代表 wire field 本身只有 1 byte**。

因此 protocol table 必須區分：

```text
source expression width
vs.
actual serializer / wire width
```

今後所有 `sub_592B20` 欄位都必須回到 writer implementation + reader pairing 再封死 field size。

---

## 5. Normal damage 的計算鏈

Normal damage 在建包前：

```c
v39 = sub_5E72C0(source, target, a5);
v40 = sub_5E72C0(source, target, a6);
```

之後依本地狀態可能乘：

```text
1.0
2.0
```

而 `n20 == 3` 的一條路徑出現：

```text
1.2
```

最後以 `sub_592B20` 序列化。

因此 Server reconstruction 應先恢復：

```text
DamageInput
    -> modifier resolution (`sub_5E72C0`)
    -> subtype/mode multiplier
    -> quantization
    -> Y_TCP_INF_REQ 165
```

不能只建立 `rawDamage -> packet`。

---

## 6. MultiDamage：subtype 16

`GameNetwork::OnSendPacketMultiDamage` 明確：

```c
Packet::possible_ctor_or_dtor_0(v23, 165);
sub_592920(v23, n16);
sub_592920(v23, 16);
sub_592920(v23, n16_1);
```

所以：

```text
165 + field1 == 16
    = MultiDamage send variant [A]
```

後續為 resource/value + 多個 target damage component，再加入 target metadata / relationship data。

注意：其中各 `sub_592B20` 欄位的實際 wire width 不應只看 `SLOBYTE()`，需以 serializer / parser pairing 最終封死。

---

## 7. Mine/Bomb damage：同一 opcode

`GameNetwork::OnSendPacketMineBombDamage` 同樣建立 165：

```text
field0 source/actor-like
field1 event subtype
field2 target/actor-like
...
damage components
...
target metadata
```

因此 Bomb/Mine damage 屬於：

```text
165 subtype-driven family
```

而非獨立 opcode。

---

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

所以：

```text
165
  field0 = u8-like a1
  field1 = u8 subtype 21
  field2 = u16 a2
  field3 = u16 a3
  field4 = i16 a4
```

`subtype 21 = BotSuicide` 是直接 C evidence，屬 A-level family fact；但 field0/a2/a3/a4 的 public semantic 仍 OPEN。

---

## 9. subtype 4：effect/resource/state event

`sub_5E5ED0()`：

```text
165
u8 n16
u8 4
u8 local player
u8 1
u8 n0x1E
u32 a3
```

`sub_5E6040()` 為相近 variant：

```text
165
u8 n16
u8 4
u8 local player
u8 n3
u8 n0x1E
u32 a6
```

兩個 caller 同時保存 event timestamp / value state，且與其他 runtime/effect path 緊密相連，因此目前以：

```text
subtype 4 = effect/resource/state family
```

比 `Damage` 更準確，但還不命名成某個具體 gameplay effect enum。

---

## 10. subtype 5 / 8：dead-position / state family

`CViewObj::TempSendDeadPosPacket` 所在 path 明確建：

```text
165
u8 local player
u8 5
...
position/orientation-related values
```

`sub_7452D0` 也建 165 + subtype 8，並序列化大量 position / transform / matrix-related data。

所以目前：

```text
5 = dead-position/event variant A [B]
8 = dead-position/state variant B [B]
```

尚不能直接宣稱 5/8 wire layout 相同。

---

## 11. subtype 9 / 10：small state events

`sub_745D60()`：

```text
165
u8 local_player
u8 9
u8 state/value at client object +152
```

`sub_745E80()`：

```text
165
u8 local_player
u8 10
```

兩者使用 `sub_602E00()` 結束 packet path，因此值得另外追 `sub_58D7D0` 與 `sub_602E00` 的 transport/finalization 差異。

---

## 12. subtype 13：vector / interaction report

`sub_5E6DF0()` 建：

```text
165
u8 n16
u8 13
u8 local player
u8 a3
u8 a4
4-byte value
4-byte value
4-byte vector.x
4-byte vector.y
4-byte vector.z
```

前三個 vector component 同樣走 `sub_592B20()`，所以目前不應把它們直接標為 1-byte vector components。

其 caller path `sub_5E3A50()` 會先做多項 target / state / geometry 檢查再進入這個 serializer，因此存在：

```text
client local geometry/interaction test
    -> 165 subtype 13 report
    -> server-side authority / validation (?)
```

後半段仍需 `166` 或其他 receive-side evidence 封閉，不能直接推論「client authoritative」。

---

## 13. `166 Y_TCP_INF_ACK` 的真正 parser

完整 `sub_749B90()`：

```c
read u8 n16;
read u8 n18;
switch(n18) { ... }
```

目前直接確認的 second-level discriminators 包含：

```text
1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,
17,18,19,20,21,22,23,24,25,26,27,29,30,31
```

其中：

```text
n18 = 3 / 20
    -> sub_747980
    -> sub_747460

n18 = 13
    -> game/round reset path
    -> NewGameStart / player-state reset

n18 = 24
    -> millisecond-style timer

n18 = 21
    -> vector/action propagation

n18 = 2 / 16
    -> large player/runtime synchronization
```

因此 `166` 也明確是 **polymorphic server→client event/state envelope**。

不能建立：

```text
165 subtype N <-> 166 subtype N
```

這種數字對稱模型。

---

## 14. 166 subtype 3/20：health/state mutation

`sub_747980()` 讀出：

```text
u32 source/event value
u8 target/source-like value
u16 resource/value
u8 n20
u8 auxiliary value
u8 auxiliary value
u32 a6
u32 n26
u8 n0x1E
```

然後進 `sub_747460()`。

核心 mutation：

```c
if ( v45[80] != 0 )
    *(v45[80] + 16) = a6;
```

因此 `a6` 是 target runtime object 上一個明確被 Server 更新的 health/value-like field。

目前應稱：

```text
runtime health/state value [high confidence]
```

只有在後續 object layout + UI + resource chain 再封死後才命名成正式 `HP`。

---

## 15. Score / K-D：現在必須區分兩層資料

### Result / synchronized scoreboard layer

```text
F6DCF8[slot] = Kill
F6DCFC[slot] = Death
```

`sub_6482C0()` 以：

```text
higher Kill
then lower Death
then F33184
```

排序。

### Runtime round-stat layer

`CViewObj::OnDeadCtrl` 直接修改：

```c
++byte_F33120[240780 * killerSlot + 240600];

if ( a4 == 0 )
    ++byte_F33120[240780 * victimSlot + 240604];
```

初始化也直接 zero 這兩個欄位。

`CyIndividualSurvivalMode::sub_76FA50()` 又直接把：

```text
+240600
```

放入 `RoundStat` UI；另一路徑則顯示 `F6DCF8`。

因此目前正確資料模型是：

```text
PlayerSlot
 ├─ runtime round-stat counters (+240600 / +240604)
 └─ result/sync counters (F6DCF8 / F6DCFC)
```

**不能再把這兩層直接視為同一對欄位。**

`F6DCF8/F6DCFC` 的完整 mutation/source 仍需繼續追。

---

## 16. Player identity：PlayerId != SlotIndex

Y_TCP_INF 與 death/score path 同時使用：

```text
sub_67D010()
sub_67D110()
sub_67D7D0()
dword_F6DCF4[slot]
dword_F6DD1C[slot]
```

因此 Server model 必須分離：

```text
PlayerId
SlotIndex
Team/Group
RuntimeObject
ConnectionState
```

不能直接把 packet 的第一個 byte 當作 slot，也不能把 slot 當成 player ID。

---

## 17. Transport boundary：`sub_58D7D0` vs `sub_602E00`

已發現部分 165 sender 結束於：

```text
sub_58D7D0(byte_13242F8, packet)
```

但部分 runtime/state event（例如 subtype 9/10，以及部分 complex transform path）會經過：

```text
sub_602E00(packet)
```

目前不應假設兩者等價。

後續必須各自追：

```text
packet finalization
 -> length/header
 -> queue/send
 -> encryption/checksum
 -> socket
```

這是確認 TCP protocol framing 與不同 packet submission path 的重要 TODO。

---

## 18. TCP framing：不能把 logical payload 當 final wire length

目前其他 network research 已確認 receive framing 會使用 packet frame length + 8-byte outer structure。

因此本文件中所有 field layout 應維持：

```text
logical payload
```

與：

```text
final TCP frame
```

分開紀錄。

尤其 Y_TCP_INF 的 serializer writer width 尚未完全封死前，不應自行計算「固定 packet length」。

---

## 19. 目前 Evidence matrix

| 項目 | C | Resource | Wiki / 實測 | 狀態 |
|---|---|---|---|---|
| 165 = `Y_TCP_INF_REQ` | A | protocol table | — | CLOSED |
| 166 = `Y_TCP_INF_ACK` | A | protocol table | — | CLOSED |
| 165 is polymorphic | A | — | — | CLOSED |
| subtype 16 = MultiDamage variant | A | — | — | CLOSED |
| subtype 21 = BotSuicide variant | A | — | — | CLOSED |
| subtype 5/8 = dead-position/state family | B | — | — | HIGH |
| subtype 13 = vector/interaction report | B | — | — | HIGH |
| 166 n18=3/20 updates runtime health/state-like value | A | — | gameplay context | HIGH |
| runtime +240600/+240604 are round K/D-like counters | A | UI evidence | mode rules | HIGH |
| F6DCF8/F6DCFC are result K/D | A | UI | Wiki result rules | CLOSED |
| 165 directly updates F6DCF8/F6DCFC | — | — | — | OPEN |
| `sub_592B20` wire width for every caller | partial | — | — | OPEN / must re-audit |
| `sub_58D7D0` vs `sub_602E00` | partial | — | — | OPEN |
| exact 165 subtype enum semantics | partial | — | — | OPEN |

---

## 20. Server reconstruction intermediate model

在證據完全封閉之前，建議 protocol abstraction 為：

```text
YTcpInfReq
    Opcode = 165
    Subtype = byte1 / event discriminator
    VariantPayload = subtype-specific
    RawUnknownFields = preserved
```

```text
YTcpInfAck
    Opcode = 166
    ActorOrSubject = first discriminator byte
    EventSubtype = second discriminator byte
    VariantPayload = subtype-specific
    RawUnknownFields = preserved
```

Server implementation 暫時應避免：

```text
one C function = one packet type
one subtype = one guessed public enum
one byte expression = one wire byte
165 = DamagePacket
166 = DamageAck
```

而應保持：

```text
Packet
 -> subtype
 -> exact serializer/parser
 -> state mutation
 -> side effect
 -> related packet
```

直到 C / ASM / Resource / Wiki evidence 足以封閉。

---

## 21. 下一輪最高優先級

### A. 完整追 `sub_592B20`

確認 implementation、所有 reader pairing，以及到底哪些 caller 實際產生 4-byte / 1-byte / packed representation。

### B. 完整追 `sub_58D7D0` / `sub_602E00`

封閉 packet length、header、queue、encryption/checksum、socket boundary。

### C. `165 subtype 2/4/5/8/9/10/13/15` 全部建立 caller→state graph

不再只列 payload；必須找到 caller 的上游 state、resource identity、下游 response。

### D. `166 n18=3/20`

把：

```text
packet field
 -> target object
 -> +16 health-like field
 -> effects
 -> death transition
 -> score/stat
```

整條鏈封閉。

### E. Runtime K/D ↔ Result K/D

確認 `+240600/+240604` 與 `F6DCF8/F6DCFC` 之間是否存在同步、重新計算、round-end aggregation 或 server authoritative replacement。

### F. Resource closure

把 Y_TCP_INF 中的 resource IDs / object IDs 串至：

```text
Extracted/
  character/
  item/
  effect/
  map/
  ui/
  sound/
```

並建立：

```text
Resource -> ID -> loader/parser -> runtime object -> packet/state usage
```

---

## 22. Anti-hallucination conclusion

目前能確定的最小描述：

```text
165 = Y_TCP_INF_REQ
     polymorphic client->server gameplay/event/state family

166 = Y_TCP_INF_ACK
     polymorphic server->client gameplay/event/state family

165 subtype 16 = MultiDamage variant [A]
165 subtype 21 = BotSuicide variant [A]
165 subtype 5/8 = dead-position/state variants [B]
165 subtype 13 = vector/interaction report [B]

166 second byte = event discriminator [A]
166 n18=3/20 = runtime health/state mutation family [A]
166 n18=13 = game/round reset path [A]
166 n18=24 = timer/state path [A]

Runtime round-stat counters:
    +240600 / +240604

Result/sync K-D counters:
    F6DCF8 / F6DCFC

Exact subtype semantics, all serializer widths,
transport/encryption boundary, and complete K/D sync chain:
    CONTINUE RESEARCH
```
