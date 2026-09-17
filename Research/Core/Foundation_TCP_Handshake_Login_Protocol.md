# PaperMan 2016 JP Final — Foundation TCP / Handshake / Login Protocol

> 研究日期：2026-09-17  
> Target：日本版 PaperMan 2016 結束營運時最終 Client  
> Primary evidence：IDA `PaperMan.exe.c` exact helper bodies, socket lifecycle, dispatcher, caller/data-flow, ClientData/resource references.  
> Rule：wire width is determined by the actual serializer/reader helper, never by Hex-Rays local prototypes.

## 1. TCP transport and framing

Two ClientSocket instances are used:

```text
dword_131F730 = login/account TCP
dword_1321D00 = lobby/gameplay TCP
```

TCP socket creation is:

```text
AF_INET / SOCK_STREAM / IPPROTO_TCP
```

Receive uses a persistent buffer and `WSARecv()`, then repeatedly parses complete frames. A single receive may contain partial or multiple packets.

Wire frame:

```text
+0x00 u16 logical_length
+0x02 u16 opcode
+0x04 u16 payload_checksum/xor-field
+0x06 u16 auxiliary/compression-related field
+0x08 payload
```

Transmit size is `logical_length + 8`.

Receive explicitly waits until at least `logical_length + 8` bytes are buffered, validates/transforms the packet, dispatches it, then removes exactly that frame and retains the remainder.

## 2. Packet integrity/transform

`sub_592220()` computes the 16-bit checksum as the sum of bit-popcounts of payload bytes.

`sub_5923D0()` computes/stores that value when header +0x04 is zero, then calls `sub_592470()`.

`sub_592470()` XORs every payload byte with the low byte of header +0x04.

`sub_592420()` reverses the XOR transform and compares the stored 16-bit value against a freshly recomputed checksum.

Therefore +0x04 is definitively an integrity/obfuscation field. Do not label it as a cryptographic key.

Header +0x06 participates in compression/decompression size validation, but its final public protocol name is still OPEN.

## 3. Fixed-width codec authority

```text
u8   read/write  = sub_592900/940 and sub_5928E0/920/960
u16  read/write  = sub_5929C0/A00 and sub_5929A0/9E0
u32  read/write  = sub_592A40/A80/AC0/B40 and sub_592A20/A60/AA0/B20
u64/raw8          = sub_592B00/B80 and sub_592AE0/B60
raw                = sub_592500 / sub_592580
raw16 (0x10)       = sub_592C40 / sub_592C20
ASCII-Z string     = sub_592730 / sub_5926F0
```

`sub_592AE0` writes 8 bytes even though Hex-Rays shows split scalar parameters; `sub_592B20` writes 4 bytes even where the prototype looks like `char`.

## 4. Login control family

The Client registration table directly binds:

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

Registration names are authoritative only for opcode naming; body schema still comes from actual reader/writer paths.

## 5. 693 — GL_TCPCONNSUCC

Dispatcher: `693 -> sub_57CAE0()`.

Handler consumes no payload fields and immediately invokes `sub_555C60()`, which sends packet 143.

```text
693 body consumed by Client = 0 bytes
role = connection-success/control transition
```

Do not invent a payload without another producer/receiver proof.

## 6. 694 — GL_ACCOUNTCONNSUCC

`CLobbyLogin::sub_43E500()` reads exactly one u16 with `sub_592A00`.

```text
694
+0x00 u16 negotiated_packet_limit
```

If the value is below `0x2580` (9600), the global packet limit is reduced accordingly. This directly connects 694 to the Packet receive/transformation ceiling.

Then the Client proceeds to 682.

## 7. 682 — GL_LOGIN_REQ

`CLobbyLogin::sub_43DF00()` constructs the packet after validating non-empty credential fields and allowed USERID characters.

Exact wire order:

```text
+0x00 ASCII-Z USERID
+.... ASCII-Z PASSWORD
+.... raw8 datarevision-derived composite
+.... u8 hardware-ID source/state
+.... raw24 hardware-ID slot
```

### 7.1 USERID

Source is the Login UI state at `(this + 132)`. Writer: `sub_5926F0`, including the NUL terminator.

### 7.2 PASSWORD

Source is the Login UI state at `(this + 260)`. Same ASCII-Z representation.

### 7.3 raw8 revision verification value

