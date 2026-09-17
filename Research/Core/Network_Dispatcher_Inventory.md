# PaperMan 2016 JP — TCP Dispatcher 完整 Function Map 與 UDP Peer Bootstrap 證據

> 研究日期：2026-09-18。
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 本文件唯一責任：保存 `sub_58B010` 的完整 TCP opcode → handler 對照，以及 UDP peer/bootstrap 的跨函式證據。它不取代各主題文件對 packet payload semantic 的主要真相。

## 1. 這份文件回答什麼

`sub_58B010` 是 TCP receive dispatcher。完整 C source 的 switch 中有 **306 個明確 `case`**，以下表格是由完整 `PaperMan.exe.c` 自動掃描得到的 opcode → direct handler 結果。[C]

注意：handler 名稱是 IDA/Hex-Rays 當前識別字；它本身不是 semantic。真正語意仍必須追 handler 的 parser、caller/callee、state writer、resource 與 Wiki。

## 2. 完整 TCP Dispatcher Map

### Opcode `1–120`
| Opcode | Direct handler |
|---:|---|
| 102 | `sub_58D6F0` |
| 106 | `sub_56A250` |
| 108 | `sub_568CE0` |
| 110 | `sub_569240` |
| 112 | `sub_56A7B0` |
| 114 | `sub_56B360` |
| 116 | `sub_56A4D0` |
| 118 | `sub_56A550` |
| 120 | `sub_56E300` |

### Opcode `121–240`
| Opcode | Direct handler |
|---:|---|
| 122 | `sub_56E530` |
| 124 | `sub_5607C0` |
| 126 | `sub_56EA80` |
| 128 | `sub_5626D0` |
| 130 | `sub_562870` |
| 132 | `sub_56ECC0` |
| 134 | `sub_562EA0` |
| 136 | `sub_56EF40` |
| 140 | `sub_563430` |
| 142 | `sub_5565D0` |
| 144 | `sub_555D50` |
| 160 | `sub_58D790` |
| 166 | `sub_58D820` |
| 168 | `sub_56F410` |
| 170 | `sub_56F4F0` |
| 172 | `sub_56F5D0` |
| 174 | `sub_56F6B0` |
| 176 | `sub_56F790` |
| 184 | `sub_563B00` |
| 188 | `sub_563D60` |
| 190 | `sub_56FBF0` |
| 192 | `sub_56FE10` |
| 194 | `sub_56FE90` |
| 198 | `sub_570550` |
| 200 | `sub_570AB0` |
| 201 | `sub_95A3B0` |
| 202 | `sub_95AE40` |
| 203 | `sub_571D50` |
| 205 | `sub_571910` |
| 207 | `sub_571B60` |
| 209 | `sub_572B80` |
| 211 | `sub_572D80` |
| 213 | `sub_572E70` |
| 215 | `sub_572F80` |
| 219 | `sub_573230` |
| 221 | `sub_5735F0` |
| 223 | `sub_556730` |
| 225 | `sub_556780` |
| 227 | `sub_5567A0` |
| 229 | `sub_5567C0` |
| 231 | `sub_5568B0` |
| 233 | `sub_5569A0` |
| 235 | `sub_5569E0` |
| 237 | `sub_556A30` |
| 239 | `sub_556A70` |

### Opcode `241–360`
| Opcode | Direct handler |
|---:|---|
| 241 | `sub_556AF0` |
| 243 | `sub_556B30` |
| 245 | `sub_556C50` |
| 247 | `sub_573EB0` |
| 255 | `sub_574270` |
| 257 | `sub_56D420` |
| 261 | `sub_56DA70` |
| 263 | `sub_56B2E0` |
| 265 | `sub_574550` |
| 267 | `sub_5749E0` |
| 269 | `sub_574B20` |
| 274 | `sub_563650` |
| 276 | `sub_578920` |
| 278 | `sub_578BC0` |
| 280 | `sub_578FB0` |
| 284 | `unknown_libname_96` |
| 286 | `sub_578D20` |
| 288 | `unknown_libname_99` |
| 290 | `sub_579830` |
| 292 | `unknown_libname_100` |
| 294 | `sub_57A540` |
| 297 | `sub_57AA50` |
| 299 | `sub_57AEF0` |
| 301 | `sub_57AFE0` |
| 303 | `sub_5616A0` |
| 305 | `sub_5618B0` |
| 307 | `sub_561AC0` |
| 309 | `sub_561FB0` |
| 311 | `sub_5728A0` |
| 313 | `sub_573320` |
| 315 | `sub_57B500` |
| 317 | `sub_557040` |
| 319 | `sub_557400` |
| 321 | `sub_557730` |
| 323 | `sub_5579A0` |
| 325 | `unknown_libname_88` |
| 327 | `sub_557D30` |
| 329 | `sub_557F90` |
| 331 | `sub_558250` |
| 333 | `sub_561E40` |
| 341 | `sub_56F870` |
| 343 | `sub_558AB0` |
| 345 | `sub_58D870` |
| 347 | `sub_58D8A0` |
| 349 | `sub_58D8D0` |
| 351 | `sub_58D900` |
| 353 | `sub_562310` |
| 357 | `sub_572420` |
| 359 | `sub_5725D0` |

