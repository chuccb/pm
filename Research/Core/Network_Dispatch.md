# TCP／UDP Packet 分發與 Handler 路徑

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：只保存 TCP／UDP receive architecture、dispatcher、opcode 到 handler 的路由與跨層入口；特定 Packet 的欄位與 gameplay semantics 不在此重複。

## 1. TCP receive architecture

ClientSocket 的 TCP receive loop 先從 stream 累積 bytes，再建立完整 `Packet`，確認 frame 完整後交給：

```text
sub_58B010(..., packet)
```

目前可固定的抽象為：

```text
WSARecv
  ↓
receive buffer
  ↓
frame reconstruction
  ↓
Packet validation / transform
  ↓
sub_58B010
  ↓
opcode dispatch
  ↓
concrete handler
```

TCP stream 不可實作為「一次 `recv` 就是一個封包」。完整 frame framing／integrity 見 [`Foundation_TCP_Handshake_Login_Protocol.md`](Foundation_TCP_Handshake_Login_Protocol.md)。[C]

## 2. `sub_58B010` 共通 receive pre-hook

進入 opcode switch 前，`sub_58B010` 會經過共通的 receive hook，包括：

```text
sub_407360(...)
CGameRule::sub_67CF90(...)
opcode = sub_591EE0(packet)
```

`CGameRule::sub_67CF90` 會檢查 `this +16` 並進一步呼叫其 virtual-style callback，因此不是單純 no-op。[C]

這一層只記錄 routing architecture；callback 的 gameplay meaning 應回到 `GameRule_Lifecycle.md` 或具體事件主文件。

## 3. TCP dispatcher：已閉合的主要 opcode routes

`sub_58B010` 直接包含多個 server-originated opcode case，例如：

```text
160 → sub_58D790
166 → sub_58D820
168 → sub_56F410
170 → sub_56F4F0
172 → sub_56F5D0
174 → sub_56F6B0
176 → sub_56F790
```

同一 dispatcher 也承接 `193–221`、`223–245`、`269` 等其他 TCP handler family；具體 route 應以對應主文件維護。[C]

重要方向性事實：

```text
165 = Y_TCP_INF_REQ
    → 不在這個 incoming switch 中出現

166 = Y_TCP_INF_ACK
    → 在 incoming switch 中出現
```

因此 `165/166` 的 client→server / server→client 方向可由具體 send/receive 路徑閉合；不要只靠 opcode 奇偶性推導 protocol rule。[C]

## 4. `166` 的第二級 dispatch 入口

`166` 的 receive route：

```text
sub_58B010
    ↓ case 166
sub_58D820
    ↓
sub_749B90
```

`sub_749B90` 的第一層可直接觀察欄位為：

```text
u8 outer_actor_like
u8 subtype
```

之後依第二個 byte 進行 subtype dispatch。[C]

本文件刻意不保存 `subtype 1..32` 的完整表格，也不重新命名其 gameplay semantics；完整內容由 [`Gameplay_166_DeepEvidence.md`](Gameplay_166_DeepEvidence.md) 維護。[C]

## 5. UDP receive architecture

UDP 不經 `sub_58B010`。入口是：

```text
CUDPNetworkManager
    ↓
sub_595A60
    ↓
sub_595E80
    ↓
opcode switch
    ↓
UDP handler
```

目前已閉合的主要 UDP routes：

```text
2   → sub_593A60
4   → sub_593AB0
5   → sub_593E60
6   → sub_5940E0
8   → sub_596940
24  → sub_596940
10  → sub_594460
12  → sub_5946C0
13  → sub_594A10
14  → sub_594CA0
15  → sub_593DF0
18  → sub_596300
20  → sub_5968C0
22  → sub_5964E0
26  → unknown_libname_107
28  → sub_594E80
29  → sub_593E20
31  → sub_594EA0
33  → sub_594EC0
34  → sub_594F20
154 → sub_5965D0
158 → sub_596910
```

[C]

UDP opcode 8/24 的 actor-record schema 與 movement/state semantics 統一見 [`UDP_Move_Inf_DeepEvidence.md`](UDP_Move_Inf_DeepEvidence.md)。

## 6. Dispatcher 與 protocol 主文件的責任邊界

```text
TCP frame / transform
    → Foundation_TCP_Handshake_Login_Protocol.md

opcode registration / dispatcher / routing
    → Network_Dispatch.md

193–221 top-level packet fields
    → Channel_Lobby_193_221_Field_Evidence.md

101–192 packet fields
    → Room_Channel_GameRule_101_192_Field_Evidence.md

198 composite order / MyInfo hydration
    → MyInfo_198_ClientData_Field_Schema.md

Shared ClientData wire families
    → ClientData_Shared_Decoder_Field_Evidence.md

166 gameplay subtype semantics
    → Gameplay_166_DeepEvidence.md

165/166 damage/event family
    → Y_TCP_INF_Damage.md

UDP movement / actor schema
    → UDP_Move_Inf_DeepEvidence.md
```

因此同一 opcode 在研究樹中可以被不同層引用，但只能有一份欄位／語意主真相。

## 7. Server reconstruction 意義

Server implementation 應把：

```text
transport
→ frame parser
→ opcode router
→ packet-specific codec
→ authoritative state mutation
```

分層實作。

不要把 `sub_58B010`、`sub_749B90` 或 `sub_595E80` 的 Client dispatch implementation 直接搬成 Server domain model；它們的價值在於揭示 routing boundary 與 event family，而非提供 Server class hierarchy。[C]

## 8. 目前 OPEN

```text
所有尚未列入主文件的 incoming opcode
部分 virtual callback 的 concrete target
未知 UDP opcode 的 handler semantics
```

發現新的 routing evidence 時更新本文件；發現欄位或 gameplay semantics 時，回到對應 Packet 主文件，不在此建立第二份研究。