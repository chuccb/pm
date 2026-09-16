# PaperMan Kick / PM_KICKUSER — Master/Room Protocol Separation

> Research snapshot: **2026-09-16**
>
> This document records an important architectural distinction discovered while tracing the packet table: `PM_KICKUSER_REQ/ACK` (396/397) is a separate master/room protocol and must not be merged with the in-game voting lifecycle packets 718–723.

## 1. Packet registration

The client packet-registration table explicitly contains:

```text
394 MASTER_ROOMINFO_REQ
395 MASTER_ROOMINFO_ACK
396 PM_KICKUSER_REQ
397 PM_KICKUSER_ACK
398 MASTER_SVRCLASS_REQ
399 MASTER_SVRCLASS_ACK
```

So 396/397 sit in the `MASTER_*` protocol family, adjacent to room/master-management operations.

## 2. 397 is actually dispatched by the master/room packet handler

The generic master-side receive dispatcher contains:

```c
switch (sub_591EE0(a4))
{
    ...
    case 395u:
        sub_579160(a4);
        break;
    case 397u:
        sub_58E410(a1, a4);
        break;
    case 403u:
        sub_579500(a4);
        break;
}
```

Therefore `397` is not handled by `IVotingNetwork::sub_9BF430`; it has its own master/room handler `sub_58E410`.

## 3. 397 body is proven to begin with one byte

`sub_58E410` performs:

```c
char status;
sub_592940(packet, &status);
sub_58AF90(this);
```

The handler then switches on that one-byte value:

```c
case 0:
    goto default;

case 1:
    message resource 0xF9;
    sub_9A7DE0(..., 68, 1);
    return;

case 2:
    message resource 0xA5;
    sub_9A7DE0(..., 69, 1);
    break;

default:
    message resource 0x38;
    sub_9A7DE0(..., 67, 1);
    break;
```

Thus the currently proven wire shape is:

```text
397 PM_KICKUSER_ACK
    +0x00 u8 status
    payload size observed by parser: 1 byte
```

At least the values `0`, `1`, and `2` are handled distinctly (`0` falls through the default path), but the exact semantic names of those status values are still OPEN.

Do not invent names such as `SUCCESS`, `NOT_FOUND`, or `DENIED` merely from control flow.

## 4. 396 request sender is not present as a direct packet constructor in the current PaperMan.exe.c export

A repository-wide search of the decompiled client did **not** find a direct constructor call of the form:

```c
Packet::possible_ctor_or_dtor_0(..., 396);
```

and the literal protocol name `PM_KICKUSER_REQ` appears only in the packet registration table.

This means there is currently insufficient evidence to state the 396 body layout from this client export alone.

Possible architectural explanations include:

- the request is generated through an indirect/virtual path whose numeric packet constructor is not recovered by the current Hex-Rays export;
- the corresponding request path lives in a separate executable/server component rather than this gameplay client;
- the request is part of a room/master operation whose trigger code is outside the voting UI cluster.

These are hypotheses, not established facts.

## 5. Separation from the in-game Kick Vote protocol

The actual in-game voting lifecycle is separately dispatched by:

```text
718  client -> server  start vote request
719  server -> client  start/request status
720  server -> client  voting session state
721  client -> server  individual vote
722  server -> client  per-voter vote result/broadcast
723  server -> client  end/result notification
```

Those packets are parsed by `IVotingNetwork::sub_9BF430`, where 719/720/722/723 are explicit switch cases.

Therefore a compatible server should model two distinct concepts:

```text
GameRule Voting
    718–723

Master/Room KickUser operation
    396–397
```

They may participate in the same user-facing kick feature at different layers, but the client binary does not justify treating their packet bodies as one protocol.

## 6. Why this distinction matters

The Japanese Wiki describes a player-vote-based in-game kick mechanism and also distinguishes the waiting-room kick performed by the room master.

The binary architecture is consistent with that distinction:

```text
in-game voting UI / game-rule state machine
        -> 718–723

master / room management layer
        -> PM_KICKUSER_REQ/ACK 396/397
```

The exact cross-layer handoff — for example, whether a successful vote ultimately causes a 396 request or whether the game server performs the kick directly — is not yet proven from the available client C export.

## 7. Evidence anchors

### Packet registration

`PaperMan.exe.c` around lines 675991–676018:

```text
PM_KICKUSER_REQ = 396
PM_KICKUSER_ACK = 397
```

### Master/room dispatcher

`PaperMan.exe.c` around lines 177329–177349:

```text
case 397u:
    sub_58E410(a1, a4);
```

### 397 parser/handler

`PaperMan.exe.c` around lines 178307–178344:

```text
sub_592940(packet, &status)
switch(status)
```

### Remaining gaps

- exact 396 request wire body;
- exact 397 status enum semantics;
- exact linkage, if any, between successful 718–723 voting and 396/397.
