# PaperMan 2016 JP — UDP Movement / Control Plane 修正附錄

> 研究日期：2026-09-18  
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。  
> 目的：修正 `Network_Protocol.md` 與 `UDP_Movement_Control_Evidence_2026-09-18.md` 中前一輪研究留下的 byte-width / semantic 命名問題。  
> 狀態：本文件只記錄已重新由 `PaperMan.exe.c` 交叉核對的修正；未證實的欄位仍保持 OPEN。

## 1. Critical correction — S→C ActorRecord 是 27 bytes，不是 26 bytes

`sub_602E30()` 的每個 actor record 依 helper 真實 wire width 計算：

```text
u8   field00                 1
u8   field01                 1
u8   ActorKey                1
u32  field03                 4
u32  field07                 4
u8   ActorStateByte          1
u16  QuantizedPos0           2
u16  QuantizedPos1           2
u16  QuantizedPos2           2
u8   field18                 1
u8   field19                 1
u8   field20                 1
u8   field21                 1
u8   StateCode               1
u32  WeaponNum               4
--------------------------------
                           = 27 bytes
```

source 順序直接由 `sub_602E30()` 可見：`v28/v19/n16/v30/v16/v25/v35/v36/v37/v23/v38/v14/v15/n0x1C/v29`，最後 `sub_592A40()` 再讀 4 bytes。[C: `PaperMan.exe.c` 234012–234143]

因此正式模型應為：

```text
payload = u8 actor_count + actor_count × 27-byte ActorRecord
```

這取代此前文件中的 `26 bytes / actor`。

## 2. S→C ActorRecord offsets — corrected

以 record 起點 `R`：

```text
R+00  u8   field00                         OPEN
R+01  u8   field01                         OPEN
R+02  u8   ActorKey                        player/actor key namespace
R+03  u32  field03                         OPEN
R+07  u32  field07                         OPEN
R+0B  u8   ActorStateByte                   confirmed actor state storage
R+0C  u16  QuantizedPos0                    /3.0
R+0E  u16  QuantizedPos1                    /3.0
R+10  u16  QuantizedPos2                    /3.0
R+12  u8   field18                         OPEN
R+13  u8   field19                         OPEN
R+14  u8   field20                         OPEN
R+15  u8   field21                         OPEN
R+16  u8   StateCode                        state / transition code
R+17  u32  WeaponNum                        CGunData index
```

`R+0B` 不是 padding：它直接送入 `sub_5B3180()`，後者寫入 actor `+233`。[C: `PaperMan.exe.c` 234130–234140]

## 3. R+0C/R+0E/R+10 的位置量化

`sub_602E30()` 對三個 `u16` 直接做：

```text
float0 = wire_u16_0 / 3.0
float1 = wire_u16_1 / 3.0
float2 = wire_u16_2 / 3.0
```

[C: `PaperMan.exe.c` 234077–234090]

Client→peer 的 movement serializer `sub_744450()` 對本地 `this+16/20/24` 分別以：

```text
wire_u16 = value * 3.0 + 0.5
```

再交給 `sub_5929A0()`；而 `sub_5929A0()` 明確只寫 2 bytes。[C: `PaperMan.exe.c` 377420–377455; 180475–180480]

因此目前可安全描述為：

```text
world coordinate family ↔ 16-bit quantized coordinate family
scale = 3
wire decode = ushort / 3.0
wire encode expression = value * 3.0 + 0.5
```

負值、overflow、最終截斷行為與 public X/Y/Z 命名仍不額外推導。

## 4. R+16 — StateCode

`R+16`（原 `n0x1C`）直接傳入：

```text
sub_5B34B0(actor, weaponNum, StateCode, ...)
```

`sub_5B76A0()` 對 `StateCode & 0x7F` 有明確內部狀態映射：

```text
7   → internal 5
0x0C → internal 5
0x0D → internal 6
1   → internal 1
2   → internal 1
4   → internal 2
5   → internal 3
6   → internal 4
0x0A → internal 7
0x0B → internal 8
```

因此 `R+16` 應正式命名成：

```text
StateCode / StateTransitionCode
```

