# PaperMan 2016 JP — TCP 101–192 Room/Channel/GameRule Field Evidence

> Target: PaperMan Japan final 2016 client
> Evidence: IDA `PaperMan.exe.c` exact dispatcher + embedded opcode-name table + parser/consumer data flow
> Rule: raw widths are fixed from serializer/parser helper implementations; semantic names are only promoted when downstream use is direct.

## 1. Independent packet-name source

`sub_58D940()` contains an explicit client opcode-name table. For this range it directly labels:

```text
101 GT_PING_REQ
102 GT_PING_ACK
105 GL_USERLIST_REQ
106 GL_USERLIST_ACK
107 GL_GAMEROOMINFO_REQ
108 GL_GAMEROOMINFO_ACK
110 GL_ROOMINFOCHANGE_ACK
111 GL_MAKEROOM_REQ
112 GL_MAKEROOM_ACK
113 GL_ENTERROOM_REQ
114 GL_ENTERROOM_ACK
116 GL_ADDUSER_ACK
118 GL_DELETEUSER_ACK
119 GL_CHATTING_REQ
120 GL_CHATTING_ACK
121 GR_MAPCHANGE_REQ
122 GR_MAPCHANGE_ACK
123 GR_LEAVE_REQ
124 GR_LEAVE_ACK
125 GR_CHATTING_REQ
126 GR_CHATTING_ACK
127 GR_READY_REQ
128 GR_READY_ACK
129 GR_START_REQ
130 GR_START_ACK
131 GR_FORCEOUT_REQ
132 GR_FORCEOUT_ACK
133 GR_END_REQ
134 GR_END_ACK
135 GR_CHANGESLOT_REQ
136 GR_CHANGESLOT_ACK
139 GG_EXITGAME_REQ
140 GG_EXITGAME_ACK
141 PM_CONNECT_REQ
142 PM_CONNECT_ACK
143 PM_UDPSTART_REQ
144 PM_UDPSTART_ACK
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
165 Y_TCP_INF_REQ
166 Y_TCP_INF_ACK
167 GR_CHANGEUSER_REQ
168 GR_CHANGEUSER_ACK
169 GR_RULECHANGE_REQ
170 GR_RULECHANGE_ACK
171 GR_WINCHANGE_REQ
172 GR_WINCHANGE_ACK
175 GR_INTRUSIONCHANGE_REQ
176 GR_INTRUSIONCHANGE_ACK
183 GL_ENDLOADING_REQ
184 GR_ENDLOADING_ACK
187 GG_STARTGAME_REQ
188 GG_STARTGAME_ACK
190 GR_CHANGEMASTER_ACK
191 GR_CALLUSER_REQ
192 GR_CALLUSER_ACK
```

The name table is not itself payload evidence; each name must still be paired with the actual parser/serializer.

## 2. Packet helper widths — verified from implementations

```text
sub_592900  → read 1 byte
sub_592940  → read 1 byte
sub_592980  → read 1 byte
sub_5929C0  → read 2 bytes
sub_592A00  → read 2 bytes
sub_592A40  → read 4 bytes
sub_592AC0  → read 4 bytes
sub_592B20  → write/copy 4 bytes
sub_592B40  → read/copy 4 bytes
sub_592730  → string-like reader
```

Duplicate 1/2/4-byte helpers are distinct functions but have the same copy width; Hex-Rays local variable type must not override these widths.

## 3. 106 — GL_USERLIST_ACK

Core parser `sub_56A250()`:

```text
u16 value_0 = v23
if value_0 != 0:
    u8 flags = v25
    u8 count = i_1
    repeat count:
        u32 user_or_object_id
        string name/text
        u32 value
        ... local list/object update
```

For each record with positive id, the Client resolves an internal list/object, stores the record id and string, applies the u32 value, then updates an `EMBLEM` texture using another u32 value. The parser therefore is a repeated user-list/object bootstrap, not a single count packet.

Some fields depend on the current gameplay/channel variant and are not yet safely public-named. Keep the following raw until the list object structure is recovered:

```text
header_u16
flags_u8
record_count_u8
record.id_u32
record.text_string
record.value0_u32
record.value1_u32
```

## 4. 108 — GL_GAMEROOMINFO_ACK

`sub_568CE0()` first reads:

```text
u8 mode_variant = n3
```

