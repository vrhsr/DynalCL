# Stage 0.5: stage05_population_advantage

## Decision: **REVISE**

Reason: confirmed meaningful advantage exists but is not stable across context lengths/horizons (P2 failed).

P1 reference reliability = True; P2 (stable across n) = False {'1': True, '5': False}; P3 (robust across r) = False {'0.25': True, '4.0': False}.

## Reference reliability (P1)

- T1 optimality: 0 violations / 2736 (z_crit 4.95, min z -0.44)
- T2 calibration of the matched reference: 0 failing / 288 cell-replicates (min p 7.80e-04, per-test level 8.7e-07)
- max quadrature node-doubling error at targets: 1.33e-15 (threshold 1e-06); max matched quadrature-cap rate: 0.0
- bootstrap vs analytic primary class agreement: 288/288

## Primary: matched reference - frontier_ctx (nats/forecast; mean [decision interval, z = 2.24]; delta = 0.02)

### E-CONT

| r | K | n | h | frontier | R1: mean [interval] class | R2: mean [interval] class | confirmed | vs Stage-0 frontier (R1) | vs strict (R1) | vs stability (R1) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 0 | 1 | 1 | stability_prior_bayes | +0.0439 [+0.0319, +0.0558] MEANINGFUL | +0.0458 [+0.0338, +0.0578] MEANINGFUL | **MEANINGFUL** | +1.6631 | +2532.5514 | +0.0439 |
| 0.25 | 0 | 1 | 5 | stability_prior_bayes | +0.0126 [+0.0070, +0.0182] NEGLIGIBLE | +0.0135 [+0.0082, +0.0189] NEGLIGIBLE | **NEGLIGIBLE** | +2.5222 | +261.6863 | +0.0126 |
| 0.25 | 0 | 2 | 1 | stability_prior_bayes | +0.0475 [+0.0365, +0.0585] MEANINGFUL | +0.0527 [+0.0412, +0.0641] MEANINGFUL | **MEANINGFUL** | +0.5662 | +3.7812 | +0.0475 |
| 0.25 | 0 | 2 | 5 | stability_prior_bayes | +0.0125 [+0.0064, +0.0186] NEGLIGIBLE | +0.0158 [+0.0104, +0.0212] INCONCLUSIVE | **DISCORDANT** | +1.3514 | +1.3514 | +0.0125 |
| 0.25 | 0 | 3 | 1 | stability_prior_bayes | +0.0534 [+0.0438, +0.0629] MEANINGFUL | +0.0455 [+0.0355, +0.0554] MEANINGFUL | **MEANINGFUL** | +0.2740 | +0.5114 | +0.0534 |
| 0.25 | 0 | 3 | 5 | stability_prior_bayes | +0.0110 [+0.0049, +0.0171] NEGLIGIBLE | +0.0161 [+0.0108, +0.0214] INCONCLUSIVE | **DISCORDANT** | +0.4820 | +0.6118 | +0.0110 |
| 0.25 | 0 | 5 | 1 | stability_prior_bayes | +0.0359 [+0.0262, +0.0456] MEANINGFUL | +0.0280 [+0.0190, +0.0371] INCONCLUSIVE | **DISCORDANT** | +0.1164 | +0.2258 | +0.0359 |
| 0.25 | 0 | 5 | 5 | stability_prior_bayes | +0.0088 [+0.0032, +0.0144] NEGLIGIBLE | +0.0140 [+0.0089, +0.0190] NEGLIGIBLE | **NEGLIGIBLE** | +0.2080 | +0.2871 | +0.0088 |
| 0.25 | 0 | 10 | 1 | stability_prior_bayes | +0.0193 [+0.0125, +0.0261] INCONCLUSIVE | +0.0194 [+0.0127, +0.0260] INCONCLUSIVE | **INCONCLUSIVE** | +0.0372 | +0.0897 | +0.0193 |
| 0.25 | 0 | 10 | 5 | stability_prior_bayes | +0.0074 [+0.0025, +0.0123] NEGLIGIBLE | +0.0092 [+0.0049, +0.0136] NEGLIGIBLE | **NEGLIGIBLE** | +0.0564 | +0.0870 | +0.0074 |
| 0.25 | 0 | 20 | 1 | stability_prior_bayes | +0.0055 [+0.0014, +0.0096] NEGLIGIBLE | +0.0037 [-0.0005, +0.0078] NEGLIGIBLE | **NEGLIGIBLE** | +0.0069 | +0.0335 | +0.0055 |
| 0.25 | 0 | 20 | 5 | stability_prior_bayes | +0.0019 [-0.0017, +0.0054] NEGLIGIBLE | +0.0041 [+0.0007, +0.0076] NEGLIGIBLE | **NEGLIGIBLE** | +0.0111 | +0.0341 | +0.0019 |
| 1 | 0 | 1 | 1 | stability_prior_bayes | +0.0416 [+0.0300, +0.0531] MEANINGFUL | +0.0440 [+0.0319, +0.0560] MEANINGFUL | **MEANINGFUL** | +0.7987 | +580.0234 | +0.0416 |
| 1 | 0 | 1 | 5 | stability_prior_bayes | +0.0122 [+0.0063, +0.0182] NEGLIGIBLE | +0.0134 [+0.0077, +0.0191] NEGLIGIBLE | **NEGLIGIBLE** | +1.2675 | +312.5390 | +0.0122 |
| 1 | 0 | 2 | 1 | stability_prior_bayes | +0.0411 [+0.0308, +0.0514] MEANINGFUL | +0.0478 [+0.0370, +0.0585] MEANINGFUL | **MEANINGFUL** | +0.3102 | +3.8234 | +0.0411 |
| 1 | 0 | 2 | 5 | stability_prior_bayes | +0.0106 [+0.0046, +0.0167] NEGLIGIBLE | +0.0137 [+0.0083, +0.0191] NEGLIGIBLE | **NEGLIGIBLE** | +0.5538 | +13.0991 | +0.0106 |
| 1 | 0 | 3 | 1 | stability_prior_bayes | +0.0463 [+0.0372, +0.0554] MEANINGFUL | +0.0395 [+0.0303, +0.0487] MEANINGFUL | **MEANINGFUL** | +0.1817 | +0.4228 | +0.0463 |
| 1 | 0 | 3 | 5 | stability_prior_bayes | +0.0097 [+0.0037, +0.0157] NEGLIGIBLE | +0.0145 [+0.0094, +0.0196] NEGLIGIBLE | **NEGLIGIBLE** | +0.3153 | +0.6118 | +0.0097 |
| 1 | 0 | 5 | 1 | stability_prior_bayes | +0.0319 [+0.0228, +0.0410] MEANINGFUL | +0.0250 [+0.0163, +0.0336] INCONCLUSIVE | **DISCORDANT** | +0.0874 | +0.1939 | +0.0319 |
| 1 | 0 | 5 | 5 | stability_prior_bayes | +0.0085 [+0.0031, +0.0139] NEGLIGIBLE | +0.0117 [+0.0067, +0.0167] NEGLIGIBLE | **NEGLIGIBLE** | +0.1521 | +0.2227 | +0.0085 |
| 1 | 0 | 10 | 1 | stability_prior_bayes | +0.0175 [+0.0111, +0.0240] INCONCLUSIVE | +0.0183 [+0.0119, +0.0247] INCONCLUSIVE | **INCONCLUSIVE** | +0.0329 | +0.0861 | +0.0175 |
| 1 | 0 | 10 | 5 | stability_prior_bayes | +0.0071 [+0.0025, +0.0117] NEGLIGIBLE | +0.0084 [+0.0042, +0.0126] NEGLIGIBLE | **NEGLIGIBLE** | +0.0490 | +0.0847 | +0.0071 |
| 1 | 0 | 20 | 1 | stability_prior_bayes | +0.0051 [+0.0011, +0.0091] NEGLIGIBLE | +0.0032 [-0.0008, +0.0072] NEGLIGIBLE | **NEGLIGIBLE** | +0.0063 | +0.0337 | +0.0051 |
| 1 | 0 | 20 | 5 | stability_prior_bayes | +0.0020 [-0.0013, +0.0054] NEGLIGIBLE | +0.0040 [+0.0007, +0.0073] NEGLIGIBLE | **NEGLIGIBLE** | +0.0104 | +0.0336 | +0.0020 |
| 4 | 0 | 1 | 1 | stability_prior_bayes | +0.0221 [+0.0129, +0.0313] INCONCLUSIVE | +0.0268 [+0.0172, +0.0365] INCONCLUSIVE | **INCONCLUSIVE** | +0.2871 | +119.2293 | +0.0221 |
| 4 | 0 | 1 | 5 | stability_prior_bayes | +0.0152 [+0.0091, +0.0213] INCONCLUSIVE | +0.0128 [+0.0069, +0.0186] NEGLIGIBLE | **DISCORDANT** | +0.4688 | +289.9107 | +0.0152 |
| 4 | 0 | 2 | 1 | stability_prior_bayes | +0.0228 [+0.0149, +0.0307] INCONCLUSIVE | +0.0242 [+0.0163, +0.0320] INCONCLUSIVE | **INCONCLUSIVE** | +0.1197 | +1.4059 | +0.0228 |
| 4 | 0 | 2 | 5 | stability_prior_bayes | +0.0094 [+0.0042, +0.0146] NEGLIGIBLE | +0.0094 [+0.0045, +0.0142] NEGLIGIBLE | **NEGLIGIBLE** | +0.2150 | +1.7113 | +0.0094 |
| 4 | 0 | 3 | 1 | stability_prior_bayes | +0.0261 [+0.0194, +0.0328] INCONCLUSIVE | +0.0205 [+0.0137, +0.0274] INCONCLUSIVE | **INCONCLUSIVE** | +0.0819 | +0.3419 | +0.0261 |
| 4 | 0 | 3 | 5 | stability_prior_bayes | +0.0083 [+0.0034, +0.0131] NEGLIGIBLE | +0.0110 [+0.0068, +0.0152] NEGLIGIBLE | **NEGLIGIBLE** | +0.1319 | +0.4150 | +0.0083 |
| 4 | 0 | 5 | 1 | stability_prior_bayes | +0.0154 [+0.0089, +0.0218] INCONCLUSIVE | +0.0134 [+0.0070, +0.0197] NEGLIGIBLE | **DISCORDANT** | +0.0381 | +0.1550 | +0.0154 |
| 4 | 0 | 5 | 5 | stability_prior_bayes | +0.0043 [-0.0004, +0.0090] NEGLIGIBLE | +0.0071 [+0.0029, +0.0113] NEGLIGIBLE | **NEGLIGIBLE** | +0.0626 | +0.1609 | +0.0043 |
| 4 | 0 | 10 | 1 | stability_prior_bayes | +0.0115 [+0.0068, +0.0162] NEGLIGIBLE | +0.0100 [+0.0052, +0.0148] NEGLIGIBLE | **NEGLIGIBLE** | +0.0195 | +0.0730 | +0.0115 |
| 4 | 0 | 10 | 5 | stability_prior_bayes | +0.0062 [+0.0030, +0.0095] NEGLIGIBLE | +0.0052 [+0.0019, +0.0086] NEGLIGIBLE | **NEGLIGIBLE** | +0.0275 | +0.0763 | +0.0062 |
| 4 | 0 | 20 | 1 | stability_prior_bayes | +0.0040 [+0.0008, +0.0072] NEGLIGIBLE | +0.0012 [-0.0021, +0.0044] NEGLIGIBLE | **NEGLIGIBLE** | +0.0047 | +0.0349 | +0.0040 |
| 4 | 0 | 20 | 5 | stability_prior_bayes | +0.0015 [-0.0012, +0.0042] NEGLIGIBLE | +0.0024 [-0.0005, +0.0052] NEGLIGIBLE | **NEGLIGIBLE** | +0.0061 | +0.0314 | +0.0015 |

### E-LIB