而不是完全未命名的 raw byte；但仍不能把每個 wire value 自行命名成具体 gameplay enum。[C: `PaperMan.exe.c` 5B76A0 附近 source]

## 5. R+17 — WeaponNum / CGunData index

`R+17` 的 `u32` 進入 `sub_5B34B0()`，再由 `sub_5B35F0()`：

```text
*a4   = sub_5F5400(CGUN_DATA, thisa)
*p_n10 = sub_5F5450(CGUN_DATA, thisa)
```

而 `sub_5F5400()` / `sub_5F5450()` 都把 `a2` 當成 `CGunDataCtrl` table index，並以每筆固定資料大小尋址；相關 API 的 diagnostics 又直接使用 `WeaponNum`、`gunindex`、`CGunDataCtrl::GetMyGunParamProtectedData` 等名稱。[C: `PaperMan.exe.c` 196961–197045; 228180–228224]

所以：

```text
S→C ActorRecord +0x17 : u32 WeaponNum / GunIndex
```

已達高可信度；不是泛稱 `ActionOrResourceValue`。

## 6. C→peer opcode 23 的 +0x16 同一 weapon namespace

`sub_744450()` 建立 opcode 23：

```text
+00 u8   session-like value = *sub_417D00()
+01 u8   byte_EE896D
+02 u8   local player slot = sub_67D010()   [normal mode]
+03 u32  dword_EE8CB4
+07 u32  n0x64_0
+0B u8   MoveStateFlags
+0C u16  quantized position 0
+0E u16  quantized position 1
+10 u16  quantized position 2
+12 u8   state/angle byte A
+13 u8   state/angle byte B
+14 u8   actor-state byte
+15 u8   StateOrActionByte
+16 u32  WeaponNum = sub_5AA5C0(current gun object)
```

`sub_5AA5C0()` 本身就是回傳所持 gun object 的 `+12` 欄位；大量使用點再以該值呼叫 `CGunDataCtrl` 的 `GetMyGunParamProtectedData`、`GetHandModel`、`GetHandAni` 等 API。[C: `PaperMan.exe.c` 192070–192104; 228180–228280]

因此兩方向可建立對稱的 wire semantic family：

```text
C→S/peer opcode 23 +0x16 = WeaponNum
S→C ActorRecord +0x17   = WeaponNum
```

兩者 wire offset 不同，但都指向相同的 `CGunDataCtrl` weapon namespace。[C][X]

## 7. ActorKey / local slot 不可混稱

`sub_67D010()` 直接以字串 `G_GetMySlot` 記錄，正常模式返回 `n0x10`，special mode 返回 `-2`。[C: `PaperMan.exe.c` 287284–287318]

因此：

```text
C→S opcode 23 +0x02
    = local player slot value (normal mode)
```

但 S→C `R+02` 經 `sub_67DF00(n16)` / `sub_67D7D0(n16)` 後具有雙 namespace 行為：

```text
16..75  → 可直接使用原值
0..15   → 與 16-player table / actor-slot mapping 互動
```

所以 S→C `R+02` 應命名：

```text
ActorKey / PlayerKey
```

而不是直接寫死 `SlotIndex`。[C: `PaperMan.exe.c` 287284–287318 及 movement consumer]

## 8. opcode 154 — value 確定是 u8，不是 u32

`sub_5965D0()`：

```text
u8 count
repeat count:
    u8 key
    u8 value
```

然後把 `value` 寫入：

```text
dword_F6D9E8[slot]
```

[C: `PaperMan.exe.c` 182595–182629]

所以正式 wire model：

```text
UDP 154 = u8 count + count × { u8 ActorKey, u8 value }
```

此前文件中的：

```text
u32 value
```

是錯誤，必須移除。

## 9. opcode 22 與 154 必須分開

`sub_5964E0()` 的 opcode-22 handler 則明確為：

```text
u8 flag
if flag == 1:
    u8 count
    repeat count:
        u8 key
        u32 value
```

[C: `PaperMan.exe.c` 182551–182578]

因此：

```text
22 → key + u32 value
154 → key + u8 value
```

兩者都更新 `F6D9E8[slot]`，但 wire width 不同，不能因目的地相同而合併。