### Opcode `361–480`
| Opcode | Direct handler |
|---:|---|
| 361 | `sub_558DD0` |
| 363 | `sub_556AB0` |
| 365 | `sub_56FAE0` |
| 367 | `sub_586090` |
| 369 | `sub_585D90` |
| 371 | `sub_570100` |
| 379 | `sub_559510` |
| 381 | `sub_556CB0` |
| 383 | `sub_556D10` |
| 385 | `sub_556D70` |
| 387 | `sub_556DD0` |
| 389 | `sub_556E30` |
| 391 | `sub_57C270` |
| 393 | `sub_58E3B0` |
| 395 | `sub_579160` |
| 397 | `sub_58E410` |
| 403 | `sub_579500` |
| 405 | `sub_579650` |
| 417 | `sub_9A7DE0` |
| 420 | `sub_559810` |
| 422 | `sub_55A310` |
| 424 | `sub_55A4F0` |
| 426 | `sub_55A630` |
| 430 | `sub_55AA90` |
| 432 | `sub_55AE10` |
| 434 | `sub_55AFC0` |
| 436 | `sub_55B2C0` |
| 440 | `sub_55B660` |
| 442 | `sub_55B9F0` |
| 444 | `sub_55BE80` |
| 446 | `sub_55C120` |
| 448 | `sub_55C220` |
| 452 | `sub_57BE30` |
| 454 | `sub_57BCF0` |
| 456 | `sub_55C340` |
| 458 | `sub_573860` |
| 462 | `sub_57CC90` |
| 465 | `sub_57CDD0` |
| 467 | `sub_573A70` |
| 469 | `sub_57CE30` |
| 471 | `sub_57D210` |
| 473 | `sub_584910` |
| 475 | `sub_584E80` |
| 477 | `sub_564A00` |

### Opcode `481–600`
| Opcode | Direct handler |
|---:|---|
| 481 | `sub_585080` |
| 482 | `sub_585F50` |
| 484 | `sub_584F70` |
| 486 | `sub_56AE30` |
| 488 | `sub_5861C0` |
| 489 | `sub_57C230` |
| 572 | `sub_58E5E0` |
| 584 | `sub_54D040` |
| 586 | `sub_54CB90` |
| 587 | `sub_550410` |

### Opcode `601–720`
| Opcode | Direct handler |
|---:|---|
| 686 | `sub_55C790` |
| 691 | `sub_55C880` |
| 692 | `sub_55C960` |
| 693 | `sub_57CAE0` |
| 696 | `sub_571D70` |
| 705 | `sub_55C9B0` |
| 709 | `sub_57C0B0` |
| 713 | `sub_56FBC0` |
| 715 | `sub_55D990` |