If `mode_variant == 3`, it delegates to `sub_580A80()` with the remaining payload.
Otherwise it reads:

```text
u8 record_count
repeat:
    u8 player_id
    u8 record_flag/state
    string-like field
    u8 state/control
    u8 / flag
    u16 × 3
    u8 flag
    u8 field
    string/raw block around 64–100 bytes
    u8 state
    u8 state
    u8 flag
    u8 flag
```

For each valid player id `< 0xD2`, the Client resolves its local room-player object, clears/rebuilds its appearance state, and calls `sub_53F830()` with the parsed values. It also loads `EMBLEM` textures from two u32 values.

If `mode_variant == 2`, there is an additional pair of room/global u32 + string + u8 blocks followed by `sub_5402A0()` on the player object.

This packet is therefore a **room-information/player-list state packet**, with mode-dependent subrecords. Exact public field names remain unresolved until `sub_53F830` and the Room UI/resource schema are fully mapped.

## 5. 110 — GL_ROOMINFOCHANGE_ACK

`sub_569240()` is a large room-state mutation parser. Its first byte selects a sub-event class:

```text
u8 record_type
```

Observed subtypes include at least:

```text
1 → player object identity/state update + conditional appearance blocks
2 → player object identity/state update + conditional appearance blocks
3 → player state reset/clear
4 → player state update with 1 control byte
5 → player state update with 1 control byte
6 → player state update with 1 byte-sized state
9 → player state update + controller subobject field
10 → player state update + player +185 byte
12 → two bits packed into a byte; dispatched to controller callbacks
14 → player state update + player +109 byte
```

For subtype 1/2, player id is followed by multiple state bytes, three 16-bit values, additional flags, then optional identity/EMBLEM data. The same internal `sub_53F830()` / `sub_5402A0()` machinery used by 108 is reused.

Important architectural conclusion:

```text
108 GL_GAMEROOMINFO_ACK
110 GL_ROOMINFOCHANGE_ACK

share the same room-player object representation/update machinery,
but 108 is bulk room snapshot while 110 is change-event oriented.
```

The exact field semantics are intentionally not guessed from variable names.

## 6. 112 — GL_MAKEROOM_ACK

`sub_56A7B0()` begins by resetting all 16 local player records, then parses:

```text
u8 status_or_room_flag
u8 room/master player id
u16 value_0
u32 value_1
u8 room/state flag
u8 room string/control flag
```

If the first status permits room initialization, it then parses the local room participant record and a pair of u32 + string blocks. It rebuilds the local player object, resets room/game state, writes the current server-selected player/channel id, and stores the parsed `value_1` into `dword_F2A65C`.

Because this handler performs full local room/game state reset and then reconstructs the room owner/player object, 112 is a **room creation ACK / room-entry state bootstrap**, not a tiny boolean response.

## 7. 114 — GL_ENTERROOM_ACK

`sub_56B360()` is a large multi-player room-enter/bootstrap parser. The initial state contains:

```text
u8 control/status
u32 room/server value
u8 flag
u32 room value
u32 room value
u16 × 3
u16[] / u32[] player/member state arrays
u8 player/state fields
string/resource/appearance blocks
```

It resolves player slots through `dword_F6DCF4[60195 * slot]`, fills the per-player object (`byte_F33120` stride 240780), loads EMBLEM/appearance resources, and applies weapon/character/controller state through `sub_5404B0`, `sub_540280`, `sub_53FBB0`, `sub_53FB10` and related helpers.

Because the packet contains many player-record fields and mode-specific blocks, it should be treated as a **full room-enter snapshot**, not a simple success code.

The exact wire schema is still under active recovery because the player object layout and string/resource tables are larger than the handler alone.

## 8. 116 — GL_ADDUSER_ACK

`sub_56A4D0()`:

```text
u32 user_id_or_room_object
string user/display name
```

Then it calls `sub_588560(id, text, 0)`.

This is a compact add-user notification; the exact namespace of the u32 remains unresolved (likely a user/member identifier, but the Client data path should be used as the authority).

## 9. 118 — GL_DELETEUSER_ACK

`sub_56A550()` reads:

```text
string user/display name
```

and passes it to `sub_5886C0()`.

The packet therefore identifies the deletion target through a string in the currently observed client path. No u32/u16 follows in this parser.

