# PaperMan 2016 JP — TCP Dispatcher 完整 Function Map 與 UDP Peer Bootstrap 證據

> 研究日期：2026-09-18。
> Target：日本版 PaperMan 2016 年服務終了時的最終 Client。
> 本文件唯一責任：保存 `sub_58B010` 的 TCP opcode → handler 對照，以及 UDP peer/bootstrap 的 dispatcher-oriented evidence。Packet payload semantic 以各 canonical domain 文件為準。

## 1. 這份文件回答什麼

`sub_58B010` 是 TCP receive dispatcher。完整 `PaperMan.exe.c` switch 中有 **306 個明確 case**；以下為目前完整的 opcode → direct handler map。[C]

Handler 名稱只是 IDA/Hex-Rays identifier，不等於 semantic；語意需追 parser、caller/callee、state writer、resource 與 Wiki。

## 2. Complete TCP Dispatcher Map

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
| `223–245` | Result / score / K-D / Quest-event family；semantic 回 `Result_Quest_Stats.md` | `[C]` |
| `269` | result/player hydration family，含 `Y_TCP_INF` 後續資料；回 `Result_Quest_Stats.md` | `[C]` |
| `680–696`、`197–221` | Login / ClientData；回 `Login_ClientData_Protocol.md` | `[C]` |
| `165/166` | polymorphic gameplay event request/ack family；回 `Gameplay_Combat.md` | `[C]` |

## 4. UDP Peer / Bootstrap dispatcher evidence

### 4.1 TCP bootstrap names

Client protocol registration 明確列出：

```text
141 PM_CONNECT_REQ
142 PM_CONNECT_ACK
143 PM_UDPSTART_REQ
144 PM_UDPSTART_ACK
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
```

`sub_5565D0()` 在 `PM_CONNECT_ACK (142)` 路徑解析：

```text
string
u32 value
u8 flag
u32 configuration value
```

並呼叫 `sub_596E60(...)` 更新 UDP endpoint configuration；`u8 flag` 亦更新 `sub_417D00()` 所代表的 local byte state。`u32` 欄位暫保留為 bootstrap endpoint/config value，不依 Hex-Rays local name 猜成固定 port。[C][OPEN]

### 4.2 UDP receive dispatcher

`sub_595E80()` 的 direct cases：

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

### 4.3 UDP endpoint table

16-entry player/peer table：

```text
dword_F6DCF4[slot]
    → player/actor identity

unk_F6D584 + 240780*slot
    → learned peer endpoint, 16 bytes

unk_F6D594 + 240780*slot
    → source/local sockaddr, 16 bytes
```

Identity 先 lookup slot，再取得 endpoint；不能假設 identity == slot。[C]

### 4.4 Peer maintenance schemas

```text
opcode 4 inbound
  u8 count
  count × (u8 identity + 16-byte endpoint)
  → update F6D584
  → outbound opcode 5 fan-out

opcode 5 inbound
  u8 identity + u32 timing-like value
  → first-arrival source capture
  → outbound opcode 6

opcode 6 inbound
  u8 identity + u32 timing-like value
  → endpoint/source state update

opcode 10 inbound
  u8 identity + 16-byte endpoint
  → update F6D584
  → outbound opcode 13

opcode 12 inbound
  u8 count
  count × (u8 identity + 16-byte endpoint)
  → bulk F6D584 update
  → outbound opcode 13 fan-out

opcode 13 inbound
  u8 identity + u32 timing-like value
  → first-arrival source capture
  → outbound opcode 14

opcode 14 inbound
  u8 identity + u32 timing-like value
  → terminal/source state update
```

Client 端 response 5/6/13/14 的 4-byte value 都由 `n0x3E8_3` 提供；其來源是 `timeGetTime() - dword_F2563C` 類 elapsed-time 計算，因此只命名為 timing-like handshake value。[C]

### 4.5 Peer readiness

```text
sub_5941D0 → 3000 ms check
sub_594DA0 → 5000 ms check
```

這證明 peer table 具有至少兩階段 timeout lifecycle；正式 state labels 尚 `[OPEN]`。[C]

### 4.6 Protocol symbol family 153–164

```text
153 UDP_ALL_PING_REQ
154 UDP_ALL_PING_ACK
155 Y_UDP_C_HOLE_INF
156 Y_UDP_S_HOLE_INF
157 UDP_TCP_DEAD_REQ
158 UDP_TCP_DEAD_ACK
159 TCP_UDP_DEAD_REQ
160 TCP_UDP_DEAD_ACK
161 UDP_TCP_LIVE_REQ
162 UDP_TCP_LIVE_ACK
163 TCP_UDP_LIVE_REQ
164 TCP_UDP_LIVE_ACK
```

Symbol registration 是名稱證據，不等於本 Client 的所有 opcode 都由 `sub_595E80()` 接收。其 direct switch 目前明確看到 `154`、`158`；155/156/157/159/160/161/162/163/164 的完整 dispatcher path 仍按各自 search 結果處理。[C][OPEN]