### Opcode `721–840`
| Opcode | Direct handler |
|---:|---|
| 725 | `sub_573B70` |
| 727 | `sub_58D840` |
| 729 | `sub_56E610` |
| 731 | `sub_55E760` |
| 732 | `sub_55EB60` |
| 734 | `sub_55DAE0` |
| 735 | `sub_55EE90` |
| 738 | `sub_55F390` |
| 740 | `sub_55F5C0` |
| 742 | `sub_55FF60` |
| 743 | `sub_5600E0` |
| 744 | `sub_5601A0` |
| 745 | `sub_560260` |
| 747 | `sub_5604E0` |
| 748 | `sub_564090` |
| 750 | `sub_5640C0` |
| 751 | `sub_5641D0` |
| 753 | `sub_564290` |
| 754 | `sub_564320` |
| 755 | `sub_564260` |
| 757 | `sub_57E030` |
| 759 | `sub_57E270` |
| 760 | `sub_57E070` |
| 761 | `sub_57E2B0` |
| 763 | `sub_57E5A0` |
| 765 | `sub_57E9A0` |
| 766 | `sub_581330` |
| 768 | `sub_581450` |
| 769 | `sub_581760` |
| 770 | `sub_5817F0` |
| 772 | `sub_57E550` |
| 775 | `sub_581980` |
| 777 | `sub_581D00` |
| 778 | `sub_581D20` |
| 779 | `sub_581D60` |
| 781 | `sub_57D6B0` |
| 782 | `sub_5643C0` |
| 784 | `sub_564480` |
| 786 | `sub_5645B0` |
| 792 | `sub_885D00` |
| 794 | `sub_885DA0` |
| 796 | `sub_885E40` |
| 803 | `sub_893DB0` |
| 810 | `sub_582250` |
| 811 | `sub_58EE30` |
| 813 | `sub_58EE60` |
| 815 | `sub_58EDA0` |
| 816 | `sub_582500` |
| 821 | `sub_582750` |
| 823 | `sub_5827C0` |
| 825 | `sub_582890` |
| 826 | `sub_582BE0` |
| 833 | `sub_583030` |
| 835 | `sub_5831D0` |
| 837 | `sub_583C20` |
| 840 | `sub_5845F0` |

### Opcode `841–960`
| Opcode | Direct handler |
|---:|---|
| 842 | `sub_5842A0` |
| 844 | `sub_584350` |
| 846 | `sub_584400` |
| 847 | `sub_584770` |
| 848 | `sub_5847E0` |
| 850 | `sub_57DDC0` |
| 852 | `sub_5854C0` |
| 856 | `sub_585920` |
| 858 | `sub_585950` |
| 860 | `sub_585980` |
| 862 | `sub_5859B0` |
| 863 | `sub_5859E0` |
| 865 | `sub_585AB0` |
| 866 | `sub_91C7B0` |
| 868 | `sub_91CC70` |
| 870 | `sub_91D290` |
| 872 | `sub_91C6F0` |
| 874 | `sub_91C1E0` |
| 875 | `sub_91D690` |
| 877 | `sub_91D7E0` |
| 879 | `sub_91CAA0` |
| 880 | `sub_407E00` |
| 881 | `sub_407E00` |
| 882 | `sub_592A40` |
| 884 | `sub_579BC0` |
| 888 | `sub_88DB50` |
| 889 | `sub_88DB90` |
| 891 | `sub_424620` |
| 893 | `sub_585CB0` |
| 895 | `sub_585E70` |
| 903 | `sub_564E30` |
| 905 | `sub_565230` |
| 907 | `sub_565560` |
| 908 | `sub_565850` |
| 910 | `sub_559150` |
| 911 | `sub_578AC0` |
| 913 | `sub_95B180` |
| 914 | `sub_565A00` |
| 919 | `sub_761B20` |
| 921 | `sub_6061A0` |
| 923 | `sub_761710` |
| 925 | `sub_558550` |
| 927 | `sub_558880` |
| 929 | `sub_761E90` |
| 931 | `sub_762170` |
| 933 | `unknown_libname_105` |
| 934 | `sub_762630` |
| 936 | `sub_7623A0` |
| 937 | `sub_762560` |
| 940 | `sub_7613D0` |
| 942 | `sub_761830` |
| 945 | `sub_585F30` |
| 946 | `sub_565AA0` |
| 947 | `sub_565BB0` |
| 949 | `sub_58EF00` |
| 954 | `sub_57DA20` |
| 958 | `sub_565E00` |
| 959 | `sub_5666D0` |
| 960 | `sub_566B30` |