## 10. 120 — GL_CHATTING_ACK

`sub_56E300()` reads:

```text
u32 value
string source/chat payload
```

It then converts the string to its internal representation and displays it only when channel/room identity checks pass. Exact meaning of the leading u32 is still unresolved.

## 11. 122 — GR_MAPCHANGE_ACK

`sub_56E530()` reads exactly:

```text
u8 mapchange_value
```

and calls `sub_42FC50(dword_EA10D0, mapchange_value)`.

This is therefore not yet safely reducible to `mapId`; the one-byte value is used as a map-change state/index by the Room/Game object.

## 12. 124 — GR_LEAVE_ACK

`sub_5607C0()` begins:

```text
u8 event_type
```

Observed branch `event_type == 1` then reads:

```text
u8 player_id
```

resolves the corresponding 16-slot player entry and executes a leave/removal path, including room/player state cleanup and optional mode-specific handling.

Branch `event_type == 2` performs a global/current-player leave/reset path without the per-player record.

Thus:

```text
124 = leave-state event family
body begins with u8 event_type
```

and branch 1 carries an additional u8 player identity.

## 13. 128 — GR_READY_ACK

`sub_5626D0()`:

```text
u8 state/value
u8 player_id
```

It resolves `player_id` to local slot and writes the first byte into the player room-state byte path. If the player is local, the same byte updates the global ready/game state.

Therefore the two bytes are structurally:

```text
ready_state : u8
player_id   : u8
```

Confidence A for widths and consumer roles; public enum values for the state byte remain raw.

## 14. 130 — GR_START_ACK

`sub_562870()` begins:

```text
u8 event_type
```

For `event_type == 1` the packet contains:

```text
u8 control
u32 match_time_or_duration
u8 player_id
u8 state
u8 state
u16 state
u8 state
u8 state
u16 state
u8 state
u8 state
u8 flag
u8 flag
u8 flag
u8 flag
u8 flag
```

The parser writes these into a player controller/state object and then reads a fixed:

```text
16 × u32
```

array into:

```text
dword_F6DD1C[60195 * i]
```

with a 10-state default applied to `byte_F6D9EC` for empty entries.

The `16 × u32` array is a particularly important cross-subsystem anchor because opcode 165 damage packets later reference `dword_F6DD1C[target]`. Therefore these DWORDs are server-sent per-player gameplay synchronization state, not padding.

## 15. 132 — GR_FORCEOUT_ACK

`sub_562EA0()` reads a compact player/game-state record containing:

```text
u8 event/state
u8 player id
u8 state
u8 state
u8 state
u8 state
u16 state
u8 state
u16 state
u8 state
u8 state
u16 state
u8 state
u8 state
u8 state
```

then applies many of these values directly to the affected player's controller/object. The final part also resets the player's local mode/game state.

Exact public field naming remains unresolved; treat this as a forced-out/state-resynchronization event family.

## 16. 134 — GR_END_ACK

`sub_562EA0()` / adjacent lifecycle logic uses the same per-player room object and resets mode/game state. Exact parser branch is kept raw pending a focused `134` call graph pass.

## 17. 136 — GR_CHANGESLOT_ACK

`sub_56EF40()` parses a compact slot-change state beginning with:

```text
u8 value
u8 player/slot id
u32 value
u16 value
u16 value
u8 value
u8 value
```

then looks up the player and updates room/gameplay state, including the active channel/player identity. Exact slot/team semantics require the corresponding `GR_CHANGESLOT_REQ (135)` sender and Room UI state to be combined.

## 18. 140 — GG_EXITGAME_ACK

`sub_563430()` begins with:

```text
u8 result/state
u8 player id
```

and then performs per-player state reset, room/game transition and optional mode-specific cleanup. It is a stateful acknowledgement, not an empty ACK.

## 19. 142 — PM_CONNECT_ACK

`sub_5565D0()` exact parser:

```text
string ip_or_host
u16 port
u8 flag
u32 value
```

Then:

```text
sub_534F20(value, word_1D0D1F8)
*sub_417D00() = flag
sub_596E60(&unk_1326908, host, port)
```

So the first three fields have concrete transport semantics:

```text
host/address : string
port         : u16
flag         : u8
```

and the final u32 is a server-provided transport/key/config value consumed by `sub_534F20`; it must remain raw until that function is fully decoded.

