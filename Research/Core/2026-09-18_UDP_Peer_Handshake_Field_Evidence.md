# 2026-09-18 UDP Peer Handshake／Endpoint Field Evidence

> Target: 日本版 PaperMan 2016 年服務終了時の最終 Client。
> 本文件專門保存 UDP peer/bootstrap maintenance family 的 byte-level parser/serializer 與 state lifecycle；不把它與 `Y_UDP_S_MOVE_INF` gameplay snapshot 混為一談。

## 1. Socket / endpoint object boundary

`CUDPSocket` constructor initializes socket handle invalid and default port value `27000`.

`sub_596D60()` creates:

```text
socket(AF_INET, SOCK_DGRAM, 0)
```

`sub_596DA0(this, ip, port)`：

```text
socket local bind address = 0.0.0.0 : this+56
configured destination endpoint = ip : port
```

`sub_596E60(this, ip, port)` writes the configured endpoint into a separate four-word `sockaddr`-like area.

Send functions prove two distinct destination paths:

```text
sub_596EB0 → socket sendto(..., this+24)
sub_596F00 → socket sendto(..., this+40)
sub_5958D0 → sendto(..., caller-supplied sockaddr)
```

`sub_595BD0()` returns the configured endpoint four-word representation; `sub_595A10()` uses that endpoint for UDP send.

## 2. Peer endpoint tables

Per player slot there are two distinct endpoint/state areas:

```text
unk_F6D584 + 240780*slot
    = endpoint/address blob learned from peer-distribution path
    size = 16 bytes

unk_F6D594 + 240780*slot
    = local/source endpoint sockaddr captured for peer response path
    size = 16 bytes
```

Identity lookup uses:

```text
dword_F6DCF4[60195*slot]
```

for 16 slots.

The code therefore maintains:

```text
Player/Actor Identity
    ↓ lookup
Player Slot
    ↓
Peer Endpoint State
```

not `identity == slot` as a universal rule.

## 3. Opcode 4 → 5: bulk endpoint distribution

### Inbound opcode 4: `sub_593AB0`

First byte:

```text
u8 count
```

Each record:

```text
u8 identity
16-byte sockaddr/endpoint blob
```

For every record, Client scans all 16 player identities and stores the 16-byte blob into the matching slot's `unk_F6D584` area; `byte_F6D5B0[slot] = 1` marks endpoint availability.

Then it constructs opcode 5:

```text
u8  local identity
u32 timing-like value = global `n0x3E8_3`
```

and sends it three times to every non-local active slot whose `byte_F6D5B0` is set.

It also records `dword_F6D5A8[slot] = timeGetTime()` after sending.

State byte:

```text
*this = 4
```

### Semantic boundary

```text
4 = bulk peer endpoint distribution/update
5 = response/ack carrying local identity + timing-like value
```

The name `ACK` is an architectural description, not a formal protocol symbol; exact public names for opcodes 4/5 are not present in the examined protocol registration strings.

## 4. Opcode 5 → 6: targeted peer handshake

### Inbound opcode 5: `sub_593E60`

Reads exactly:

```text
u8 identity
u32 value
```

The received `u32` is parsed but is not subsequently consumed by the visible body.

Identity is mapped to a slot. If `byte_F6D5A4[slot]` is already nonzero, it is incremented and no response packet is constructed.

First-time path:

```text
byte_F6D5A4[slot] = 1
byte_F6D5A5[slot] = 1
unk_F6D594[slot] = current local/source sockaddr (16 bytes)
```

Then builds opcode 6:

```text
u8  local identity
u32 global `n0x3E8_3`
```

and sends it three times directly to the stored peer/source endpoint.

### Semantic boundary

The exact meaning of the 4-byte field remains `[OPEN]`, but the important fact is:

```text
received value != necessary input to response construction
response value = local/global timing-like state
```

Therefore it should not be named `nonce`, `timestamp`, or `ping` without more evidence.

## 5. Opcode 6: final state capture for this branch

`sub_5940E0()` reads:

```text
u8 identity
u32 value
```

maps identity to slot, and if `byte_F6D5A5[slot] == 0`:

```text
byte_F6D5A4[slot] = 1
byte_F6D5A5[slot] = 1
unk_F6D594[slot] = local/source sockaddr
```

No outbound packet is built in the shown handler.

The parsed `u32 value` is not consumed by the visible body.

Thus the client-side state effect is more certain than the value semantic:

```text
6
  → establish peer-source endpoint state
  → mark A4/A5 handshake state
```

## 6. Opcode 10 → 13: targeted endpoint update

### Inbound opcode 10: `sub_594460`

Reads:

```text
u8 identity
16-byte endpoint blob
```

Maps identity to one of 16 slots.

On first endpoint registration for the slot:

```text
unk_F6D584[slot] = 16-byte endpoint blob
byte_F6D5B0[slot] = 1
```

Then builds opcode 13:

```text
u8  local identity
u32 `n0x3E8_3`
```

and sends it three times directly to the stored endpoint.

The handler then sets its local handshake state to `2`.

