# PaperMan 2016 JP — `GL_LOGIN_ACK (681)` Server-Record Field Schema

> 研究日期：2026-09-17
> Target：日本版 2016 Final Client
> Primary evidence：`PaperMan.exe.c` `CLobbyLogin::sub_43E500` + `sub_58E690/sub_58F120/sub_5902A0` + server-list UI consumers
> Rule：wire layout 與 Client storage/view layout 必須分開；固定 132-byte stride 是 Client storage，不是 wire record size。

## 1. Top-level 681 success prefix

```text
u32 status
```

Only `status == 1` enters the successful bootstrap parser.

Then:

```text
u32 v144
u32 n100
u32 v140
if v140 > 0:
    u32 v120
    u32 v141
    u8  v135
else:
    no extra fields
```

The Client stores:

```text
v144 -> dword_EE8970
n100 -> global n100
v135 != 0 -> byte_231807D
```

`n100` is reused by `143 PM_UDPSTART_REQ`, proving an inter-packet dependency.

## 2. Server-list wire record

After the top-level prefix, Client reads `u16 record_count`.

For every record:

```text
u16 src
ASCII-Z string v122
ASCII-Z string v124
u16 v125
u8  v129
u16 v128

repeat 3:
    u16 v127
    if v127 > 0:
        u8 n3
        ASCII-Z string v123
        u16 v126
        u8 v132
        if n3 == 3:
            u8 v131
        sub_58E690(serverListStorage, src)
```

The exact public business label of every wire field is not inferred from variable order. The following are direct structural facts:

- `src` is passed into `sub_58E690` and becomes the key/identity used by the Client server-record collection.
- Strings are NUL-terminated and therefore variable-length on the wire.
- The three nested entries are conditional on their preceding `u16 v127` being positive.
- The final `u8` exists only for nested `n3 == 3`.

## 3. Client raw storage record is fixed 132 bytes

`sub_58E890()` returns records with a stride of exactly 132 bytes.

`sub_58F120()` / `sub_5902A0()` copy the source structure with `0x84` bytes (=132).

This is a **Client-side canonical storage record**, not a fixed network record.

Therefore a compatible Server must serialize the variable-length wire strings and conditional nested fields in their original order rather than writing a 132-byte fixed record.

## 4. Direct UI/state consumers of raw 132-byte storage

The server-list UI accesses these storage offsets:

```text
+52   -> copied into SERVERNAME-related display/view input
+61   -> aggregate/value used by server-list processing
+62   -> aggregate/value used by server-list processing
+63   -> FACE index source; a derived value feeds FACE_%d icon lookup
+122  -> USERS current
+124  -> USERS maximum
+128  -> KINDOFSERVER lookup/index
+129  -> server state category
+130  -> server state subtype when +129 == 3
```

The visible user count is formatted exactly as:

```text
"%d/%d", record+122, record+124
```

When `record+129 == 3`, `record+130` is mapped:

```text
2 -> 3
3 -> 4
4 -> 7
5 -> 5
1 or 6 -> 6
0 -> 8
```

The result is used by later localized server-state presentation.

`record+128` is converted through a `+905` resource-id calculation before localization, so it is a server-kind/type index rather than a user count.

## 5. 80-byte `CLobbyServerData` view is a separate layer

`CLobbyServerData` uses a fixed 80-byte internal representation.

Relevant functions:

```text
sub_4193F0  -> +80-byte iterator stride
sub_419490  -> converts 80-byte records into 20 DWORDs
sub_419760  -> copies a CLobbyServerData record
sub_4198B0/419900 -> construct/copy view records
```

Therefore:

```text
681 wire record
    ↓
132-byte raw Client storage
    ↓
80-byte CLobbyServerData view
    ↓
Server-list UI
```

Do not use the 80-byte view offsets as direct wire offsets.

## 6. Evidence boundary

### Closed

```text
681 status width = u32
record count width = u16
server-record wire field order = closed
all wire scalar widths = closed
all wire strings = NUL-terminated
three nested subrecords = conditional and structurally closed
nested n3 == 3 extra byte = closed
raw storage stride = 132 bytes
raw +122/+124 = current/max users
raw +128 = server-kind/type lookup index
raw +129/+130 = state category/subcategory path
raw +63 = face/icon source
```

### Still semantic-opaque

```text
wire v124 string exact public label
wire v125/v129/v128 exact public labels
wire v127/n3/v126/v132/v131 exact public labels
raw +0 exact display/business meaning
raw +61/+62 exact public labels
some raw fields not surfaced by the final server-list UI
```

These remain raw until a unique caller/resource/UI consumer proves a better name.
