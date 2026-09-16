# `Y_TCP_INF_REQ (165)` / `Y_TCP_INF_ACK (166)`：Damage-family Packet 逆向

> 研究日期：2026-09-16
>
> 這是目前最重要的 gameplay network 發現之一：**opcode 165 並不是「單一語意的 damage packet」；client protocol table 把它命名為 `Y_TCP_INF_REQ`，但多個 `GameNetwork` send path 共用同一 opcode，並用第二個 byte 等欄位形成不同 subtype。**
>
> 因此 Server implementation 不應建立 `Opcode 165 = DamagePacket` 這種過度簡化模型。

---

## 1. Protocol registration：165/166 的官方 client 名稱

C 的 packet registration 明確：

```text
165 -> Y_TCP_INF_REQ
166 -> Y_TCP_INF_ACK
```

同一 registration table 中：

```text
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
167 GR_CHANGEUSER_REQ
168 GR_CHANGEUSER_ACK
```

[C] `PaperMan.exe.c` 約 L178198-L178210；resource/protocol symbol table 約 L673334-L673356。

因此 165/166 位於 TCP/UDP / game networking 的核心 packet namespace，而不是 `GR_* Room setting` namespace。

---

## 2. `165` 被至少四種 send path 共用

目前已直接找到：

```text
GameNetwork::OnSendPacketDamage
GameNetwork::OnSendPacketMultiDamage
GameNetwork::OnSendPacketMineBombDamage
GameNetwork::OnSendPacketBotSuicide
```

都建立：

```c
Packet::possible_ctor_or_dtor_0(..., 165);
```

[C]

這是非常強的 evidence：

```text
one opcode
   └─ subtype / payload variant
       ├─ normal damage
       ├─ multi damage
       ├─ mine/bomb damage
       └─ bot suicide
```

### 重要反證

不能因為某一個 caller 叫 `OnSendPacketDamage`，就把 165 全域命名為：

```text
DamagePacket
```

client 自己的另一條 `OnSendPacketBotSuicide` 也使用同一 opcode。[C]

---

## 3. Common subtype pattern：第二個 byte 非常關鍵

### 3.1 Normal `OnSendPacketDamage`

在 packet 建立後最早的欄位是：

```c
sub_592920(v33, n16);
sub_592920(v33, n20);
...
sub_592920(v33, n16a);
```

其中 `n20` 在 special environment 下還會：

```c
if ( sub_67EB70() && n20 == 1 )
    n20 = 20;
```

而後續對 `n20` 做 subtype-specific branch：

```c
if ( n20 == 1 || n20 == 3 || n20 == 14 ||
     n20 == 19 || n20 == 17 || n20 == 16 || n20 == 20 )
{
    ...
    sub_592920(v33, n3_2);
}
```

[C] `PaperMan.exe.c` 約 L154609-L154667。

所以目前可以安全稱：

```text
field0 = u8 source/actor-like value [semantic OPEN]
field1 = u8 damage/event subtype-like value [C high]
```

但 **不能** 在沒有 receive-side handler 的情況下把 `n20=1/3/14/...` 寫成 public enum。

---

## 4. Normal damage 的 payload：目前已知結構

`OnSendPacketDamage` 在一般 client path 下依序寫入：

```text
field 0  u8      n16
field 1  u8      n20
field 2  [optional u16 x3, anti-special-environment only]
field 3  u8      n16a
field 4  optional u8 subtype-derived value
field 5  u16     a4
field 6  i8/u8   computed damage component
field 7  i8/u8   computed damage component
field 8  u8      n4
field 9  u8      a8
field 10 u8      a9
field 11 u32     target player metadata / `dword_F6DD1C[n16a]` in normal client
field 12 u32     a10
field 13 u8      a11
field 14 u8      a12
field 15 u8      a13
```

後面還有一段：

```text
if (n4 == 4)
    append attacker/target relationship data
```

[C] 約 L154614-L154687。

### 重要精度聲明

這裡的 `field N` 是 **目前由 C serializer 順序建立出的 protocol position**；其中一些欄位的 public semantic 仍 OPEN。

特別是：

```text
a4
n4
 a8/a9
 a10..a13
```

目前不應自行改名成 weapon ID / hit bone / damage type / animation ID 等。

---

## 5. Damage amount 的來源不是隨便一個整數

Normal damage path 會先：

```c
v39 = sub_5E72C0(n16, n16a, a5);
v40 = sub_5E72C0(n16, n16a, a6);
```

再依本地狀態乘以：

```text
1.0
2.0
```

而在 `n20 == 3` 時另一部分使用：

```text
1.2
```