## 5. UDP Movement：corrected 27-byte ActorRecord

`sub_596940()` 的明文診斷：

```text
BUGCUDPNetworkManager::OnY_UDP_S_MOVE_INF : [g_byGamePlay : %d]
```

只有 gameplay gate `n15 == 13` 時才把 movement Packet queue 到 `sub_602E30()`。[C]

### 5.1 Correct fixed record

`sub_602E30()` 每筆 fixed actor record 實際消費：

```text
R+00  u8
R+01  u8
R+02  u8
R+03  u32
R+07  u32
R+0B  u8
R+0C  u16
R+0E  u16
R+10  u16
R+12  u8
R+13  u8
R+14  u8
R+15  u8
R+16  u8
R+17  u32
```

總長：

```text
27 bytes = 0x1B
```

所以：

```text
u8 actor_count
N × 27-byte ActorRecord
```

**舊 26-byte 結論已撤銷。** 根因是 local array/scratch size 被誤當成 wire consumption；實際 fixed-width reader 明確再消費 `R+16/R+17`。[C]

### 5.2 Field semantics currently supported

```text
R+00  u8   field00                         [OPEN]
R+01  u8   field01                         [OPEN]
R+02  u8   actor/player identity           [Strongly Supported]
R+03  u32  field03                         [OPEN]
R+07  u32  field07                         [OPEN]
R+0B  u8   actor state byte                [Strongly Supported]
R+0C  u16  spatial component 0             [Confirmed]
R+0E  u16  spatial component 1             [Confirmed]
R+10  u16  spatial component 2             [Confirmed]
R+12  u8   controller/state byte           [OPEN]
R+13  u8   controller/state byte           [OPEN]
R+14  u8   controller/state byte           [OPEN]
R+15  u8   controller/state byte           [OPEN]
R+16  u8   generic state/action selector   [Strongly Supported]
R+17  u32  Resource/Action identity cand.  [Strongly Supported]
```

`R+02` 經 `sub_67DF00()` / `sub_67D7D0()` 找 16-entry remote player object；`R+0B` 經 `sub_5B3180()` 寫 actor `+233`；`R+16` 進 generic actor state machinery；`R+17` 進 Resource/Action whitelist/anomaly path。[C]

### 5.3 Spatial quantization

```text
S→C:
R+0C/R+0E/R+10 → u16 / 3.0

C→S/peer:
opcode 23
R+0C/R+0E/R+10 → u16(value*3.0 + 0.5)
```

這兩端形成直接對稱 evidence；axis naming、negative range、overflow、origin 與 exact rounding policy 仍 `[OPEN]`。[C][X]

### 5.4 State/Emotion subdomain

```text
16..25 = Emotion command/state IDs
```

由 `sub_9A8580()` 的 `16 <= n <= 25` 判斷與 `sub_7170F0()` 的 emotion1..emotion10 mapping 共同確認；整個 R+16 仍是 generic state/action selector。[C]

### 5.5 Opcode 23 fixed producer

`sub_744450()`：

```text
+00 u8  *sub_417D00()
+01 u8  byte_EE896D
+02 u8  sub_67D010()
+03 u32 dword_EE8CB4
+07 u32 n0x64_0
+0B u8  sub_720AA0(1,0)
+0C u16 (this+16)*3+0.5
+0E u16 (this+20)*3+0.5
+10 u16 (this+24)*3+0.5
+12 u8  sub_744310()
+13 u8  derived/directional state
+14 u8  derived/directional state
+15 u8  this+848
+16 u8  derived movement/action state
+17 u32 sub_5AA5C0(n9)
```

固定 27 bytes。與 8/24 inbound schema 形成 offset/width 對稱，因此為 **Strongly Supported / effectively bidirectional fixed-schema evidence**。[C][X]

## 6. Movement-adjacent nested event/effect data

`sub_5E2570()`：

```text
type 0 → none

type 1 → u8 type + u8 + u8 + 6×u16 = 15 bytes

type 2 → u8 type + u16 + u8 + 6×u16 = 16 bytes

type 3 → u8 type + u8 + 6×u16 = 14 bytes

type 4 → u8 type + u32 + u32 + 6×float = 33 bytes
```

Type 1/2/3 生成 runtime node type 1；type 4 生成 runtime node type 2；node 經 `sub_59E490(this+5387, ...)` 進 persistent linked/pooled queue。[C]

`sub_5E1D50()` 又會把 node serialize 回相同四種 wire form，Type 1 branch 另存在 vector difference → normalize → length+10 → offset 的 geometry correction，因此 decode/encode 已形成 bidirectional evidence；public event name 仍 `[OPEN]`。[C]

## 7. UDP recovery / health

UDP opcode 18：

```text
sub_596300
→ sub_556530
→ TCP opcode 141 = PM_CONNECT_REQ
→ empty payload
```

