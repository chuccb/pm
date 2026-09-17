# `680–696` 登入鄰近協定與 `GL_LOGIN_ACK (681)` 完整結構

> 研究目標：日本版 PaperMan 2016 年最終 Client。
> 更新基準：2026-09-17。
>
> 本文件整合原本 `Login_Adjacent_680_696_Field_Schema.md` 與 `Login_681_Server_Record_Field_Schema.md`。因此 `680–696` 及 `681` server-record schema 現在集中在同一份登入鄰近協定主文件。

## 1. 協定註冊空間

Client 直接註冊：

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

封包註冊只代表 opcode identity，不能單憑 registration 推導 body。

## 2. 680 `GL_LOGIN_BASE`

目前 C export 中沒有找到可靠的 concrete sender/receiver body。

```text
狀態 = 僅註冊
body = unknown
```

不得自行建立 payload。

## 3. 681 `GL_LOGIN_ACK`

Concrete receiver：`CLobbyLogin::sub_43E500`。

### 3.1 成功前綴

```text
u32 status
```

只有 `status == 1` 進入成功 bootstrap。接著：

```text
u32 v144
u32 n100
u32 v140
if v140 > 0:
    u32 v120
    u32 v141
    u8  v135
```

Client 儲存：

```text
v144 → dword_EE8970
n100 → global n100
v135 != 0 → byte_231807D
```

`n100` 之後會被 `143 PM_UDPSTART_REQ` 使用，因此存在明確的跨封包依賴。[C]

### 3.2 Server-list record count

成功前綴後讀：

```text
u16 record_count
```

並重複解析 server-list record。

### 3.3 Server-list wire record

每筆依序：

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

因此 wire grammar 包含變長字串與巢狀條件欄位，不能改寫成固定長度 record。[C]

目前已直接確認的結構：

- `src` 被用作 server-record collection 的 key/identity。[C]
- 兩個主要字串使用 NUL 結束。[C]
- 三個巢狀 subrecord 僅在前置 u16 大於 0 時出現。[C]
- `n3 == 3` 時才多一個 u8。[C]

### 3.4 132-byte Client raw storage

`sub_58E890()` 使用固定 132-byte stride；`sub_58F120()` / `sub_5902A0()` 會以 `0x84` bytes 複製。[C]

這是 **Client-side canonical storage record**，不是 wire record size。

因此：

```text
681 wire record
    → 132-byte raw Client storage
```

wire implementation 必須保留變長字串及 conditional nested grammar。[C]

### 3.5 Raw storage 的 UI consumers

已知：

```text
+52   → SERVERNAME 類顯示資料
+61   → aggregate/value processing
+62   → aggregate/value processing
+63   → FACE index source
+122  → current users
+124  → maximum users
+128  → KINDOFSERVER lookup/index
+129  → server state category
+130  → server state subtype（+129 == 3 時）
```

使用者數顯示格式直接是：

```text
"%d/%d", record+122, record+124
```

若 `record+129 == 3`，`record+130` 會映射到後續 server-state presentation：

```text
2 → 3
3 → 4
4 → 7
5 → 5
1 或 6 → 6
0 → 8
```

`record+128` 還會經過 `+905` 的 Resource ID calculation 後進入 localization，因此不能把它當成 user count。[C]

### 3.6 `CLobbyServerData` 80-byte view

Client 還有另一層固定 80-byte 的 `CLobbyServerData` representation：

```text
681 wire record
    → 132-byte raw storage
    → 80-byte CLobbyServerData view
    → Server-list UI
```

因此 80-byte view offset 同樣不可直接當 wire offset。[C]

### 3.7 681 證據邊界

已閉合：

```text
status = u32
record_count = u16
wire field order
wire scalar widths
NUL-terminated strings
3 個 conditional nested records
n3 == 3 的額外 u8
raw storage stride = 132
raw +122/+124 = current/max users
raw +128 = server-kind/type lookup
raw +129/+130 = state category/subcategory path
raw +63 = face/icon source
```

仍保留 raw：

```text
v124 的正式公開名稱
v125/v129/v128 的正式公開名稱
v127/n3/v126/v132/v131 的正式公開名稱
raw +0 的正式業務語意
raw +61/+62 的正式公開名稱
```

## 4. 682 `GL_LOGIN_REQ`

Concrete sender：`CLobbyLogin::sub_43DF00`。

目前可直接觀察：

```text
ASCII-Z USERID
ASCII-Z PASSWORD
u64 datarevision-derived verification composite
u8  hardware-ID source/state
raw 24-byte hardware-ID slot
```

USERID/PASSWORD 來自 Login UI state。第三個 `sub_401B50()` 屬於 Client state update，而非第三個 wire string。[C]

## 5. 683 `GL_SERVERLIST_NOTICE`

沒有找到可靠的 concrete receiver/sender。

```text
狀態 = 僅註冊
body = unknown
```

## 6. 684 `GL_LOGIN_DUPLICATE`

沒有找到可靠的 concrete receiver/sender。

```text
狀態 = 僅註冊
body = unknown
```

## 7. 685 `GL_TUTORIALINDEX_REQ`

Concrete sender：`sub_55C6F0`。

```text
payload = 0 bytes
```

## 8. 686 `GL_TUTORIALINDEX_ACK`