### Opcode `961–1080`
| Opcode | Direct handler |
|---:|---|
| 961 | `sub_566BF0` |
| 963 | `sub_5672E0` |
| 965 | `sub_566040` |
| 966 | `sub_565EF0` |
| 968 | `sub_566200` |
| 970 | `sub_586180` |
| 972 | `sub_566400` |
| 974 | `sub_566650` |
| 976 | `sub_57D660` |
| 984 | `sub_5865A0` |
| 985 | `sub_586610` |
| 986 | `sub_5880A0` |
| 987 | `unknown_libname_104` |
| 989 | `sub_588020` |
| 991 | `sub_56FA00` |
| 994 | `sub_5676D0` |
| 995 | `sub_567AE0` |
| 997 | `sub_567F20` |
| 999 | `sub_568170` |
| 1001 | `sub_567D50` |
| 1003 | `sub_567BD0` |
| 1005 | `sub_5884C0` |
| 1007 | `unknown_libname_94` |
| 1009 | `unknown_libname_95` |
| 1010 | `sub_5680E0` |

## 3. 已閉合的主要 family

| Family | 目前可確認的內容 | 主要證據 |
|---|---|---|
| `101–221` | Channel/Lobby/Room/GameRule、connect、UDP bootstrap、Y_TCP_INF 等 family；精確 bytes 回 `Room_Channel_GameRule_101_221_Field_Evidence.md` | `[C]` dispatcher + 各 handler/resource |
| `223–245` | Result / score / K-D / Quest-event family；主要 semantic 回 `Result_Quest_Stats.md` | `[C]` |
| `269` | result/player hydration family，含 `Y_TCP_INF` 後續資料；回 `Result_Quest_Stats.md` | `[C]` |
| `680–696`、`197–221` | Login / ClientData；回 `Login_ClientData_Protocol.md` | `[C]` |
| `165/166` | polymorphic gameplay event request/ack family；回 `Gameplay_Combat.md` | `[C]` |

## 4. UDP Peer / Bootstrap：已閉合的證據鏈

### 4.1 TCP bootstrap 命名

Client message table 與 handler registration 明確列出：

```text
141  PM_CONNECT_REQ
142  PM_CONNECT_ACK
143  PM_UDPSTART_REQ
144  PM_UDPSTART_ACK
159  TCP_UDP_DEAD_REQ
160  TCP_UDP_DEAD_ACK
```

`sub_5565D0()` 在 `PM_CONNECT_ACK (142)` 路徑會解析：

```text
string
u32 value
u8 flag
u32 configuration value
```

並呼叫 `sub_596E60(&unk_1326908, string, value)`；`u32 configuration value` 另外經 `sub_534F20(..., word_1D0D1F8)`，`u8 flag` 更新 `sub_417D00()` 所代表的 local byte state。[C]

目前不能把 `u32 value` 僅依 Hex-Rays local 名稱直接定義成 `port`；它應保留為 bootstrap endpoint/config value，直到 `sub_596E60` 與其 constructor/consumer 再閉合。[C][OPEN]

### 4.2 UDP endpoint table

UDP manager 內存在固定 **16 個 player entries**；`dword_F6DCF4[16]` 儲存每 entry 的 player/actor identity，而 `unk_F6D584[...]` 保存 16-byte endpoint/address data。程式不是單純「把玩家編號當 slot」：先用 identity 搜尋，再取得對應 entry。[C]

`sub_594460()`（UDP opcode 10）接收：

```text
u8 identity
16-byte endpoint/address blob
```

找到對應 player entry 後保存 endpoint，建立 opcode 13，並以 `sub_595980()` 對該 endpoint 發送 3 次。[C]

`sub_5946C0()`（UDP opcode 12）則一次接收 count 個：

```text
u8 identity + 16-byte endpoint/address blob
```

逐一更新 peer endpoint table，再對除自身以外的 active entries 發送 opcode 13。[C]

### 4.3 Peer-addressed traffic

`sub_595980()` 最終使用 WinSock `sendto()`，因此這些 packet 並非只走單一 connected UDP peer；呼叫端明確可以指定保存的對端 `sockaddr`。[C]

`sub_593AB0()` 建立 opcode 5 時，也會對所有已登錄且非本地 identity 的 peer endpoint 做三次點對點送出；這些傳輸與 16-entry endpoint table 直接相連。[C]

因此技術上可以確認：

```text
Client
  -> 維護每 player 的 endpoint
  -> 依 player identity 找 endpoint
  -> 以 sendto(endpoint) 直接傳送
```

是否在歷史文件中把整個機制命名為「P2P」仍不應僅靠玩家用語判斷；目前安全名稱是 **peer-addressed UDP traffic / UDP sender architecture**。[C][OPEN]

