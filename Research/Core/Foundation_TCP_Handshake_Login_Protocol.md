# PaperMan 2016 JP Final — TCP／封包基礎與共用 Codec

> 研究日期：2026-09-17。
> 目標版本：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 文件角色：只保存 TCP transport、frame framing、integrity／transform 與共用讀寫 helper。`680–696` 登入鄰近封包的具體 schema 統一見 `Login_Adjacent_680_696_Field_Schema.md`。

## 1. TCP 連線分層

目前 Client 至少存在兩個主要 TCP ClientSocket：

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

具體 Login／Lobby opcode 不在本文件重複維護。[C]

## 2. TCP frame framing

Client 使用持續接收緩衝區處理 TCP stream；一次 `WSARecv()` 可能得到：

```text
部分封包
一個完整封包
多個連續封包
```

目前閉合的 frame 形式為：

```text
+0x00 u16 logical_length
+0x02 u16 opcode
+0x04 u16 integrity / XOR field
+0x06 u16 auxiliary compression-related field
+0x08 payload
```

送出長度：

```text
logical_length + 8
```

接收端只有在緩衝區至少具有完整 `logical_length + 8` bytes 後才進行處理；完成後移除恰好一個 frame，剩餘 bytes 保留給下一個 frame。[C]

這直接證明 TCP stream 不能以「一次 recv = 一個 packet」實作。

## 3. Integrity／XOR transform

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

因此可以確定：

```text
header +0x04
    = integrity value + XOR mask source
```

目前沒有充分證據把它命名成 cryptographic key；應避免在 Server 中過度命名。

## 4. Checksum 定義

`sub_592220()` 對 payload bytes 計算每一 byte 的 bit-popcount，再累加為 16-bit 結果。[C]

因此目前最安全的 reconstruction 名稱為：

```text
PayloadBitCountChecksum : ushort
```

實作時應以實際 Client C／ASM 再確認 overflow／signedness 細節；不要自行換成 CRC、MD5 或常見 checksum 演算法。

## 5. Header +0x06

`+0x06` 參與壓縮／解壓縮大小或 validation path，但它的完整公開語意尚未完全閉合。[C][OPEN]

目前應保持：

```text
header_aux_u16
```

不要假設它就是 compression flag、sequence、reserved 或 payload length。

## 6. 共用 fixed-width codec helper

以實際 helper body 為最高優先級：

```text
u8    read/write → sub_592900 / sub_592940 / sub_5928E0 / sub_592920 / sub_592960
u16   read/write → sub_5929C0 / sub_592A00 / sub_5929A0 / sub_5929E0
u32   read/write → sub_592A40 / sub_592A80 / sub_592AC0 / sub_592B40 / sub_592A20 / sub_592A60 / sub_592AA0 / sub_592B20
u64/raw8         → sub_592B00 / sub_592B80 / sub_592AE0 / sub_592B60
raw              → sub_592500 / sub_592580
raw16            → sub_592C40 / sub_592C20
ASCII-Z string   → sub_592730 / sub_5926F0
```

重要原則：

```text
Hex-Rays local prototype
    ≠
actual wire width
```

例如 `sub_592B20` 雖可能被呼叫端呈現成 char-like 參數，實際 wire copy 仍是 4 bytes；`sub_592AE0` 也確實寫入 8 bytes。[C]

Server reconstruction 必須追到底層 helper，而不是直接翻譯 Hex-Rays 表面型別。

## 7. TCP parser 的共通模型

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

不要把：

```text
transport framing
packet schema
runtime state
server semantic model
```

混成同一層。

## 8. 登入封包的文件邊界

以下資料已集中於：

```text
Research/Core/Login_Adjacent_680_696_Field_Schema.md
```

因此本文件不再重複保存：

```text
680 GL_LOGIN_BASE
681 GL_LOGIN_ACK
682 GL_LOGIN_REQ
683–696 login-adjacent opcodes
681 server-list record
682 credential / revision / hardware-ID payload
```

需要登入資料時直接回到該主文件。

## 9. 與其它資料域的關係

```text
Foundation_TCP_Handshake_Login_Protocol.md
    = TCP framing / transform / codec authority

Login_Adjacent_680_696_Field_Schema.md
    = 680–696 packet truth

Network_Dispatch.md
    = opcode registration / routing

ClientData_Shared_Decoder_Field_Evidence.md
    = reusable application-level wire families
```

這四層必須保持分離，避免相同 frame／field 在不同文件重新定義。

## 10. 目前 OPEN

```text
header +0x06 的正式語意
compress/decompress validation 的完整條件
是否存在額外 sequence／ordering state
所有 transport error／retry path
```

後續取得新的 C/LST/ASM 證據時，優先更新本文件；但任何特定 opcode 的 payload schema 應回到該 opcode 的唯一主文件。