之後以：

```c
sub_592B20(..., SLOBYTE(v39 * multiplier));
sub_592B20(..., SLOBYTE(v40 * multiplier));
```

寫入 byte-sized damage components。[C]

這表示 packet 中的 damage values 是 **經過 client-side calculation / quantization 的結果**，不是單純把某個原始 float 原封不動送出。

Server reconstruction 必須先知道 `sub_5E72C0()` 的真正輸入／輸出語意，才適合定義正式 `DamageAmount` model。

---

## 6. `OnSendPacketMultiDamage`：同 opcode 的第二種 payload

MultiDamage 同樣：

```c
Packet::possible_ctor_or_dtor_0(v23, 165);
```

但其前幾個欄位是：

```text
field 0  u8      n16
field 1  u8      16
field 2  u8      n16_1
field 3  u8      n8_1 or 3
field 4  u16     a3
field 5  byte    computed aggregate damage
field 6  byte    target damage component #0
field 7  byte    target damage component #1
field 8  byte    target damage component #2
field 9  byte    target damage component #3
...
```

後續在 target slot `< 16` 時還會：

```text
u32 target/session metadata (`dword_F6DD1C[target]`)
u32 a7
u8  a8
u8 0
u8 0
u32/u8 relationship data
```

[C] `OnSendPacketMultiDamage` 約 L154890-L155000。

### 強結論

```text
165 + field1 == 16
```

是目前非常明顯的 MultiDamage subtype marker。

但不要直接寫成 `DamageType.Multi`，因為正式 enum semantics 仍須 receive-side / server evidence。

---

## 7. `OnSendPacketMineBombDamage`：同 opcode 的第三種 payload

Bomb/Mine path：

```c
Packet::possible_ctor_or_dtor_0(v15, 165);
```

開頭：

```text
field 0 u8      n16
field 1 u8      n14
field 2 u8      n16a
field 3 optional u8 n3
field 4 u16     a4
field 5 byte    damage component
field 6 byte    damage component
field 7 u8      0
field 8 u8      0
field 9 u8      0
```

若 `n16a < 16`，追加：

```text
u32 dword_F6DD1C[target]
u32 0
a7
u32/u8 a8
```

[C] 約 L154745-L154835。

因此：

```text
165 + subtype/event code
    → mine/bomb-specific damage encoding
```

比建立另一個 opcode 的假設更符合現有 C。

---

## 8. `OnSendPacketBotSuicide`：同 opcode 的第四種 payload

`sub_5658B0()` 是 `GameNetwork::OnSendPacketBotSuicide`，建立：

```c
Packet::possible_ctor_or_dtor_0(v5, 165);
sub_592920(v5, a1);
sub_592920(v5, 21);
sub_5929E0(v5, a2);
sub_5929E0(v5, a3);
sub_5929E0(v5, a4);
```

即：

```text
field 0 u8  a1
field 1 u8  21
field 2 u16 a2
field 3 u16 a3
field 4 i16 a4
```

[C] `PaperMan.exe.c` 約 L159251-L159269。

這是目前最漂亮的 subtype 證據之一：

```text
165 + subtype 21 = bot suicide variant
165 + subtype 16 = MultiDamage variant
```

但 `field0` / `a2..a4` 的 public semantic 仍需要 server / receive-side closure。

---

## 9. `Y_TCP_INF_REQ` 不是簡單的「Request → ACK」CRUD 模型

Registration 看起來是：

```text
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
```

但現在從 outgoing client data flow 看到：

```text
165
├─ normal damage
├─ multi damage
├─ mine/bomb damage
└─ bot suicide
```

所以較合理的模型是：

```text
Y_TCP_INF_REQ
    └─ event subtype
         └─ variant payload
```

而 `166` 是該 protocol pair 的 ACK direction；目前尚未從 `PaperMan.exe.c` 封死其 receive-side payload，因此不能自行假設每一個 165 event 都有一個固定 166 response。

---

## 10. `GR_*` Room packet 與 `165` 必須分 layer

目前已經可以清楚分層：

```text
Room / Lobby
    121..160
    167..192

Gameplay / network information
    165/166 Y_TCP_INF_*

更高層 / GG / GL / PM
    100..160, 183+, 300+
```

尤其 `165` 正好位於：

```text
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
167 GR_CHANGEUSER_REQ
```

這說明 protocol namespace 是歷史累積的 layered design，而不是現代化單一 enum。

---

## 11. 與 Kill / Death scoreboard 的關係：目前只能建立「候選鏈」

已由其他 C 結果 UI 封死：

```text
dword_F6DCF8[slot] = Kill count

dword_F6DCFC[slot] = Death count
```