### 4.4 UDP peer handshake / maintenance family

目前 direct C evidence 顯示 opcode `5/6/13/14` 都屬於這個 peer/address maintenance 子系統，但各自 payload semantic 尚不能合併：

```text
opcode 5
  = identity/time-like local data
    -> peer endpoints fan-out

opcode 6
  = endpoint/status related response
    -> targeted peer

opcode 13
  = identity/time-like local data
    -> active peer fan-out

opcode 14
  = endpoint/status related response
    -> targeted peer
```

`sub_593AB0` 會把接收到的 identity 對應到 endpoint table 後建立 opcode 5；`sub_594460` / `sub_594A10` 則會在對應條件下建立 opcode 13 / 14；`sub_5941D0`、`sub_594DA0` 使用 3000 ms / 5000 ms timeout-like checks 判斷 peer state。[C][OPEN]

這裡的「maintenance / handshake」是架構性描述，不是捏造的正式 protocol enum。

### 4.5 UDP 8/24 的方向性

完整 UDP manager 的 client-side constructor 搜尋沒有找到 opcode `8` 或 `24` 的 sender；`sub_595E80()` 的 inbound switch 反而把 `8`、`24` 都導向 `sub_596940()`，而 `sub_596940()` 明文名稱為：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF
```

因此正式記錄為：

```text
8 / 24
  = Server → Client inbound Y_UDP_S_MOVE_INF family
  = Client-side exact sender: 未在此 Client C 中找到
```

未知部分是 server producer／完整 counterpart，而不是要求從 client C 虛構一個不存在的 sender。[C][OPEN]

## 5. UDP Movement：26-byte Actor Record

`sub_602E30()` 逐筆解析一個 actor snapshot。第一個 byte 是 actor count，之後每 actor 固定 26 bytes：[C]

```text
R+00  u8   v28
R+01  u8   v19
R+02  u8   n16
R+03  u32  v30
R+07  u32  v16
R+11  u8   v25[0]
R+12  u16  v35
R+14  u16  v36
R+16  u16  v37
R+18  u8   v23
R+19  u8   v38
R+20  u8   v14
R+21  u8   v15[0]
R+22  u8   n0x1C
R+23  u32  v29
```

```text
payload
= u8 actor_count
+ actor_count × 26-byte record
```

### 5.1 Identity

`R+02 n16` 會進：

```text
sub_67DF00(n16)
sub_67D7D0(n16)
```

並在 valid range 內映射到 PlayerSlot-like runtime object；因此它是高度可信的 actor/player identity，但仍不應直接命名為 `SlotIndex`。[C][OPEN]

### 5.2 Spatial vector

```text
R+12/R+14/R+16
    -> / 3.0
    -> 3D vector
```

這三個值確實是位置／空間量化資料；exact axis ordering、world origin 與 unit conversion 仍 `[OPEN]`。[C]

### 5.3 `R+23 v29`：Resource/Action Identity

這裡現在有比「event/sample value」更直接的證據。

`sub_602E30()` 將 `v29` 作為 `sub_548E80(..., a2=v29, ...)` 的第二參數；而 `sub_548C80(this, a2)` 明確比較：

```text
sub_5F5500(..., L"BOMBPLANT")
sub_5F5500(..., L"Pulp_A")
sub_5F5500(..., L"Pulp_B")
sub_5F5500(..., L"magic_finger")
sub_5F5500(..., L"Escape")
```

此外還逐一比對 player 目前四個 weapon/resource block 的 identity 欄位。這表示 `v29` 的值域可以與 **Resource / Action identity** 直接比較，而不是任意 movement scalar。[C]

因此目前 semantic 等級提升為：

```text
R+23
  = Resource/Action Identity
  confidence: Strongly Supported
```

更細的 namespace（例如是哪一個 runtime table、是否所有 action 都共用同一 namespace）仍 `[OPEN]`。

### 5.4 `R+22 n0x1C`：PState / action-state candidate

`sub_5B34B0(actor, v29, n0x1C, v38, v34, n16)` 會將 `n0x1C` 傳進 state transition path；`sub_5B3350` 會將它保存於 actor `+286`，並透過 `sub_7173E0(n0x1Ca)` 找對應 state description。`sub_5B75F0` 更直接對 `(n0x1C & 0x7F) == 8` 的 transition 做特殊處理。[C]

因此目前比「generic state byte」更精確的安全命名是：

```text
R+22
  = PState / action-state selector candidate