| r | K | n | h | frontier | R1: mean [interval] class | R2: mean [interval] class | confirmed | vs Stage-0 frontier (R1) | vs strict (R1) | vs stability (R1) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 2 | 1 | 1 | stability_prior_bayes | +0.0564 [+0.0457, +0.0670] MEANINGFUL | +0.0528 [+0.0429, +0.0627] MEANINGFUL | **MEANINGFUL** | +1.7348 | +24351.4265 | +0.0564 |
| 0.25 | 2 | 1 | 5 | stability_prior_bayes | +0.0486 [+0.0398, +0.0574] MEANINGFUL | +0.0454 [+0.0374, +0.0534] MEANINGFUL | **MEANINGFUL** | +4.3242 | +1388.0400 | +0.0486 |
| 0.25 | 2 | 2 | 1 | stability_prior_bayes | +0.0608 [+0.0486, +0.0731] MEANINGFUL | +0.0640 [+0.0518, +0.0761] MEANINGFUL | **MEANINGFUL** | +0.5408 | +4.0250 | +0.0608 |
| 0.25 | 2 | 2 | 5 | stability_prior_bayes | +0.0494 [+0.0402, +0.0585] MEANINGFUL | +0.0506 [+0.0421, +0.0591] MEANINGFUL | **MEANINGFUL** | +0.9222 | +0.9222 | +0.0494 |
| 0.25 | 2 | 3 | 1 | stability_prior_bayes | +0.0585 [+0.0464, +0.0707] MEANINGFUL | +0.0567 [+0.0443, +0.0691] MEANINGFUL | **MEANINGFUL** | +0.2893 | +0.5184 | +0.0585 |
| 0.25 | 2 | 3 | 5 | stability_prior_bayes | +0.0480 [+0.0398, +0.0562] MEANINGFUL | +0.0416 [+0.0334, +0.0499] MEANINGFUL | **MEANINGFUL** | +0.5159 | +0.6159 | +0.0480 |
| 0.25 | 2 | 5 | 1 | stability_prior_bayes | +0.0547 [+0.0429, +0.0664] MEANINGFUL | +0.0483 [+0.0366, +0.0600] MEANINGFUL | **MEANINGFUL** | +0.1271 | +0.2451 | +0.0547 |
| 0.25 | 2 | 5 | 5 | stability_prior_bayes | +0.0336 [+0.0250, +0.0422] MEANINGFUL | +0.0316 [+0.0234, +0.0397] MEANINGFUL | **MEANINGFUL** | +0.2002 | +0.2518 | +0.0336 |
| 0.25 | 2 | 10 | 1 | stability_prior_bayes | +0.0458 [+0.0357, +0.0559] MEANINGFUL | +0.0483 [+0.0379, +0.0587] MEANINGFUL | **MEANINGFUL** | +0.0607 | +0.1230 | +0.0458 |
| 0.25 | 2 | 10 | 5 | stability_prior_bayes | +0.0182 [+0.0113, +0.0251] INCONCLUSIVE | +0.0196 [+0.0120, +0.0272] INCONCLUSIVE | **INCONCLUSIVE** | +0.0498 | +0.0939 | +0.0182 |
| 0.25 | 2 | 20 | 1 | stability_prior_bayes | +0.0214 [+0.0136, +0.0293] INCONCLUSIVE | +0.0189 [+0.0112, +0.0267] INCONCLUSIVE | **INCONCLUSIVE** | +0.0225 | +0.0435 | +0.0214 |
| 0.25 | 2 | 20 | 5 | stability_prior_bayes | +0.0090 [+0.0046, +0.0134] NEGLIGIBLE | +0.0112 [+0.0066, +0.0158] NEGLIGIBLE | **NEGLIGIBLE** | +0.0118 | +0.0293 | +0.0090 |
| 0.25 | 4 | 1 | 1 | stability_prior_bayes | +0.0707 [+0.0575, +0.0838] MEANINGFUL | +0.0735 [+0.0610, +0.0859] MEANINGFUL | **MEANINGFUL** | +1.7094 | +1476.1147 | +0.0707 |
| 0.25 | 4 | 1 | 5 | stability_prior_bayes | +0.0156 [+0.0106, +0.0206] INCONCLUSIVE | +0.0073 [+0.0020, +0.0127] NEGLIGIBLE | **DISCORDANT** | +4.1851 | +963.8960 | +0.0156 |
| 0.25 | 4 | 2 | 1 | stability_prior_bayes | +0.0614 [+0.0490, +0.0738] MEANINGFUL | +0.0629 [+0.0505, +0.0753] MEANINGFUL | **MEANINGFUL** | +0.5194 | +4.1404 | +0.0614 |
| 0.25 | 4 | 2 | 5 | stability_prior_bayes | +0.0169 [+0.0120, +0.0218] INCONCLUSIVE | +0.0122 [+0.0066, +0.0178] NEGLIGIBLE | **DISCORDANT** | +1.0942 | +1.0942 | +0.0169 |
| 0.25 | 4 | 3 | 1 | stability_prior_bayes | +0.0527 [+0.0408, +0.0646] MEANINGFUL | +0.0563 [+0.0446, +0.0680] MEANINGFUL | **MEANINGFUL** | +0.2875 | +0.5128 | +0.0527 |
| 0.25 | 4 | 3 | 5 | stability_prior_bayes | +0.0179 [+0.0128, +0.0229] INCONCLUSIVE | +0.0113 [+0.0059, +0.0168] NEGLIGIBLE | **DISCORDANT** | +0.5212 | +0.5534 | +0.0179 |
| 0.25 | 4 | 5 | 1 | stability_prior_bayes | +0.0429 [+0.0326, +0.0532] MEANINGFUL | +0.0360 [+0.0256, +0.0464] MEANINGFUL | **MEANINGFUL** | +0.1144 | +0.2332 | +0.0429 |
| 0.25 | 4 | 5 | 5 | stability_prior_bayes | +0.0150 [+0.0101, +0.0199] NEGLIGIBLE | +0.0125 [+0.0068, +0.0182] NEGLIGIBLE | **NEGLIGIBLE** | +0.2080 | +0.2928 | +0.0150 |
| 0.25 | 4 | 10 | 1 | stability_prior_bayes | +0.0280 [+0.0201, +0.0360] MEANINGFUL | +0.0266 [+0.0184, +0.0348] INCONCLUSIVE | **DISCORDANT** | +0.0458 | +0.1087 | +0.0280 |
| 0.25 | 4 | 10 | 5 | stability_prior_bayes | +0.0089 [+0.0046, +0.0132] NEGLIGIBLE | +0.0137 [+0.0090, +0.0183] NEGLIGIBLE | **NEGLIGIBLE** | +0.0569 | +0.0973 | +0.0089 |
| 0.25 | 4 | 20 | 1 | stability_prior_bayes | +0.0124 [+0.0068, +0.0180] NEGLIGIBLE | +0.0105 [+0.0055, +0.0156] NEGLIGIBLE | **NEGLIGIBLE** | +0.0146 | +0.0372 | +0.0124 |
| 0.25 | 4 | 20 | 5 | stability_prior_bayes | +0.0068 [+0.0036, +0.0100] NEGLIGIBLE | +0.0039 [-0.0007, +0.0085] NEGLIGIBLE | **NEGLIGIBLE** | +0.0161 | +0.0365 | +0.0068 |
| 0.25 | 8 | 1 | 1 | stability_prior_bayes | +0.0736 [+0.0606, +0.0866] MEANINGFUL | +0.0735 [+0.0610, +0.0860] MEANINGFUL | **MEANINGFUL** | +1.7089 | +19668.5272 | +0.0736 |
| 0.25 | 8 | 1 | 5 | stability_prior_bayes | +0.0107 [+0.0058, +0.0156] NEGLIGIBLE | +0.0079 [+0.0035, +0.0124] NEGLIGIBLE | **NEGLIGIBLE** | +4.1988 | +306.5649 | +0.0107 |
| 0.25 | 8 | 2 | 1 | stability_prior_bayes | +0.0679 [+0.0556, +0.0802] MEANINGFUL | +0.0620 [+0.0496, +0.0745] MEANINGFUL | **MEANINGFUL** | +0.5256 | +4.7226 | +0.0679 |
| 0.25 | 8 | 2 | 5 | stability_prior_bayes | +0.0091 [+0.0039, +0.0144] NEGLIGIBLE | +0.0110 [+0.0060, +0.0160] NEGLIGIBLE | **NEGLIGIBLE** | +0.9172 | +2.5482 | +0.0091 |
| 0.25 | 8 | 3 | 1 | stability_prior_bayes | +0.0491 [+0.0378, +0.0605] MEANINGFUL | +0.0538 [+0.0421, +0.0656] MEANINGFUL | **MEANINGFUL** | +0.2792 | +0.5061 | +0.0491 |
| 0.25 | 8 | 3 | 5 | stability_prior_bayes | +0.0143 [+0.0099, +0.0187] NEGLIGIBLE | +0.0087 [+0.0037, +0.0137] NEGLIGIBLE | **NEGLIGIBLE** | +0.5119 | +0.5317 | +0.0143 |
| 0.25 | 8 | 5 | 1 | stability_prior_bayes | +0.0425 [+0.0326, +0.0525] MEANINGFUL | +0.0362 [+0.0263, +0.0460] MEANINGFUL | **MEANINGFUL** | +0.1152 | +0.2323 | +0.0425 |
| 0.25 | 8 | 5 | 5 | stability_prior_bayes | +0.0121 [+0.0073, +0.0169] NEGLIGIBLE | +0.0106 [+0.0057, +0.0155] NEGLIGIBLE | **NEGLIGIBLE** | +0.2095 | +0.2976 | +0.0121 |
| 0.25 | 8 | 10 | 1 | stability_prior_bayes | +0.0271 [+0.0196, +0.0345] INCONCLUSIVE | +0.0230 [+0.0160, +0.0300] INCONCLUSIVE | **INCONCLUSIVE** | +0.0438 | +0.1038 | +0.0271 |
| 0.25 | 8 | 10 | 5 | stability_prior_bayes | +0.0082 [+0.0038, +0.0127] NEGLIGIBLE | +0.0096 [+0.0049, +0.0143] NEGLIGIBLE | **NEGLIGIBLE** | +0.0601 | +0.1013 | +0.0082 |
| 0.25 | 8 | 20 | 1 | stability_prior_bayes | +0.0086 [+0.0036, +0.0137] NEGLIGIBLE | +0.0057 [+0.0011, +0.0104] NEGLIGIBLE | **NEGLIGIBLE** | +0.0118 | +0.0335 | +0.0086 |
| 0.25 | 8 | 20 | 5 | stability_prior_bayes | +0.0051 [+0.0012, +0.0090] NEGLIGIBLE | +0.0048 [+0.0007, +0.0090] NEGLIGIBLE | **NEGLIGIBLE** | +0.0171 | +0.0377 | +0.0051 |
| 1 | 2 | 1 | 1 | stability_prior_bayes | +0.0705 [+0.0581, +0.0829] MEANINGFUL | +0.0645 [+0.0527, +0.0764] MEANINGFUL | **MEANINGFUL** | +0.8506 | +918.2080 | +0.0705 |
| 1 | 2 | 1 | 5 | stability_prior_bayes | +0.0506 [+0.0417, +0.0596] MEANINGFUL | +0.0470 [+0.0391, +0.0549] MEANINGFUL | **MEANINGFUL** | +1.3932 | +75.6337 | +0.0506 |
| 1 | 2 | 2 | 1 | stability_prior_bayes | +0.0573 [+0.0452, +0.0693] MEANINGFUL | +0.0625 [+0.0504, +0.0747] MEANINGFUL | **MEANINGFUL** | +0.3011 | +2.1959 | +0.0573 |
| 1 | 2 | 2 | 5 | stability_prior_bayes | +0.0454 [+0.0366, +0.0542] MEANINGFUL | +0.0472 [+0.0391, +0.0553] MEANINGFUL | **MEANINGFUL** | +0.5476 | +1.0304 | +0.0454 |
| 1 | 2 | 3 | 1 | stability_prior_bayes | +0.0573 [+0.0454, +0.0692] MEANINGFUL | +0.0511 [+0.0388, +0.0633] MEANINGFUL | **MEANINGFUL** | +0.1931 | +0.4402 | +0.0573 |
| 1 | 2 | 3 | 5 | stability_prior_bayes | +0.0430 [+0.0349, +0.0511] MEANINGFUL | +0.0382 [+0.0303, +0.0461] MEANINGFUL | **MEANINGFUL** | +0.3337 | +0.5712 | +0.0430 |
| 1 | 2 | 5 | 1 | stability_prior_bayes | +0.0521 [+0.0408, +0.0634] MEANINGFUL | +0.0460 [+0.0347, +0.0574] MEANINGFUL | **MEANINGFUL** | +0.1030 | +0.2224 | +0.0521 |
| 1 | 2 | 5 | 5 | stability_prior_bayes | +0.0302 [+0.0218, +0.0386] MEANINGFUL | +0.0276 [+0.0197, +0.0355] INCONCLUSIVE | **DISCORDANT** | +0.1484 | +0.2077 | +0.0302 |
| 1 | 2 | 10 | 1 | stability_prior_bayes | +0.0433 [+0.0333, +0.0533] MEANINGFUL | +0.0452 [+0.0350, +0.0554] MEANINGFUL | **MEANINGFUL** | +0.0545 | +0.1175 | +0.0433 |
| 1 | 2 | 10 | 5 | stability_prior_bayes | +0.0164 [+0.0097, +0.0231] INCONCLUSIVE | +0.0176 [+0.0103, +0.0249] INCONCLUSIVE | **INCONCLUSIVE** | +0.0408 | +0.0979 | +0.0164 |
| 1 | 2 | 20 | 1 | stability_prior_bayes | +0.0201 [+0.0124, +0.0277] INCONCLUSIVE | +0.0178 [+0.0102, +0.0254] INCONCLUSIVE | **INCONCLUSIVE** | +0.0209 | +0.0417 | +0.0201 |
| 1 | 2 | 20 | 5 | stability_prior_bayes | +0.0087 [+0.0044, +0.0130] NEGLIGIBLE | +0.0106 [+0.0061, +0.0150] NEGLIGIBLE | **NEGLIGIBLE** | +0.0110 | +0.0293 | +0.0087 |
| 1 | 4 | 1 | 1 | stability_prior_bayes | +0.0617 [+0.0490, +0.0744] MEANINGFUL | +0.0616 [+0.0493, +0.0739] MEANINGFUL | **MEANINGFUL** | +0.8279 | +1636.1994 | +0.0617 |
| 1 | 4 | 1 | 5 | stability_prior_bayes | +0.0190 [+0.0141, +0.0240] INCONCLUSIVE | +0.0088 [+0.0033, +0.0144] NEGLIGIBLE | **DISCORDANT** | +1.3566 | +206.0872 | +0.0190 |
| 1 | 4 | 2 | 1 | stability_prior_bayes | +0.0513 [+0.0395, +0.0631] MEANINGFUL | +0.0541 [+0.0425, +0.0656] MEANINGFUL | **MEANINGFUL** | +0.2848 | +1.8536 | +0.0513 |
| 1 | 4 | 2 | 5 | stability_prior_bayes | +0.0175 [+0.0128, +0.0223] INCONCLUSIVE | +0.0127 [+0.0071, +0.0184] NEGLIGIBLE | **DISCORDANT** | +0.5457 | +1.0370 | +0.0175 |
| 1 | 4 | 3 | 1 | stability_prior_bayes | +0.0500 [+0.0386, +0.0614] MEANINGFUL | +0.0476 [+0.0365, +0.0587] MEANINGFUL | **MEANINGFUL** | +0.1916 | +0.4392 | +0.0500 |
| 1 | 4 | 3 | 5 | stability_prior_bayes | +0.0181 [+0.0130, +0.0232] INCONCLUSIVE | +0.0112 [+0.0058, +0.0166] NEGLIGIBLE | **DISCORDANT** | +0.3444 | +0.6402 | +0.0181 |
| 1 | 4 | 5 | 1 | stability_prior_bayes | +0.0389 [+0.0292, +0.0485] MEANINGFUL | +0.0330 [+0.0230, +0.0430] MEANINGFUL | **MEANINGFUL** | +0.0887 | +0.2102 | +0.0389 |
| 1 | 4 | 5 | 5 | stability_prior_bayes | +0.0138 [+0.0090, +0.0186] NEGLIGIBLE | +0.0110 [+0.0052, +0.0168] NEGLIGIBLE | **NEGLIGIBLE** | +0.1553 | +0.2427 | +0.0138 |
| 1 | 4 | 10 | 1 | stability_prior_bayes | +0.0258 [+0.0181, +0.0334] INCONCLUSIVE | +0.0245 [+0.0165, +0.0325] INCONCLUSIVE | **INCONCLUSIVE** | +0.0395 | +0.1024 | +0.0258 |
| 1 | 4 | 10 | 5 | stability_prior_bayes | +0.0079 [+0.0036, +0.0121] NEGLIGIBLE | +0.0131 [+0.0084, +0.0177] NEGLIGIBLE | **NEGLIGIBLE** | +0.0476 | +0.0939 | +0.0079 |
| 1 | 4 | 20 | 1 | stability_prior_bayes | +0.0116 [+0.0063, +0.0169] NEGLIGIBLE | +0.0099 [+0.0050, +0.0149] NEGLIGIBLE | **NEGLIGIBLE** | +0.0134 | +0.0356 | +0.0116 |
| 1 | 4 | 20 | 5 | stability_prior_bayes | +0.0063 [+0.0031, +0.0095] NEGLIGIBLE | +0.0040 [-0.0005, +0.0085] NEGLIGIBLE | **NEGLIGIBLE** | +0.0145 | +0.0350 | +0.0063 |
| 1 | 8 | 1 | 1 | stability_prior_bayes | +0.0635 [+0.0510, +0.0760] MEANINGFUL | +0.0607 [+0.0485, +0.0728] MEANINGFUL | **MEANINGFUL** | +0.8238 | +896.8571 | +0.0635 |
| 1 | 8 | 1 | 5 | stability_prior_bayes | +0.0124 [+0.0072, +0.0175] NEGLIGIBLE | +0.0100 [+0.0058, +0.0143] NEGLIGIBLE | **NEGLIGIBLE** | +1.3477 | +794.1147 | +0.0124 |
| 1 | 8 | 2 | 1 | stability_prior_bayes | +0.0557 [+0.0444, +0.0671] MEANINGFUL | +0.0528 [+0.0413, +0.0643] MEANINGFUL | **MEANINGFUL** | +0.2925 | +2.3205 | +0.0557 |
| 1 | 8 | 2 | 5 | stability_prior_bayes | +0.0083 [+0.0030, +0.0135] NEGLIGIBLE | +0.0109 [+0.0060, +0.0158] NEGLIGIBLE | **NEGLIGIBLE** | +0.5315 | +1.3118 | +0.0083 |
| 1 | 8 | 3 | 1 | stability_prior_bayes | +0.0464 [+0.0359, +0.0570] MEANINGFUL | +0.0451 [+0.0340, +0.0562] MEANINGFUL | **MEANINGFUL** | +0.1871 | +0.4324 | +0.0464 |
| 1 | 8 | 3 | 5 | stability_prior_bayes | +0.0119 [+0.0069, +0.0169] NEGLIGIBLE | +0.0082 [+0.0032, +0.0131] NEGLIGIBLE | **NEGLIGIBLE** | +0.3343 | +0.6144 | +0.0119 |
| 1 | 8 | 5 | 1 | stability_prior_bayes | +0.0391 [+0.0298, +0.0484] MEANINGFUL | +0.0314 [+0.0222, +0.0406] MEANINGFUL | **MEANINGFUL** | +0.0911 | +0.2082 | +0.0391 |
| 1 | 8 | 5 | 5 | stability_prior_bayes | +0.0111 [+0.0064, +0.0158] NEGLIGIBLE | +0.0100 [+0.0051, +0.0149] NEGLIGIBLE | **NEGLIGIBLE** | +0.1582 | +0.2455 | +0.0111 |
| 1 | 8 | 10 | 1 | stability_prior_bayes | +0.0254 [+0.0182, +0.0326] INCONCLUSIVE | +0.0205 [+0.0138, +0.0273] INCONCLUSIVE | **INCONCLUSIVE** | +0.0389 | +0.0997 | +0.0254 |
| 1 | 8 | 10 | 5 | stability_prior_bayes | +0.0078 [+0.0033, +0.0122] NEGLIGIBLE | +0.0092 [+0.0046, +0.0138] NEGLIGIBLE | **NEGLIGIBLE** | +0.0510 | +0.0969 | +0.0078 |
| 1 | 8 | 20 | 1 | stability_prior_bayes | +0.0078 [+0.0029, +0.0127] NEGLIGIBLE | +0.0049 [+0.0004, +0.0094] NEGLIGIBLE | **NEGLIGIBLE** | +0.0105 | +0.0322 | +0.0078 |
| 1 | 8 | 20 | 5 | stability_prior_bayes | +0.0048 [+0.0009, +0.0086] NEGLIGIBLE | +0.0047 [+0.0006, +0.0088] NEGLIGIBLE | **NEGLIGIBLE** | +0.0154 | +0.0369 | +0.0048 |
| 4 | 2 | 1 | 1 | stability_prior_bayes | +0.0802 [+0.0662, +0.0943] MEANINGFUL | +0.0651 [+0.0519, +0.0783] MEANINGFUL | **MEANINGFUL** | +0.3346 | +7634.2905 | +0.0802 |
| 4 | 2 | 1 | 5 | stability_prior_bayes | +0.0358 [+0.0279, +0.0438] MEANINGFUL | +0.0364 [+0.0296, +0.0432] MEANINGFUL | **MEANINGFUL** | +0.4343 | +1060.7609 | +0.0358 |
| 4 | 2 | 2 | 1 | stability_prior_bayes | +0.0382 [+0.0277, +0.0487] MEANINGFUL | +0.0452 [+0.0350, +0.0554] MEANINGFUL | **MEANINGFUL** | +0.1129 | +1.0182 | +0.0382 |
| 4 | 2 | 2 | 5 | stability_prior_bayes | +0.0265 [+0.0196, +0.0334] INCONCLUSIVE | +0.0278 [+0.0217, +0.0339] MEANINGFUL | **DISCORDANT** | +0.1845 | +1.3833 | +0.0265 |
| 4 | 2 | 3 | 1 | stability_prior_bayes | +0.0374 [+0.0278, +0.0469] MEANINGFUL | +0.0265 [+0.0167, +0.0362] INCONCLUSIVE | **DISCORDANT** | +0.0796 | +0.3457 | +0.0374 |
| 4 | 2 | 3 | 5 | stability_prior_bayes | +0.0246 [+0.0185, +0.0307] INCONCLUSIVE | +0.0193 [+0.0129, +0.0256] INCONCLUSIVE | **INCONCLUSIVE** | +0.1206 | +0.3530 | +0.0246 |
| 4 | 2 | 5 | 1 | stability_prior_bayes | +0.0347 [+0.0257, +0.0438] MEANINGFUL | +0.0318 [+0.0229, +0.0406] MEANINGFUL | **MEANINGFUL** | +0.0514 | +0.1668 | +0.0347 |
| 4 | 2 | 5 | 5 | stability_prior_bayes | +0.0173 [+0.0108, +0.0238] INCONCLUSIVE | +0.0128 [+0.0067, +0.0189] NEGLIGIBLE | **DISCORDANT** | +0.0601 | +0.1609 | +0.0173 |
| 4 | 2 | 10 | 1 | stability_prior_bayes | +0.0289 [+0.0206, +0.0371] MEANINGFUL | +0.0301 [+0.0216, +0.0386] MEANINGFUL | **MEANINGFUL** | +0.0328 | +0.0981 | +0.0289 |
| 4 | 2 | 10 | 5 | stability_prior_bayes | +0.0097 [+0.0046, +0.0147] NEGLIGIBLE | +0.0102 [+0.0047, +0.0158] NEGLIGIBLE | **NEGLIGIBLE** | +0.0191 | +0.0671 | +0.0097 |
| 4 | 2 | 20 | 1 | stability_prior_bayes | +0.0144 [+0.0079, +0.0210] INCONCLUSIVE | +0.0124 [+0.0059, +0.0190] NEGLIGIBLE | **DISCORDANT** | +0.0148 | +0.0360 | +0.0144 |
| 4 | 2 | 20 | 5 | stability_prior_bayes | +0.0057 [+0.0021, +0.0092] NEGLIGIBLE | +0.0068 [+0.0031, +0.0105] NEGLIGIBLE | **NEGLIGIBLE** | +0.0067 | +0.0282 | +0.0057 |
| 4 | 4 | 1 | 1 | stability_prior_bayes | +0.0449 [+0.0351, +0.0546] MEANINGFUL | +0.0320 [+0.0228, +0.0412] MEANINGFUL | **MEANINGFUL** | +0.3211 | +233.2654 | +0.0449 |
| 4 | 4 | 1 | 5 | stability_prior_bayes | +0.0289 [+0.0229, +0.0349] MEANINGFUL | +0.0181 [+0.0111, +0.0251] INCONCLUSIVE | **DISCORDANT** | +0.4800 | +833.9293 | +0.0289 |
| 4 | 4 | 2 | 1 | stability_prior_bayes | +0.0224 [+0.0134, +0.0315] INCONCLUSIVE | +0.0351 [+0.0264, +0.0438] MEANINGFUL | **DISCORDANT** | +0.1038 | +1063.6628 | +0.0224 |
| 4 | 4 | 2 | 5 | stability_prior_bayes | +0.0194 [+0.0143, +0.0246] INCONCLUSIVE | +0.0162 [+0.0097, +0.0226] INCONCLUSIVE | **INCONCLUSIVE** | +0.2109 | +2282.7400 | +0.0194 |
| 4 | 4 | 3 | 1 | stability_prior_bayes | +0.0288 [+0.0197, +0.0379] INCONCLUSIVE | +0.0223 [+0.0139, +0.0307] INCONCLUSIVE | **INCONCLUSIVE** | +0.0779 | +0.3394 | +0.0288 |
| 4 | 4 | 3 | 5 | stability_prior_bayes | +0.0193 [+0.0143, +0.0242] INCONCLUSIVE | +0.0107 [+0.0051, +0.0164] NEGLIGIBLE | **DISCORDANT** | +0.1429 | +0.3929 | +0.0193 |
| 4 | 4 | 5 | 1 | stability_prior_bayes | +0.0234 [+0.0159, +0.0309] INCONCLUSIVE | +0.0211 [+0.0135, +0.0287] INCONCLUSIVE | **INCONCLUSIVE** | +0.0417 | +0.1601 | +0.0234 |
| 4 | 4 | 5 | 5 | stability_prior_bayes | +0.0113 [+0.0069, +0.0157] NEGLIGIBLE | +0.0107 [+0.0049, +0.0165] NEGLIGIBLE | **NEGLIGIBLE** | +0.0678 | +0.1814 | +0.0113 |
| 4 | 4 | 10 | 1 | stability_prior_bayes | +0.0166 [+0.0104, +0.0228] INCONCLUSIVE | +0.0164 [+0.0100, +0.0229] INCONCLUSIVE | **INCONCLUSIVE** | +0.0225 | +0.0878 | +0.0166 |
| 4 | 4 | 10 | 5 | stability_prior_bayes | +0.0051 [+0.0014, +0.0088] NEGLIGIBLE | +0.0081 [+0.0038, +0.0124] NEGLIGIBLE | **NEGLIGIBLE** | +0.0237 | +0.0810 | +0.0051 |
| 4 | 4 | 20 | 1 | stability_prior_bayes | +0.0102 [+0.0057, +0.0147] NEGLIGIBLE | +0.0075 [+0.0031, +0.0118] NEGLIGIBLE | **NEGLIGIBLE** | +0.0111 | +0.0332 | +0.0102 |
| 4 | 4 | 20 | 5 | stability_prior_bayes | +0.0051 [+0.0021, +0.0080] NEGLIGIBLE | +0.0030 [-0.0012, +0.0071] NEGLIGIBLE | **NEGLIGIBLE** | +0.0090 | +0.0309 | +0.0051 |
| 4 | 8 | 1 | 1 | stability_prior_bayes | +0.0393 [+0.0300, +0.0485] MEANINGFUL | +0.0264 [+0.0173, +0.0355] INCONCLUSIVE | **DISCORDANT** | +0.3171 | +4626.2857 | +0.0393 |
| 4 | 8 | 1 | 5 | stability_prior_bayes | +0.0180 [+0.0116, +0.0244] INCONCLUSIVE | +0.0163 [+0.0107, +0.0219] INCONCLUSIVE | **INCONCLUSIVE** | +0.4718 | +917.3335 | +0.0180 |
| 4 | 8 | 2 | 1 | stability_prior_bayes | +0.0311 [+0.0223, +0.0399] MEANINGFUL | +0.0310 [+0.0229, +0.0391] MEANINGFUL | **MEANINGFUL** | +0.1133 | +1.6240 | +0.0311 |
| 4 | 8 | 2 | 5 | stability_prior_bayes | +0.0112 [+0.0052, +0.0171] NEGLIGIBLE | +0.0138 [+0.0086, +0.0189] NEGLIGIBLE | **NEGLIGIBLE** | +0.2025 | +1.5842 | +0.0112 |
| 4 | 8 | 3 | 1 | stability_prior_bayes | +0.0248 [+0.0171, +0.0325] INCONCLUSIVE | +0.0183 [+0.0101, +0.0265] INCONCLUSIVE | **INCONCLUSIVE** | +0.0775 | +0.3385 | +0.0248 |
| 4 | 8 | 3 | 5 | stability_prior_bayes | +0.0124 [+0.0070, +0.0179] NEGLIGIBLE | +0.0068 [+0.0022, +0.0115] NEGLIGIBLE | **NEGLIGIBLE** | +0.1388 | +0.3800 | +0.0124 |
| 4 | 8 | 5 | 1 | stability_prior_bayes | +0.0214 [+0.0143, +0.0284] INCONCLUSIVE | +0.0189 [+0.0121, +0.0258] INCONCLUSIVE | **INCONCLUSIVE** | +0.0405 | +0.1574 | +0.0214 |
| 4 | 8 | 5 | 5 | stability_prior_bayes | +0.0094 [+0.0044, +0.0144] NEGLIGIBLE | +0.0098 [+0.0053, +0.0143] NEGLIGIBLE | **NEGLIGIBLE** | +0.0717 | +0.1869 | +0.0094 |
| 4 | 8 | 10 | 1 | stability_prior_bayes | +0.0181 [+0.0126, +0.0236] INCONCLUSIVE | +0.0141 [+0.0088, +0.0194] NEGLIGIBLE | **DISCORDANT** | +0.0240 | +0.0883 | +0.0181 |
| 4 | 8 | 10 | 5 | stability_prior_bayes | +0.0060 [+0.0021, +0.0100] NEGLIGIBLE | +0.0075 [+0.0036, +0.0115] NEGLIGIBLE | **NEGLIGIBLE** | +0.0255 | +0.0790 | +0.0060 |
| 4 | 8 | 20 | 1 | stability_prior_bayes | +0.0051 [+0.0010, +0.0092] NEGLIGIBLE | +0.0026 [-0.0013, +0.0065] NEGLIGIBLE | **NEGLIGIBLE** | +0.0062 | +0.0286 | +0.0051 |
| 4 | 8 | 20 | 5 | stability_prior_bayes | +0.0037 [+0.0002, +0.0071] NEGLIGIBLE | +0.0027 [-0.0010, +0.0065] NEGLIGIBLE | **NEGLIGIBLE** | +0.0092 | +0.0313 | +0.0037 |