Client obtains the revision state from `(this + 396)` and emits 8 bytes through `sub_592AE0`.

Because the low DWORD is zero before the constant XOR operations:

```text
low32  = 0x0000000E
high32 = datarevision ^ 0xB1A9D7C7
```

Final extracted Client:

```text
datarevision = 811034967 = 0x30576957
high32       = 0x81FEBE90
```

Exact semantic boundary:

```text
build/datarevision-derived protocol verification composite
```

It is not justified to call this a cryptographic hash.

### 7.4 hardware-ID source byte

Initial value is `2`.

Primary path: `sub_9A8790()` attempts to collect an OS/device identifier.

Fallback path: `sub_9A86A0()` uses `GetAdaptersInfo()` and copies a six-byte adapter MAC when a six-byte address is available.

Thus this byte is a source/status discriminator, not a payload-length field.

### 7.5 24-byte hardware-ID slot

Exactly 24 raw bytes are written. The Client uses the collected identifier and zero padding or adapter-derived data depending on source path.

## 8. 681 — GL_LOGIN_ACK

The first field is definitely a u32:

```text
+0x00 u32 status
```

`status == 1` enters the success bootstrap; all other status paths are failure/error/control branches and do not consume the success schema.

### 8.1 Success prefix

```text
+0x00 u32 status = 1
+0x04 u32 v144 → dword_EE8970
+0x08 u32 n100 → global n100
+0x0C u32 v140 → NetCafe count/enable discriminator
[if v140 > 0]
    u32 v120
    u32 v141
    u8  v135
    -> NetCafe object/state
+.... u16 server_record_count
```

`n100` is later reused by 143.

`v140/v120/v141/v135` are tied directly to `sNetCafeInfo` and the NetCafe UI/filter state. `v135` is also copied to `byte_231807D` as a boolean.

### 8.2 Login server-record wire schema

For each server record:

```text
u16 src
ASCII-Z field[1]      // 50-byte local buffer
ASCII-Z field[2]      // 50-byte local buffer
ASCII-Z field[3]      // 16-byte local buffer
u16 field[4]
u8  field[5]
u16 field[6]
repeat 3:
    u16 sub_present_or_id
    if > 0:
        u8  sub_type
        ASCII-Z sub_string (50-byte local buffer)
        u16 sub_value
        u8  sub_flag
        if sub_type == 3:
            u8 sub_flag2
```

The Client copies a contiguous 132-byte record beginning at the `src` local into its server-record collection. The stack layout proves the exact 132-byte storage footprint:

```text
+000 u16
+002 50 bytes
+052 50 bytes
+102 16 bytes
+118 4 bytes
+122 2 bytes
+124 2 bytes
+126 2 bytes
+128 1 byte
+129 1 byte
+130 1 byte
+131 5 bytes
```

The important distinction is that some of these storage fields are larger than the actual value read on that path because the contiguous record object preserves a fixed 132-byte layout.

### 8.3 Server-record fields directly closed by downstream consumers

```text
record +0   = server/source/key identifier used for sorting/lookup
record +52  = server name string; Client feeds it to SERVERNAME UI
record +122 = current user count
record +124 = maximum user count
record +128 = server-kind/type code used to derive KINDOFSERVER resource
record +129 = server state-category discriminator
record +130 = state subcode when +129 == 3
```

`+122/+124` are rendered as `%d/%d` in `USERS`.

For `+129 == 3`, `+130` is mapped to the UI state resource through:

```text
2 -> state 3
3 -> state 4
4 -> state 7
5 -> state 5
1/6 -> state 6
0 -> state 8
```

If TournamentManager override `sub_417E30()[492]` is active, the Client replaces record +130 with `sub_417E30()[12]` before mapping it.

### 8.4 Fields not yet semantically unique

The remaining fixed record fields are wire-known but not uniquely named by their final Client consumers:

```text
+2..+51
+102..+117
+118..+121
+126..+127
+131..+135
```

They remain raw fields until caller/consumer or resource evidence distinguishes them.

### 8.5 Success trailer

After the server-record array, Client reads:

```text
u32 v142
u32 v137
```

They are written into the UI argument structure used by `sub_7092C0`, but no unique public label is proven yet. Do not guess their business names.

## 9. 197 / 198 — MyInfo bootstrap

### 197 GL_MYINFO_REQ

Exact body:

```text
0 bytes
```