```

仍不能直接寫成某個完整 public enum；`sub_7173E0` 的 message mapping 主要提供 state description lookup，本身不足以證明所有 numeric values 的官方名稱。[C][OPEN]

### 5.5 `R+11 v25[0]`

`sub_5B3180(actor, v25[0])` 直接寫入 actor runtime `+233`，故它是真正的 actor state byte，不是 local padding。[C]

其 exact enum semantic 尚 `[OPEN]`。

### 5.6 `R+03/R+07` 與其他 byte fields

以下暫時保持 conservative naming：

```text
R+03 v30    -> auxiliary state / transform-related u32 [OPEN]
R+07 v16    -> snapshot scalar / movement-related u32 [OPEN]
R+18 v23    -> controller/state byte [OPEN]
R+19 v38    -> controller/state byte [OPEN]
R+20 v14    -> controller/state byte [OPEN]
R+21 v15    -> controller/state/raw byte [OPEN]
```

不能因排列位置或常見 FPS 協定習慣把它們自行命名成 jump/crouch/fire/stance。

## 6. Actor-side downstream consumers

每一筆 movement actor record 解析後會進入多層 state application：

```text
n16
 ├─ sub_67DF00 / sub_67D7D0
 └─ actor identity / PlayerSlot-like object

v16 + (v35/v36/v37)/3
 └─ sub_9BCB00
    └─ snapshot/interpolation state

v25[0]
 └─ sub_5B3180
    └─ actor +233 state byte

v29 + n0x1C + v38 + v34 + n16
 └─ sub_5B34B0
    └─ action/state transition path

v29
 └─ sub_548E80
    └─ resource/action whitelist test
    └─ anomaly counter
    └─ opcode 714 report after threshold
```

`sub_5E2570()` 也會以 `v29` 作為參數建立 event/effect-like runtime object；其內部先讀另一個 nested type byte，再依 1/2/3/4 建立不同 payload 形態，因此 `v29` 同時參與 movement-adjacent effect/state processing。[C][OPEN]

## 7. Opcode 714：目前已知的 Client-side report path

`sub_548E80()` 的條件鏈非常具體：

```text
if actor already reported
    -> stop

if a2 == 0
or a2 == BOMBPLANT
or a2 == Pulp_A/Pulp_B
or a2 == magic_finger
or a2 == Escape
or a2 matches one of 4 equipped resource identities
    -> suppress this path

else
    ++actor-local counter

counter <= 40
    -> no 714 packet

counter > 40
    -> construct TCP opcode 714
```

714 packet 的已確認欄位寫入順序為：

```text
u16 local/player identity      <- *sub_417D00()
u16 state/local byte           <- a3
u16 actor-local value          <- *(this + 240596)
string                         <- *(this + 64)
u32 Resource/Action Identity   <- a2
```

之後交給：

```text
sub_55D960
  -> sub_555090(&dword_1321D00, packet)
```

所以目前最安全的 semantic 是：

```text
714 = client-side action/resource anomaly telemetry report
```

「anti-cheat」可以是合理架構解釋，但目前沒有 server receiver evidence 足以把它提升成正式命名。[C][OPEN]

## 8. UDP periodic / health traffic

`sub_596180()`：

```text
每 >= 1000 ms
→ opcode 17
→ local UDP socket
```

`sub_596670()`：

```text
每約 500 ms
→ opcode 19
→ peer-addressed UDP path
```

opcode 19 的 body 至少包含 local identity、local byte state、mode-like byte、u32 state、localized/string payload；存在 retry/count-like state 與 escalation path。不能直接稱為普通 heartbeat。[C][OPEN]

`sub_5934B0()` / `sub_593510()` 還存在 30000 ms timeout path，條件成立時產生 TCP opcode 697；697 的完整 server semantic 仍 `[OPEN]`。

## 9. PM_CONNECT / PM_UDPSTART 與 peer table 的關係

目前可以穩定建模成：

```text
TCP 141/142 PM_CONNECT
    ↓
建立 / 更新 Client-side UDP endpoint 基礎設定
    ↓
TCP 143/144 PM_UDPSTART
    ↓
