# PaperMan 2016 JP Final — 網路、封包傳輸與 Dispatcher

> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 更新基準：2026-09-17。
> 文件責任：將 TCP/UDP transport、frame framing、integrity/transform、共用 codec、packet submission、opcode registration 與 dispatcher 集中於同一網路主文件。特定 opcode 的完整 payload semantic 仍由各遊戲領域章節或主文件維護。

## 先看這裡：這份文件回答什麼

如果問題是「封包怎麼進出 Client、TCP/UDP 怎麼分、frame 怎麼組、哪裡 dispatch」，看這份文件。

如果問題是「某個 opcode 的欄位語意」，沿著 dispatcher 找到對應領域文件，不要在這裡建立第二份 payload schema。

最短理解路徑：

```text
Socket / stream
  ↓
Frame
  ↓
Integrity / XOR
  ↓
Packet
  ↓
Dispatcher
  ↓
Opcode handler
  ↓
State / gameplay
```

## 1. 研究範圍與分層

本文件整合原本分散的：

```text
Foundation_TCP_Handshake_Login_Protocol.md
Network_Dispatch.md
Y_TCP_INF_Transport.md
```

目前網路層採以下分層：

```text
Socket / stream
    ↓
receive buffer / send queue
    ↓
outer frame
    ↓
integrity / XOR transform
    ↓
Packet object
    ↓
opcode dispatcher
    ↓
opcode-specific parser / serializer
    ↓
game state / gameplay subsystem
```

不要把 transport、wire packet schema、runtime state 或 Server domain model 混成同一層。

## 2. TCP socket 與 connection 分層

Client 至少存在兩個主要 TCP ClientSocket：

```text
dword_131F730 → Login / Account TCP

dword_1321D00 → Lobby / Gameplay TCP
```

兩者都是：

```text
AF_INET
SOCK_STREAM
IPPROTO_TCP
```

具體 login/lobby opcode 不在這裡重複保存。

## 3. TCP receive stream 與 frame reassembly

Client 使用持續接收緩衝區處理 TCP stream；一次 `WSARecv()` 可能取得：

```text
部分封包
一個完整封包
多個連續封包
```

目前閉合的 outer frame：

```text
+0x00 u16 logical_length
+0x02 u16 opcode
+0x04 u16 integrity / XOR field
+0x06 u16 auxiliary field
+0x08 payload
```

送出長度：

```text
logical_length + 8
```

接收端只有在 buffer 至少具備完整 `logical_length + 8` bytes 後才處理；完成一個 frame 後移除恰好一個 frame，剩餘 bytes 保留給下一個 frame。[C]

因此 Server 不得採用：

```text
一次 recv = 一個 packet
```

## 4. Integrity / XOR transform

目前共用流程：

```text
sub_592220
    → 計算 16-bit checksum

sub_5923D0
    → header +0x04 為空時建立 checksum
    → sub_592470

sub_592470
    → 每個 payload byte XOR header +0x04 的低位元組

sub_592420
    → 反轉 XOR
    → 重新計算 checksum
    → 比對 header +0x04
```

因此：

```text
header +0x04
    = integrity value + XOR mask source
```

目前沒有充分證據將它命名成 cryptographic key；Server 實作應保留中性名稱。

## 5. Checksum

`sub_592220()` 對 payload 每一 byte 計算 bit-popcount，再累加為 16-bit 結果。[C]

目前最安全的 reconstruction 名稱：

```text
PayloadBitCountChecksum : ushort
```

overflow、signedness 與所有邊界行為仍以 C/ASM 為準；不可自行替換成 CRC、MD5 或其他常見 checksum。

## 6. Header +0x06

`+0x06` 參與壓縮／解壓縮大小或 validation path，但完整公開語意尚未閉合。[C][OPEN]

目前保持：

```text
header_aux_u16
```

不要假設它是 compression flag、sequence、reserved 或 payload length。

## 7. 共用 fixed-width codec

以 helper implementation 為最高優先級：

```text
u8    read/write → sub_592900 / sub_592940 / sub_5928E0 / sub_592920 / sub_592960
u16   read/write → sub_5929C0 / sub_592A00 / sub_5929A0 / sub_5929E0
u32   read/write → sub_592A40 / sub_592A80 / sub_592AC0 / sub_592B40 / sub_592A20 / sub_592A60 / sub_592AA0 / sub_592B20
u64/raw8         → sub_592B00 / sub_592B80 / sub_592AE0 / sub_592B60
raw              → sub_592500 / sub_592580
raw16            → sub_592C40 / sub_592C20
ASCII-Z string   → sub_592730 / sub_5926F0
```

其中目前特別重要：

```text
sub_592B20 → 實際序列化 4 bytes
sub_592B40 → 實際讀 4 bytes
sub_592AE0 → 實際寫 8 bytes
```

所以：

```text
Hex-Rays local prototype
    ≠
actual wire width
```

例如：

```c
sub_592B20(packet, SLOBYTE(value));
```

不能因此寫成 `u8` wire field。

## 8. TCP parser 共通模型

