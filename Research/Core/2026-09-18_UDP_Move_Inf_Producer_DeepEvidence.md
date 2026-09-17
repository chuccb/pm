# 2026-09-18 UDP `Y_UDP_S_MOVE_INF` Producer／Movement Record Deep Evidence

> Target: 日本版 PaperMan 2016 年服務終了時的最終 Client。
> Purpose: 追查 `Y_UDP_S_MOVE_INF` (`8/24`) 的 producer、26-byte actor record serializer 與前後資料流；只寫目前直接證據，不以常見 FPS protocol 慣例補欄位。

## 1. Confirmed receiver boundary

`sub_602E30()` 對 inbound movement payload 逐 actor 解析：

```text
u8 actor_count
actor_count × record
```

每筆 record 的固定 parser consumption：

```text
+00 u8
+01 u8
+02 u8
+03 u32
+07 u32
+0B u8[4]
+0F u16
+11 u16
+13 u16
+15 u8
+16 u8
+17 u8
+18 u8
+19 u8
+1A u32
```

總長 = `0x1A = 26` bytes。

位置-like `+0F/+11/+13` 經 `/3.0` 轉成 float-like 3D values。

## 2. Receiver's immediate state application

同一 actor record 會形成以下 data-flow：

```text
record +02
   ↓ sub_67DF00 / sub_67D7D0
actor runtime object / PlayerSlot-like identity

record +03/+07
   ↓
auxiliary snapshot/state values [OPEN]

record +0F/+11/+13
   ↓ /3.0
3D spatial state
   ↓ sub_9BCB00
snapshot/interpolation path

record +0B byte
   ↓ sub_5B3180
actor +233 state byte

record +1A u32
   ↓ sub_548E80
resource/action identity validation
   ↓ possible 714 report

record +1B? (actually +0x1? parser local layout must be read from exact decompiler offsets)
   ↓ sub_5B34B0
PState/action transition path
```

此圖中最後兩者在 Hex-Rays local naming 上存在 overlap/offset ambiguity；真正 wire-relative offsets 應以 serializer/consumer pair 再閉合，不得由 local variable name 自動生成 public field name。

## 3. Nested event/effect object: stronger direct evidence

`sub_5E2570()` 在 movement actor record parsing 後讀取 nested subtype：

```text
n2_1 = first nested type byte
```

### Type 1 / 2 / 3

都會落到 runtime object type `1`，並保存：

```text
object +00 = 1
object +02 = caller-provided `a7`
object +04 = actor identity (`n16`)
object +08..+10 = one 3D vector
object +11..+13 = second 3D vector
object +05 / +06 = subtype-specific identity/value
object +07 = outer `a6`
```

Type-specific wire decoding：

```text
Subtype 1
  u8 value
  u8 value
  6 × u16 values

Subtype 2
  u16 value
  u8 value
  6 × u16 values

Subtype 3
  u8 value
  6 × u16 values
```

### Type 4

```text
runtime object +00 = 2
+02 = `a7`
+04 = actor identity
+08..+10 = first 3D vector
+11..+13 = second 3D vector
+56 = (u32 != 0)
+57 = (u32 != 0)
```

它直接來自：

```text
u32 v33
u32 v36
6 × float values
```

而不是由 movement record 固定的 26-byte fields 本身推導。

### Queue insertion

object materialize 後直接：

```text
sub_59E490(this + 5387, ..., &object)
```

因此這些資料進入另一個持續 runtime queue/list；不是 parser local temporary only。

## 4. Producer search result

目前直接掃描 `PaperMan.exe.c` 後，尚未找到可對稱命名的單一 Client-side serializer：

```text
Y_UDP_S_MOVE_INF

=> receiver `sub_602E30` exists
=> direct producer in this executable remains OPEN
```

重要原因：`sub_602E30` 是 consumer-side parser，不能從其 field list 反向假定 Server serializer 一定就在 Client 中存在；它很可能是 Server→Client protocol 的 receiver-only message。

因此：

```text
26-byte record parser = Confirmed
26-byte record serializer = Unknown
```

## 5. UDP transport relation

UDP receive manager 在 peer/address infrastructure 之外還存在 periodic/health traffic；movement parser 不是 peer endpoint distribution parser。

目前可以安全分成：

```text
UDP peer-address / maintenance family
    ≠
Y_UDP_S_MOVE_INF gameplay snapshot family
```

兩者共享 UDP transport，但 payload semantics 與 state application 完全不同。

## 6. High-value unresolved mappings

```text
R+00 exact semantic
R+01 exact semantic
R+02 exact identity namespace
R+03 exact u32 semantic
R+07 exact u32 semantic
R+0B[0] exact state byte semantic
R+15/R+16/R+17/R+18/R+19 exact byte semantics
R+1A exact Resource/Action namespace
```

下一步應優先從：

```text
sub_5B3180
sub_5B34B0
sub_5B71F0
sub_548C80
sub_67DF00
sub_67D7D0
sub_9BCB00
sub_5E2570
```

的所有 caller/consumer 與 string/resource references 反向閉合。