## 10. opcode 19 / 20 的重新定位

`sub_596670()` 約每 500 ms 建立 UDP opcode 19；其 payload 由 session/channel-like byte、`byte_EE896D`、special-mode flag、local slot/game identifier、`dword_EE8CB4` 與一個 `sub_537740(byte_EE8968)` 取得的字串構成，並送往 current peer。[C: `PaperMan.exe.c` 182620 附近]

其 retry/count state：

```text
next send ≈ +500 ms
count++
count > 5 && count < 100
    → sub_560720()
```

opcode 20 的 handler `sub_5968C0()` 則：

```text
byte_1D0CFE7 = 1
count = 0
state reset
sub_594F00(...)
```

因此目前最安全的名稱是：

```text
19 = recurring UDP readiness/liveness probe
20 = corresponding response/reset path
```

是否應正式稱為 `REQ/ACK`，仍保留 OPEN，因為目前直接看到的 opcode-20 registration name 尚不足以獨立證明所有語境都完全等價於 ACK。[C]

## 11. PM_UDPSTART / PM_CONNECT hierarchy

Protocol registration 明確：

```text
141 PM_CONNECT_REQ
142 PM_CONNECT_ACK
143 PM_UDPSTART_REQ
144 PM_UDPSTART_ACK
```

[C: `PaperMan.exe.c` 178120–178219]

`sub_555C60()` 建立 TCP opcode 143：

```text
string
u32 n100
u8 = 1
u32 dword_231800C
```

再送往 lobby/game TCP socket。[C: `PaperMan.exe.c` 150850–150929]

`sub_5565D0()` 處理 opcode 142 時讀取：

```text
string cp
u16 hostshort
u8 v15
u32 v14-like value
```

並把 endpoint 設給 UDP-related endpoint storage。[C: `PaperMan.exe.c` 151069–151278]

所以：

```text
PM_CONNECT_ACK
    → supplies UDP endpoint/session-related setup
    → PM_UDPSTART_REQ
    → PM_UDPSTART_ACK
```

但 `PM_UDPSTART_ACK` 本身的所有 payload 欄位還沒有完全閉合，不在此提前命名。

## 12. UDP socket port caveat

`CUDPSocket` constructor 的 `+56` port-like member 預設是 `27000`，但 `sub_596DA0()` 真正 bind 使用 runtime `*(this+56)`；因此：

```text
27000 = constructor default
≠ 已證明的最終 runtime bind port
```

[C: `PaperMan.exe.c` 182700–182759]

## 13. Server implementation implications

Server 目前應以以下 binary model 為基線：

```text
S→C UDP 8/24
    u8 actorCount
    repeat actorCount:
        ActorRecord[27]

C→S/current-peer UDP 23
    fixed 27-byte LocalMovementState
```

並且：

```text
ActorRecord[0x17].WeaponNum
    → validate against CGunData / weapon table

LocalMovementState[0x16].WeaponNum
    → same conceptual weapon namespace

ActorRecord[0x16].StateCode
    → validate against supported state domain

ActorRecord[0x02].ActorKey
    → resolve through the client-observed key/slot mapping
```

Server 不應：

```text
把 ActorRecord 寫成 C# struct + padding 然後猜 layout
把 opcode 154 的 value 寫成 u32
把 S→C ActorKey 直接當 0..15 slot
把 opcode 23 與 S→C 27-byte ActorRecord 共用同一 struct
```

## 14. Evidence discipline

本附錄目前最高可信的新結論是：

```text
1. S→C ActorRecord = 27 bytes
2. S→C +0x17 = WeaponNum / GunIndex
3. C→peer opcode23 +0x16 = same WeaponNum family
4. S→C +0x16 = StateCode, with observed internal mapping
5. opcode154 value = u8
6. opcode22 value = u32
7. C→peer opcode23 +0x02 = G_GetMySlot-derived value
8. S→C +0x02 = broader ActorKey / PlayerKey namespace
```

這些結論以 `PaperMan.exe.c` 的實際 read/write width、consumer 與 runtime table usage 為主；Wiki / extracted resources 只在 semantic cross-validation 時加權，不拿名字取代 binary evidence。