Concrete receiver：`sub_55C790`。

```text
+00 u32 tutorial_index
```

寫入 tutorial/global state。[C]

## 9. 687 `GL_TUTORIAL_START`

Concrete sender：`sub_5624D0`。

```text
payload = 0 bytes
```

只有在 `sub_67EC20() == nullptr` 時送出。[C]

## 10. 688 `GL_TUTORIAL_END`

Concrete sender：`sub_562570`。

```text
payload = 0 bytes
```

送出後另有 local tutorial state 更新。[C]

## 11. 689 `GL_TUTORIAL_INDEX_SET_REQ`

Concrete sender：`sub_55C7D0`。

雖然 Hex-Rays prototype 可能顯示：

```c
sub_55C7D0(char n100)
```

但其呼叫的 serializer 是 4-byte writer，因此真正 wire field 為：

```text
+00 u32 tutorial_index
```

這是本專案必須保留的「decompiler prototype ≠ wire width」典型案例。[C]

## 12. 690 `GL_TUTORIAL_INDEX_SET_ACK`

目前為 registration-only：

```text
body = unknown
```

## 13. 691 `GL_ITEM_MODIFY_NOTIFIER`

Concrete receiver：`sub_55C880`。

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

重要：這是 `if / else if`，不是兩個獨立 flags 同時作用。整個 packet 共用同一組 flags。[C]

`0x01` 路徑進 `sub_534450()`，`0x10` 路徑進 `sub_528D20()`。[C]

## 14. 692 `GG_CP_TERMINATE_APP`

Concrete receiver：`sub_55C960`。

```text
+00 u32 message/resource key
```

Client 透過 localization resource key 顯示訊息；wire 本身沒有直接帶文字。[C]

## 15. 693 `GL_TCPCONNSUCC`

Concrete receiver：`sub_57CAE0`。

```text
payload = 0 bytes
```

處理後進入後續連線／143 path。[C]

## 16. 694 `GL_ACCOUNTCONNSUCC`

Concrete receiver：`CLobbyLogin::sub_43E500`。

```text
+00 u16 negotiated_packet_limit
```

值會受 `0x2580`（9600）上限約束，對應 Client packet buffer ceiling；之後轉入 682 login request path。[C]

## 17. 695 `GS_BUY_ONCEITEM_REQ`

695 在 Client 中是 polymorphic request，同一 opcode 根據 item descriptor class 具有不同 wire grammar。

已知 generic concrete grammar 包含：

```text
Class A:
    u32 item/resource key
    ASCII-Z secondary string
    u8 item-duration/type
    u8 period/count

Class B/C/D:
    u32 item/resource key
    u8 item-duration/type
    u8 period/count

Special range:
    u32 transformed item/resource key
    u32 period/count/value

某一 weapon-shooting path:
    u32 fixed item/resource key
    u8 validated category/value
    u8 caller-provided category/value
    u16 encoded negative quantity/state
```

`sub_9A8620`、`sub_9A8640`、`sub_9A8660`、`sub_9A8680`、`sub_9A85E0` 與 item/resource address range 共同決定 grammar。[C]

已知固定 descriptor class：

```text
E975A1 → class 1
E975A2 → class 2
E975A7 → class 3
E975A4 → class 4
E975A3 → class 5
```

class 名稱仍應保持 resource-side identity，未有直接證據前不要改成猜測的業務 item name。

## 18. 696 `GS_BUY_ONCEITEM_ACK`

Concrete receiver：`sub_571D70`。

前綴：

```text
+00 u8  ack_mode
+01 u32 item/resource descriptor
```

`ack_mode` 會選擇後續不同 payload grammar，因此不要簡化為單純 success/error byte。

### 18.1 ack_mode == 0

```text
u32 value
```

### 18.2 ack_mode == 1 + 固定特殊 item E975BE

```text
u32 value
```

經 `sub_5392A0` 套用。[C]

### 18.3 E975A3/E975A4 family

```text
u32 resource/key
u32 value
```

部分 branch 在 `n11 == 6` 時會經 `sub_534450` 更新 ClientData。[C]

### 18.4 E975A1 family

```text
ASCII-Z string
```

之後進 Client state setter 與 UI feedback path。[C]

### 18.5 E975A2 family

```text
nested ClientData decoder
u32 value
u32 value
```

### 18.6 其它 descriptor/category family

不同 item descriptor 會追加 u32、u8、u16 或 string 欄位；目前必須以相同 item predicate 與 Resource range 判斷 branch。[C]

共同 trailer 包含數個 u32 context/state 值，但尚無唯一公共名稱時保留 raw。[OPEN]

## 19. 登入主鏈

目前最可靠的 transport-critical login chain：

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

具體 socket ownership 與某些事件的先後仍應以 object/data-flow 為準，不可只依 opcode 編號排序。[C][OPEN]

Tutorial 與 purchase 的 685–696 位於相鄰 opcode namespace，但不是全部屬於最小 credential handshake。[C]

## 20. 最終重建規則

對 680–696 統一採用：

```text
registration name
    = opcode identity only

actual sender/receiver
    = concrete Final Client evidence

wire width
    = actual reader/writer helper

semantic name
    = consumer/resource/data-flow evidence
```

未知 body 不因「封包名稱看起來應該如此」而自行補齊。
