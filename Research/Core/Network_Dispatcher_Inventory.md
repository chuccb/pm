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

## 3. High-value dispatcher cross-reference

本文件只維護 `sub_58B010` 的完整 TCP opcode → direct handler inventory；不要在此複製各 packet 的 field/schema/semantic。

已知重要入口僅列索引：

| Opcode | Handler | 對應主題 |
|---:|---|---|
| 142 | `sub_5565D0` | PM_CONNECT_ACK → UDP bootstrap；細節見 `UDP_Movement_Control_Evidence_2026-09-18.md` |
| 144 | `sub_555D50` | PM_UDPSTART_ACK |
| 166 | `sub_58D820` | Gameplay 事件；細節見 `Gameplay_Combat.md` |
| 269 | `sub_574B20` | Result / player hydration；細節見 `Result_Quest_Stats.md` |
| 715 | `sub_55D990` | Invalid-WPData ACK；細節見 `Network_Protocol.md` |

UDP direct dispatcher map 不在此重複保存；完整 UDP movement / peer / recovery evidence 統一由：
`Network_Protocol.md`（wire truth）與
`UDP_Movement_Control_Evidence_2026-09-18.md`（deep evidence）承載。

## 4. Ownership / evidence discipline

- Handler 名稱是 IDA identifier，不等於 semantic。
- Packet bytes 與 state semantic 不在本文件建立第二套定義。
- 新 semantic evidence 應更新對應主題文件，再由本文件只保留 dispatcher index。
- `Network_Protocol.md` = transport / wire truth。
- `UDP_Movement_Control_Evidence_2026-09-18.md` = UDP movement/control 的 function-level evidence。