## Secondary: finite library - continuous-prior Bayes

E-CONT: library (mismatched) - continuous (matched). E-LIB: library (matched) - continuous (mismatched).

| condition | r | K | n | h | R1: mean [interval] class | R2: mean [interval] class | confirmed |
|---|---|---|---|---|---|---|---|
| E-CONT | 0.25 | 2 | 1 | 1 | -0.0094 [-0.0155, -0.0033] EQUIVALENT | -0.0070 [-0.0123, -0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 2 | 1 | 5 | -0.0404 [-0.0572, -0.0237] DISTINGUISHABLE | -0.0260 [-0.0373, -0.0147] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 0.25 | 2 | 2 | 1 | -0.0263 [-0.0359, -0.0167] INCONCLUSIVE | -0.0260 [-0.0360, -0.0161] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 2 | 5 | -0.0495 [-0.0689, -0.0301] DISTINGUISHABLE | -0.0273 [-0.0402, -0.0144] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 0.25 | 2 | 3 | 1 | -0.0344 [-0.0471, -0.0218] DISTINGUISHABLE | -0.0315 [-0.0438, -0.0192] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 0.25 | 2 | 3 | 5 | -0.0546 [-0.0740, -0.0352] DISTINGUISHABLE | -0.0296 [-0.0432, -0.0159] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 0.25 | 2 | 5 | 1 | -0.0595 [-0.0770, -0.0421] DISTINGUISHABLE | -0.0443 [-0.0579, -0.0307] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 2 | 5 | 5 | -0.0788 [-0.1066, -0.0510] DISTINGUISHABLE | -0.0438 [-0.0627, -0.0250] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 2 | 10 | 1 | -0.0657 [-0.0869, -0.0446] DISTINGUISHABLE | -0.0502 [-0.0677, -0.0326] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 2 | 10 | 5 | -0.0782 [-0.1058, -0.0505] DISTINGUISHABLE | -0.0490 [-0.0693, -0.0286] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 2 | 20 | 1 | -0.0864 [-0.1086, -0.0642] DISTINGUISHABLE | -0.0718 [-0.0926, -0.0510] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 2 | 20 | 5 | -0.0879 [-0.1178, -0.0580] DISTINGUISHABLE | -0.0779 [-0.1133, -0.0425] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 0.25 | 4 | 1 | 1 | -0.0061 [-0.0095, -0.0026] EQUIVALENT | -0.0054 [-0.0089, -0.0019] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 1 | 5 | -0.0010 [-0.0029, +0.0009] EQUIVALENT | -0.0000 [-0.0009, +0.0009] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 2 | 1 | -0.0030 [-0.0060, +0.0001] EQUIVALENT | -0.0039 [-0.0084, +0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 2 | 5 | -0.0020 [-0.0043, +0.0003] EQUIVALENT | -0.0004 [-0.0016, +0.0007] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 3 | 1 | +0.0004 [-0.0025, +0.0033] EQUIVALENT | -0.0030 [-0.0061, +0.0002] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 3 | 5 | -0.0018 [-0.0040, +0.0004] EQUIVALENT | +0.0001 [-0.0011, +0.0013] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 5 | 1 | -0.0041 [-0.0084, +0.0001] EQUIVALENT | -0.0034 [-0.0070, +0.0002] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 5 | 5 | -0.0050 [-0.0094, -0.0005] EQUIVALENT | -0.0014 [-0.0036, +0.0009] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 10 | 1 | -0.0037 [-0.0085, +0.0012] EQUIVALENT | -0.0047 [-0.0089, -0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 10 | 5 | -0.0044 [-0.0093, +0.0005] EQUIVALENT | -0.0006 [-0.0035, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 20 | 1 | -0.0074 [-0.0121, -0.0026] EQUIVALENT | -0.0121 [-0.0182, -0.0060] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 20 | 5 | -0.0054 [-0.0112, +0.0005] EQUIVALENT | -0.0066 [-0.0146, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 1 | 1 | -0.0058 [-0.0091, -0.0025] EQUIVALENT | -0.0054 [-0.0088, -0.0021] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 1 | 5 | -0.0006 [-0.0026, +0.0015] EQUIVALENT | -0.0006 [-0.0023, +0.0011] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 2 | 1 | -0.0024 [-0.0053, +0.0006] EQUIVALENT | -0.0031 [-0.0070, +0.0008] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 2 | 5 | -0.0015 [-0.0036, +0.0007] EQUIVALENT | -0.0011 [-0.0027, +0.0005] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 3 | 1 | +0.0005 [-0.0022, +0.0032] EQUIVALENT | -0.0028 [-0.0057, +0.0001] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 3 | 5 | -0.0011 [-0.0031, +0.0010] EQUIVALENT | -0.0007 [-0.0023, +0.0009] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 5 | 1 | -0.0026 [-0.0061, +0.0010] EQUIVALENT | -0.0025 [-0.0056, +0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 5 | 5 | -0.0032 [-0.0068, +0.0003] EQUIVALENT | -0.0016 [-0.0036, +0.0005] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 10 | 1 | -0.0022 [-0.0061, +0.0016] EQUIVALENT | -0.0034 [-0.0066, -0.0002] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 10 | 5 | -0.0030 [-0.0068, +0.0009] EQUIVALENT | -0.0006 [-0.0029, +0.0018] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 20 | 1 | -0.0042 [-0.0076, -0.0008] EQUIVALENT | -0.0074 [-0.0118, -0.0031] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 20 | 5 | -0.0032 [-0.0076, +0.0013] EQUIVALENT | -0.0045 [-0.0107, +0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 2 | 1 | 1 | -0.0247 [-0.0349, -0.0146] INCONCLUSIVE | -0.0161 [-0.0247, -0.0075] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 1 | 5 | -0.0497 [-0.0699, -0.0295] DISTINGUISHABLE | -0.0317 [-0.0448, -0.0186] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 1 | 2 | 2 | 1 | -0.0385 [-0.0506, -0.0265] DISTINGUISHABLE | -0.0342 [-0.0461, -0.0223] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 2 | 5 | -0.0587 [-0.0806, -0.0369] DISTINGUISHABLE | -0.0320 [-0.0470, -0.0170] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 1 | 2 | 3 | 1 | -0.0421 [-0.0566, -0.0276] DISTINGUISHABLE | -0.0358 [-0.0494, -0.0222] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 3 | 5 | -0.0604 [-0.0816, -0.0392] DISTINGUISHABLE | -0.0342 [-0.0493, -0.0192] INCONCLUSIVE | **DISCORDANT** |
| E-CONT | 1 | 2 | 5 | 1 | -0.0646 [-0.0834, -0.0459] DISTINGUISHABLE | -0.0484 [-0.0628, -0.0341] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 5 | 5 | -0.0840 [-0.1124, -0.0557] DISTINGUISHABLE | -0.0472 [-0.0667, -0.0276] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 10 | 1 | -0.0676 [-0.0887, -0.0465] DISTINGUISHABLE | -0.0506 [-0.0685, -0.0328] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 10 | 5 | -0.0796 [-0.1071, -0.0520] DISTINGUISHABLE | -0.0506 [-0.0710, -0.0302] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 20 | 1 | -0.0866 [-0.1090, -0.0643] DISTINGUISHABLE | -0.0722 [-0.0932, -0.0512] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 2 | 20 | 5 | -0.0875 [-0.1174, -0.0577] DISTINGUISHABLE | -0.0795 [-0.1160, -0.0430] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 1 | 4 | 1 | 1 | -0.0061 [-0.0099, -0.0022] EQUIVALENT | -0.0053 [-0.0090, -0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 1 | 5 | -0.0019 [-0.0045, +0.0006] EQUIVALENT | -0.0000 [-0.0012, +0.0011] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 2 | 1 | -0.0029 [-0.0060, +0.0002] EQUIVALENT | -0.0041 [-0.0089, +0.0008] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 2 | 5 | -0.0027 [-0.0055, +0.0000] EQUIVALENT | -0.0007 [-0.0023, +0.0010] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 3 | 1 | +0.0003 [-0.0029, +0.0034] EQUIVALENT | -0.0030 [-0.0062, +0.0003] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 3 | 5 | -0.0024 [-0.0049, +0.0002] EQUIVALENT | +0.0001 [-0.0014, +0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 5 | 1 | -0.0046 [-0.0089, -0.0003] EQUIVALENT | -0.0037 [-0.0073, -0.0000] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 5 | 5 | -0.0055 [-0.0098, -0.0012] EQUIVALENT | -0.0017 [-0.0042, +0.0007] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 10 | 1 | -0.0043 [-0.0093, +0.0007] EQUIVALENT | -0.0045 [-0.0087, -0.0003] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 10 | 5 | -0.0046 [-0.0096, +0.0004] EQUIVALENT | -0.0006 [-0.0035, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 20 | 1 | -0.0077 [-0.0125, -0.0030] EQUIVALENT | -0.0124 [-0.0185, -0.0063] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 20 | 5 | -0.0055 [-0.0114, +0.0005] EQUIVALENT | -0.0070 [-0.0154, +0.0014] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 1 | 1 | -0.0053 [-0.0088, -0.0018] EQUIVALENT | -0.0053 [-0.0087, -0.0019] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 1 | 5 | -0.0013 [-0.0036, +0.0009] EQUIVALENT | -0.0003 [-0.0021, +0.0014] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 2 | 1 | -0.0021 [-0.0050, +0.0008] EQUIVALENT | -0.0030 [-0.0071, +0.0011] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 2 | 5 | -0.0020 [-0.0045, +0.0004] EQUIVALENT | -0.0011 [-0.0029, +0.0007] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 3 | 1 | +0.0005 [-0.0022, +0.0033] EQUIVALENT | -0.0028 [-0.0057, +0.0000] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 3 | 5 | -0.0015 [-0.0038, +0.0007] EQUIVALENT | -0.0003 [-0.0021, +0.0014] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 5 | 1 | -0.0028 [-0.0064, +0.0007] EQUIVALENT | -0.0025 [-0.0056, +0.0005] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 5 | 5 | -0.0037 [-0.0071, -0.0003] EQUIVALENT | -0.0016 [-0.0037, +0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 10 | 1 | -0.0026 [-0.0065, +0.0014] EQUIVALENT | -0.0032 [-0.0064, +0.0000] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 10 | 5 | -0.0030 [-0.0069, +0.0009] EQUIVALENT | -0.0004 [-0.0028, +0.0020] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 20 | 1 | -0.0043 [-0.0077, -0.0009] EQUIVALENT | -0.0076 [-0.0120, -0.0032] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 20 | 5 | -0.0032 [-0.0077, +0.0013] EQUIVALENT | -0.0049 [-0.0113, +0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 2 | 1 | 1 | -0.2404 [-0.2845, -0.1963] DISTINGUISHABLE | -0.1752 [-0.2117, -0.1386] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 1 | 5 | -0.1586 [-0.2081, -0.1091] DISTINGUISHABLE | -0.1083 [-0.1428, -0.0738] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 2 | 1 | -0.1776 [-0.2135, -0.1417] DISTINGUISHABLE | -0.1367 [-0.1668, -0.1066] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 2 | 5 | -0.1445 [-0.1882, -0.1008] DISTINGUISHABLE | -0.0880 [-0.1202, -0.0559] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 3 | 1 | -0.1324 [-0.1645, -0.1004] DISTINGUISHABLE | -0.1037 [-0.1320, -0.0755] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 3 | 5 | -0.1214 [-0.1594, -0.0833] DISTINGUISHABLE | -0.0831 [-0.1128, -0.0534] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 5 | 1 | -0.1217 [-0.1532, -0.0901] DISTINGUISHABLE | -0.0902 [-0.1132, -0.0671] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 5 | 5 | -0.1260 [-0.1640, -0.0879] DISTINGUISHABLE | -0.0791 [-0.1068, -0.0515] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 10 | 1 | -0.0819 [-0.1051, -0.0587] DISTINGUISHABLE | -0.0624 [-0.0832, -0.0415] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 10 | 5 | -0.0944 [-0.1254, -0.0635] DISTINGUISHABLE | -0.0641 [-0.0875, -0.0407] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 20 | 1 | -0.0891 [-0.1123, -0.0660] DISTINGUISHABLE | -0.0754 [-0.0979, -0.0529] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 20 | 5 | -0.0913 [-0.1220, -0.0606] DISTINGUISHABLE | -0.0884 [-0.1299, -0.0470] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 4 | 1 | 1 | -0.0162 [-0.0245, -0.0079] INCONCLUSIVE | -0.0165 [-0.0252, -0.0078] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 1 | 5 | -0.0131 [-0.0213, -0.0049] INCONCLUSIVE | -0.0055 [-0.0105, -0.0006] EQUIVALENT | **DISCORDANT** |
| E-CONT | 4 | 4 | 2 | 1 | -0.0075 [-0.0122, -0.0027] EQUIVALENT | -0.0088 [-0.0160, -0.0016] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 2 | 5 | -0.0121 [-0.0193, -0.0050] EQUIVALENT | -0.0046 [-0.0102, +0.0010] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 3 | 1 | -0.0014 [-0.0063, +0.0035] EQUIVALENT | -0.0077 [-0.0124, -0.0030] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 3 | 5 | -0.0101 [-0.0165, -0.0037] EQUIVALENT | -0.0046 [-0.0095, +0.0003] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 5 | 1 | -0.0099 [-0.0156, -0.0043] EQUIVALENT | -0.0051 [-0.0097, -0.0005] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 5 | 5 | -0.0123 [-0.0191, -0.0055] EQUIVALENT | -0.0047 [-0.0093, -0.0001] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 10 | 1 | -0.0055 [-0.0113, +0.0003] EQUIVALENT | -0.0057 [-0.0106, -0.0009] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 10 | 5 | -0.0090 [-0.0151, -0.0030] EQUIVALENT | -0.0021 [-0.0061, +0.0018] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 20 | 1 | -0.0097 [-0.0148, -0.0047] EQUIVALENT | -0.0126 [-0.0191, -0.0062] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 4 | 20 | 5 | -0.0069 [-0.0132, -0.0006] EQUIVALENT | -0.0094 [-0.0193, +0.0005] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 1 | 1 | -0.0107 [-0.0168, -0.0046] EQUIVALENT | -0.0111 [-0.0178, -0.0045] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 1 | 5 | -0.0095 [-0.0158, -0.0033] EQUIVALENT | -0.0033 [-0.0072, +0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 2 | 1 | -0.0040 [-0.0077, -0.0004] EQUIVALENT | -0.0050 [-0.0106, +0.0006] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 2 | 5 | -0.0084 [-0.0138, -0.0031] EQUIVALENT | -0.0028 [-0.0071, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 3 | 1 | -0.0003 [-0.0041, +0.0034] EQUIVALENT | -0.0049 [-0.0084, -0.0014] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 3 | 5 | -0.0068 [-0.0116, -0.0020] EQUIVALENT | -0.0029 [-0.0066, +0.0008] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 5 | 1 | -0.0062 [-0.0104, -0.0019] EQUIVALENT | -0.0025 [-0.0060, +0.0010] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 5 | 5 | -0.0079 [-0.0129, -0.0028] EQUIVALENT | -0.0027 [-0.0063, +0.0008] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 10 | 1 | -0.0028 [-0.0072, +0.0016] EQUIVALENT | -0.0035 [-0.0070, -0.0000] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 10 | 5 | -0.0056 [-0.0102, -0.0011] EQUIVALENT | -0.0009 [-0.0040, +0.0021] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 20 | 1 | -0.0048 [-0.0084, -0.0013] EQUIVALENT | -0.0073 [-0.0118, -0.0027] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 20 | 5 | -0.0042 [-0.0089, +0.0006] EQUIVALENT | -0.0065 [-0.0140, +0.0010] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 1 | 1 | +0.0135 [+0.0094, +0.0177] EQUIVALENT | +0.0104 [+0.0063, +0.0146] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 1 | 5 | +0.0151 [+0.0093, +0.0209] INCONCLUSIVE | +0.0151 [+0.0101, +0.0201] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 2 | 1 | +0.0096 [+0.0038, +0.0154] EQUIVALENT | +0.0169 [+0.0114, +0.0224] INCONCLUSIVE | **DISCORDANT** |
| E-LIB | 0.25 | 2 | 2 | 5 | +0.0168 [+0.0109, +0.0227] INCONCLUSIVE | +0.0170 [+0.0116, +0.0223] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 3 | 1 | +0.0151 [+0.0091, +0.0211] INCONCLUSIVE | +0.0088 [+0.0026, +0.0151] EQUIVALENT | **DISCORDANT** |
| E-LIB | 0.25 | 2 | 3 | 5 | +0.0177 [+0.0126, +0.0228] INCONCLUSIVE | +0.0133 [+0.0080, +0.0186] EQUIVALENT | **DISCORDANT** |
| E-LIB | 0.25 | 2 | 5 | 1 | +0.0136 [+0.0074, +0.0197] EQUIVALENT | +0.0110 [+0.0048, +0.0171] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 5 | 5 | +0.0119 [+0.0061, +0.0178] EQUIVALENT | +0.0091 [+0.0035, +0.0147] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 10 | 1 | +0.0149 [+0.0092, +0.0207] INCONCLUSIVE | +0.0201 [+0.0139, +0.0263] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 10 | 5 | +0.0060 [+0.0011, +0.0109] EQUIVALENT | +0.0075 [+0.0020, +0.0131] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 20 | 1 | +0.0076 [+0.0025, +0.0128] EQUIVALENT | +0.0083 [+0.0029, +0.0138] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 20 | 5 | +0.0048 [+0.0012, +0.0084] EQUIVALENT | +0.0067 [+0.0031, +0.0104] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 1 | 1 | +0.0006 [-0.0021, +0.0033] EQUIVALENT | +0.0027 [+0.0002, +0.0052] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 1 | 5 | +0.0000 [-0.0008, +0.0008] EQUIVALENT | +0.0006 [-0.0004, +0.0017] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 2 | 1 | +0.0022 [-0.0006, +0.0050] EQUIVALENT | +0.0020 [-0.0006, +0.0047] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 2 | 5 | +0.0002 [-0.0008, +0.0013] EQUIVALENT | +0.0004 [-0.0005, +0.0014] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 3 | 1 | +0.0014 [-0.0014, +0.0043] EQUIVALENT | +0.0041 [+0.0015, +0.0068] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 3 | 5 | +0.0005 [-0.0007, +0.0017] EQUIVALENT | +0.0007 [-0.0004, +0.0019] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 5 | 1 | +0.0024 [-0.0002, +0.0049] EQUIVALENT | +0.0014 [-0.0013, +0.0042] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 5 | 5 | +0.0007 [-0.0004, +0.0017] EQUIVALENT | +0.0006 [-0.0011, +0.0023] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 10 | 1 | +0.0032 [+0.0006, +0.0057] EQUIVALENT | +0.0037 [+0.0007, +0.0067] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 10 | 5 | +0.0002 [-0.0015, +0.0020] EQUIVALENT | +0.0018 [-0.0004, +0.0041] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 20 | 1 | +0.0024 [-0.0003, +0.0051] EQUIVALENT | +0.0025 [-0.0000, +0.0050] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 20 | 5 | +0.0027 [+0.0009, +0.0044] EQUIVALENT | +0.0013 [-0.0013, +0.0040] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 1 | 1 | +0.0012 [-0.0015, +0.0039] EQUIVALENT | +0.0025 [-0.0001, +0.0050] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 1 | 5 | +0.0008 [-0.0009, +0.0026] EQUIVALENT | +0.0025 [+0.0007, +0.0044] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 2 | 1 | +0.0044 [+0.0018, +0.0070] EQUIVALENT | +0.0019 [-0.0008, +0.0046] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 2 | 5 | +0.0006 [-0.0012, +0.0024] EQUIVALENT | +0.0016 [-0.0003, +0.0034] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 3 | 1 | +0.0022 [-0.0004, +0.0048] EQUIVALENT | +0.0038 [+0.0011, +0.0065] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 3 | 5 | +0.0010 [-0.0007, +0.0028] EQUIVALENT | +0.0027 [+0.0009, +0.0044] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 5 | 1 | +0.0034 [+0.0010, +0.0058] EQUIVALENT | +0.0034 [+0.0010, +0.0058] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 5 | 5 | +0.0011 [-0.0007, +0.0028] EQUIVALENT | +0.0021 [+0.0003, +0.0038] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 10 | 1 | +0.0031 [+0.0010, +0.0052] EQUIVALENT | +0.0025 [+0.0003, +0.0046] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 10 | 5 | +0.0025 [+0.0003, +0.0047] EQUIVALENT | +0.0008 [-0.0012, +0.0029] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 20 | 1 | +0.0012 [-0.0009, +0.0034] EQUIVALENT | +0.0005 [-0.0015, +0.0025] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 20 | 5 | +0.0017 [-0.0007, +0.0040] EQUIVALENT | -0.0001 [-0.0024, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 1 | 1 | +0.0198 [+0.0141, +0.0255] INCONCLUSIVE | +0.0172 [+0.0117, +0.0227] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 1 | 5 | +0.0156 [+0.0097, +0.0215] INCONCLUSIVE | +0.0158 [+0.0108, +0.0208] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 2 | 1 | +0.0096 [+0.0038, +0.0155] EQUIVALENT | +0.0179 [+0.0121, +0.0238] INCONCLUSIVE | **DISCORDANT** |
| E-LIB | 1 | 2 | 2 | 5 | +0.0157 [+0.0099, +0.0215] INCONCLUSIVE | +0.0167 [+0.0115, +0.0218] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 3 | 1 | +0.0154 [+0.0094, +0.0213] INCONCLUSIVE | +0.0083 [+0.0020, +0.0145] EQUIVALENT | **DISCORDANT** |
| E-LIB | 1 | 2 | 3 | 5 | +0.0165 [+0.0115, +0.0215] INCONCLUSIVE | +0.0123 [+0.0071, +0.0175] EQUIVALENT | **DISCORDANT** |
| E-LIB | 1 | 2 | 5 | 1 | +0.0132 [+0.0072, +0.0193] EQUIVALENT | +0.0113 [+0.0052, +0.0174] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 5 | 5 | +0.0113 [+0.0056, +0.0171] EQUIVALENT | +0.0080 [+0.0025, +0.0135] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 10 | 1 | +0.0145 [+0.0088, +0.0202] INCONCLUSIVE | +0.0192 [+0.0131, +0.0254] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 10 | 5 | +0.0057 [+0.0009, +0.0105] EQUIVALENT | +0.0069 [+0.0015, +0.0123] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 20 | 1 | +0.0073 [+0.0021, +0.0124] EQUIVALENT | +0.0080 [+0.0026, +0.0134] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 20 | 5 | +0.0048 [+0.0012, +0.0083] EQUIVALENT | +0.0064 [+0.0028, +0.0100] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 1 | 1 | +0.0007 [-0.0022, +0.0035] EQUIVALENT | +0.0029 [+0.0003, +0.0054] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 1 | 5 | +0.0004 [-0.0004, +0.0012] EQUIVALENT | +0.0004 [-0.0008, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 2 | 1 | +0.0019 [-0.0010, +0.0047] EQUIVALENT | +0.0019 [-0.0007, +0.0045] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 2 | 5 | +0.0004 [-0.0006, +0.0014] EQUIVALENT | +0.0003 [-0.0008, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 3 | 1 | +0.0021 [-0.0008, +0.0049] EQUIVALENT | +0.0039 [+0.0012, +0.0065] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 3 | 5 | +0.0006 [-0.0007, +0.0018] EQUIVALENT | +0.0008 [-0.0006, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 5 | 1 | +0.0026 [+0.0000, +0.0051] EQUIVALENT | +0.0020 [-0.0007, +0.0048] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 5 | 5 | +0.0007 [-0.0003, +0.0018] EQUIVALENT | +0.0010 [-0.0009, +0.0028] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 10 | 1 | +0.0033 [+0.0007, +0.0058] EQUIVALENT | +0.0036 [+0.0006, +0.0066] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 10 | 5 | +0.0001 [-0.0017, +0.0019] EQUIVALENT | +0.0017 [-0.0006, +0.0040] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 20 | 1 | +0.0025 [-0.0002, +0.0051] EQUIVALENT | +0.0025 [-0.0000, +0.0050] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 20 | 5 | +0.0024 [+0.0007, +0.0042] EQUIVALENT | +0.0017 [-0.0010, +0.0043] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 1 | 1 | +0.0016 [-0.0011, +0.0042] EQUIVALENT | +0.0028 [+0.0002, +0.0053] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 1 | 5 | +0.0006 [-0.0012, +0.0024] EQUIVALENT | +0.0025 [+0.0008, +0.0043] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 2 | 1 | +0.0039 [+0.0014, +0.0064] EQUIVALENT | +0.0015 [-0.0011, +0.0041] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 2 | 5 | +0.0003 [-0.0016, +0.0023] EQUIVALENT | +0.0015 [-0.0002, +0.0033] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 3 | 1 | +0.0023 [-0.0002, +0.0048] EQUIVALENT | +0.0031 [+0.0005, +0.0058] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 3 | 5 | +0.0007 [-0.0012, +0.0025] EQUIVALENT | +0.0022 [+0.0005, +0.0038] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 5 | 1 | +0.0036 [+0.0012, +0.0060] EQUIVALENT | +0.0033 [+0.0009, +0.0057] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 5 | 5 | +0.0011 [-0.0007, +0.0029] EQUIVALENT | +0.0021 [+0.0003, +0.0040] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 10 | 1 | +0.0034 [+0.0013, +0.0055] EQUIVALENT | +0.0025 [+0.0004, +0.0046] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 10 | 5 | +0.0025 [+0.0003, +0.0047] EQUIVALENT | +0.0011 [-0.0009, +0.0032] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 20 | 1 | +0.0012 [-0.0010, +0.0033] EQUIVALENT | +0.0003 [-0.0017, +0.0023] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 20 | 5 | +0.0016 [-0.0008, +0.0039] EQUIVALENT | -0.0001 [-0.0024, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 1 | 1 | +0.0398 [+0.0302, +0.0494] DISTINGUISHABLE | +0.0333 [+0.0241, +0.0424] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-LIB | 4 | 2 | 1 | 5 | +0.0138 [+0.0084, +0.0192] EQUIVALENT | +0.0149 [+0.0104, +0.0194] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 2 | 1 | +0.0110 [+0.0048, +0.0172] EQUIVALENT | +0.0183 [+0.0120, +0.0245] INCONCLUSIVE | **DISCORDANT** |
| E-LIB | 4 | 2 | 2 | 5 | +0.0106 [+0.0058, +0.0153] EQUIVALENT | +0.0119 [+0.0079, +0.0159] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 3 | 1 | +0.0122 [+0.0067, +0.0177] EQUIVALENT | +0.0054 [-0.0002, +0.0111] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 3 | 5 | +0.0104 [+0.0062, +0.0146] EQUIVALENT | +0.0072 [+0.0028, +0.0116] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 5 | 1 | +0.0109 [+0.0055, +0.0163] EQUIVALENT | +0.0104 [+0.0050, +0.0158] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 5 | 5 | +0.0079 [+0.0033, +0.0126] EQUIVALENT | +0.0038 [-0.0007, +0.0083] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 10 | 1 | +0.0114 [+0.0062, +0.0165] EQUIVALENT | +0.0146 [+0.0090, +0.0201] INCONCLUSIVE | **DISCORDANT** |
| E-LIB | 4 | 2 | 10 | 5 | +0.0040 [+0.0002, +0.0078] EQUIVALENT | +0.0044 [+0.0002, +0.0086] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 20 | 1 | +0.0059 [+0.0012, +0.0106] EQUIVALENT | +0.0063 [+0.0014, +0.0111] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 20 | 5 | +0.0034 [+0.0003, +0.0064] EQUIVALENT | +0.0043 [+0.0012, +0.0074] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 1 | 1 | +0.0073 [+0.0038, +0.0107] EQUIVALENT | +0.0046 [+0.0013, +0.0079] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 1 | 5 | +0.0056 [+0.0028, +0.0085] EQUIVALENT | +0.0038 [+0.0007, +0.0069] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 2 | 1 | +0.0004 [-0.0029, +0.0037] EQUIVALENT | +0.0053 [+0.0021, +0.0085] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 2 | 5 | +0.0030 [+0.0009, +0.0052] EQUIVALENT | +0.0029 [-0.0002, +0.0060] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 3 | 1 | +0.0035 [+0.0002, +0.0068] EQUIVALENT | +0.0024 [-0.0007, +0.0054] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 3 | 5 | +0.0034 [+0.0009, +0.0059] EQUIVALENT | +0.0029 [+0.0002, +0.0055] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 5 | 1 | +0.0027 [-0.0001, +0.0055] EQUIVALENT | +0.0035 [+0.0005, +0.0066] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 5 | 5 | +0.0023 [+0.0002, +0.0043] EQUIVALENT | +0.0026 [-0.0005, +0.0056] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 10 | 1 | +0.0033 [+0.0007, +0.0059] EQUIVALENT | +0.0040 [+0.0009, +0.0070] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 10 | 5 | +0.0004 [-0.0017, +0.0025] EQUIVALENT | +0.0005 [-0.0021, +0.0031] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 20 | 1 | +0.0041 [+0.0015, +0.0066] EQUIVALENT | +0.0025 [-0.0000, +0.0051] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 20 | 5 | +0.0027 [+0.0006, +0.0047] EQUIVALENT | +0.0017 [-0.0010, +0.0045] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 1 | 1 | +0.0044 [+0.0013, +0.0074] EQUIVALENT | +0.0034 [+0.0004, +0.0064] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 1 | 5 | +0.0034 [-0.0001, +0.0069] EQUIVALENT | +0.0042 [+0.0016, +0.0068] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 2 | 1 | +0.0041 [+0.0013, +0.0070] EQUIVALENT | +0.0022 [-0.0004, +0.0048] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 2 | 5 | +0.0021 [-0.0012, +0.0054] EQUIVALENT | +0.0034 [+0.0010, +0.0059] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 3 | 1 | +0.0017 [-0.0010, +0.0044] EQUIVALENT | +0.0007 [-0.0021, +0.0035] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 3 | 5 | +0.0018 [-0.0012, +0.0047] EQUIVALENT | +0.0023 [+0.0001, +0.0046] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 5 | 1 | +0.0030 [+0.0005, +0.0054] EQUIVALENT | +0.0025 [+0.0001, +0.0049] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 5 | 5 | +0.0023 [-0.0002, +0.0048] EQUIVALENT | +0.0032 [+0.0006, +0.0059] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 10 | 1 | +0.0044 [+0.0025, +0.0064] EQUIVALENT | +0.0030 [+0.0009, +0.0050] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 10 | 5 | +0.0028 [+0.0004, +0.0051] EQUIVALENT | +0.0021 [-0.0002, +0.0043] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 20 | 1 | +0.0010 [-0.0011, +0.0030] EQUIVALENT | +0.0002 [-0.0017, +0.0022] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 20 | 5 | +0.0012 [-0.0011, +0.0036] EQUIVALENT | -0.0003 [-0.0027, +0.0021] EQUIVALENT | **EQUIVALENT** |

Secondary confirmed-class counts: E-CONT: {'EQUIVALENT': 71, 'DISCORDANT': 8, 'INCONCLUSIVE': 3, 'DISTINGUISHABLE': 26}; E-LIB: {'EQUIVALENT': 92, 'INCONCLUSIVE': 7, 'DISCORDANT': 8, 'DISTINGUISHABLE': 1}

## Sensitivity of the primary classification to the effect threshold (confirmed MEANINGFUL cells, E-CONT)

- threshold 0.01 nats: 13/36 cells
- threshold 0.04 nats: 0/36 cells

## Baseline performance and calibration (E-CONT, replicate R1)

| r | n | h | predictor | mean log score | coverage 0.5 / 0.8 / 0.95 | PIT KS p | fallback | quad cap |
|---|---|---|---|---|---|---|---|---|
| 0.25 | 1 | 1 | matched_reference | -1.4795 | 0.480 / 0.784 / 0.944 | 2.01e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 1 | flat_prior_bayes | -3.1426 | 0.426 / 0.763 / 0.938 | 1.39e-06 | 0.00 | 0.000 |
| 0.25 | 1 | 1 | ols_gaussian | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 1.00 | nan |
| 0.25 | 1 | 1 | ols_student_t | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_rolling_origin | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_blocked | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_leave_one_out | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 1.00 | nan |
| 0.25 | 1 | 1 | persistence | -2534.0309 | 0.297 / 0.509 / 0.658 | 2.82e-72 | 0.00 | nan |
| 0.25 | 1 | 1 | stability_prior_bayes | -1.5234 | 0.507 / 0.804 / 0.954 | 2.48e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 5 | matched_reference | -1.6047 | 0.493 / 0.795 / 0.946 | 1.56e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 5 | flat_prior_bayes | -4.1269 | 0.512 / 0.806 / 0.948 | 3.34e-01 | 0.00 | 0.061 |
| 0.25 | 1 | 5 | ols_gaussian | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 1.00 | nan |
| 0.25 | 1 | 5 | ols_student_t | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_rolling_origin | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_blocked | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_leave_one_out | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 1.00 | nan |
| 0.25 | 1 | 5 | persistence | -263.2910 | 0.514 / 0.726 / 0.822 | 9.26e-15 | 0.00 | nan |
| 0.25 | 1 | 5 | stability_prior_bayes | -1.6173 | 0.531 / 0.839 / 0.970 | 1.45e-02 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | matched_reference | -1.4599 | 0.503 / 0.803 / 0.948 | 7.57e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | flat_prior_bayes | -2.0262 | 0.475 / 0.775 / 0.936 | 5.07e-02 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | ols_gaussian | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 1.00 | nan |
| 0.25 | 2 | 1 | ols_student_t | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_rolling_origin | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_blocked | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_leave_one_out | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 1.00 | nan |
| 0.25 | 2 | 1 | persistence | -5.2412 | 0.390 / 0.629 / 0.782 | 3.36e-29 | 0.00 | nan |
| 0.25 | 2 | 1 | stability_prior_bayes | -1.5074 | 0.513 / 0.812 / 0.953 | 4.58e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 5 | matched_reference | -1.6063 | 0.494 / 0.787 / 0.942 | 4.99e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 5 | flat_prior_bayes | -2.5677 | 0.594 / 0.845 / 0.967 | 6.53e-08 | 0.00 | 0.001 |
| 0.25 | 2 | 5 | ols_gaussian | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 1.00 | nan |
| 0.25 | 2 | 5 | ols_student_t | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_rolling_origin | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_blocked | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_leave_one_out | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 1.00 | nan |
| 0.25 | 2 | 5 | persistence | -2.9577 | 0.577 / 0.827 / 0.917 | 1.55e-08 | 0.00 | nan |
| 0.25 | 2 | 5 | stability_prior_bayes | -1.6188 | 0.528 / 0.831 / 0.968 | 5.86e-02 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | matched_reference | -1.4293 | 0.504 / 0.810 / 0.956 | 4.93e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | flat_prior_bayes | -1.7033 | 0.507 / 0.801 / 0.950 | 3.17e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | ols_gaussian | -13.9122 | 0.382 / 0.604 / 0.740 | 9.96e-43 | 0.00 | nan |
| 0.25 | 3 | 1 | ols_student_t | -1.9407 | 0.528 / 0.825 / 0.964 | 9.70e-04 | 0.00 | nan |
| 0.25 | 3 | 1 | kernel_rolling_origin | -2.5088 | 0.386 / 0.649 / 0.814 | 4.66e-24 | 1.00 | nan |
| 0.25 | 3 | 1 | kernel_blocked | -2.5088 | 0.386 / 0.649 / 0.814 | 4.66e-24 | 1.00 | nan |
| 0.25 | 3 | 1 | kernel_leave_one_out | -6.8873 | 0.380 / 0.613 / 0.768 | 1.96e-33 | 0.00 | nan |
| 0.25 | 3 | 1 | persistence | -2.4126 | 0.415 / 0.673 / 0.840 | 4.18e-14 | 0.00 | nan |
| 0.25 | 3 | 1 | stability_prior_bayes | -1.4827 | 0.518 / 0.815 / 0.957 | 1.34e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | matched_reference | -1.5921 | 0.493 / 0.802 / 0.950 | 5.98e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | flat_prior_bayes | -2.0741 | 0.623 / 0.894 / 0.983 | 2.91e-15 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | ols_gaussian | -9.6696 | 0.400 / 0.633 / 0.771 | 2.54e-27 | 0.00 | nan |
| 0.25 | 3 | 5 | ols_student_t | -2.4884 | 0.661 / 0.893 / 0.979 | 2.70e-20 | 0.00 | nan |
| 0.25 | 3 | 5 | kernel_rolling_origin | -2.2040 | 0.637 / 0.858 / 0.952 | 1.60e-15 | 1.00 | nan |
| 0.25 | 3 | 5 | kernel_blocked | -2.2040 | 0.637 / 0.858 / 0.952 | 1.60e-15 | 1.00 | nan |
| 0.25 | 3 | 5 | kernel_leave_one_out | -2.2040 | 0.637 / 0.858 / 0.952 | 1.60e-15 | 1.00 | nan |
| 0.25 | 3 | 5 | persistence | -2.2040 | 0.637 / 0.858 / 0.952 | 1.60e-15 | 0.00 | nan |
| 0.25 | 3 | 5 | stability_prior_bayes | -1.6031 | 0.526 / 0.839 / 0.973 | 2.76e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | matched_reference | -1.4535 | 0.498 / 0.801 / 0.947 | 3.94e-01 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | flat_prior_bayes | -1.5699 | 0.502 / 0.798 / 0.947 | 6.85e-01 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | ols_gaussian | -2.1811 | 0.425 / 0.686 / 0.842 | 8.27e-13 | 0.00 | nan |
| 0.25 | 5 | 1 | ols_student_t | -1.6792 | 0.508 / 0.813 / 0.960 | 3.66e-01 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_rolling_origin | -17.3711 | 0.352 / 0.578 / 0.737 | 1.15e-40 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_blocked | -2.4103 | 0.473 / 0.726 / 0.867 | 1.46e-06 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_leave_one_out | -2.2429 | 0.398 / 0.651 / 0.824 | 2.04e-20 | 0.00 | nan |
| 0.25 | 5 | 1 | persistence | -1.8409 | 0.448 / 0.723 / 0.885 | 4.38e-06 | 0.00 | nan |
| 0.25 | 5 | 1 | stability_prior_bayes | -1.4893 | 0.508 / 0.797 / 0.949 | 2.57e-01 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | matched_reference | -1.6045 | 0.484 / 0.788 / 0.947 | 6.90e-01 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | flat_prior_bayes | -1.8125 | 0.569 / 0.874 / 0.979 | 3.98e-06 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | ols_gaussian | -2.2505 | 0.447 / 0.722 / 0.862 | 1.02e-07 | 0.00 | nan |
| 0.25 | 5 | 5 | ols_student_t | -1.8916 | 0.559 / 0.851 / 0.967 | 3.13e-05 | 0.00 | nan |
| 0.25 | 5 | 5 | kernel_rolling_origin | -1926.0303 | 0.260 / 0.475 / 0.663 | 3.16e-88 | 1.00 | nan |
| 0.25 | 5 | 5 | kernel_blocked | -1926.0303 | 0.260 / 0.475 / 0.663 | 3.16e-88 | 1.00 | nan |
| 0.25 | 5 | 5 | kernel_leave_one_out | -1926.0303 | 0.260 / 0.475 / 0.663 | 3.16e-88 | 1.00 | nan |
| 0.25 | 5 | 5 | persistence | -1926.0303 | 0.260 / 0.475 / 0.663 | 3.16e-88 | 0.00 | nan |
| 0.25 | 5 | 5 | stability_prior_bayes | -1.6133 | 0.514 / 0.822 / 0.964 | 1.74e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | matched_reference | -1.4420 | 0.515 / 0.797 / 0.948 | 3.79e-02 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | flat_prior_bayes | -1.4792 | 0.518 / 0.794 / 0.949 | 3.79e-02 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | ols_gaussian | -1.5998 | 0.477 / 0.751 / 0.906 | 7.12e-05 | 0.00 | nan |
| 0.25 | 10 | 1 | ols_student_t | -1.5317 | 0.516 / 0.812 / 0.952 | 4.48e-02 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_rolling_origin | -1.7568 | 0.448 / 0.728 / 0.883 | 3.46e-06 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_blocked | -1.7292 | 0.487 / 0.767 / 0.905 | 7.60e-03 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_leave_one_out | -1.7675 | 0.434 / 0.707 / 0.879 | 3.02e-09 | 0.00 | nan |
| 0.25 | 10 | 1 | persistence | -1.7107 | 0.470 / 0.751 / 0.911 | 2.34e-03 | 0.00 | nan |
| 0.25 | 10 | 1 | stability_prior_bayes | -1.4613 | 0.522 / 0.795 / 0.950 | 6.56e-02 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | matched_reference | -1.5777 | 0.496 / 0.811 / 0.954 | 9.72e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | flat_prior_bayes | -1.6340 | 0.536 / 0.856 / 0.974 | 1.48e-03 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | ols_gaussian | -1.7118 | 0.478 / 0.773 / 0.919 | 1.27e-01 | 0.00 | nan |
| 0.25 | 10 | 5 | ols_student_t | -1.6647 | 0.513 / 0.821 / 0.954 | 3.26e-01 | 0.00 | nan |
| 0.25 | 10 | 5 | kernel_rolling_origin | -1.9662 | 0.476 / 0.763 / 0.908 | 8.33e-03 | 1.00 | nan |
| 0.25 | 10 | 5 | kernel_blocked | -1.9662 | 0.476 / 0.763 / 0.908 | 8.33e-03 | 1.00 | nan |
| 0.25 | 10 | 5 | kernel_leave_one_out | -2.7214 | 0.355 / 0.601 / 0.769 | 6.50e-32 | 0.00 | nan |
| 0.25 | 10 | 5 | persistence | -2.0867 | 0.430 / 0.719 / 0.881 | 1.35e-06 | 0.00 | nan |
| 0.25 | 10 | 5 | stability_prior_bayes | -1.5851 | 0.521 / 0.835 / 0.965 | 7.59e-02 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | matched_reference | -1.4194 | 0.515 / 0.804 / 0.953 | 9.02e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | flat_prior_bayes | -1.4263 | 0.516 / 0.807 / 0.956 | 5.29e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | ols_gaussian | -1.4626 | 0.496 / 0.784 / 0.932 | 4.46e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | ols_student_t | -1.4529 | 0.516 / 0.809 / 0.952 | 3.80e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_rolling_origin | -1.5452 | 0.491 / 0.788 / 0.928 | 6.78e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_blocked | -1.5543 | 0.500 / 0.790 / 0.931 | 4.85e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_leave_one_out | -1.5617 | 0.462 / 0.755 / 0.911 | 5.74e-03 | 0.00 | nan |
| 0.25 | 20 | 1 | persistence | -1.6383 | 0.497 / 0.779 / 0.933 | 3.96e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | stability_prior_bayes | -1.4249 | 0.515 / 0.807 / 0.954 | 7.38e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | matched_reference | -1.5974 | 0.496 / 0.790 / 0.944 | 5.52e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | flat_prior_bayes | -1.6085 | 0.521 / 0.809 / 0.955 | 8.55e-02 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | ols_gaussian | -1.6461 | 0.493 / 0.774 / 0.926 | 5.36e-02 | 0.00 | nan |
| 0.25 | 20 | 5 | ols_student_t | -1.6315 | 0.509 / 0.794 / 0.945 | 5.86e-01 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_rolling_origin | -1.9258 | 0.459 / 0.728 / 0.882 | 1.09e-05 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_blocked | -1.9777 | 0.488 / 0.749 / 0.883 | 2.79e-05 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_leave_one_out | -1.9096 | 0.410 / 0.681 / 0.857 | 1.71e-13 | 0.00 | nan |
| 0.25 | 20 | 5 | persistence | -1.9492 | 0.489 / 0.765 / 0.919 | 1.02e-02 | 0.00 | nan |
| 0.25 | 20 | 5 | stability_prior_bayes | -1.5993 | 0.515 / 0.805 / 0.953 | 3.13e-01 | 0.00 | 0.000 |
| 1 | 1 | 1 | matched_reference | -1.4856 | 0.478 / 0.786 / 0.940 | 2.40e-01 | 0.00 | 0.000 |
| 1 | 1 | 1 | flat_prior_bayes | -2.2843 | 0.425 / 0.733 / 0.927 | 6.87e-06 | 0.00 | 0.000 |
| 1 | 1 | 1 | ols_gaussian | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 1.00 | nan |
| 1 | 1 | 1 | ols_student_t | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 1.00 | nan |
| 1 | 1 | 1 | kernel_rolling_origin | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 1.00 | nan |
| 1 | 1 | 1 | kernel_blocked | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 1.00 | nan |
| 1 | 1 | 1 | kernel_leave_one_out | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 1.00 | nan |
| 1 | 1 | 1 | persistence | -581.5089 | 0.347 / 0.566 / 0.692 | 5.64e-53 | 0.00 | nan |
| 1 | 1 | 1 | stability_prior_bayes | -1.5271 | 0.493 / 0.799 / 0.950 | 4.06e-01 | 0.00 | 0.000 |
| 1 | 1 | 5 | matched_reference | -1.6042 | 0.494 / 0.793 / 0.947 | 2.69e-01 | 0.00 | 0.000 |
| 1 | 1 | 5 | flat_prior_bayes | -2.8717 | 0.530 / 0.825 / 0.959 | 8.48e-02 | 0.00 | 0.017 |
| 1 | 1 | 5 | ols_gaussian | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 1.00 | nan |
| 1 | 1 | 5 | ols_student_t | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 1.00 | nan |
| 1 | 1 | 5 | kernel_rolling_origin | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 1.00 | nan |
| 1 | 1 | 5 | kernel_blocked | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 1.00 | nan |
| 1 | 1 | 5 | kernel_leave_one_out | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 1.00 | nan |
| 1 | 1 | 5 | persistence | -314.1432 | 0.543 / 0.736 / 0.827 | 7.90e-13 | 0.00 | nan |
| 1 | 1 | 5 | stability_prior_bayes | -1.6164 | 0.532 / 0.837 / 0.970 | 1.74e-02 | 0.00 | 0.000 |
| 1 | 2 | 1 | matched_reference | -1.4582 | 0.504 / 0.801 / 0.947 | 6.15e-01 | 0.00 | 0.000 |
| 1 | 2 | 1 | flat_prior_bayes | -1.7684 | 0.511 / 0.797 / 0.944 | 6.57e-01 | 0.00 | 0.000 |
| 1 | 2 | 1 | ols_gaussian | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 1.00 | nan |
| 1 | 2 | 1 | ols_student_t | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 1.00 | nan |
| 1 | 2 | 1 | kernel_rolling_origin | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 1.00 | nan |
| 1 | 2 | 1 | kernel_blocked | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 1.00 | nan |
| 1 | 2 | 1 | kernel_leave_one_out | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 1.00 | nan |
| 1 | 2 | 1 | persistence | -5.2816 | 0.417 / 0.666 / 0.809 | 1.86e-20 | 0.00 | nan |
| 1 | 2 | 1 | stability_prior_bayes | -1.4993 | 0.518 / 0.808 / 0.953 | 4.25e-01 | 0.00 | 0.000 |
| 1 | 2 | 5 | matched_reference | -1.6025 | 0.496 / 0.791 / 0.942 | 7.07e-01 | 0.00 | 0.000 |
| 1 | 2 | 5 | flat_prior_bayes | -2.1563 | 0.611 / 0.879 / 0.978 | 2.46e-10 | 0.00 | 0.000 |
| 1 | 2 | 5 | ols_gaussian | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 1.00 | nan |
| 1 | 2 | 5 | ols_student_t | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 1.00 | nan |
| 1 | 2 | 5 | kernel_rolling_origin | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 1.00 | nan |
| 1 | 2 | 5 | kernel_blocked | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 1.00 | nan |
| 1 | 2 | 5 | kernel_leave_one_out | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 1.00 | nan |
| 1 | 2 | 5 | persistence | -14.7016 | 0.623 / 0.836 / 0.923 | 2.64e-16 | 0.00 | nan |
| 1 | 2 | 5 | stability_prior_bayes | -1.6132 | 0.529 / 0.829 / 0.967 | 5.78e-02 | 0.00 | 0.000 |
| 1 | 3 | 1 | matched_reference | -1.4283 | 0.509 / 0.811 / 0.956 | 4.73e-01 | 0.00 | 0.000 |
| 1 | 3 | 1 | flat_prior_bayes | -1.6100 | 0.504 / 0.809 / 0.949 | 2.45e-01 | 0.00 | 0.000 |
| 1 | 3 | 1 | ols_gaussian | -365.3018 | 0.399 / 0.628 / 0.779 | 1.35e-31 | 0.00 | nan |
| 1 | 3 | 1 | ols_student_t | -1.8511 | 0.530 / 0.830 / 0.962 | 1.09e-03 | 0.00 | nan |
| 1 | 3 | 1 | kernel_rolling_origin | -2.3902 | 0.417 / 0.672 / 0.837 | 4.59e-16 | 1.00 | nan |
| 1 | 3 | 1 | kernel_blocked | -2.3902 | 0.417 / 0.672 / 0.837 | 4.59e-16 | 1.00 | nan |
| 1 | 3 | 1 | kernel_leave_one_out | -4.8379 | 0.384 / 0.618 / 0.769 | 9.21e-33 | 0.00 | nan |
| 1 | 3 | 1 | persistence | -2.2911 | 0.439 / 0.706 / 0.857 | 9.11e-10 | 0.00 | nan |
| 1 | 3 | 1 | stability_prior_bayes | -1.4746 | 0.520 / 0.811 / 0.957 | 2.25e-01 | 0.00 | 0.000 |
| 1 | 3 | 5 | matched_reference | -1.5886 | 0.495 / 0.801 / 0.950 | 6.03e-01 | 0.00 | 0.000 |
| 1 | 3 | 5 | flat_prior_bayes | -1.9039 | 0.604 / 0.892 / 0.985 | 1.82e-11 | 0.00 | 0.000 |
| 1 | 3 | 5 | ols_gaussian | -513.0417 | 0.420 / 0.660 / 0.799 | 9.17e-21 | 0.00 | nan |
| 1 | 3 | 5 | ols_student_t | -2.1941 | 0.603 / 0.865 / 0.971 | 4.30e-10 | 0.00 | nan |
| 1 | 3 | 5 | kernel_rolling_origin | -2.2004 | 0.660 / 0.874 / 0.953 | 4.02e-21 | 1.00 | nan |
| 1 | 3 | 5 | kernel_blocked | -2.2004 | 0.660 / 0.874 / 0.953 | 4.02e-21 | 1.00 | nan |
| 1 | 3 | 5 | kernel_leave_one_out | -2.2004 | 0.660 / 0.874 / 0.953 | 4.02e-21 | 1.00 | nan |
| 1 | 3 | 5 | persistence | -2.2004 | 0.660 / 0.874 / 0.953 | 4.02e-21 | 0.00 | nan |
| 1 | 3 | 5 | stability_prior_bayes | -1.5983 | 0.527 / 0.837 / 0.972 | 5.51e-02 | 0.00 | 0.000 |
| 1 | 5 | 1 | matched_reference | -1.4517 | 0.500 / 0.801 / 0.947 | 4.27e-01 | 0.00 | 0.000 |
| 1 | 5 | 1 | flat_prior_bayes | -1.5391 | 0.507 / 0.798 / 0.947 | 3.79e-01 | 0.00 | 0.000 |
| 1 | 5 | 1 | ols_gaussian | -1.9473 | 0.435 / 0.701 / 0.852 | 9.92e-11 | 0.00 | nan |
| 1 | 5 | 1 | ols_student_t | -1.6456 | 0.520 / 0.814 / 0.962 | 1.05e-01 | 0.00 | nan |
| 1 | 5 | 1 | kernel_rolling_origin | -25.1039 | 0.351 / 0.582 / 0.737 | 1.84e-39 | 0.00 | nan |
| 1 | 5 | 1 | kernel_blocked | -2.6971 | 0.481 / 0.730 / 0.864 | 7.17e-07 | 0.00 | nan |
| 1 | 5 | 1 | kernel_leave_one_out | -2.1931 | 0.405 / 0.651 / 0.827 | 1.05e-18 | 0.00 | nan |
| 1 | 5 | 1 | persistence | -1.7853 | 0.460 / 0.741 / 0.898 | 5.23e-04 | 0.00 | nan |
| 1 | 5 | 1 | stability_prior_bayes | -1.4836 | 0.509 / 0.798 / 0.948 | 2.35e-01 | 0.00 | 0.000 |
| 1 | 5 | 5 | matched_reference | -1.6021 | 0.487 / 0.789 / 0.947 | 7.68e-01 | 0.00 | 0.000 |
| 1 | 5 | 5 | flat_prior_bayes | -1.7542 | 0.559 / 0.866 / 0.978 | 5.21e-05 | 0.00 | 0.000 |
| 1 | 5 | 5 | ols_gaussian | -2.0613 | 0.450 / 0.723 / 0.875 | 3.86e-06 | 0.00 | nan |
| 1 | 5 | 5 | ols_student_t | -1.8248 | 0.542 / 0.837 / 0.964 | 8.14e-03 | 0.00 | nan |
| 1 | 5 | 5 | kernel_rolling_origin | -375.2417 | 0.356 / 0.574 / 0.718 | 1.41e-43 | 1.00 | nan |
| 1 | 5 | 5 | kernel_blocked | -375.2417 | 0.356 / 0.574 / 0.718 | 1.41e-43 | 1.00 | nan |
| 1 | 5 | 5 | kernel_leave_one_out | -375.2417 | 0.356 / 0.574 / 0.718 | 1.41e-43 | 1.00 | nan |
| 1 | 5 | 5 | persistence | -375.2417 | 0.356 / 0.574 / 0.718 | 1.41e-43 | 0.00 | nan |
| 1 | 5 | 5 | stability_prior_bayes | -1.6106 | 0.516 / 0.823 / 0.962 | 2.86e-01 | 0.00 | 0.000 |
| 1 | 10 | 1 | matched_reference | -1.4406 | 0.512 / 0.796 / 0.947 | 2.11e-02 | 0.00 | 0.000 |
| 1 | 10 | 1 | flat_prior_bayes | -1.4735 | 0.519 / 0.794 / 0.949 | 4.70e-02 | 0.00 | 0.000 |
| 1 | 10 | 1 | ols_gaussian | -1.5895 | 0.476 / 0.753 / 0.904 | 2.19e-04 | 0.00 | nan |
| 1 | 10 | 1 | ols_student_t | -1.5267 | 0.517 / 0.814 / 0.950 | 3.87e-02 | 0.00 | nan |
| 1 | 10 | 1 | kernel_rolling_origin | -1.7491 | 0.455 / 0.726 / 0.885 | 1.08e-06 | 0.00 | nan |
| 1 | 10 | 1 | kernel_blocked | -1.7209 | 0.492 / 0.764 / 0.903 | 5.69e-03 | 0.00 | nan |
| 1 | 10 | 1 | kernel_leave_one_out | -1.7556 | 0.438 / 0.709 / 0.882 | 6.64e-10 | 0.00 | nan |
| 1 | 10 | 1 | persistence | -1.7029 | 0.475 / 0.761 / 0.917 | 1.02e-02 | 0.00 | nan |
| 1 | 10 | 1 | stability_prior_bayes | -1.4581 | 0.519 / 0.795 / 0.948 | 3.88e-02 | 0.00 | 0.000 |
| 1 | 10 | 5 | matched_reference | -1.5761 | 0.497 / 0.815 / 0.956 | 9.39e-01 | 0.00 | 0.000 |
| 1 | 10 | 5 | flat_prior_bayes | -1.6251 | 0.528 / 0.851 / 0.971 | 4.38e-03 | 0.00 | 0.000 |
| 1 | 10 | 5 | ols_gaussian | -1.7066 | 0.476 / 0.770 / 0.920 | 1.05e-01 | 0.00 | nan |
| 1 | 10 | 5 | ols_student_t | -1.6608 | 0.511 / 0.813 / 0.953 | 6.04e-01 | 0.00 | nan |
| 1 | 10 | 5 | kernel_rolling_origin | -1.9679 | 0.500 / 0.783 / 0.920 | 7.25e-02 | 1.00 | nan |
| 1 | 10 | 5 | kernel_blocked | -1.9679 | 0.500 / 0.783 / 0.920 | 7.25e-02 | 1.00 | nan |
| 1 | 10 | 5 | kernel_leave_one_out | -2.7297 | 0.362 / 0.601 / 0.768 | 1.58e-31 | 0.00 | nan |
| 1 | 10 | 5 | persistence | -2.0902 | 0.448 / 0.734 / 0.893 | 5.74e-05 | 0.00 | nan |
| 1 | 10 | 5 | stability_prior_bayes | -1.5831 | 0.519 / 0.836 / 0.964 | 8.51e-02 | 0.00 | 0.000 |
| 1 | 20 | 1 | matched_reference | -1.4188 | 0.513 / 0.806 / 0.953 | 8.37e-01 | 0.00 | 0.000 |
| 1 | 20 | 1 | flat_prior_bayes | -1.4251 | 0.514 / 0.808 / 0.954 | 5.10e-01 | 0.00 | 0.000 |
| 1 | 20 | 1 | ols_gaussian | -1.4625 | 0.499 / 0.783 / 0.931 | 4.64e-01 | 0.00 | nan |
| 1 | 20 | 1 | ols_student_t | -1.4525 | 0.520 / 0.812 / 0.952 | 4.33e-01 | 0.00 | nan |
| 1 | 20 | 1 | kernel_rolling_origin | -1.5415 | 0.498 / 0.795 / 0.929 | 7.20e-01 | 0.00 | nan |
| 1 | 20 | 1 | kernel_blocked | -1.5478 | 0.499 / 0.795 / 0.931 | 6.87e-01 | 0.00 | nan |
| 1 | 20 | 1 | kernel_leave_one_out | -1.5632 | 0.466 / 0.756 / 0.912 | 2.49e-02 | 0.00 | nan |
| 1 | 20 | 1 | persistence | -1.6372 | 0.499 / 0.786 / 0.935 | 6.22e-01 | 0.00 | nan |
| 1 | 20 | 1 | stability_prior_bayes | -1.4239 | 0.515 / 0.808 / 0.952 | 7.00e-01 | 0.00 | 0.000 |
| 1 | 20 | 5 | matched_reference | -1.5975 | 0.498 / 0.790 / 0.945 | 5.53e-01 | 0.00 | 0.000 |
| 1 | 20 | 5 | flat_prior_bayes | -1.6079 | 0.520 / 0.809 / 0.955 | 9.99e-02 | 0.00 | 0.000 |
| 1 | 20 | 5 | ols_gaussian | -1.6459 | 0.493 / 0.774 / 0.925 | 7.07e-02 | 0.00 | nan |
| 1 | 20 | 5 | ols_student_t | -1.6312 | 0.508 / 0.794 / 0.944 | 6.74e-01 | 0.00 | nan |
| 1 | 20 | 5 | kernel_rolling_origin | -1.9143 | 0.457 / 0.727 / 0.877 | 2.12e-05 | 0.00 | nan |
| 1 | 20 | 5 | kernel_blocked | -1.9860 | 0.484 / 0.749 / 0.882 | 3.05e-05 | 0.00 | nan |
| 1 | 20 | 5 | kernel_leave_one_out | -1.9220 | 0.415 / 0.682 / 0.853 | 9.82e-14 | 0.00 | nan |
| 1 | 20 | 5 | persistence | -1.9418 | 0.495 / 0.773 / 0.923 | 4.73e-02 | 0.00 | nan |
| 1 | 20 | 5 | stability_prior_bayes | -1.5995 | 0.515 / 0.803 / 0.952 | 2.29e-01 | 0.00 | 0.000 |
| 4 | 1 | 1 | matched_reference | -1.5051 | 0.483 / 0.781 / 0.937 | 3.12e-01 | 0.00 | 0.000 |
| 4 | 1 | 1 | flat_prior_bayes | -1.7922 | 0.470 / 0.763 / 0.932 | 5.12e-02 | 0.00 | 0.000 |
| 4 | 1 | 1 | ols_gaussian | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 1.00 | nan |
| 4 | 1 | 1 | ols_student_t | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 1.00 | nan |
| 4 | 1 | 1 | kernel_rolling_origin | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 1.00 | nan |
| 4 | 1 | 1 | kernel_blocked | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 1.00 | nan |
| 4 | 1 | 1 | kernel_leave_one_out | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 1.00 | nan |
| 4 | 1 | 1 | persistence | -120.7344 | 0.534 / 0.724 / 0.806 | 3.25e-17 | 0.00 | nan |
| 4 | 1 | 1 | stability_prior_bayes | -1.5272 | 0.507 / 0.787 / 0.942 | 4.66e-01 | 0.00 | 0.000 |
| 4 | 1 | 5 | matched_reference | -1.6022 | 0.496 / 0.797 / 0.949 | 2.21e-01 | 0.00 | 0.000 |
| 4 | 1 | 5 | flat_prior_bayes | -2.0710 | 0.512 / 0.811 / 0.958 | 1.92e-01 | 0.00 | 0.003 |
| 4 | 1 | 5 | ols_gaussian | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 1.00 | nan |
| 4 | 1 | 5 | ols_student_t | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 1.00 | nan |
| 4 | 1 | 5 | kernel_rolling_origin | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 1.00 | nan |
| 4 | 1 | 5 | kernel_blocked | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 1.00 | nan |
| 4 | 1 | 5 | kernel_leave_one_out | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 1.00 | nan |
| 4 | 1 | 5 | persistence | -291.5129 | 0.662 / 0.805 / 0.864 | 1.27e-33 | 0.00 | nan |
| 4 | 1 | 5 | stability_prior_bayes | -1.6174 | 0.519 / 0.822 / 0.961 | 2.58e-02 | 0.00 | 0.000 |
| 4 | 2 | 1 | matched_reference | -1.4496 | 0.512 / 0.801 / 0.952 | 4.64e-01 | 0.00 | 0.000 |
| 4 | 2 | 1 | flat_prior_bayes | -1.5693 | 0.513 / 0.802 / 0.950 | 8.44e-01 | 0.00 | 0.000 |
| 4 | 2 | 1 | ols_gaussian | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 1.00 | nan |
| 4 | 2 | 1 | ols_student_t | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 1.00 | nan |
| 4 | 2 | 1 | kernel_rolling_origin | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 1.00 | nan |
| 4 | 2 | 1 | kernel_blocked | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 1.00 | nan |
| 4 | 2 | 1 | kernel_leave_one_out | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 1.00 | nan |
| 4 | 2 | 1 | persistence | -2.8555 | 0.591 / 0.806 / 0.905 | 1.59e-09 | 0.00 | nan |
| 4 | 2 | 1 | stability_prior_bayes | -1.4724 | 0.522 / 0.805 / 0.952 | 4.83e-01 | 0.00 | 0.000 |
| 4 | 2 | 5 | matched_reference | -1.5918 | 0.499 / 0.798 / 0.946 | 8.45e-01 | 0.00 | 0.000 |
| 4 | 2 | 5 | flat_prior_bayes | -1.8068 | 0.546 / 0.834 / 0.965 | 1.53e-03 | 0.00 | 0.000 |
| 4 | 2 | 5 | ols_gaussian | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 1.00 | nan |
| 4 | 2 | 5 | ols_student_t | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 1.00 | nan |
| 4 | 2 | 5 | kernel_rolling_origin | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 1.00 | nan |
| 4 | 2 | 5 | kernel_blocked | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 1.00 | nan |
| 4 | 2 | 5 | kernel_leave_one_out | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 1.00 | nan |
| 4 | 2 | 5 | persistence | -3.3030 | 0.741 / 0.889 / 0.946 | 1.10e-60 | 0.00 | nan |
| 4 | 2 | 5 | stability_prior_bayes | -1.6012 | 0.527 / 0.816 / 0.960 | 1.05e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | matched_reference | -1.4233 | 0.509 / 0.811 / 0.956 | 5.84e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | flat_prior_bayes | -1.5052 | 0.501 / 0.804 / 0.953 | 2.96e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | ols_gaussian | -11.8861 | 0.416 / 0.647 / 0.795 | 4.10e-23 | 0.00 | nan |
| 4 | 3 | 1 | ols_student_t | -1.7652 | 0.509 / 0.817 / 0.952 | 1.05e-01 | 0.00 | nan |
| 4 | 3 | 1 | kernel_rolling_origin | -2.5191 | 0.582 / 0.806 / 0.910 | 2.69e-07 | 1.00 | nan |
| 4 | 3 | 1 | kernel_blocked | -2.5191 | 0.582 / 0.806 / 0.910 | 2.69e-07 | 1.00 | nan |
| 4 | 3 | 1 | kernel_leave_one_out | -6.8379 | 0.419 / 0.659 / 0.799 | 3.90e-23 | 0.00 | nan |
| 4 | 3 | 1 | persistence | -2.4549 | 0.589 / 0.824 / 0.925 | 7.17e-08 | 0.00 | nan |
| 4 | 3 | 1 | stability_prior_bayes | -1.4494 | 0.512 / 0.807 / 0.957 | 3.05e-01 | 0.00 | 0.000 |
| 4 | 3 | 5 | matched_reference | -1.5772 | 0.497 / 0.801 / 0.954 | 6.39e-01 | 0.00 | 0.000 |
| 4 | 3 | 5 | flat_prior_bayes | -1.7091 | 0.546 / 0.851 / 0.971 | 2.14e-03 | 0.00 | 0.000 |
| 4 | 3 | 5 | ols_gaussian | -62.1376 | 0.432 / 0.661 / 0.801 | 6.75e-19 | 0.00 | nan |
| 4 | 3 | 5 | ols_student_t | -1.9922 | 0.547 / 0.827 / 0.953 | 3.45e-03 | 0.00 | nan |
| 4 | 3 | 5 | kernel_rolling_origin | -3.1139 | 0.771 / 0.919 / 0.966 | 3.45e-65 | 1.00 | nan |
| 4 | 3 | 5 | kernel_blocked | -3.1139 | 0.771 / 0.919 / 0.966 | 3.45e-65 | 1.00 | nan |
| 4 | 3 | 5 | kernel_leave_one_out | -3.1139 | 0.771 / 0.919 / 0.966 | 3.45e-65 | 1.00 | nan |
| 4 | 3 | 5 | persistence | -3.1139 | 0.771 / 0.919 / 0.966 | 3.45e-65 | 0.00 | nan |
| 4 | 3 | 5 | stability_prior_bayes | -1.5855 | 0.522 / 0.824 / 0.966 | 1.19e-01 | 0.00 | 0.000 |
| 4 | 5 | 1 | matched_reference | -1.4379 | 0.501 / 0.803 / 0.948 | 2.45e-01 | 0.00 | 0.000 |
| 4 | 5 | 1 | flat_prior_bayes | -1.4760 | 0.504 / 0.801 / 0.950 | 4.55e-01 | 0.00 | 0.000 |
| 4 | 5 | 1 | ols_gaussian | -1.8264 | 0.450 / 0.718 / 0.872 | 9.16e-08 | 0.00 | nan |
| 4 | 5 | 1 | ols_student_t | -1.5929 | 0.512 / 0.806 / 0.955 | 2.25e-01 | 0.00 | nan |
| 4 | 5 | 1 | kernel_rolling_origin | -9.5400 | 0.351 / 0.581 / 0.746 | 8.07e-40 | 0.00 | nan |
| 4 | 5 | 1 | kernel_blocked | -2.3700 | 0.536 / 0.784 / 0.890 | 1.36e-03 | 0.00 | nan |
| 4 | 5 | 1 | kernel_leave_one_out | -2.1500 | 0.435 / 0.684 / 0.856 | 1.29e-12 | 0.00 | nan |
| 4 | 5 | 1 | persistence | -1.7554 | 0.585 / 0.831 / 0.945 | 4.84e-08 | 0.00 | nan |
| 4 | 5 | 1 | stability_prior_bayes | -1.4533 | 0.505 / 0.800 / 0.950 | 2.85e-01 | 0.00 | 0.000 |
| 4 | 5 | 5 | matched_reference | -1.5965 | 0.491 / 0.792 / 0.948 | 8.21e-01 | 0.00 | 0.000 |
| 4 | 5 | 5 | flat_prior_bayes | -1.6591 | 0.523 / 0.835 / 0.964 | 4.29e-02 | 0.00 | 0.000 |
| 4 | 5 | 5 | ols_gaussian | -2.0451 | 0.452 / 0.731 / 0.879 | 6.11e-06 | 0.00 | nan |
| 4 | 5 | 5 | ols_student_t | -1.7573 | 0.516 / 0.816 / 0.959 | 2.56e-01 | 0.00 | nan |
| 4 | 5 | 5 | kernel_rolling_origin | -69.8602 | 0.649 / 0.798 / 0.876 | 2.54e-26 | 1.00 | nan |
| 4 | 5 | 5 | kernel_blocked | -69.8602 | 0.649 / 0.798 / 0.876 | 2.54e-26 | 1.00 | nan |
| 4 | 5 | 5 | kernel_leave_one_out | -69.8602 | 0.649 / 0.798 / 0.876 | 2.54e-26 | 1.00 | nan |
| 4 | 5 | 5 | persistence | -69.8602 | 0.649 / 0.798 / 0.876 | 2.54e-26 | 0.00 | nan |
| 4 | 5 | 5 | stability_prior_bayes | -1.6008 | 0.509 / 0.817 / 0.958 | 5.23e-01 | 0.00 | 0.000 |
| 4 | 10 | 1 | matched_reference | -1.4369 | 0.513 / 0.796 / 0.949 | 2.13e-02 | 0.00 | 0.000 |
| 4 | 10 | 1 | flat_prior_bayes | -1.4564 | 0.515 / 0.797 / 0.949 | 8.51e-02 | 0.00 | 0.000 |
| 4 | 10 | 1 | ols_gaussian | -1.5540 | 0.476 / 0.760 / 0.907 | 1.17e-03 | 0.00 | nan |
| 4 | 10 | 1 | ols_student_t | -1.5099 | 0.507 / 0.807 / 0.947 | 7.14e-02 | 0.00 | nan |
| 4 | 10 | 1 | kernel_rolling_origin | -1.7465 | 0.457 / 0.729 / 0.883 | 5.67e-07 | 0.00 | nan |
| 4 | 10 | 1 | kernel_blocked | -1.7146 | 0.519 / 0.786 / 0.924 | 1.23e-02 | 0.00 | nan |
| 4 | 10 | 1 | kernel_leave_one_out | -1.7240 | 0.452 / 0.722 / 0.888 | 2.60e-06 | 0.00 | nan |
| 4 | 10 | 1 | persistence | -1.7053 | 0.545 / 0.821 / 0.946 | 1.58e-04 | 0.00 | nan |
| 4 | 10 | 1 | stability_prior_bayes | -1.4484 | 0.515 / 0.797 / 0.950 | 6.39e-02 | 0.00 | 0.000 |
| 4 | 10 | 5 | matched_reference | -1.5691 | 0.503 / 0.813 / 0.953 | 9.84e-01 | 0.00 | 0.000 |
| 4 | 10 | 5 | flat_prior_bayes | -1.5966 | 0.519 / 0.834 / 0.962 | 1.33e-01 | 0.00 | 0.000 |
| 4 | 10 | 5 | ols_gaussian | -1.6881 | 0.478 / 0.771 / 0.919 | 4.36e-02 | 0.00 | nan |
| 4 | 10 | 5 | ols_student_t | -1.6454 | 0.507 / 0.807 / 0.951 | 8.52e-01 | 0.00 | nan |
| 4 | 10 | 5 | kernel_rolling_origin | -1.9914 | 0.642 / 0.871 / 0.957 | 1.58e-18 | 1.00 | nan |
| 4 | 10 | 5 | kernel_blocked | -1.9914 | 0.642 / 0.871 / 0.957 | 1.58e-18 | 1.00 | nan |
| 4 | 10 | 5 | kernel_leave_one_out | -2.7207 | 0.351 / 0.595 / 0.766 | 1.20e-33 | 0.00 | nan |
| 4 | 10 | 5 | persistence | -2.0721 | 0.596 / 0.839 / 0.940 | 4.95e-08 | 0.00 | nan |
| 4 | 10 | 5 | stability_prior_bayes | -1.5754 | 0.516 / 0.827 / 0.958 | 3.48e-01 | 0.00 | 0.000 |
| 4 | 20 | 1 | matched_reference | -1.4152 | 0.515 / 0.807 / 0.953 | 6.79e-01 | 0.00 | 0.000 |
| 4 | 20 | 1 | flat_prior_bayes | -1.4198 | 0.515 / 0.807 / 0.952 | 6.67e-01 | 0.00 | 0.000 |
| 4 | 20 | 1 | ols_gaussian | -1.4586 | 0.501 / 0.784 / 0.930 | 5.64e-01 | 0.00 | nan |
| 4 | 20 | 1 | ols_student_t | -1.4501 | 0.515 / 0.808 / 0.951 | 5.20e-01 | 0.00 | nan |
| 4 | 20 | 1 | kernel_rolling_origin | -1.5461 | 0.497 / 0.793 / 0.927 | 5.14e-01 | 0.00 | nan |
| 4 | 20 | 1 | kernel_blocked | -1.5565 | 0.520 / 0.812 / 0.935 | 1.03e-01 | 0.00 | nan |
| 4 | 20 | 1 | kernel_leave_one_out | -1.5575 | 0.472 / 0.770 / 0.921 | 9.31e-02 | 0.00 | nan |
| 4 | 20 | 1 | persistence | -1.6427 | 0.534 / 0.821 / 0.952 | 2.45e-02 | 0.00 | nan |
| 4 | 20 | 1 | stability_prior_bayes | -1.4192 | 0.516 / 0.806 / 0.951 | 6.87e-01 | 0.00 | 0.000 |
| 4 | 20 | 5 | matched_reference | -1.5940 | 0.495 / 0.793 / 0.946 | 5.41e-01 | 0.00 | 0.000 |
| 4 | 20 | 5 | flat_prior_bayes | -1.6001 | 0.508 / 0.804 / 0.953 | 4.04e-01 | 0.00 | 0.000 |
| 4 | 20 | 5 | ols_gaussian | -1.6378 | 0.489 / 0.775 / 0.928 | 1.24e-01 | 0.00 | nan |
| 4 | 20 | 5 | ols_student_t | -1.6254 | 0.502 / 0.793 / 0.942 | 8.19e-01 | 0.00 | nan |
| 4 | 20 | 5 | kernel_rolling_origin | -1.9133 | 0.449 / 0.728 / 0.877 | 2.56e-05 | 0.00 | nan |
| 4 | 20 | 5 | kernel_blocked | -1.9927 | 0.492 / 0.753 / 0.885 | 4.54e-04 | 0.00 | nan |
| 4 | 20 | 5 | kernel_leave_one_out | -1.9313 | 0.404 / 0.679 / 0.853 | 7.65e-15 | 0.00 | nan |
| 4 | 20 | 5 | persistence | -1.9512 | 0.568 / 0.829 / 0.951 | 1.01e-04 | 0.00 | nan |
| 4 | 20 | 5 | stability_prior_bayes | -1.5955 | 0.506 / 0.803 / 0.951 | 4.80e-01 | 0.00 | 0.000 |