取得 / 啟動 gameplay UDP context
    ↓
UDP peer endpoint distribution
    ↓
16-entry identity → endpoint table
    ↓
peer-addressed UDP traffic
    ↓
UDP movement / gameplay transport
```

但 `141/142/143/144` 的完整 field-by-field conversion、server-side endpoint generation 以及每個 peer opcode 的正式 enum 還需要繼續從 producer/consumer 閉合。[C][OPEN]

## 10. Evidence / Confidence

| 結論 | 等級 | 原因 |
|---|---|---|
| `sub_58B010` 有 306 個 explicit cases | Confirmed | 完整 `PaperMan.exe.c` switch 全檔掃描 |
| 141/142/143/144 是 PM connect/UDP bootstrap 命名 | Confirmed | handler registration 與 protocol/resource strings 同時出現 |
| UDP 使用 16-entry player identity → endpoint table | Confirmed | identity lookup、16 次迴圈、endpoint store、point-to-point send |
| UDP 存在 client-side peer-addressed send | Confirmed | `sub_595980` 最終呼叫 `sendto` |
| 8/24 是 inbound `Y_UDP_S_MOVE_INF` | Confirmed | inbound switch + `OnY_UDP_S_MOVE_INF` 明文名稱 |
| movement actor record = 26 bytes | Confirmed | `sub_602E30` 實際 parser read widths |
| movement R+23 = Resource/Action Identity | Strongly Supported | `sub_548C80` 與 action/resource identities 直接比對 |
| R+22 = PState/action-state selector candidate | Strongly Supported | `sub_5B34B0` → `sub_5B3350` → state lookup/transition |
| opcode 714 是 client-side anomaly telemetry report | Strongly Supported | explicit threshold + suppressed action whitelist + concrete packet construction |
| 714 server-side semantic | Unknown | client C 中未找到 receiver counterpart |
| 「完整 P2P 協定」歷史命名 | Unknown | 已證明 endpoint-addressed traffic，但完整外部協定仍未完全閉合 |

## 11. 目前真正 OPEN

```text
TCP dispatcher 每個 handler 的 semantic 尚未全部閉合

UDP opcode 4/5/6/10/12/13/14 的完整 payload schema
UDP peer endpoint value 的 server 產生流程
UDP 8/24 server-side producer 與 26-byte record serializer
TCP header +0x06 與完整 transform/compression 條件
165/166 全 subtype payload 與 server validation contract
714 server receiver/counterpart
movement R+00/R+01/R+03/R+07/R+11/R+18/R+19/R+20/R+21 的 exact semantic
movement R+02 identity namespace 的 exact conversion
R+12/R+14/R+16 exact axis/unit encoding
R+23 exact Resource/Action namespace
sub_5E2570 nested event/effect object 的完整 type/value schema
```

## 12. 後續最高價值追查順序

```text
A. sub_59E4F0 / sub_59A590 / sub_5E2570
   → close movement-adjacent event/effect object

B. sub_548E80 / opcode 714 receiver search
   → close action/resource anomaly report

C. UDP peer opcode 4/5/6/10/12/13/14
   → exact byte schema + producer/consumer pairing

D. all consumers of movement R+00/R+01/R+03/R+07/R+11/R+18..R+21
   → formalize movement fields

E. n16 → sub_67D7D0 → exact actor identity namespace

F. 165/166 subtype pairs
   → complete gameplay event schema

G. itemdata.pat category-specific fields
   → close static ItemDefinition

H. TCP header +0x06 / transform
   → close outer protocol
```

## 13. Evidence discipline

```text
[C]     IDA C direct evidence
[RES]   Extracted resource evidence
[WIKI]  Wiki / player-observable historical behavior
[X]     at least two independent evidence classes agree
[OPEN]  unresolved; do not silently replace with 0 or invented enum
```

Parser/serializer implementation has priority over Hex-Rays guessed local types. Resource definitions, runtime state, and network wire layouts must remain distinct until a conversion path is directly established.

## 14. 相關主文件

```text
Network_Protocol.md
Login_ClientData_Protocol.md
Room_Channel_GameRule_101_221_Field_Evidence.md
Gameplay_Combat.md
Result_Quest_Stats.md
Character_Inventory_Equipment.md
Resource_Pack_Model.md
Server_State_Model.md
```