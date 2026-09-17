# PaperMan 2016 JP Final — Login-Adjacent Protocol 680–696

> 研究日期：2026-09-17
> Target：日本版 2016 Final Client
> Primary evidence：`PaperMan.exe.c` registration table + receive dispatcher + concrete sender/receiver bodies.
> Purpose：把 Login 前後緊鄰的 680–696 協定族與真正存在於 Final Client 的 wire grammar 分開。

## 1. Official registration namespace

The Client directly registers:

```text
680 GL_LOGIN_BASE
681 GL_LOGIN_ACK
682 GL_LOGIN_REQ
683 GL_SERVERLIST_NOTICE
684 GL_LOGIN_DUPLICATE
685 GL_TUTORIALINDEX_REQ
686 GL_TUTORIALINDEX_ACK
687 GL_TUTORIAL_START
688 GL_TUTORIAL_END
689 GL_TUTORIAL_INDEX_SET_REQ
690 GL_TUTORIAL_INDEX_SET_ACK
691 GL_ITEM_MODIFY_NOTIFIER
692 GG_CP_TERMINATE_APP
693 GL_TCPCONNSUCC
694 GL_ACCOUNTCONNSUCC
695 GS_BUY_ONCEITEM_REQ
696 GS_BUY_ONCEITEM_ACK
```

Registration alone does not prove that a packet has a final-client handler.

## 2. Packets with concrete Final Client handlers/senders

### 680 GL_LOGIN_BASE

No concrete Packet constructor or `sub_58B010` receive case was located in the current C export.

```text
status: registration-only in this Client export
body: unknown
```

Do not invent a body.

### 681 GL_LOGIN_ACK

Concrete receiver: `CLobbyLogin::sub_43E500`.

```text
+00 u32 status
```

`status == 1` enters success bootstrap; failure branches do not consume the success record grammar.

Success then:

```text
u32 v144
u32 n100
u32 v140
if v140 > 0:
    u32 v120
    u32 v141
    u8  v135
u16 server_record_count
repeat records:
    server-record variable grammar
u32 v142
u32 v137
```

`n100` is reused by 143.

Server-record wire grammar and 132-byte Client storage are documented separately in `Login_681_Server_Record_Field_Schema.md`.

### 682 GL_LOGIN_REQ

Concrete sender: `CLobbyLogin::sub_43DF00`.

```text
ASCII-Z USERID
ASCII-Z PASSWORD
u64 datarevision-derived verification composite
u8  hardware-ID source/state
raw 24-byte hardware-ID slot
```

USERID/PASSWORD are sourced from Login UI state at `this+132` / `this+260`. The third `sub_401B50()` after serialization is client state update and is not a third wire string.

### 683 GL_SERVERLIST_NOTICE

No concrete receive case or sender was located in the current final-client C export.

```text
status: registration-only
body: unknown
```

### 684 GL_LOGIN_DUPLICATE

No concrete receive case or sender was located in the current final-client C export.

```text
status: registration-only
body: unknown
```

### 685 GL_TUTORIALINDEX_REQ

Concrete sender: `sub_55C6F0`.

```text
payload = 0 bytes
```

### 686 GL_TUTORIALINDEX_ACK

Concrete receiver: `sub_55C790`, dispatcher case 686.

```text
+00 u32 tutorial_index
```

The u32 is stored in the global/tutorial state consumed by `sub_4422B0`.

### 687 GL_TUTORIAL_START

Concrete sender: `sub_5624D0`.

```text
payload = 0 bytes
```

Sent only when `sub_67EC20() == nullptr`.

### 688 GL_TUTORIAL_END

Concrete sender: `sub_562570`.

```text
payload = 0 bytes
```

The sender updates a local tutorial/game state flag after sending; the packet itself has no payload.

### 689 GL_TUTORIAL_INDEX_SET_REQ

Concrete sender: `sub_55C7D0`.

Despite its Hex-Rays prototype:

```c
sub_55C7D0(char n100)
```

it calls `sub_592A20`, therefore the wire field is:

```text
+00 u32 tutorial_index
```

The decompiler parameter type must not be copied into the protocol definition.

### 690 GL_TUTORIAL_INDEX_SET_ACK

No concrete receive case or sender was located in the current final-client C export.

```text
status: registration-only
body: unknown
```

### 691 GL_ITEM_MODIFY_NOTIFIER

Concrete receiver: `sub_55C880`, dispatcher case 691.

Exact grammar:

```text
+00 u32 count
+04 u32 flags
repeat count:
    if (flags & 0x01):
        u32 key/resource_id
        u32 value
    else if (flags & 0x10):
        u32 key/resource_id
        u32 value
```

