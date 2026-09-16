# Y_TCP_INF Transport / Serialization Boundary

> 研究日期：2026-09-16
> Target：日本版 PaperMan 2016 年最終 Client

## 1. Packet construction 與 socket submission 是不同層

PaperMan 的 gameplay packet 建立通常是：

```text
Packet ctor(opcode)
  ↓
sub_5929xx / sub_592Bxx field serializers
  ↓
packet buffer
  ↓
submission wrapper
  ↓
socket/send queue
```

不要把 `Packet` field serializer 誤當成 socket framing。

---

## 2. `sub_592B20` 的實際 wire width

完整 C：

```c
void *__thiscall sub_592B20(void *this, char a2)
{
    sub_592580(this, &a2, 4u);
    return this;
}
```

因此：

```text
sub_592B20 = 4-byte serializer
```

即使 caller：

```c
sub_592B20(packet, SLOBYTE(value));
```

也不能將 wire field 判定成 1 byte。

同一 serializer family：

```text
sub_592B20 -> 4 bytes
sub_592B40 -> 4 bytes from buffer
sub_592B60 -> 8 bytes
sub_592B80 -> 8 bytes
```

這個 distinction 已在 Damage、MultiDamage、subtype 7/8/13 等多條 Y_TCP_INF path 產生實質影響。

Evidence：完整 `PaperMan.exe.c` 約 `sub_592B20`。

---

## 3. `sub_58D7D0` 是主要 submission wrapper

```c
_BYTE *__thiscall sub_58D7D0(_BYTE *this, int a2)
{
    if ( sub_67F120() == nullptr )
    {
        if ( sub_67EC20() == nullptr )
        {
            if ( *(this + 52) != 0 )
                this_3 += sub_555090(&dword_1321D00, a2);
        }
    }
    return ...;
}
```

因此一般 client path：

```text
packet
  -> sub_58D7D0
  -> sub_555090(&dword_1321D00, packet)
  -> socket / send queue layer
```

`dword_1321D00` 被反編譯成 `SOCKET`。

Evidence：`PaperMan.exe.c` `sub_58D7D0` 約 L177985+。

---

## 4. `sub_602E00` 不是另一套 transport

完整 C：

```c
_BYTE *__stdcall sub_602E00(int a1)
{
    result = sub_67EAC0();
    if ( result == nullptr )
    {
        result = sub_67F120();
        if ( result == nullptr )
            return sub_58D7D0(byte_13242F8, a1);
    }
    return result;
}
```

因此：

```text
sub_602E00
    = conditional front-end
    -> sub_58D7D0
    -> sub_555090
```

它不能建立成：

```text
602E00 = UDP transport
```

或另一套獨立 TCP transport。

它只是根據特殊環境條件決定是否進入正常 `58D7D0` submission path。

Evidence：完整 `PaperMan.exe.c` `sub_602E00`。

---

## 5. Y_TCP_INF 的兩層 framing

目前應至少分：

```text
Logical Packet Payload
    ↑
field serializers (`sub_5929xx`, `sub_592Bxx`...)
    ↓
Packet object / internal buffer
    ↓
outer packet framing
    ↓
submission (`sub_58D7D0`)
    ↓
`sub_555090`
    ↓
Socket / queue
```

其他 network research 已證明 TCP receive framing 存在額外 8-byte outer structure，因此不能用「所有 payload field 總和」直接當 final TCP frame length。

---

## 6. Y_TCP_INF 兼容性分析的重要原則

對每個 opcode/subtype 必須同時記錄：

```text
expression type at caller
serializer used
serializer byte count
logical field semantic
outer frame contribution
```

例如：

```c
sub_592B20(packet, SLOBYTE(damage));
```

不能寫成：

```text
damage: u8
```

在未完成 parser pairing 前，至少要寫：

```text
source expression: low-byte value
serializer: sub_592B20
wire width: 4 bytes
semantic: OPEN/HIGH depending on caller
```

---

## 7. Server reconstruction implication

Server packet codec 不應直接照 Hex-Rays 的 C prototype 產生 C# struct。

應先建立：

```text
ProtocolField
  - LogicalType
  - WireWidth
  - Signedness
  - Serializer
  - Parser
  - Semantic
  - Confidence
```

再建立具體：

```text
YTcpInfReq<TSubtype>
YTcpInfAck<TEvent>
```

這樣可以避免：

```text
char expression
    => guessed u8 wire field
```

這種逆向最常見的 compatibility bug。

## Evidence

- `[C]` `sub_592B20`
- `[C]` `sub_58D7D0`
- `[C]` `sub_602E00`
- `[C]` `sub_555090` caller relationship