### 198 GL_MYINFO_ACK

Leading status:

```text
+0x00 u8 status
```

Success then delegates large portions of the packet to reusable ClientData/player decoders (`sub_523BF0`, `sub_524010`, `sub_524660`, `sub_527550`, `sub_527D00`) and hydrates profile/avatar state. Later fields include explicit `u16`, `u32`, a u8 count and a bounded list of u8 entries.

The Client resource manifest independently contains `character`, `item`, `ui`, `ui_temp`, `data.pat`, `convars.pat`, `pmClient.dat`, and `datarevision.txt`, so this is a genuine resource-backed bootstrap rather than a simple status ACK.

The nested decoder schemas are still being decomposed individually; no guessed labels are inserted here.

## 10. 141 / 142 — secondary gameplay connection

### 141 PM_CONNECT_REQ

```text
payload = 0 bytes
```

### 142 PM_CONNECT_ACK

Exact reader order:

```text
ASCII-Z host/address string
u32 endpoint/port-like raw value
u8  connection-mode/state
u32 packed date/time context
```

The second value is physically read as u32, despite the Hex-Rays local being typed as `u_short`. Only its low 16 bits are consumed by the actual endpoint setup.

The final u32 is passed to `sub_534F20()`. The exact bit packing is:

```text
year   = bits 24..31 + 2000
field1 = bits 19..23
field3 = bits 13..18
field4 = bits 7..12
field5 = bits 0..6
```

This exactly corresponds to a compact year/month/day/hour/minute style timestamp container used by the Client.

## 11. 143 / 144 — UDP bootstrap

### 143 PM_UDPSTART_REQ

Exact body:

```text
ASCII-Z global connection/config string
u32 ::n100
u8  literal 1
u32 dword_231800C
```

`::n100` is the value received from 681.

`dword_231800C` is used extensively by NetCafe-specific UI branches, so it is a NetCafe activity/feature selector at the Client level, while the exact server-public field name remains OPEN.

### 144 PM_UDPSTART_ACK

Exact parsed prefix:

```text
u8  n108
u8  v65
u32 dword_1D0D23C
ASCII-Z string (40-byte local buffer)
u32 v72
u32 v68
raw4 v70
f32 v75
u32 v69 → dword_F2A684
u8  v66
```

When `v66 != 0`, an additional block follows:

```text
u8 v73
u8 v63
u8 v64
u8 v67
8 × u32 v62[]
```

`sub_A1C800` stores the four bytes into the NetCafe/configuration object. `sub_A1C910` normalizes the eight u32 values into internal pointer/offset-like values. Do not call them action IDs without stronger evidence.

`v73` is later used as `value * 0.01`, so it is a ratio/percentage-like scalar.

`dword_F2A684` is reused as a u32 in many later packet senders, proving it is significant shared game/session state; its final public name is still OPEN.

Status branches are explicitly implemented:

```text
0      failure
1      success mode A
2      success mode B
3..10  connection/bootstrap failure messages
101..108 additional failure messages
```

UDP endpoint setup is independently confirmed by `inet_addr(host)` + `htons(low16(port))` on an `AF_INET/SOCK_DGRAM/IPPROTO_UDP` socket.

## 12. Tutorial packets adjacent to login

```text
685 GL_TUTORIALINDEX_REQ       = 0 bytes
686 GL_TUTORIALINDEX_ACK       = u32
687 GL_TUTORIAL_START           = 0 bytes
688 GL_TUTORIAL_END             = 0 bytes
689 GL_TUTORIAL_INDEX_SET_REQ   = u32
```

686 stores the received u32 as the Client tutorial index state. 689 is another explicit example where the decompiler prototype is narrower than the actual wire writer.

## 13. Evidence boundary

At this point the following are genuinely closed at wire level:

```text
TCP framing and stream reassembly
header +0/+2/+4/+6 widths
integrity/XOR transform
all primitive readers/writers
693
694
682 complete field order/width
681 status + success parse tree + 132-byte server record layout
197
198 leading status + nested decoder structure
141
142 width/order + timestamp packing + effective port
143 exact body
144 exact leading/optional body + status branches
685/686/687/688/689
```

The remaining uncertainty is semantic naming of a limited number of fields that the Client consumes only through generic/configuration structures. Those should remain typed-but-opaque rather than being replaced by invented `serverId/channelId/region/etc.` names.