The first branch calls:

```text
sub_534450(dword_EE3E98, key, value)
```

The second branch calls:

```text
sub_528D20(CClientData, key, value)
```

Important: this is an `if / else if`, not two independent flags per entry. Because `flags` is shared by the whole packet, every record in one packet uses the same selected branch.

### 692 GG_CP_TERMINATE_APP

Concrete receiver: `sub_55C960`, dispatcher case 692.

```text
+00 u32 message/resource key
```

The value is passed to the localization lookup with resource key `0x31D` and displayed to the user.

This handler does not itself read a text string from the wire.

### 693 GL_TCPCONNSUCC

Concrete receiver: `sub_57CAE0`, dispatcher case 693.

The handler consumes no fields:

```text
payload consumed = 0 bytes
```

It performs a client-side state update and sends 143.

### 694 GL_ACCOUNTCONNSUCC

Concrete receiver: `CLobbyLogin::sub_43E500`.

```text
+00 u16 negotiated_packet_limit
```

The value is bounded against `0x2580` (9600), the Client's packet-buffer ceiling. The packet therefore participates in transport framing/configuration negotiation, not ordinary account data.

694 transitions the client into the 682 Login request path.

### 695 GS_BUY_ONCEITEM_REQ

Concrete senders exist in multiple item/purchase contexts.

The opcode is **polymorphic by item descriptor class**. The Client does not use one fixed body grammar for all 695 requests.

Generic concrete grammars include:

```text
Class A:
    u32 item/resource key
    ASCII-Z secondary string
    u8 item-duration/type byte
    u8 period/count byte

Class B/C/D:
    u32 item/resource key
    u8 item-duration/type byte
    u8 period/count byte

Special range:
    u32 transformed item/resource key
    u32 period/count/value

One known gun-shooting path:
    u32 fixed item/resource key
    u8 validated item category/value
    u8 caller-provided category/value
    u16 encoded negative quantity/state
```

The exact grammar is selected by `sub_9A8620`, `sub_9A8640`, `sub_9A8660`, `sub_9A8680`, `sub_9A85E0` and item/resource-address ranges.

`sub_46EC10` provides stable item-class codes for known fixed descriptors:

```text
E975A1 → class 1
E975A2 → class 2
E975A7 → class 3
E975A4 → class 4
E975A3 → class 5
```

Do not rename these classes to business item names without resource evidence.

### 696 GS_BUY_ONCEITEM_ACK

Concrete receiver: `sub_571D70`, dispatcher case 696.

Leading field:

```text
+00 u8 ack_mode
+01 u32 item/resource descriptor
```

`ack_mode` is deliberately named this way because it selects different payload grammars rather than behaving as a simple success/error enum.

#### ack_mode == 0

```text
u32 value
```

#### ack_mode == 1 + fixed special item E975BE

```text
u32 value
```

The value is applied through `sub_5392A0`.

#### item class E975A3/E975A4 family (`sub_9A8660`)

```text
u32 resource/key
u32 value
```

On one branch the second value updates ClientData through `sub_534450` when `n11 == 6`.

#### item class E975A1 (`sub_9A8620`)

```text
ASCII-Z string
```

on `ack_mode == 1`; the string is fed into a Client-side state setter (`sub_5375B0`) and UI feedback path.

#### item class E975A2 (`sub_9A8640`)

```text
nested ClientData decoder (`sub_523A90`)
u32 value
u32 value
```

#### additional resource/category families

The handler conditionally consumes further `u32`, `u8`, `u16`, or string fields depending on the item descriptor. These branches are tied to the same predicates used by request 695.

After the branch-specific section, `ack_mode == 1` has a common trailer:

```text
u32 v28 → EE8D18
u32 v31 → ArgList-related state
u32 v45 → EE8D1C
u32 v32 → local/context value
```

The exact business names of these trailer values are not unique in the current Client; retain raw names until a stronger consumer is found.

## 3. Fixed Login-chain conclusion

For the final Client, the transport-critical login chain is:

```text
693
 → 143
 → 694
 → 682
 → 681
 → server-list records
 → secondary connection 141/142
 → 143/144 UDP bootstrap
```

The exact ordering between 693/694 depends on connection ownership/state transitions; do not assume both arrive on the same socket without tracing the socket object.

The tutorial and purchase packets 685–696 are adjacent protocol namespace but are not all part of the minimal credential handshake.

## 4. Absolute reconstruction rule

For 680–696:

```text
registration name = opcode identity only
receiver/sender = actual final-client evidence
wire width = actual reader/writer helper
semantic name = consumer/resource evidence
```

No missing field should be fabricated merely because the registration table suggests what a packet "ought" to contain.