## 7. Opcode 12 → 13: bulk endpoint update

### Inbound opcode 12: `sub_5946C0`

Reads:

```text
u8 count
count × (
    u8 identity
    16-byte endpoint blob
)
```

For each valid identity:

```text
unk_F6D584[slot] = endpoint blob
byte_F6D5B0[slot] = 1
```

It then constructs opcode 13:

```text
u8  local identity
u32 `n0x3E8_3`
```

and sends it three times to each non-local active slot with known endpoint state.

It updates `dword_F6D5A8[slot]` after each send and sets local handshake state to `4`.

Therefore 12 is the bulk counterpart of the 10 targeted path.

## 8. Opcode 13 → 14: second-stage response

### Inbound opcode 13: `sub_594A10`

Reads:

```text
u8 identity
u32 value
```

On first arrival for a slot:

```text
byte_F6D5A4[slot] = 1
byte_F6D5A5[slot] = 1
unk_F6D594[slot] = current local/source sockaddr
```

Then builds opcode 14:

```text
u8  local identity
u32 `n0x3E8_3`
```

and sends it three times to that peer endpoint.

On repeated arrivals the handler increments `byte_F6D5A4[slot]` instead of constructing a new packet.

The incoming `u32 value` is parsed but unused in the visible handler.

## 9. Opcode 14: terminal receive-side state update

`sub_594CA0()` reads:

```text
u8 identity
u32 value
```

If `byte_F6D5A5[slot] == 0`, it establishes:

```text
byte_F6D5A4[slot] = 1
byte_F6D5A5[slot] = 1
unk_F6D594[slot] = local/source sockaddr
```

and sets local handshake state to `4`.

No outbound packet is built in the shown function.

Again, the `u32` is parsed but not used by the visible state transition.

## 10. Timing-like field `n0x3E8_3`

`sub_593A60()` handles inbound UDP opcode 2 and initializes a global transition value with:

```text
n0x3E8_3 = timeGetTime() - dword_F2563C
```

`sub_5946C0()` explicitly refreshes:

```text
n0x3E8_3 = timeGetTime() - dword_F2563C
```

before emitting opcode 13.

Opcode 1 / 9 send paths also update related timing state from `dword_F2563C`.

Therefore the repeated 4-byte field transmitted in opcodes 5/6/13/14 is currently best described as:

```text
elapsed/timing-like handshake value
```

It is **not yet safe** to call it RTT, timestamp, nonce, or sequence number.

## 11. Peer readiness / timeout state

`sub_5941D0()`:

```text
For each unoccupied slot:
    if byte_F6D5A5[slot] == 0
       and timeGetTime() - dword_F6D5A8[slot] > 3000 ms
    → return -1
```

`sub_594DA0()` performs the corresponding check with:

```text
5000 ms
```

and both also consider whether all required slot states have reached A5-ready.

This establishes at least two distinct timeout phases:

```text
~3 s = one readiness/peer-address phase
~5 s = later peer state phase
```

Exact state machine labels remain `[OPEN]`.

## 12. Local transport configuration vs learned peer address

The code maintains two conceptually different endpoint sources:

```text
Configured server/local UDP destination
    = CUDPSocket +40 area
    = used by sub_595A10 / sub_596F00

Learned peer endpoint
    = per-player unk_F6D584 or unk_F6D594
    = used by sub_595980 / sendto(caller sockaddr)
```

This is direct evidence that the game can communicate both with a configured UDP endpoint and with per-player peer addresses.

It is not sufficient to infer that all gameplay UDP is peer-to-peer; endpoint addressing is only one transport capability. `Y_UDP_S_MOVE_INF` remains a separate message family.

## 13. Confirmed field schemas

| Opcode | Direction | Payload |
|---:|---|---|
| 4 | inbound | `u8 count` + `count × (u8 identity + 16-byte endpoint)` |
| 5 | inbound | `u8 identity + u32 timing-like value` |
| 6 | inbound | `u8 identity + u32 timing-like value` |
| 10 | inbound | `u8 identity + 16-byte endpoint` |
| 12 | inbound | `u8 count` + `count × (u8 identity + 16-byte endpoint)` |
| 13 | inbound | `u8 identity + u32 timing-like value` |
| 14 | inbound | `u8 identity + u32 timing-like value` |

The outbound schemas constructed by the same functions are:

```text
5  = u8 local identity + u32 timing-like value
6  = u8 local identity + u32 timing-like value
13 = u8 local identity + u32 timing-like value
14 = u8 local identity + u32 timing-like value
```

## 14. Current state machine model

```text
Configured UDP socket
        ↓
UDP startup / timer state
        ↓
peer endpoint distribution
   4 / 10 / 12
        ↓
known peer endpoint (F6D5B0)
        ↓
identity + timing response
   5 / 13
        ↓
local/source sockaddr capture (F6D594)
        ↓
handshake state A4/A5
        ↓
6 / 14 final response/update
        ↓
peer readiness / timeout checks
```

The exact protocol intention is still `[OPEN]`, but the byte schemas and endpoint/state transitions above are direct Client-side evidence.