已 Confirmed `18 → 141` cross-transport transition。[C]

Movement health path：

```text
sub_5934B0:
  stored timestamp == 0 → healthy
  elapsed <= 30000 ms   → healthy
  elapsed > 30000 ms    → clear + unhealthy

sub_593510:
  n15 == 13 && timeout failure
  → TCP opcode 697
  → u16 payload = 1
```

Protocol registration：

```text
697 = GG_CHEATER_REPORT_REQ
```

因此 30 秒 timeout → Client 697 是 Confirmed；不能把 timeout 本身當作 cheating proof，server counterpart 尚 `[OPEN]`。[C]

## 8. Opcode 714 / 715

Protocol registration：

```text
714 = GG_INVALIDWPDATA_REQ
715 = GG_INVALIDWPDATA_ACK
```

`sub_548E80()` 在 invalid/unrecognized Resource/Action identity 累積超過 40 次後送 714。實際 writer：

```text
u8  local/player identity
u8  local context/state byte
u8  actor-local value
ANSI NUL-terminated string
u32 Resource/Action identity candidate
```

前三欄由 `sub_592920()` 寫 1 byte，最後欄由 `sub_592A20()` 寫 4 bytes。[C]

`sub_55D990()` 處理 715：

```text
shutdown(socket, 2)
→ closesocket
→ connection reset
→ UI/message path 0x320
```

handler 本身沒有 Packet body reader，因此 715 body fields 在 Client 中 `[OPEN]`。[C]

Client-side interaction model：

```text
invalid Resource/Action identity anomaly
→ 714
→ Server implementation [OPEN]
→ 715
→ TCP disconnect
```

Confidence：**Strongly Supported**。[C]

## 9. Periodic UDP control

Opcode 17：

```text
sub_596180
→ >=1000 ms
→ opcode 17
```

`sub_596240()` 也建立 opcode 17 並帶 string payload。[C]

Opcode 19：

```text
sub_596670
→ 約每 500 ms
→ opcode 19
→ current/peer UDP path
```

存在 retry/count-like state 與 >5 escalation，因此目前不把它命名成 generic heartbeat。[C][OPEN]

## 10. Confidence summary

| Conclusion | Confidence | Evidence |
|---|---|---|
| `sub_58B010` = TCP receive dispatcher, 306 explicit cases | Confirmed | complete C switch scan |
| UDP `sub_595E80` direct map above | Confirmed | direct switch |
| 141–144 bootstrap names | Confirmed | protocol registration + handlers |
| 16-entry identity → peer endpoint table | Confirmed | identity lookup + fixed loop + endpoint storage |
| UDP 4/5/6/10/12/13/14 peer-maintenance family | Confirmed at Client-behavior level | parser/serializer/state flow |
| 8/24 = `Y_UDP_S_MOVE_INF` | Confirmed | diagnostic string + dispatcher |
| 8/24 fixed ActorRecord = 27 bytes | Confirmed | exact reader widths + opcode 23 symmetry |
| opcode 23 fixed producer = 27 bytes | Confirmed | `sub_744450` |
| movement 16..25 = Emotion IDs | Confirmed | predicate + ten-entry mapping |
| movement R+17 = Resource/Action identity candidate | Strongly Supported | whitelist + anomaly reporting |
| opcode 18 → TCP 141 | Confirmed | direct call + empty packet |
| 697 after 30s timeout | Confirmed | timer + packet construction |
| 714 first three fields are u8 | Confirmed | byte-width helper |
| 715 causes Client TCP close | Confirmed | socket shutdown/close path |
| exact server-side peer/movement serializer | Unknown | server implementation unavailable |
| 23 formal public name | Unknown | symbol not independently closed |
| 155/156 exact wire schema | Unknown | symbol only; direct Client dispatcher path not closed |

## 11. Remaining high-value OPEN

```text
TCP handlers not yet semantic-closed
UDP 8/24 server-side producer
UDP 23 formal protocol name
Movement R+00/R+01/R+03/R+07/R+12/R+13/R+14/R+15 exact semantics
Movement R+02 exact identity namespace
Movement R+16 non-Emotion enum/state domain
Movement R+17 exact Resource/Action namespace
Nested event type 1/2/3/4 public event mapping
UDP 155/156 producer/consumer + wire fields
UDP 17/19 exact semantics
UDP 154 one-byte unit
3s/5s peer state-machine labels
UDP 697 server counterpart
TCP 165/166 complete subtype schemas
P+0x04/P+0x06 complete lifecycle (see Network_Protocol.md)
```

## 12. 相關主文件

```text
Network_Protocol.md
UDP_Movement_Control_Evidence_2026-09-18.md
Login_ClientData_Protocol.md
Room_Channel_GameRule_101_221_Field_Evidence.md
Gameplay_Combat.md
Result_Quest_Stats.md
Character_Inventory_Equipment.md
Resource_Pack_Model.md
Server_State_Model.md
```