所有 TCP opcode 應採：

```text
TCP stream
    ↓
frame reassembly
    ↓
integrity / XOR reverse transform
    ↓
opcode dispatch
    ↓
opcode-specific parser
    ↓
state mutation
```

## 9. TCP receive dispatcher

TCP receive loop 完成 frame 後交給：

```text
sub_58B010(..., packet)
```

抽象為：

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

進入 opcode switch 前，`sub_58B010` 還會經過共通 receive hook：

```text
sub_407360(...)
CGameRule::sub_67CF90(...)
opcode = sub_591EE0(packet)
```

`CGameRule::sub_67CF90` 會檢查 `this +16` 並進一步呼叫 virtual-style callback，因此不是單純 no-op。[C]

## 10. 主要 TCP opcode routes

`sub_58B010` 已直接觀察到主要 server-originated route：

```text
160 → sub_58D790
166 → sub_58D820
168 → sub_56F410
170 → sub_56F4F0
172 → sub_56F5D0
174 → sub_56F6B0
176 → sub_56F790
```

同一 dispatcher 亦承接 `193–221`、`223–245`、`269` 等其他 TCP family；具體 route 應由相關網路領域主文件描述。[C]

重要方向性事實：

```text
165 = Y_TCP_INF_REQ
    → client→server send family

166 = Y_TCP_INF_ACK
    → server→client receive family
```

此方向由具體 send/receive path 閉合，不靠 opcode 奇偶性猜測。[C]

## 11. UDP receive architecture

UDP 不經 `sub_58B010`。目前入口：

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

已閉合的主要 UDP routes：

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

UDP 8/24 的 actor record 與 movement/state semantics 應與 Gameplay/Movement 主文件交叉驗證。[C]

## 12. Packet construction 與 socket submission

Gameplay packet 建立通常為：

```text
Packet ctor(opcode)
  ↓
sub_5929xx / sub_592Bxx field serializers
  ↓
packet buffer
  ↓
submission wrapper
  ↓
socket / send queue
```

Packet field serializer 不等於 socket framing。

### `sub_58D7D0`

主要 submission wrapper：

```text
packet
  → sub_58D7D0
  → sub_555090(&dword_1321D00, packet)
  → socket / send queue
```

`dword_1321D00` 在反編譯結果中對應 SOCKET。[C]

### `sub_602E00`

`sub_602E00()` 不是另一套 transport，而是 conditional front-end：

```text
sub_602E00
    → 檢查特殊條件
    → 正常情況進 sub_58D7D0
    → sub_555090
```

因此不得將：

```text
602E00 = UDP transport
```

或另一套獨立 TCP transport。[C]

## 13. Y_TCP_INF 的傳輸邊界

目前至少分成：

```text
Logical Packet Payload
    ↑
field serializers
    ↓
Packet object / internal buffer
    ↓
outer packet framing
    ↓
submission
    ↓
Socket / queue
```

因此 payload field 總和不能直接當 final TCP frame size。

對每個 `Y_TCP_INF` opcode/subtype，至少同時記錄：

```text
caller expression type
serializer used
serializer byte count
logical semantic
outer frame contribution
```

## 14. 166 第二級 dispatcher

`166` receive route：

```text
sub_58B010
    ↓ case 166
sub_58D820
    ↓
sub_749B90
```

第一層：

```text
u8 outer_actor_like
u8 subtype
```

之後依第二個 byte 進 subtype dispatch。[C]

`166` 完整 subtype evidence 回 Gameplay 主文件；這裡只保留 routing boundary。

## 15. 登入封包邊界

以下資料的具體 packet schema 應集中在 Login/ClientData 主文件：

```text
680–696
681 server-list record
682 credential / revision / hardware-ID payload
```

本文件只負責 transport、frame、codec 與 dispatcher。

## 16. Server reconstruction

Server implementation 應維持：

```text
transport
→ frame parser
→ opcode router
→ packet-specific codec
→ authoritative state mutation
```

不要將 Client 的 `sub_58B010`、`sub_749B90` 或 `sub_595E80` 直接翻譯成 Server class hierarchy；它們的主要價值是揭示 routing boundary 與事件分層。

## 17. 跨文件責任

```text
Network_Protocol.md
    = TCP/UDP transport、frame、transform、codec、submission、dispatcher

Login / ClientData 主文件
    = 680–696、198、ClientData nested records 與玩家資料

Room / Lobby / GameRule 主文件
    = 101–192、193–221 的具體 packet/state

Gameplay / Combat 主文件
    = 165/166 gameplay event、UDP movement、combat
```

同一 opcode 可以在不同章節被引用，但不應建立第二份完整欄位真相。

## 18. 目前 OPEN

```text
header +0x06 的正式 semantic
compress/decompress validation 的完整條件
是否存在額外 sequence / ordering state
所有 transport error / retry path
尚未映射的 incoming opcode
部分 virtual callback 的 concrete target
未知 UDP opcode 的 handler semantics
```

新的 transport 證據優先更新本文件；具體 packet semantic 則更新相應遊戲領域主文件。