而 `sub_6482C0()` 依：

```text
higher Kill
then lower Death
then dword_F33184
```

排序。

另一方面，165 payload 明確會攜帶 player/target metadata，例如：

```text
dword_F6DD1C[target]
target slot / actor-like bytes
```

因此 165 **很可能是 gameplay event propagation 的一部分**。

但是目前還不能宣稱：

```text
165 incoming
   → F6DCF8++
165 incoming
   → F6DCFC++
```

因為尚未找到確定的 receive handler 與 counter write path。

### 目前正確狀態

```text
Kill/Death state          = [C] confirmed
165 is gameplay event    = [C] high confidence
165 directly increments
Kill/Death                = [C] not yet proven
```

這個區分必須保留。

---

## 12. 三方交叉驗證現況

| 項目 | C / IDA | Wiki | Extracted RES | 結論 |
|---|---|---|---|---|
| 165/166 protocol names | `Y_TCP_INF_REQ/ACK` | 無直接 public packet 說明 | protocol/resource symbol table | **C closed** |
| Normal damage path | `OnSendPacketDamage` + opcode 165 | public battle rules間接相關 | resource/weapon data 尚待串 | **C closed as send path** |
| MultiDamage | opcode 165 + subtype 16 | 無直接 Wiki packet | 尚未閉合 | **C closed as variant** |
| Mine/Bomb damage | opcode 165 + `OnSendPacketMineBombDamage` | `爆破ミッション` 是 public mode | Bomb resource/runtime 尚待閉合 | **C high** |
| Bot suicide | opcode 165 + subtype 21 | 無直接 packet 說明 | bot resources 尚待閉合 | **C closed as variant** |
| Kill/Death scoreboard | F6DCF8/F6DCFC + result labels | Wiki 有 K/D / result behavior | result/UI resources 尚待 key-level mapping | **C closed** |
| 165 → Kill/Death counter update | 尚未找到 write path | 規則上有 kill/death | 未閉合 | **OPEN** |

### 為什麼不勉強做「三方完全閉合」

這個 protocol 本身是 internal wire contract，Wiki 不會直接列出每個 internal field；因此合理的三方策略不是「每一欄都硬找 Wiki」，而是：

```text
Wiki  -> public mechanic
C     -> wire/data flow
RES   -> concrete resource/object identity
```

三者能接上的地方提升 confidence；接不上的地方保留 raw protocol evidence。

---

## 13. Server reconstruction 應採取的模型

推薦 protocol 層先寫成：

```text
YTcpInfReq
    Opcode = 165
    Subtype = byte1
    Payload = subtype-specific
```

例如：

```text
Subtype 16
    -> MultiDamagePayload

Subtype 21
    -> BotSuicidePayload

Other normal values
    -> Damage-family payloads

Subtype semantics
    -> central registry, not global magic numbers
```

同時保留：

```text
RawPayload
RawUnknownFields
```

直到 receive path / server-side data model 被封死。

---

## 14. 下一步真正高價值的追蹤

### A. 找 165 的 receive handler

目標：

```text
Y_TCP_INF_REQ (165)
      ↓
server/client receive dispatcher
      ↓
subtype byte
      ↓
normal damage / multi / bomb / suicide
```

### B. 找 `166 Y_TCP_INF_ACK` parser

確認是不是：

```text
fixed ACK
```

還是也帶 subtype / result fields。

### C. 追 `dword_F6DCF8` / `F6DCFC` write path

尋找：

```text
Kill++
Death++
```

是否發生在：

```text
165 family
```

還是另一個 `TCP_UDP_DEAD` / `GR_END` / `GG_GAMEEND` family。

### D. 追 `sub_5E72C0()`

這是把 weapon / hit / damage inputs 變成 packet byte 的關鍵函式之一；若封死，其結果將直接決定 `OnSendPacketDamage` 的 `field5/field6` 語意。

---

## 15. 最重要的 anti-hallucination conclusion

目前絕對不要把 protocol 寫成：

```text
165 = damage
165 = attackerID,targetID,damage
166 = damageAck
```

這樣會丟掉 client 真正的 polymorphic structure。

目前證據支持的最小正確描述只有：

```text
165 = Y_TCP_INF_REQ
     subtype-driven gameplay/network information request/event

subtype 16 = MultiDamage send variant [C]
subtype 21 = BotSuicide send variant [C]
normal damage / mine-bomb damage also reuse opcode 165 [C]

exact field semantics = continue reverse engineering
```

這個描述才適合作為後續 Server implementation 的 compatibility-safe intermediate specification。