## 20. 144 — PM_UDPSTART_ACK

`sub_555D50()` exact prefix:

```text
u8 status/mode = n108
u8 flag = v65
u32 dword_1D0D23C
string block (40-byte local buffer)
u32 value0 = v72
u32 value1 = v68
u32 value2 raw4 = v70
f32/raw32 value3 = v75
u32 value4 = v69 → dword_F2A684
u8 udp_flag = v66
```

When `udp_flag != 0`, it additionally reads:

```text
u8 v73
u8 v63
u8 v64
u8 v67
8 × u32 table values
```

It then configures the networking/game environment and maps several values into global UDP/gameplay state.

This packet is a **UDP startup/configuration ACK**, not a generic boolean acknowledgement. Several fields likely represent transport/config/session parameters, but exact semantics must be recovered from the corresponding `PM_UDPSTART_REQ (143)` and downstream UDP initialization.

## 21. 168/170/172/174/176 — compact GameRule changes

The corresponding handlers are intentionally kept very conservative:

```text
168 GR_CHANGEUSER_ACK → u16? (sub_56F410 reads 2 bytes)
170 GR_RULECHANGE_ACK → u8 state
172 GR_WINCHANGE_ACK → u16/value
174 GR_INTRUSIONCHANGE_ACK → u8 state
176 GR_* ACK → u8 state
```

These exact widths come from the parser helpers, but their complete field semantics need caller-side request comparison and Room UI state. They should not be guessed from opcode names alone.

## 22. 184 — GR_ENDLOADING_ACK

`sub_563B00()` begins:

```text
u8 loading_event_type
```

Branches:

```text
0 → reads u8 player/state then timing callback
1 → gameplay loading complete callback
2 → reads u8 player/state; if not local, invokes player update path
3 → timing callback only
4 → gameplay loading callback
5 → reads u8 state and invokes `sub_406AB0`
```

Therefore 184 is a **multi-branch loading lifecycle event**, not a single completion byte.

## 23. 188 — GG_STARTGAME_ACK

`sub_563D60()`:

```text
u8 start_event_type
```

For branch 1:

```text
u8 count
repeat count:
    u8 player id
```

Each listed player is reset/initialized through `sub_548830()` and `sub_406E50()`.

Branch 2 resets current/global game state and enters the game lifecycle reset path.

Therefore 188 is a multi-branch start-game state notification.

## 24. 190 — GR_CHANGEMASTER_ACK

`sub_56FBF0()` begins with:

```text
u8 new_master_or_player id
```

and updates the room master/player state plus room UI/global state. Full semantic verification requires the `GR_CHANGEMASTER_REQ` sender and room master UI callsites.

## 25. 192 — GR_CALLUSER_ACK

`sub_56FE10()` first reads:

```text
u8 value
```

and branches according to current game state. The value is not yet safely named as a user id or result code; retain raw until the caller/request pair is traced.

## 26. Critical cross-packet relationships

### 130 → 165

```text
GR_START_ACK (130)
    → 16 × u32 F6DD1C[player]
    → opcode 165 damage packet includes F6DD1C[target]
```

This is a direct cross-packet state dependency and should be preserved in Server reconstruction.

### 108 ↔ 110 ↔ 114

```text
108 bulk room snapshot
110 room-info change event
114 room-enter snapshot
    ↓
shared per-player room object
    ↓
identity / emblem / character / weapon / state fields
```

### 142 ↔ 144

```text
142 PM_CONNECT_ACK
    → host + port + transport/config value

144 PM_UDPSTART_ACK
    → UDP startup/config/session parameters
```

These are transport bootstrap packets, not gameplay movement packets.

### 121–136

```text
map / leave / ready / start / forceout / end / slot-change
```

form the core room/game lifecycle family and should be modeled as state transitions rather than isolated request/response structs.

## 27. Remaining proof targets

```text
1. Fully decode 108/110/114 player record shared structure.
2. Fully decode 130 fixed 16×u32 F6DD1C semantic.
3. Pair every 121–136 request with request constructor and ACK mutation.
4. Decode 142/144 transport config end-to-end.
5. Decode 168–176 with request-side values and UI state.
6. Recover exact 134 parser and 136 slot/team semantics.
7. Cross-reference Room/Character/Weapon extracted resources with the per-player bootstrap fields.
```
