# Stage 0.5: stage05_pilot

## Decision: **NOT DECIDABLE**

Reason: fewer than two evaluation replicates (pilot or misconfiguration).

P1 reference reliability = True; P2 (stable across n) = False {'1': False, '5': False}; P3 (robust across r) = False {'0.25': False, '4.0': False}.

## Reference reliability (P1)

- T1 optimality: 0 violations / 1368 (z_crit 4.82, min z -1.63)
- T2 calibration of the matched reference: 0 failing / 144 cell-replicates (min p 1.27e-04, per-test level 1.7e-06)
- max quadrature node-doubling error at targets: 1.78e-15 (threshold 1e-06); max matched quadrature-cap rate: 0.0
- bootstrap vs analytic primary class agreement: 0/0

## Primary: matched reference - frontier_ctx (nats/forecast; mean [decision interval, z = 2.24]; delta = 0.02)

### E-CONT

| r | K | n | h | frontier | R1: mean [interval] class | confirmed | vs Stage-0 frontier (R1) | vs strict (R1) | vs stability (R1) |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 0 | 1 | 1 | stability_prior_bayes | +0.0344 [-0.0035, +0.0723] INCONCLUSIVE | **INCONCLUSIVE** | +1.6852 | +17.4618 | +0.0344 |
| 0.25 | 0 | 1 | 5 | stability_prior_bayes | +0.0161 [-0.0014, +0.0335] INCONCLUSIVE | **INCONCLUSIVE** | +2.5683 | +4.0885 | +0.0161 |
| 0.25 | 0 | 2 | 1 | stability_prior_bayes | +0.0513 [+0.0120, +0.0906] INCONCLUSIVE | **INCONCLUSIVE** | +0.5680 | +13.8779 | +0.0513 |
| 0.25 | 0 | 2 | 5 | stability_prior_bayes | +0.0040 [-0.0181, +0.0260] INCONCLUSIVE | **INCONCLUSIVE** | +0.7974 | +0.7974 | +0.0040 |
| 0.25 | 0 | 3 | 1 | stability_prior_bayes | +0.0472 [+0.0054, +0.0889] INCONCLUSIVE | **INCONCLUSIVE** | +0.2571 | +0.4964 | +0.0472 |
| 0.25 | 0 | 3 | 5 | stability_prior_bayes | +0.0014 [-0.0211, +0.0239] INCONCLUSIVE | **INCONCLUSIVE** | +0.5653 | +0.5653 | +0.0014 |
| 0.25 | 0 | 5 | 1 | stability_prior_bayes | +0.0329 [+0.0032, +0.0626] INCONCLUSIVE | **INCONCLUSIVE** | +0.1162 | +0.1982 | +0.0329 |
| 0.25 | 0 | 5 | 5 | stability_prior_bayes | +0.0225 [+0.0096, +0.0354] INCONCLUSIVE | **INCONCLUSIVE** | +0.2234 | +0.2815 | +0.0225 |
| 0.25 | 0 | 10 | 1 | stability_prior_bayes | +0.0172 [-0.0050, +0.0394] INCONCLUSIVE | **INCONCLUSIVE** | +0.0282 | +0.0681 | +0.0172 |
| 0.25 | 0 | 10 | 5 | stability_prior_bayes | +0.0090 [-0.0053, +0.0234] INCONCLUSIVE | **INCONCLUSIVE** | +0.0565 | +0.0886 | +0.0090 |
| 0.25 | 0 | 20 | 1 | stability_prior_bayes | +0.0266 [+0.0091, +0.0441] INCONCLUSIVE | **INCONCLUSIVE** | +0.0280 | +0.0676 | +0.0266 |
| 0.25 | 0 | 20 | 5 | stability_prior_bayes | +0.0026 [-0.0088, +0.0140] NEGLIGIBLE | **NEGLIGIBLE** | +0.0081 | +0.0344 | +0.0026 |
| 1 | 0 | 1 | 1 | stability_prior_bayes | +0.0331 [-0.0057, +0.0720] INCONCLUSIVE | **INCONCLUSIVE** | +0.8080 | +1079.8626 | +0.0331 |
| 1 | 0 | 1 | 5 | stability_prior_bayes | +0.0227 [+0.0051, +0.0403] INCONCLUSIVE | **INCONCLUSIVE** | +1.3361 | +222.3145 | +0.0227 |
| 1 | 0 | 2 | 1 | stability_prior_bayes | +0.0492 [+0.0119, +0.0864] INCONCLUSIVE | **INCONCLUSIVE** | +0.3585 | +1.2811 | +0.0492 |
| 1 | 0 | 2 | 5 | stability_prior_bayes | +0.0090 [-0.0096, +0.0276] INCONCLUSIVE | **INCONCLUSIVE** | +0.5731 | +0.9068 | +0.0090 |
| 1 | 0 | 3 | 1 | stability_prior_bayes | +0.0417 [+0.0024, +0.0810] INCONCLUSIVE | **INCONCLUSIVE** | +0.1598 | +0.3958 | +0.0417 |
| 1 | 0 | 3 | 5 | stability_prior_bayes | +0.0026 [-0.0187, +0.0238] INCONCLUSIVE | **INCONCLUSIVE** | +0.2872 | +0.5464 | +0.0026 |
| 1 | 0 | 5 | 1 | stability_prior_bayes | +0.0301 [+0.0013, +0.0590] INCONCLUSIVE | **INCONCLUSIVE** | +0.0930 | +0.1663 | +0.0301 |
| 1 | 0 | 5 | 5 | stability_prior_bayes | +0.0205 [+0.0082, +0.0327] INCONCLUSIVE | **INCONCLUSIVE** | +0.1671 | +0.2239 | +0.0205 |
| 1 | 0 | 10 | 1 | stability_prior_bayes | +0.0110 [-0.0083, +0.0303] INCONCLUSIVE | **INCONCLUSIVE** | +0.0194 | +0.0585 | +0.0110 |
| 1 | 0 | 10 | 5 | stability_prior_bayes | +0.0104 [-0.0023, +0.0230] INCONCLUSIVE | **INCONCLUSIVE** | +0.0505 | +0.0843 | +0.0104 |
| 1 | 0 | 20 | 1 | stability_prior_bayes | +0.0257 [+0.0086, +0.0429] INCONCLUSIVE | **INCONCLUSIVE** | +0.0268 | +0.0664 | +0.0257 |
| 1 | 0 | 20 | 5 | stability_prior_bayes | +0.0029 [-0.0083, +0.0142] NEGLIGIBLE | **NEGLIGIBLE** | +0.0073 | +0.0339 | +0.0029 |
| 4 | 0 | 1 | 1 | stability_prior_bayes | +0.0372 [+0.0019, +0.0725] INCONCLUSIVE | **INCONCLUSIVE** | +0.3217 | +82.4776 | +0.0372 |
| 4 | 0 | 1 | 5 | stability_prior_bayes | +0.0297 [+0.0107, +0.0488] INCONCLUSIVE | **INCONCLUSIVE** | +0.5370 | +26.4369 | +0.0297 |
| 4 | 0 | 2 | 1 | stability_prior_bayes | +0.0383 [+0.0083, +0.0683] INCONCLUSIVE | **INCONCLUSIVE** | +0.1729 | +0.8555 | +0.0383 |
| 4 | 0 | 2 | 5 | stability_prior_bayes | +0.0103 [-0.0060, +0.0266] INCONCLUSIVE | **INCONCLUSIVE** | +0.2403 | +0.9865 | +0.0103 |
| 4 | 0 | 3 | 1 | stability_prior_bayes | +0.0256 [+0.0011, +0.0501] INCONCLUSIVE | **INCONCLUSIVE** | +0.0751 | +0.2776 | +0.0256 |
| 4 | 0 | 3 | 5 | stability_prior_bayes | -0.0055 [-0.0264, +0.0154] NEGLIGIBLE | **NEGLIGIBLE** | +0.0994 | +0.3504 | -0.0055 |
| 4 | 0 | 5 | 1 | stability_prior_bayes | +0.0168 [-0.0027, +0.0363] INCONCLUSIVE | **INCONCLUSIVE** | +0.0488 | +0.1332 | +0.0168 |
| 4 | 0 | 5 | 5 | stability_prior_bayes | +0.0113 [+0.0015, +0.0210] INCONCLUSIVE | **INCONCLUSIVE** | +0.0727 | +0.1647 | +0.0113 |
| 4 | 0 | 10 | 1 | stability_prior_bayes | +0.0038 [-0.0086, +0.0162] NEGLIGIBLE | **NEGLIGIBLE** | +0.0083 | +0.0437 | +0.0038 |
| 4 | 0 | 10 | 5 | stability_prior_bayes | +0.0078 [-0.0011, +0.0167] NEGLIGIBLE | **NEGLIGIBLE** | +0.0265 | +0.0532 | +0.0078 |
| 4 | 0 | 20 | 1 | stability_prior_bayes | +0.0134 [+0.0016, +0.0253] INCONCLUSIVE | **INCONCLUSIVE** | +0.0135 | +0.0454 | +0.0134 |
| 4 | 0 | 20 | 5 | stability_prior_bayes | +0.0003 [-0.0102, +0.0108] NEGLIGIBLE | **NEGLIGIBLE** | +0.0005 | +0.0325 | +0.0003 |

### E-LIB

| r | K | n | h | frontier | R1: mean [interval] class | confirmed | vs Stage-0 frontier (R1) | vs strict (R1) | vs stability (R1) |
|---|---|---|---|---|---|---|---|---|---|
| 0.25 | 2 | 1 | 1 | stability_prior_bayes | +0.0523 [+0.0250, +0.0796] MEANINGFUL | **MEANINGFUL** | +1.6173 | +137.6825 | +0.0523 |
| 0.25 | 2 | 1 | 5 | stability_prior_bayes | +0.0532 [+0.0330, +0.0733] MEANINGFUL | **MEANINGFUL** | +2.5043 | +39.2810 | +0.0532 |
| 0.25 | 2 | 2 | 1 | stability_prior_bayes | +0.0465 [+0.0123, +0.0806] INCONCLUSIVE | **INCONCLUSIVE** | +0.5615 | +15.3926 | +0.0465 |
| 0.25 | 2 | 2 | 5 | stability_prior_bayes | +0.0422 [+0.0127, +0.0717] INCONCLUSIVE | **INCONCLUSIVE** | +31.7794 | +31.7794 | +0.0422 |
| 0.25 | 2 | 3 | 1 | stability_prior_bayes | +0.0843 [+0.0474, +0.1211] MEANINGFUL | **MEANINGFUL** | +0.3499 | +0.5865 | +0.0843 |
| 0.25 | 2 | 3 | 5 | stability_prior_bayes | +0.0405 [+0.0125, +0.0685] INCONCLUSIVE | **INCONCLUSIVE** | +0.5135 | +0.5705 | +0.0405 |
| 0.25 | 2 | 5 | 1 | stability_prior_bayes | +0.0542 [+0.0182, +0.0902] INCONCLUSIVE | **INCONCLUSIVE** | +0.1150 | +0.2721 | +0.0542 |
| 0.25 | 2 | 5 | 5 | stability_prior_bayes | +0.0345 [+0.0103, +0.0588] INCONCLUSIVE | **INCONCLUSIVE** | +0.2013 | +0.1972 | +0.0345 |
| 0.25 | 2 | 10 | 1 | stability_prior_bayes | +0.0142 [-0.0261, +0.0545] INCONCLUSIVE | **INCONCLUSIVE** | +0.0195 | +0.0424 | +0.0142 |
| 0.25 | 2 | 10 | 5 | stability_prior_bayes | +0.0297 [+0.0129, +0.0465] INCONCLUSIVE | **INCONCLUSIVE** | +0.0592 | +0.0447 | +0.0297 |
| 0.25 | 2 | 20 | 1 | stability_prior_bayes | +0.0185 [-0.0044, +0.0413] INCONCLUSIVE | **INCONCLUSIVE** | +0.0194 | +0.0178 | +0.0185 |
| 0.25 | 2 | 20 | 5 | ols_gaussian | +0.0357 [+0.0050, +0.0663] INCONCLUSIVE | **INCONCLUSIVE** | +0.0357 | +0.0357 | +0.0003 |
| 0.25 | 4 | 1 | 1 | stability_prior_bayes | +0.0618 [+0.0271, +0.0964] MEANINGFUL | **MEANINGFUL** | +1.6089 | +130.8859 | +0.0618 |
| 0.25 | 4 | 1 | 5 | stability_prior_bayes | +0.0341 [+0.0192, +0.0490] INCONCLUSIVE | **INCONCLUSIVE** | +2.4750 | +39.2439 | +0.0341 |
| 0.25 | 4 | 2 | 1 | stability_prior_bayes | +0.0481 [+0.0094, +0.0867] INCONCLUSIVE | **INCONCLUSIVE** | +0.5491 | +15.3924 | +0.0481 |
| 0.25 | 4 | 2 | 5 | stability_prior_bayes | +0.0319 [+0.0104, +0.0534] INCONCLUSIVE | **INCONCLUSIVE** | +31.9378 | +31.9378 | +0.0319 |
| 0.25 | 4 | 3 | 1 | stability_prior_bayes | +0.0862 [+0.0486, +0.1239] MEANINGFUL | **MEANINGFUL** | +0.3612 | +0.5860 | +0.0862 |
| 0.25 | 4 | 3 | 5 | stability_prior_bayes | +0.0309 [+0.0099, +0.0520] INCONCLUSIVE | **INCONCLUSIVE** | +0.5351 | +0.5351 | +0.0309 |
| 0.25 | 4 | 5 | 1 | stability_prior_bayes | +0.0523 [+0.0151, +0.0896] INCONCLUSIVE | **INCONCLUSIVE** | +0.1069 | +0.2614 | +0.0523 |
| 0.25 | 4 | 5 | 5 | stability_prior_bayes | +0.0193 [-0.0062, +0.0448] INCONCLUSIVE | **INCONCLUSIVE** | +0.1960 | +0.2106 | +0.0193 |
| 0.25 | 4 | 10 | 1 | stability_prior_bayes | +0.0065 [-0.0372, +0.0501] INCONCLUSIVE | **INCONCLUSIVE** | +0.0144 | +0.0349 | +0.0065 |
| 0.25 | 4 | 10 | 5 | stability_prior_bayes | +0.0251 [+0.0059, +0.0443] INCONCLUSIVE | **INCONCLUSIVE** | +0.0647 | +0.0472 | +0.0251 |
| 0.25 | 4 | 20 | 1 | stability_prior_bayes | +0.0084 [-0.0135, +0.0303] INCONCLUSIVE | **INCONCLUSIVE** | +0.0094 | +0.0064 | +0.0084 |
| 0.25 | 4 | 20 | 5 | stability_prior_bayes | -0.0003 [-0.0194, +0.0189] NEGLIGIBLE | **NEGLIGIBLE** | +0.0047 | +0.0368 | -0.0003 |
| 0.25 | 8 | 1 | 1 | stability_prior_bayes | +0.0429 [+0.0076, +0.0782] INCONCLUSIVE | **INCONCLUSIVE** | +1.5892 | +130.7533 | +0.0429 |
| 0.25 | 8 | 1 | 5 | stability_prior_bayes | +0.0231 [+0.0093, +0.0369] INCONCLUSIVE | **INCONCLUSIVE** | +2.4535 | +75.6288 | +0.0231 |
| 0.25 | 8 | 2 | 1 | stability_prior_bayes | +0.0264 [-0.0124, +0.0653] INCONCLUSIVE | **INCONCLUSIVE** | +0.5216 | +15.9488 | +0.0264 |
| 0.25 | 8 | 2 | 5 | stability_prior_bayes | +0.0320 [+0.0133, +0.0507] INCONCLUSIVE | **INCONCLUSIVE** | +32.0017 | +32.0017 | +0.0320 |
| 0.25 | 8 | 3 | 1 | stability_prior_bayes | +0.0570 [+0.0204, +0.0935] MEANINGFUL | **MEANINGFUL** | +0.3264 | +0.5604 | +0.0570 |
| 0.25 | 8 | 3 | 5 | stability_prior_bayes | +0.0297 [+0.0094, +0.0500] INCONCLUSIVE | **INCONCLUSIVE** | +0.5030 | +0.5030 | +0.0297 |
| 0.25 | 8 | 5 | 1 | stability_prior_bayes | +0.0295 [-0.0065, +0.0655] INCONCLUSIVE | **INCONCLUSIVE** | +0.0818 | +0.2341 | +0.0295 |
| 0.25 | 8 | 5 | 5 | stability_prior_bayes | +0.0285 [+0.0124, +0.0447] INCONCLUSIVE | **INCONCLUSIVE** | +0.2170 | +0.2576 | +0.0285 |
| 0.25 | 8 | 10 | 1 | stability_prior_bayes | +0.0120 [-0.0148, +0.0387] INCONCLUSIVE | **INCONCLUSIVE** | +0.0214 | +0.0400 | +0.0120 |
| 0.25 | 8 | 10 | 5 | stability_prior_bayes | +0.0189 [-0.0003, +0.0382] INCONCLUSIVE | **INCONCLUSIVE** | +0.0590 | +0.0442 | +0.0189 |
| 0.25 | 8 | 20 | 1 | stability_prior_bayes | +0.0022 [-0.0144, +0.0187] NEGLIGIBLE | **NEGLIGIBLE** | +0.0032 | +0.0045 | +0.0022 |
| 0.25 | 8 | 20 | 5 | stability_prior_bayes | -0.0018 [-0.0204, +0.0168] NEGLIGIBLE | **NEGLIGIBLE** | +0.0028 | +0.0384 | -0.0018 |
| 1 | 2 | 1 | 1 | stability_prior_bayes | +0.0576 [+0.0286, +0.0865] MEANINGFUL | **MEANINGFUL** | +0.7988 | +156.1638 | +0.0576 |
| 1 | 2 | 1 | 5 | stability_prior_bayes | +0.0531 [+0.0331, +0.0732] MEANINGFUL | **MEANINGFUL** | +1.2528 | +28.5981 | +0.0531 |
| 1 | 2 | 2 | 1 | stability_prior_bayes | +0.0399 [+0.0060, +0.0738] INCONCLUSIVE | **INCONCLUSIVE** | +0.2800 | +1.7334 | +0.0399 |
| 1 | 2 | 2 | 5 | stability_prior_bayes | +0.0384 [+0.0122, +0.0645] INCONCLUSIVE | **INCONCLUSIVE** | +0.5438 | +1.4375 | +0.0384 |
| 1 | 2 | 3 | 1 | stability_prior_bayes | +0.0835 [+0.0477, +0.1193] MEANINGFUL | **MEANINGFUL** | +0.2444 | +0.4982 | +0.0835 |
| 1 | 2 | 3 | 5 | stability_prior_bayes | +0.0363 [+0.0096, +0.0630] INCONCLUSIVE | **INCONCLUSIVE** | +0.3311 | +0.5609 | +0.0363 |
| 1 | 2 | 5 | 1 | stability_prior_bayes | +0.0497 [+0.0171, +0.0824] INCONCLUSIVE | **INCONCLUSIVE** | +0.0860 | +0.2514 | +0.0497 |
| 1 | 2 | 5 | 5 | stability_prior_bayes | +0.0302 [+0.0082, +0.0523] INCONCLUSIVE | **INCONCLUSIVE** | +0.1427 | +0.1508 | +0.0302 |
| 1 | 2 | 10 | 1 | stability_prior_bayes | +0.0084 [-0.0303, +0.0471] INCONCLUSIVE | **INCONCLUSIVE** | +0.0114 | +0.0388 | +0.0084 |
| 1 | 2 | 10 | 5 | stability_prior_bayes | +0.0273 [+0.0113, +0.0433] INCONCLUSIVE | **INCONCLUSIVE** | +0.0495 | +0.0421 | +0.0273 |
| 1 | 2 | 20 | 1 | stability_prior_bayes | +0.0205 [-0.0016, +0.0427] INCONCLUSIVE | **INCONCLUSIVE** | +0.0213 | +0.0195 | +0.0205 |
| 1 | 2 | 20 | 5 | ols_gaussian | +0.0373 [+0.0060, +0.0686] INCONCLUSIVE | **INCONCLUSIVE** | +0.0373 | +0.0373 | +0.0011 |
| 1 | 4 | 1 | 1 | stability_prior_bayes | +0.0523 [+0.0189, +0.0857] INCONCLUSIVE | **INCONCLUSIVE** | +0.7900 | +206.0580 | +0.0523 |
| 1 | 4 | 1 | 5 | stability_prior_bayes | +0.0377 [+0.0225, +0.0528] MEANINGFUL | **MEANINGFUL** | +1.2514 | +26.9915 | +0.0377 |
| 1 | 4 | 2 | 1 | stability_prior_bayes | +0.0397 [+0.0024, +0.0769] INCONCLUSIVE | **INCONCLUSIVE** | +0.2766 | +2.4717 | +0.0397 |
| 1 | 4 | 2 | 5 | stability_prior_bayes | +0.0326 [+0.0144, +0.0509] INCONCLUSIVE | **INCONCLUSIVE** | +0.5586 | +2.2756 | +0.0326 |
| 1 | 4 | 3 | 1 | stability_prior_bayes | +0.0878 [+0.0517, +0.1238] MEANINGFUL | **MEANINGFUL** | +0.2559 | +0.4967 | +0.0878 |
| 1 | 4 | 3 | 5 | stability_prior_bayes | +0.0312 [+0.0115, +0.0510] INCONCLUSIVE | **INCONCLUSIVE** | +0.3473 | +0.5981 | +0.0312 |
| 1 | 4 | 5 | 1 | stability_prior_bayes | +0.0456 [+0.0122, +0.0789] INCONCLUSIVE | **INCONCLUSIVE** | +0.0767 | +0.2430 | +0.0456 |
| 1 | 4 | 5 | 5 | stability_prior_bayes | +0.0164 [-0.0071, +0.0400] INCONCLUSIVE | **INCONCLUSIVE** | +0.1375 | +0.1561 | +0.0164 |
| 1 | 4 | 10 | 1 | stability_prior_bayes | +0.0001 [-0.0421, +0.0423] INCONCLUSIVE | **INCONCLUSIVE** | +0.0058 | +0.0317 | +0.0001 |
| 1 | 4 | 10 | 5 | stability_prior_bayes | +0.0236 [+0.0049, +0.0422] INCONCLUSIVE | **INCONCLUSIVE** | +0.0550 | +0.0419 | +0.0236 |
| 1 | 4 | 20 | 1 | stability_prior_bayes | +0.0099 [-0.0113, +0.0311] INCONCLUSIVE | **INCONCLUSIVE** | +0.0108 | +0.0076 | +0.0099 |
| 1 | 4 | 20 | 5 | stability_prior_bayes | +0.0005 [-0.0174, +0.0183] NEGLIGIBLE | **NEGLIGIBLE** | +0.0051 | +0.0385 | +0.0005 |
| 1 | 8 | 1 | 1 | stability_prior_bayes | +0.0296 [-0.0051, +0.0643] INCONCLUSIVE | **INCONCLUSIVE** | +0.7648 | +1217.3714 | +0.0296 |
| 1 | 8 | 1 | 5 | stability_prior_bayes | +0.0250 [+0.0088, +0.0413] INCONCLUSIVE | **INCONCLUSIVE** | +1.2471 | +355.7303 | +0.0250 |
| 1 | 8 | 2 | 1 | stability_prior_bayes | +0.0211 [-0.0148, +0.0570] INCONCLUSIVE | **INCONCLUSIVE** | +0.2669 | +2.1067 | +0.0211 |
| 1 | 8 | 2 | 5 | stability_prior_bayes | +0.0340 [+0.0177, +0.0502] INCONCLUSIVE | **INCONCLUSIVE** | +0.5782 | +1.5062 | +0.0340 |
| 1 | 8 | 3 | 1 | stability_prior_bayes | +0.0576 [+0.0223, +0.0928] MEANINGFUL | **MEANINGFUL** | +0.2254 | +0.4657 | +0.0576 |
| 1 | 8 | 3 | 5 | stability_prior_bayes | +0.0305 [+0.0107, +0.0504] INCONCLUSIVE | **INCONCLUSIVE** | +0.3571 | +0.5537 | +0.0305 |
| 1 | 8 | 5 | 1 | stability_prior_bayes | +0.0261 [-0.0060, +0.0583] INCONCLUSIVE | **INCONCLUSIVE** | +0.0578 | +0.2229 | +0.0261 |
| 1 | 8 | 5 | 5 | stability_prior_bayes | +0.0273 [+0.0126, +0.0421] INCONCLUSIVE | **INCONCLUSIVE** | +0.1616 | +0.2041 | +0.0273 |
| 1 | 8 | 10 | 1 | stability_prior_bayes | +0.0071 [-0.0185, +0.0326] INCONCLUSIVE | **INCONCLUSIVE** | +0.0133 | +0.0377 | +0.0071 |
| 1 | 8 | 10 | 5 | stability_prior_bayes | +0.0174 [-0.0016, +0.0364] INCONCLUSIVE | **INCONCLUSIVE** | +0.0479 | +0.0395 | +0.0174 |
| 1 | 8 | 20 | 1 | stability_prior_bayes | +0.0039 [-0.0120, +0.0199] NEGLIGIBLE | **NEGLIGIBLE** | +0.0049 | +0.0066 | +0.0039 |
| 1 | 8 | 20 | 5 | stability_prior_bayes | +0.0001 [-0.0165, +0.0167] NEGLIGIBLE | **NEGLIGIBLE** | +0.0045 | +0.0418 | +0.0001 |
| 4 | 2 | 1 | 1 | stability_prior_bayes | +0.0679 [+0.0375, +0.0982] MEANINGFUL | **MEANINGFUL** | +0.2930 | +94.3917 | +0.0679 |
| 4 | 2 | 1 | 5 | stability_prior_bayes | +0.0419 [+0.0236, +0.0602] MEANINGFUL | **MEANINGFUL** | +0.4237 | +39.2655 | +0.0419 |
| 4 | 2 | 2 | 1 | stability_prior_bayes | +0.0241 [-0.0056, +0.0538] INCONCLUSIVE | **INCONCLUSIVE** | +0.1127 | +2.6737 | +0.0241 |
| 4 | 2 | 2 | 5 | stability_prior_bayes | +0.0223 [+0.0045, +0.0401] INCONCLUSIVE | **INCONCLUSIVE** | +0.1945 | +1.2453 | +0.0223 |
| 4 | 2 | 3 | 1 | stability_prior_bayes | +0.0421 [+0.0164, +0.0679] INCONCLUSIVE | **INCONCLUSIVE** | +0.0925 | +0.3639 | +0.0421 |
| 4 | 2 | 3 | 5 | stability_prior_bayes | +0.0208 [+0.0014, +0.0402] INCONCLUSIVE | **INCONCLUSIVE** | +0.1172 | +0.3175 | +0.0208 |
| 4 | 2 | 5 | 1 | stability_prior_bayes | +0.0385 [+0.0132, +0.0638] INCONCLUSIVE | **INCONCLUSIVE** | +0.0528 | +0.2394 | +0.0385 |
| 4 | 2 | 5 | 5 | stability_prior_bayes | +0.0164 [+0.0004, +0.0324] INCONCLUSIVE | **INCONCLUSIVE** | +0.0588 | +0.1209 | +0.0164 |
| 4 | 2 | 10 | 1 | stability_prior_bayes | +0.0004 [-0.0333, +0.0340] INCONCLUSIVE | **INCONCLUSIVE** | +0.0016 | +0.0354 | +0.0004 |
| 4 | 2 | 10 | 5 | stability_prior_bayes | +0.0162 [+0.0030, +0.0294] INCONCLUSIVE | **INCONCLUSIVE** | +0.0252 | +0.0369 | +0.0162 |
| 4 | 2 | 20 | 1 | stability_prior_bayes | +0.0183 [+0.0006, +0.0361] INCONCLUSIVE | **INCONCLUSIVE** | +0.0187 | +0.0177 | +0.0183 |
| 4 | 2 | 20 | 5 | stability_prior_bayes | +0.0015 [-0.0141, +0.0170] NEGLIGIBLE | **NEGLIGIBLE** | +0.0028 | +0.0414 | +0.0015 |
| 4 | 4 | 1 | 1 | stability_prior_bayes | +0.0547 [+0.0251, +0.0842] MEANINGFUL | **MEANINGFUL** | +0.2890 | +543.5414 | +0.0547 |
| 4 | 4 | 1 | 5 | stability_prior_bayes | +0.0466 [+0.0297, +0.0635] MEANINGFUL | **MEANINGFUL** | +0.4535 | +110.0913 | +0.0466 |
| 4 | 4 | 2 | 1 | stability_prior_bayes | +0.0260 [-0.0043, +0.0564] INCONCLUSIVE | **INCONCLUSIVE** | +0.1171 | +0.7561 | +0.0260 |
| 4 | 4 | 2 | 5 | stability_prior_bayes | +0.0252 [+0.0101, +0.0403] INCONCLUSIVE | **INCONCLUSIVE** | +0.2153 | +1.0567 | +0.0252 |
| 4 | 4 | 3 | 1 | stability_prior_bayes | +0.0463 [+0.0218, +0.0708] MEANINGFUL | **MEANINGFUL** | +0.1027 | +0.3807 | +0.0463 |
| 4 | 4 | 3 | 5 | stability_prior_bayes | +0.0224 [+0.0061, +0.0386] INCONCLUSIVE | **INCONCLUSIVE** | +0.1325 | +0.3592 | +0.0224 |
| 4 | 4 | 5 | 1 | stability_prior_bayes | +0.0339 [+0.0086, +0.0592] INCONCLUSIVE | **INCONCLUSIVE** | +0.0434 | +0.2318 | +0.0339 |
| 4 | 4 | 5 | 5 | stability_prior_bayes | +0.0090 [-0.0049, +0.0229] INCONCLUSIVE | **INCONCLUSIVE** | +0.0551 | +0.1249 | +0.0090 |
| 4 | 4 | 10 | 1 | stability_prior_bayes | -0.0080 [-0.0445, +0.0285] INCONCLUSIVE | **INCONCLUSIVE** | -0.0061 | +0.0242 | -0.0080 |
| 4 | 4 | 10 | 5 | stability_prior_bayes | +0.0133 [-0.0029, +0.0294] INCONCLUSIVE | **INCONCLUSIVE** | +0.0267 | +0.0377 | +0.0133 |
| 4 | 4 | 20 | 1 | stability_prior_bayes | +0.0083 [-0.0090, +0.0257] INCONCLUSIVE | **INCONCLUSIVE** | +0.0086 | +0.0069 | +0.0083 |
| 4 | 4 | 20 | 5 | stability_prior_bayes | +0.0028 [-0.0108, +0.0163] NEGLIGIBLE | **NEGLIGIBLE** | +0.0056 | +0.0406 | +0.0028 |
| 4 | 8 | 1 | 1 | stability_prior_bayes | +0.0483 [+0.0170, +0.0796] INCONCLUSIVE | **INCONCLUSIVE** | +0.3017 | +21.4237 | +0.0483 |
| 4 | 8 | 1 | 5 | stability_prior_bayes | +0.0443 [+0.0204, +0.0682] MEANINGFUL | **MEANINGFUL** | +0.4766 | +13.3061 | +0.0443 |
| 4 | 8 | 2 | 1 | stability_prior_bayes | +0.0097 [-0.0228, +0.0421] INCONCLUSIVE | **INCONCLUSIVE** | +0.1051 | +1.1758 | +0.0097 |
| 4 | 8 | 2 | 5 | stability_prior_bayes | +0.0342 [+0.0184, +0.0499] INCONCLUSIVE | **INCONCLUSIVE** | +0.2354 | +1.1296 | +0.0342 |
| 4 | 8 | 3 | 1 | stability_prior_bayes | +0.0437 [+0.0137, +0.0738] INCONCLUSIVE | **INCONCLUSIVE** | +0.1026 | +0.3462 | +0.0437 |
| 4 | 8 | 3 | 5 | stability_prior_bayes | +0.0278 [+0.0093, +0.0463] INCONCLUSIVE | **INCONCLUSIVE** | +0.1438 | +0.3288 | +0.0278 |
| 4 | 8 | 5 | 1 | stability_prior_bayes | +0.0226 [-0.0023, +0.0475] INCONCLUSIVE | **INCONCLUSIVE** | +0.0339 | +0.2225 | +0.0226 |
| 4 | 8 | 5 | 5 | stability_prior_bayes | +0.0247 [+0.0128, +0.0366] INCONCLUSIVE | **INCONCLUSIVE** | +0.0786 | +0.1558 | +0.0247 |
| 4 | 8 | 10 | 1 | stability_prior_bayes | +0.0014 [-0.0187, +0.0216] INCONCLUSIVE | **INCONCLUSIVE** | +0.0043 | +0.0348 | +0.0014 |
| 4 | 8 | 10 | 5 | stability_prior_bayes | +0.0113 [-0.0065, +0.0290] INCONCLUSIVE | **INCONCLUSIVE** | +0.0230 | +0.0304 | +0.0113 |
| 4 | 8 | 20 | 1 | stability_prior_bayes | +0.0085 [-0.0046, +0.0215] INCONCLUSIVE | **INCONCLUSIVE** | +0.0088 | +0.0124 | +0.0085 |
| 4 | 8 | 20 | 5 | stability_prior_bayes | +0.0039 [-0.0092, +0.0171] NEGLIGIBLE | **NEGLIGIBLE** | +0.0063 | +0.0421 | +0.0039 |

## Secondary: finite library - continuous-prior Bayes

E-CONT: library (mismatched) - continuous (matched). E-LIB: library (matched) - continuous (mismatched).

| condition | r | K | n | h | R1: mean [interval] class | confirmed |
|---|---|---|---|---|---|---|
| E-CONT | 0.25 | 2 | 1 | 1 | -0.0088 [-0.0271, +0.0095] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 1 | 5 | -0.0064 [-0.0357, +0.0229] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 2 | 1 | -0.0062 [-0.0280, +0.0156] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 2 | 5 | -0.0306 [-0.0622, +0.0010] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 3 | 1 | -0.0098 [-0.0336, +0.0139] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 3 | 5 | -0.0389 [-0.0764, -0.0013] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 5 | 1 | -0.0243 [-0.0562, +0.0076] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 5 | 5 | -0.0131 [-0.0420, +0.0157] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 10 | 1 | -0.0464 [-0.0840, -0.0088] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 10 | 5 | -0.0161 [-0.0484, +0.0161] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 20 | 1 | -0.0108 [-0.0438, +0.0222] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 2 | 20 | 5 | -0.0637 [-0.1608, +0.0334] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 1 | 1 | -0.0063 [-0.0147, +0.0021] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 1 | 5 | -0.0000 [-0.0132, +0.0131] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 2 | 1 | -0.0000 [-0.0115, +0.0115] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 2 | 5 | -0.0059 [-0.0208, +0.0091] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 3 | 1 | -0.0017 [-0.0140, +0.0105] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 3 | 5 | -0.0117 [-0.0304, +0.0069] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 5 | 1 | -0.0065 [-0.0205, +0.0074] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 5 | 5 | -0.0017 [-0.0155, +0.0120] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 10 | 1 | -0.0083 [-0.0260, +0.0093] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 10 | 5 | +0.0013 [-0.0141, +0.0166] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 4 | 20 | 1 | +0.0119 [-0.0056, +0.0294] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 4 | 20 | 5 | -0.0271 [-0.0837, +0.0295] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 8 | 1 | 1 | -0.0017 [-0.0049, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 1 | 5 | -0.0008 [-0.0085, +0.0068] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 2 | 1 | +0.0018 [-0.0027, +0.0064] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 2 | 5 | +0.0013 [-0.0080, +0.0106] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 3 | 1 | -0.0048 [-0.0110, +0.0015] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 3 | 5 | -0.0037 [-0.0159, +0.0085] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 5 | 1 | -0.0001 [-0.0080, +0.0078] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 5 | 5 | +0.0015 [-0.0073, +0.0103] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 10 | 1 | -0.0011 [-0.0120, +0.0099] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 10 | 5 | +0.0040 [-0.0072, +0.0152] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 0.25 | 8 | 20 | 1 | -0.0101 [-0.0228, +0.0027] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 0.25 | 8 | 20 | 5 | -0.0216 [-0.0722, +0.0290] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 1 | 1 | -0.0197 [-0.0448, +0.0054] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 1 | 5 | -0.0102 [-0.0467, +0.0263] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 2 | 1 | -0.0071 [-0.0334, +0.0191] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 2 | 5 | -0.0284 [-0.0603, +0.0035] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 3 | 1 | -0.0112 [-0.0353, +0.0130] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 3 | 5 | -0.0431 [-0.0816, -0.0046] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 5 | 1 | -0.0251 [-0.0586, +0.0084] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 5 | 5 | -0.0149 [-0.0422, +0.0125] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 10 | 1 | -0.0498 [-0.0871, -0.0125] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 10 | 5 | -0.0152 [-0.0473, +0.0170] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 20 | 1 | -0.0098 [-0.0425, +0.0228] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 2 | 20 | 5 | -0.0617 [-0.1572, +0.0338] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 1 | 1 | -0.0095 [-0.0205, +0.0015] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 1 | 5 | -0.0021 [-0.0208, +0.0166] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 2 | 1 | +0.0004 [-0.0128, +0.0136] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 2 | 5 | -0.0043 [-0.0197, +0.0110] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 3 | 1 | -0.0032 [-0.0164, +0.0099] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 3 | 5 | -0.0142 [-0.0333, +0.0049] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 5 | 1 | -0.0068 [-0.0214, +0.0079] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 5 | 5 | -0.0025 [-0.0148, +0.0098] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 10 | 1 | -0.0106 [-0.0279, +0.0067] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 10 | 5 | +0.0016 [-0.0137, +0.0170] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 4 | 20 | 1 | +0.0125 [-0.0047, +0.0297] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 4 | 20 | 5 | -0.0258 [-0.0812, +0.0296] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 8 | 1 | 1 | -0.0008 [-0.0050, +0.0033] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 1 | 5 | -0.0021 [-0.0146, +0.0105] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 2 | 1 | +0.0010 [-0.0051, +0.0071] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 2 | 5 | +0.0025 [-0.0071, +0.0122] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 3 | 1 | -0.0060 [-0.0132, +0.0012] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 3 | 5 | -0.0050 [-0.0176, +0.0075] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 5 | 1 | -0.0019 [-0.0101, +0.0062] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 5 | 5 | +0.0011 [-0.0063, +0.0084] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 10 | 1 | -0.0003 [-0.0112, +0.0106] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 10 | 5 | +0.0043 [-0.0071, +0.0157] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 1 | 8 | 20 | 1 | -0.0106 [-0.0231, +0.0019] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 1 | 8 | 20 | 5 | -0.0204 [-0.0699, +0.0292] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 1 | 1 | -0.1183 [-0.2023, -0.0343] DISTINGUISHABLE | **DISTINGUISHABLE** |
| E-CONT | 4 | 2 | 1 | 5 | -0.0720 [-0.1843, +0.0404] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 2 | 1 | -0.0575 [-0.1231, +0.0081] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 2 | 5 | -0.0594 [-0.1323, +0.0135] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 3 | 1 | -0.0455 [-0.0924, +0.0014] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 3 | 5 | -0.0842 [-0.1608, -0.0077] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 5 | 1 | -0.0566 [-0.1206, +0.0074] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 5 | 5 | -0.0375 [-0.0848, +0.0098] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 10 | 1 | -0.0573 [-0.0953, -0.0193] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 10 | 5 | -0.0187 [-0.0541, +0.0167] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 20 | 1 | -0.0119 [-0.0451, +0.0214] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 2 | 20 | 5 | -0.0569 [-0.1467, +0.0330] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 1 | 1 | -0.0224 [-0.0515, +0.0067] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 1 | 5 | -0.0305 [-0.0931, +0.0320] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 2 | 1 | -0.0042 [-0.0295, +0.0210] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 2 | 5 | -0.0196 [-0.0576, +0.0184] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 3 | 1 | -0.0110 [-0.0289, +0.0069] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 3 | 5 | -0.0361 [-0.0766, +0.0044] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 5 | 1 | -0.0180 [-0.0445, +0.0086] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 5 | 5 | -0.0126 [-0.0366, +0.0115] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 10 | 1 | -0.0139 [-0.0311, +0.0034] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 10 | 5 | -0.0025 [-0.0201, +0.0151] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 20 | 1 | +0.0116 [-0.0055, +0.0287] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 4 | 20 | 5 | -0.0226 [-0.0734, +0.0281] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 1 | 1 | +0.0002 [-0.0224, +0.0228] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 1 | 5 | -0.0279 [-0.0816, +0.0258] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 2 | 1 | -0.0058 [-0.0250, +0.0134] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 2 | 5 | -0.0122 [-0.0436, +0.0193] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 3 | 1 | -0.0067 [-0.0189, +0.0055] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 3 | 5 | -0.0267 [-0.0603, +0.0068] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 5 | 1 | -0.0119 [-0.0337, +0.0098] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 5 | 5 | -0.0091 [-0.0292, +0.0111] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 10 | 1 | -0.0027 [-0.0142, +0.0088] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 10 | 5 | +0.0013 [-0.0128, +0.0154] EQUIVALENT | **EQUIVALENT** |
| E-CONT | 4 | 8 | 20 | 1 | -0.0101 [-0.0224, +0.0021] INCONCLUSIVE | **INCONCLUSIVE** |
| E-CONT | 4 | 8 | 20 | 5 | -0.0175 [-0.0627, +0.0277] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 1 | 1 | +0.0146 [+0.0045, +0.0246] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 1 | 5 | +0.0190 [+0.0075, +0.0305] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 2 | 1 | +0.0047 [-0.0114, +0.0207] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 2 | 5 | +0.0122 [-0.0026, +0.0269] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 3 | 1 | +0.0214 [+0.0041, +0.0388] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 3 | 5 | +0.0086 [-0.0092, +0.0264] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 5 | 1 | +0.0024 [-0.0118, +0.0167] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 5 | 5 | +0.0116 [-0.0040, +0.0271] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 10 | 1 | +0.0110 [-0.0056, +0.0276] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 10 | 5 | +0.0158 [+0.0044, +0.0272] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 2 | 20 | 1 | +0.0053 [-0.0065, +0.0171] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 2 | 20 | 5 | -0.0046 [-0.0187, +0.0094] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 1 | 1 | +0.0049 [+0.0006, +0.0092] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 1 | 5 | +0.0087 [+0.0045, +0.0129] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 2 | 1 | +0.0003 [-0.0074, +0.0080] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 2 | 5 | +0.0062 [+0.0002, +0.0122] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 3 | 1 | +0.0129 [+0.0037, +0.0221] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 0.25 | 4 | 3 | 5 | +0.0027 [-0.0076, +0.0130] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 5 | 1 | +0.0017 [-0.0076, +0.0109] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 5 | 5 | +0.0016 [-0.0136, +0.0169] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 10 | 1 | +0.0004 [-0.0162, +0.0170] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 10 | 5 | +0.0080 [-0.0029, +0.0189] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 20 | 1 | +0.0021 [-0.0078, +0.0119] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 4 | 20 | 5 | -0.0038 [-0.0156, +0.0080] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 1 | 1 | +0.0004 [-0.0025, +0.0032] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 1 | 5 | +0.0055 [+0.0025, +0.0085] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 2 | 1 | +0.0015 [-0.0042, +0.0071] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 2 | 5 | +0.0050 [+0.0026, +0.0074] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 3 | 1 | +0.0078 [+0.0015, +0.0141] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 3 | 5 | +0.0019 [-0.0062, +0.0101] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 5 | 1 | +0.0057 [-0.0017, +0.0131] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 5 | 5 | +0.0059 [-0.0001, +0.0120] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 10 | 1 | +0.0066 [-0.0032, +0.0165] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 10 | 5 | +0.0005 [-0.0086, +0.0096] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 20 | 1 | +0.0042 [-0.0059, +0.0144] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 0.25 | 8 | 20 | 5 | -0.0006 [-0.0102, +0.0090] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 1 | 1 | +0.0199 [+0.0076, +0.0323] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 1 | 5 | +0.0189 [+0.0069, +0.0308] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 2 | 1 | +0.0032 [-0.0136, +0.0200] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 2 | 5 | +0.0103 [-0.0043, +0.0250] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 3 | 1 | +0.0222 [+0.0042, +0.0402] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 3 | 5 | +0.0085 [-0.0088, +0.0258] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 5 | 1 | +0.0038 [-0.0104, +0.0179] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 5 | 5 | +0.0107 [-0.0033, +0.0247] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 10 | 1 | +0.0098 [-0.0064, +0.0260] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 10 | 5 | +0.0151 [+0.0040, +0.0262] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 2 | 20 | 1 | +0.0068 [-0.0049, +0.0185] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 2 | 20 | 5 | -0.0038 [-0.0179, +0.0102] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 1 | 1 | +0.0057 [-0.0004, +0.0117] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 1 | 5 | +0.0100 [+0.0049, +0.0150] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 2 | 1 | -0.0009 [-0.0102, +0.0085] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 2 | 5 | +0.0059 [-0.0005, +0.0123] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 3 | 1 | +0.0158 [+0.0059, +0.0258] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 1 | 4 | 3 | 5 | +0.0039 [-0.0064, +0.0143] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 5 | 1 | +0.0026 [-0.0064, +0.0116] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 5 | 5 | +0.0017 [-0.0114, +0.0148] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 10 | 1 | -0.0012 [-0.0177, +0.0152] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 10 | 5 | +0.0076 [-0.0029, +0.0181] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 20 | 1 | +0.0030 [-0.0066, +0.0127] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 4 | 20 | 5 | -0.0026 [-0.0133, +0.0082] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 1 | 1 | +0.0023 [-0.0021, +0.0066] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 1 | 5 | +0.0052 [-0.0005, +0.0108] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 2 | 1 | +0.0001 [-0.0071, +0.0073] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 2 | 5 | +0.0047 [+0.0011, +0.0083] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 3 | 1 | +0.0081 [+0.0004, +0.0157] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 3 | 5 | +0.0027 [-0.0060, +0.0114] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 5 | 1 | +0.0067 [-0.0012, +0.0146] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 5 | 5 | +0.0062 [+0.0007, +0.0117] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 10 | 1 | +0.0060 [-0.0038, +0.0158] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 10 | 5 | +0.0003 [-0.0087, +0.0093] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 20 | 1 | +0.0053 [-0.0050, +0.0157] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 1 | 8 | 20 | 5 | +0.0008 [-0.0078, +0.0094] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 1 | 1 | +0.0343 [+0.0162, +0.0523] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 2 | 1 | 5 | +0.0162 [+0.0044, +0.0279] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 2 | 2 | 1 | +0.0005 [-0.0168, +0.0179] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 2 | 5 | +0.0049 [-0.0072, +0.0170] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 3 | 1 | +0.0129 [-0.0034, +0.0293] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 2 | 3 | 5 | +0.0055 [-0.0072, +0.0181] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 5 | 1 | +0.0063 [-0.0056, +0.0181] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 5 | 5 | +0.0071 [-0.0027, +0.0170] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 10 | 1 | +0.0071 [-0.0078, +0.0220] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 2 | 10 | 5 | +0.0100 [+0.0006, +0.0195] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 20 | 1 | +0.0079 [-0.0023, +0.0181] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 2 | 20 | 5 | -0.0020 [-0.0142, +0.0102] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 1 | 1 | +0.0143 [+0.0031, +0.0254] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 4 | 1 | 5 | +0.0156 [+0.0076, +0.0235] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 4 | 2 | 1 | +0.0002 [-0.0111, +0.0115] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 2 | 5 | +0.0046 [-0.0033, +0.0125] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 3 | 1 | +0.0121 [+0.0028, +0.0213] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 4 | 3 | 5 | +0.0056 [-0.0025, +0.0138] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 5 | 1 | +0.0052 [-0.0027, +0.0131] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 5 | 5 | +0.0029 [-0.0033, +0.0091] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 10 | 1 | -0.0037 [-0.0192, +0.0118] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 10 | 5 | +0.0040 [-0.0052, +0.0132] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 20 | 1 | +0.0031 [-0.0055, +0.0116] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 4 | 20 | 5 | +0.0000 [-0.0085, +0.0085] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 1 | 1 | +0.0132 [+0.0008, +0.0255] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 8 | 1 | 5 | +0.0106 [-0.0032, +0.0244] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 8 | 2 | 1 | -0.0071 [-0.0192, +0.0050] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 2 | 5 | +0.0055 [-0.0023, +0.0134] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 3 | 1 | +0.0159 [+0.0027, +0.0292] INCONCLUSIVE | **INCONCLUSIVE** |
| E-LIB | 4 | 8 | 3 | 5 | +0.0076 [-0.0015, +0.0167] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 5 | 1 | +0.0054 [-0.0031, +0.0139] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 5 | 5 | +0.0080 [+0.0022, +0.0138] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 10 | 1 | +0.0044 [-0.0050, +0.0138] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 10 | 5 | +0.0011 [-0.0078, +0.0100] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 20 | 1 | +0.0072 [-0.0022, +0.0166] EQUIVALENT | **EQUIVALENT** |
| E-LIB | 4 | 8 | 20 | 5 | +0.0016 [-0.0067, +0.0100] EQUIVALENT | **EQUIVALENT** |

Secondary confirmed-class counts: E-CONT: {'INCONCLUSIVE': 73, 'EQUIVALENT': 34, 'DISTINGUISHABLE': 1}; E-LIB: {'INCONCLUSIVE': 29, 'EQUIVALENT': 79}

## Sensitivity of the primary classification to the effect threshold (confirmed MEANINGFUL cells, E-CONT)

- threshold 0.01 nats: 3/36 cells
- threshold 0.04 nats: 0/36 cells

## Baseline performance and calibration (E-CONT, replicate R1)

| r | n | h | predictor | mean log score | coverage 0.5 / 0.8 / 0.95 | PIT KS p | fallback | quad cap |
|---|---|---|---|---|---|---|---|---|
| 0.25 | 1 | 1 | matched_reference | -1.4440 | 0.497 / 0.797 / 0.947 | 3.68e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 1 | flat_prior_bayes | -3.1292 | 0.450 / 0.807 / 0.953 | 2.91e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 1 | ols_gaussian | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 1.00 | nan |
| 0.25 | 1 | 1 | ols_student_t | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_rolling_origin | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_blocked | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 1.00 | nan |
| 0.25 | 1 | 1 | kernel_leave_one_out | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 1.00 | nan |
| 0.25 | 1 | 1 | persistence | -18.9058 | 0.323 / 0.510 / 0.637 | 8.41e-09 | 0.00 | nan |
| 0.25 | 1 | 1 | stability_prior_bayes | -1.4784 | 0.537 / 0.810 / 0.967 | 2.65e-01 | 0.00 | 0.000 |
| 0.25 | 1 | 5 | matched_reference | -1.5500 | 0.547 / 0.813 / 0.947 | 9.40e-02 | 0.00 | 0.000 |
| 0.25 | 1 | 5 | flat_prior_bayes | -4.1183 | 0.543 / 0.823 / 0.937 | 5.49e-01 | 0.00 | 0.083 |
| 0.25 | 1 | 5 | ols_gaussian | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 1.00 | nan |
| 0.25 | 1 | 5 | ols_student_t | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_rolling_origin | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_blocked | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 1.00 | nan |
| 0.25 | 1 | 5 | kernel_leave_one_out | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 1.00 | nan |
| 0.25 | 1 | 5 | persistence | -5.6385 | 0.503 / 0.733 / 0.837 | 4.24e-02 | 0.00 | nan |
| 0.25 | 1 | 5 | stability_prior_bayes | -1.5660 | 0.587 / 0.853 / 0.973 | 1.95e-02 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | matched_reference | -1.4326 | 0.510 / 0.830 / 0.953 | 1.71e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | flat_prior_bayes | -2.0005 | 0.463 / 0.780 / 0.917 | 7.91e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 1 | ols_gaussian | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 1.00 | nan |
| 0.25 | 2 | 1 | ols_student_t | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_rolling_origin | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_blocked | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 1.00 | nan |
| 0.25 | 2 | 1 | kernel_leave_one_out | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 1.00 | nan |
| 0.25 | 2 | 1 | persistence | -15.3105 | 0.397 / 0.633 / 0.787 | 1.08e-02 | 0.00 | nan |
| 0.25 | 2 | 1 | stability_prior_bayes | -1.4839 | 0.533 / 0.823 / 0.943 | 1.86e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 5 | matched_reference | -1.6675 | 0.453 / 0.757 / 0.933 | 1.30e-01 | 0.00 | 0.000 |
| 0.25 | 2 | 5 | flat_prior_bayes | -2.6151 | 0.580 / 0.833 / 0.960 | 6.55e-02 | 0.00 | 0.000 |
| 0.25 | 2 | 5 | ols_gaussian | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 1.00 | nan |
| 0.25 | 2 | 5 | ols_student_t | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_rolling_origin | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_blocked | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 1.00 | nan |
| 0.25 | 2 | 5 | kernel_leave_one_out | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 1.00 | nan |
| 0.25 | 2 | 5 | persistence | -2.4649 | 0.587 / 0.820 / 0.920 | 5.94e-02 | 0.00 | nan |
| 0.25 | 2 | 5 | stability_prior_bayes | -1.6715 | 0.493 / 0.810 / 0.957 | 2.48e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | matched_reference | -1.4549 | 0.520 / 0.773 / 0.943 | 6.42e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | flat_prior_bayes | -1.7119 | 0.483 / 0.790 / 0.970 | 2.98e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 1 | ols_gaussian | -8.4341 | 0.320 / 0.593 / 0.730 | 1.23e-04 | 0.00 | nan |
| 0.25 | 3 | 1 | ols_student_t | -1.9513 | 0.523 / 0.823 / 0.970 | 3.11e-01 | 0.00 | nan |
| 0.25 | 3 | 1 | kernel_rolling_origin | -2.8650 | 0.337 / 0.613 / 0.820 | 6.03e-05 | 1.00 | nan |
| 0.25 | 3 | 1 | kernel_blocked | -2.8650 | 0.337 / 0.613 / 0.820 | 6.03e-05 | 1.00 | nan |
| 0.25 | 3 | 1 | kernel_leave_one_out | -3.1718 | 0.353 / 0.590 / 0.787 | 4.89e-05 | 0.00 | nan |
| 0.25 | 3 | 1 | persistence | -2.8341 | 0.380 / 0.663 / 0.803 | 8.44e-04 | 0.00 | nan |
| 0.25 | 3 | 1 | stability_prior_bayes | -1.5020 | 0.517 / 0.763 / 0.950 | 6.99e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | matched_reference | -1.6456 | 0.463 / 0.797 / 0.937 | 4.70e-01 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | flat_prior_bayes | -2.1165 | 0.630 / 0.897 / 0.983 | 4.92e-02 | 0.00 | 0.000 |
| 0.25 | 3 | 5 | ols_gaussian | -7.0488 | 0.360 / 0.613 / 0.750 | 3.25e-04 | 0.00 | nan |
| 0.25 | 3 | 5 | ols_student_t | -2.5484 | 0.603 / 0.870 / 0.987 | 9.44e-02 | 0.00 | nan |
| 0.25 | 3 | 5 | kernel_rolling_origin | -2.2109 | 0.590 / 0.860 / 0.940 | 1.19e-02 | 1.00 | nan |
| 0.25 | 3 | 5 | kernel_blocked | -2.2109 | 0.590 / 0.860 / 0.940 | 1.19e-02 | 1.00 | nan |
| 0.25 | 3 | 5 | kernel_leave_one_out | -2.2109 | 0.590 / 0.860 / 0.940 | 1.19e-02 | 1.00 | nan |
| 0.25 | 3 | 5 | persistence | -2.2109 | 0.590 / 0.860 / 0.940 | 1.19e-02 | 0.00 | nan |
| 0.25 | 3 | 5 | stability_prior_bayes | -1.6470 | 0.497 / 0.840 / 0.960 | 5.30e-01 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | matched_reference | -1.4186 | 0.543 / 0.807 / 0.943 | 6.77e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | flat_prior_bayes | -1.5347 | 0.563 / 0.810 / 0.953 | 7.51e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 1 | ols_gaussian | -2.2278 | 0.477 / 0.730 / 0.883 | 1.70e-01 | 0.00 | nan |
| 0.25 | 5 | 1 | ols_student_t | -1.6168 | 0.573 / 0.833 / 0.970 | 8.66e-02 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_rolling_origin | -14.7070 | 0.373 / 0.623 / 0.767 | 1.91e-03 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_blocked | -2.1027 | 0.507 / 0.747 / 0.880 | 5.20e-01 | 0.00 | nan |
| 0.25 | 5 | 1 | kernel_leave_one_out | -2.0959 | 0.420 / 0.687 / 0.820 | 2.48e-02 | 0.00 | nan |
| 0.25 | 5 | 1 | persistence | -1.8123 | 0.467 / 0.733 / 0.893 | 1.06e-02 | 0.00 | nan |
| 0.25 | 5 | 1 | stability_prior_bayes | -1.4514 | 0.527 / 0.827 / 0.950 | 6.46e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | matched_reference | -1.5416 | 0.550 / 0.840 / 0.953 | 9.07e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | flat_prior_bayes | -1.7650 | 0.620 / 0.890 / 0.970 | 1.36e-02 | 0.00 | 0.000 |
| 0.25 | 5 | 5 | ols_gaussian | -2.3938 | 0.470 / 0.763 / 0.887 | 2.54e-01 | 0.00 | nan |
| 0.25 | 5 | 5 | ols_student_t | -1.8231 | 0.610 / 0.867 / 0.977 | 3.41e-02 | 0.00 | nan |
| 0.25 | 5 | 5 | kernel_rolling_origin | -70.2296 | 0.280 / 0.537 / 0.677 | 1.39e-08 | 1.00 | nan |
| 0.25 | 5 | 5 | kernel_blocked | -70.2296 | 0.280 / 0.537 / 0.677 | 1.39e-08 | 1.00 | nan |
| 0.25 | 5 | 5 | kernel_leave_one_out | -70.2296 | 0.280 / 0.537 / 0.677 | 1.39e-08 | 1.00 | nan |
| 0.25 | 5 | 5 | persistence | -70.2296 | 0.280 / 0.537 / 0.677 | 1.39e-08 | 0.00 | nan |
| 0.25 | 5 | 5 | stability_prior_bayes | -1.5641 | 0.573 / 0.863 / 0.960 | 4.23e-02 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | matched_reference | -1.3853 | 0.517 / 0.827 / 0.963 | 8.30e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | flat_prior_bayes | -1.4135 | 0.540 / 0.840 / 0.953 | 6.48e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 1 | ols_gaussian | -1.4716 | 0.490 / 0.800 / 0.917 | 7.91e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | ols_student_t | -1.4534 | 0.533 / 0.830 / 0.960 | 6.34e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_rolling_origin | -1.6161 | 0.480 / 0.713 / 0.897 | 1.20e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_blocked | -1.5987 | 0.517 / 0.773 / 0.910 | 9.20e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | kernel_leave_one_out | -1.5627 | 0.477 / 0.703 / 0.907 | 1.41e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | persistence | -1.5400 | 0.533 / 0.797 / 0.950 | 4.68e-01 | 0.00 | nan |
| 0.25 | 10 | 1 | stability_prior_bayes | -1.4025 | 0.537 / 0.840 / 0.953 | 5.95e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | matched_reference | -1.6215 | 0.490 / 0.787 / 0.947 | 1.73e-01 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | flat_prior_bayes | -1.6780 | 0.500 / 0.817 / 0.970 | 7.66e-02 | 0.00 | 0.000 |
| 0.25 | 10 | 5 | ols_gaussian | -1.7690 | 0.437 / 0.740 / 0.907 | 2.05e-02 | 0.00 | nan |
| 0.25 | 10 | 5 | ols_student_t | -1.7101 | 0.460 / 0.787 / 0.943 | 9.02e-02 | 0.00 | nan |
| 0.25 | 10 | 5 | kernel_rolling_origin | -2.0642 | 0.450 / 0.713 / 0.880 | 5.42e-02 | 1.00 | nan |
| 0.25 | 10 | 5 | kernel_blocked | -2.0642 | 0.450 / 0.713 / 0.880 | 5.42e-02 | 1.00 | nan |
| 0.25 | 10 | 5 | kernel_leave_one_out | -3.0654 | 0.353 / 0.560 / 0.727 | 1.55e-07 | 0.00 | nan |
| 0.25 | 10 | 5 | persistence | -2.1542 | 0.417 / 0.730 / 0.853 | 1.73e-03 | 0.00 | nan |
| 0.25 | 10 | 5 | stability_prior_bayes | -1.6305 | 0.507 / 0.807 / 0.953 | 2.29e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | matched_reference | -1.4322 | 0.497 / 0.813 / 0.937 | 4.84e-02 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | flat_prior_bayes | -1.4602 | 0.483 / 0.807 / 0.940 | 3.83e-02 | 0.00 | 0.000 |
| 0.25 | 20 | 1 | ols_gaussian | -1.5156 | 0.467 / 0.780 / 0.900 | 6.64e-02 | 0.00 | nan |
| 0.25 | 20 | 1 | ols_student_t | -1.4998 | 0.487 / 0.797 / 0.947 | 1.16e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_rolling_origin | -1.5637 | 0.487 / 0.770 / 0.923 | 4.04e-02 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_blocked | -1.6158 | 0.493 / 0.773 / 0.923 | 2.00e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | kernel_leave_one_out | -1.6186 | 0.453 / 0.740 / 0.903 | 9.70e-03 | 0.00 | nan |
| 0.25 | 20 | 1 | persistence | -1.6078 | 0.517 / 0.813 / 0.930 | 1.42e-01 | 0.00 | nan |
| 0.25 | 20 | 1 | stability_prior_bayes | -1.4588 | 0.480 / 0.807 / 0.937 | 4.79e-02 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | matched_reference | -1.6103 | 0.457 / 0.777 / 0.953 | 7.71e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | flat_prior_bayes | -1.6183 | 0.487 / 0.780 / 0.963 | 8.55e-01 | 0.00 | 0.000 |
| 0.25 | 20 | 5 | ols_gaussian | -1.6447 | 0.490 / 0.760 / 0.950 | 5.64e-01 | 0.00 | nan |
| 0.25 | 20 | 5 | ols_student_t | -1.6285 | 0.490 / 0.783 / 0.960 | 8.02e-01 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_rolling_origin | -1.9517 | 0.430 / 0.703 / 0.847 | 1.22e-01 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_blocked | -2.0760 | 0.470 / 0.680 / 0.873 | 2.77e-02 | 0.00 | nan |
| 0.25 | 20 | 5 | kernel_leave_one_out | -1.9736 | 0.413 / 0.660 / 0.843 | 1.85e-02 | 0.00 | nan |
| 0.25 | 20 | 5 | persistence | -1.9893 | 0.440 / 0.730 / 0.920 | 3.90e-01 | 0.00 | nan |
| 0.25 | 20 | 5 | stability_prior_bayes | -1.6128 | 0.480 / 0.780 / 0.960 | 8.40e-01 | 0.00 | 0.000 |
| 1 | 1 | 1 | matched_reference | -1.4402 | 0.483 / 0.797 / 0.950 | 3.36e-01 | 0.00 | 0.000 |
| 1 | 1 | 1 | flat_prior_bayes | -2.2482 | 0.453 / 0.793 / 0.960 | 4.10e-01 | 0.00 | 0.000 |
| 1 | 1 | 1 | ols_gaussian | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 1.00 | nan |
| 1 | 1 | 1 | ols_student_t | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 1.00 | nan |
| 1 | 1 | 1 | kernel_rolling_origin | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 1.00 | nan |
| 1 | 1 | 1 | kernel_blocked | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 1.00 | nan |
| 1 | 1 | 1 | kernel_leave_one_out | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 1.00 | nan |
| 1 | 1 | 1 | persistence | -1081.3027 | 0.387 / 0.580 / 0.697 | 5.19e-06 | 0.00 | nan |
| 1 | 1 | 1 | stability_prior_bayes | -1.4733 | 0.527 / 0.813 / 0.967 | 3.30e-01 | 0.00 | 0.000 |
| 1 | 1 | 5 | matched_reference | -1.5488 | 0.537 / 0.817 / 0.947 | 1.17e-01 | 0.00 | 0.000 |
| 1 | 1 | 5 | flat_prior_bayes | -2.8849 | 0.543 / 0.830 / 0.933 | 3.71e-01 | 0.00 | 0.020 |
| 1 | 1 | 5 | ols_gaussian | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 1.00 | nan |
| 1 | 1 | 5 | ols_student_t | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 1.00 | nan |
| 1 | 1 | 5 | kernel_rolling_origin | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 1.00 | nan |
| 1 | 1 | 5 | kernel_blocked | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 1.00 | nan |
| 1 | 1 | 5 | kernel_leave_one_out | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 1.00 | nan |
| 1 | 1 | 5 | persistence | -223.8632 | 0.543 / 0.743 / 0.810 | 4.62e-03 | 0.00 | nan |
| 1 | 1 | 5 | stability_prior_bayes | -1.5715 | 0.580 / 0.857 / 0.963 | 1.55e-02 | 0.00 | 0.000 |
| 1 | 2 | 1 | matched_reference | -1.4308 | 0.520 / 0.833 / 0.953 | 9.09e-02 | 0.00 | 0.000 |
| 1 | 2 | 1 | flat_prior_bayes | -1.7892 | 0.500 / 0.773 / 0.923 | 7.95e-01 | 0.00 | 0.000 |
| 1 | 2 | 1 | ols_gaussian | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 1.00 | nan |
| 1 | 2 | 1 | ols_student_t | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 1.00 | nan |
| 1 | 2 | 1 | kernel_rolling_origin | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 1.00 | nan |
| 1 | 2 | 1 | kernel_blocked | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 1.00 | nan |
| 1 | 2 | 1 | kernel_leave_one_out | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 1.00 | nan |
| 1 | 2 | 1 | persistence | -2.7119 | 0.447 / 0.663 / 0.820 | 1.95e-02 | 0.00 | nan |
| 1 | 2 | 1 | stability_prior_bayes | -1.4799 | 0.537 / 0.810 / 0.953 | 1.18e-01 | 0.00 | 0.000 |
| 1 | 2 | 5 | matched_reference | -1.6682 | 0.450 / 0.757 / 0.930 | 1.73e-01 | 0.00 | 0.000 |
| 1 | 2 | 5 | flat_prior_bayes | -2.2413 | 0.587 / 0.833 / 0.970 | 9.14e-02 | 0.00 | 0.000 |
| 1 | 2 | 5 | ols_gaussian | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 1.00 | nan |
| 1 | 2 | 5 | ols_student_t | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 1.00 | nan |
| 1 | 2 | 5 | kernel_rolling_origin | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 1.00 | nan |
| 1 | 2 | 5 | kernel_blocked | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 1.00 | nan |
| 1 | 2 | 5 | kernel_leave_one_out | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 1.00 | nan |
| 1 | 2 | 5 | persistence | -2.5750 | 0.653 / 0.840 / 0.930 | 6.07e-03 | 0.00 | nan |
| 1 | 2 | 5 | stability_prior_bayes | -1.6772 | 0.473 / 0.813 / 0.953 | 2.54e-01 | 0.00 | 0.000 |
| 1 | 3 | 1 | matched_reference | -1.4456 | 0.507 / 0.783 / 0.947 | 6.38e-01 | 0.00 | 0.000 |
| 1 | 3 | 1 | flat_prior_bayes | -1.6055 | 0.480 / 0.797 / 0.967 | 2.50e-01 | 0.00 | 0.000 |
| 1 | 3 | 1 | ols_gaussian | -3.3307 | 0.347 / 0.623 / 0.750 | 1.42e-04 | 0.00 | nan |
| 1 | 3 | 1 | ols_student_t | -1.8415 | 0.513 / 0.810 / 0.973 | 1.93e-01 | 0.00 | nan |
| 1 | 3 | 1 | kernel_rolling_origin | -2.1937 | 0.363 / 0.643 / 0.843 | 3.77e-05 | 1.00 | nan |
| 1 | 3 | 1 | kernel_blocked | -2.1937 | 0.363 / 0.643 / 0.843 | 3.77e-05 | 1.00 | nan |
| 1 | 3 | 1 | kernel_leave_one_out | -3.5819 | 0.350 / 0.587 / 0.757 | 2.26e-06 | 0.00 | nan |
| 1 | 3 | 1 | persistence | -2.0522 | 0.413 / 0.687 / 0.847 | 3.84e-03 | 0.00 | nan |
| 1 | 3 | 1 | stability_prior_bayes | -1.4874 | 0.523 / 0.767 / 0.957 | 6.49e-01 | 0.00 | 0.000 |
| 1 | 3 | 5 | matched_reference | -1.6410 | 0.457 / 0.797 / 0.937 | 5.65e-01 | 0.00 | 0.000 |
| 1 | 3 | 5 | flat_prior_bayes | -1.9282 | 0.610 / 0.890 / 0.983 | 1.07e-01 | 0.00 | 0.000 |
| 1 | 3 | 5 | ols_gaussian | -3.6543 | 0.403 / 0.653 / 0.800 | 1.34e-02 | 0.00 | nan |
| 1 | 3 | 5 | ols_student_t | -2.1289 | 0.550 / 0.850 / 0.980 | 1.79e-01 | 0.00 | nan |
| 1 | 3 | 5 | kernel_rolling_origin | -2.1875 | 0.620 / 0.883 / 0.957 | 3.34e-04 | 1.00 | nan |
| 1 | 3 | 5 | kernel_blocked | -2.1875 | 0.620 / 0.883 / 0.957 | 3.34e-04 | 1.00 | nan |
| 1 | 3 | 5 | kernel_leave_one_out | -2.1875 | 0.620 / 0.883 / 0.957 | 3.34e-04 | 1.00 | nan |
| 1 | 3 | 5 | persistence | -2.1875 | 0.620 / 0.883 / 0.957 | 3.34e-04 | 0.00 | nan |
| 1 | 3 | 5 | stability_prior_bayes | -1.6436 | 0.493 / 0.837 / 0.963 | 5.56e-01 | 0.00 | 0.000 |
| 1 | 5 | 1 | matched_reference | -1.4179 | 0.543 / 0.810 / 0.943 | 5.60e-02 | 0.00 | 0.000 |
| 1 | 5 | 1 | flat_prior_bayes | -1.5109 | 0.543 / 0.817 / 0.950 | 4.06e-02 | 0.00 | 0.000 |
| 1 | 5 | 1 | ols_gaussian | -2.1519 | 0.493 / 0.737 / 0.877 | 9.18e-02 | 0.00 | nan |
| 1 | 5 | 1 | ols_student_t | -1.5842 | 0.550 / 0.830 / 0.963 | 3.35e-02 | 0.00 | nan |
| 1 | 5 | 1 | kernel_rolling_origin | -5.3548 | 0.370 / 0.617 / 0.757 | 1.72e-03 | 0.00 | nan |
| 1 | 5 | 1 | kernel_blocked | -1.9873 | 0.497 / 0.767 / 0.887 | 4.08e-01 | 0.00 | nan |
| 1 | 5 | 1 | kernel_leave_one_out | -1.8669 | 0.440 / 0.723 / 0.843 | 6.33e-02 | 0.00 | nan |
| 1 | 5 | 1 | persistence | -1.7510 | 0.477 / 0.757 / 0.903 | 1.66e-02 | 0.00 | nan |
| 1 | 5 | 1 | stability_prior_bayes | -1.4480 | 0.540 / 0.813 / 0.947 | 1.02e-01 | 0.00 | 0.000 |
| 1 | 5 | 5 | matched_reference | -1.5394 | 0.550 / 0.840 / 0.957 | 9.20e-02 | 0.00 | 0.000 |
| 1 | 5 | 5 | flat_prior_bayes | -1.7065 | 0.597 / 0.887 / 0.970 | 1.37e-02 | 0.00 | 0.000 |
| 1 | 5 | 5 | ols_gaussian | -2.3834 | 0.470 / 0.760 / 0.870 | 1.07e-01 | 0.00 | nan |
| 1 | 5 | 5 | ols_student_t | -1.7633 | 0.563 / 0.853 / 0.977 | 6.10e-02 | 0.00 | nan |
| 1 | 5 | 5 | kernel_rolling_origin | -105.2421 | 0.400 / 0.603 / 0.733 | 2.65e-04 | 1.00 | nan |
| 1 | 5 | 5 | kernel_blocked | -105.2421 | 0.400 / 0.603 / 0.733 | 2.65e-04 | 1.00 | nan |
| 1 | 5 | 5 | kernel_leave_one_out | -105.2421 | 0.400 / 0.603 / 0.733 | 2.65e-04 | 1.00 | nan |
| 1 | 5 | 5 | persistence | -105.2421 | 0.400 / 0.603 / 0.733 | 2.65e-04 | 0.00 | nan |
| 1 | 5 | 5 | stability_prior_bayes | -1.5599 | 0.580 / 0.860 / 0.967 | 2.92e-02 | 0.00 | 0.000 |
| 1 | 10 | 1 | matched_reference | -1.3809 | 0.523 / 0.833 / 0.963 | 8.21e-01 | 0.00 | 0.000 |
| 1 | 10 | 1 | flat_prior_bayes | -1.4003 | 0.550 / 0.843 / 0.963 | 6.07e-01 | 0.00 | 0.000 |
| 1 | 10 | 1 | ols_gaussian | -1.4490 | 0.503 / 0.783 / 0.923 | 8.58e-01 | 0.00 | nan |
| 1 | 10 | 1 | ols_student_t | -1.4395 | 0.557 / 0.837 / 0.963 | 5.45e-01 | 0.00 | nan |
| 1 | 10 | 1 | kernel_rolling_origin | -1.6293 | 0.470 / 0.733 / 0.893 | 1.84e-01 | 0.00 | nan |
| 1 | 10 | 1 | kernel_blocked | -1.5811 | 0.490 / 0.773 / 0.923 | 8.84e-01 | 0.00 | nan |
| 1 | 10 | 1 | kernel_leave_one_out | -1.5662 | 0.443 / 0.720 / 0.907 | 1.55e-01 | 0.00 | nan |
| 1 | 10 | 1 | persistence | -1.5404 | 0.553 / 0.803 / 0.957 | 4.27e-01 | 0.00 | nan |
| 1 | 10 | 1 | stability_prior_bayes | -1.3919 | 0.543 / 0.843 / 0.963 | 6.96e-01 | 0.00 | 0.000 |
| 1 | 10 | 5 | matched_reference | -1.6235 | 0.490 / 0.793 / 0.950 | 1.81e-01 | 0.00 | 0.000 |
| 1 | 10 | 5 | flat_prior_bayes | -1.6740 | 0.493 / 0.810 / 0.960 | 5.85e-02 | 0.00 | 0.000 |
| 1 | 10 | 5 | ols_gaussian | -1.7686 | 0.440 / 0.730 / 0.920 | 4.20e-02 | 0.00 | nan |
| 1 | 10 | 5 | ols_student_t | -1.7078 | 0.460 / 0.787 / 0.940 | 7.93e-02 | 0.00 | nan |
| 1 | 10 | 5 | kernel_rolling_origin | -2.1589 | 0.477 / 0.727 / 0.897 | 3.21e-02 | 1.00 | nan |
| 1 | 10 | 5 | kernel_blocked | -2.1589 | 0.477 / 0.727 / 0.897 | 3.21e-02 | 1.00 | nan |
| 1 | 10 | 5 | kernel_leave_one_out | -2.9298 | 0.340 / 0.587 / 0.750 | 1.26e-06 | 0.00 | nan |
| 1 | 10 | 5 | persistence | -2.2361 | 0.433 / 0.737 / 0.870 | 2.66e-03 | 0.00 | nan |
| 1 | 10 | 5 | stability_prior_bayes | -1.6339 | 0.507 / 0.807 / 0.950 | 1.92e-01 | 0.00 | 0.000 |
| 1 | 20 | 1 | matched_reference | -1.4333 | 0.490 / 0.813 / 0.940 | 6.05e-02 | 0.00 | 0.000 |
| 1 | 20 | 1 | flat_prior_bayes | -1.4601 | 0.473 / 0.810 / 0.940 | 5.88e-02 | 0.00 | 0.000 |
| 1 | 20 | 1 | ols_gaussian | -1.5149 | 0.457 / 0.783 / 0.900 | 7.74e-02 | 0.00 | nan |
| 1 | 20 | 1 | ols_student_t | -1.4996 | 0.487 / 0.803 / 0.950 | 1.21e-01 | 0.00 | nan |
| 1 | 20 | 1 | kernel_rolling_origin | -1.5611 | 0.490 / 0.777 / 0.923 | 3.10e-02 | 0.00 | nan |
| 1 | 20 | 1 | kernel_blocked | -1.5988 | 0.473 / 0.773 / 0.923 | 3.37e-02 | 0.00 | nan |
| 1 | 20 | 1 | kernel_leave_one_out | -1.5935 | 0.427 / 0.753 / 0.900 | 7.78e-03 | 0.00 | nan |
| 1 | 20 | 1 | persistence | -1.6072 | 0.520 / 0.807 / 0.933 | 1.29e-01 | 0.00 | nan |
| 1 | 20 | 1 | stability_prior_bayes | -1.4590 | 0.473 / 0.810 / 0.940 | 5.86e-02 | 0.00 | 0.000 |
| 1 | 20 | 5 | matched_reference | -1.6124 | 0.450 / 0.780 / 0.953 | 8.35e-01 | 0.00 | 0.000 |
| 1 | 20 | 5 | flat_prior_bayes | -1.6197 | 0.487 / 0.783 / 0.963 | 8.67e-01 | 0.00 | 0.000 |
| 1 | 20 | 5 | ols_gaussian | -1.6463 | 0.487 / 0.760 / 0.950 | 5.79e-01 | 0.00 | nan |
| 1 | 20 | 5 | ols_student_t | -1.6299 | 0.490 / 0.793 / 0.957 | 7.86e-01 | 0.00 | nan |
| 1 | 20 | 5 | kernel_rolling_origin | -1.8996 | 0.443 / 0.707 / 0.853 | 9.79e-02 | 0.00 | nan |
| 1 | 20 | 5 | kernel_blocked | -2.1121 | 0.437 / 0.680 / 0.860 | 6.78e-02 | 0.00 | nan |
| 1 | 20 | 5 | kernel_leave_one_out | -2.0003 | 0.380 / 0.660 / 0.837 | 1.38e-02 | 0.00 | nan |
| 1 | 20 | 5 | persistence | -1.9815 | 0.453 / 0.733 / 0.920 | 4.84e-01 | 0.00 | nan |
| 1 | 20 | 5 | stability_prior_bayes | -1.6153 | 0.477 / 0.783 / 0.960 | 9.22e-01 | 0.00 | 0.000 |
| 4 | 1 | 1 | matched_reference | -1.4597 | 0.467 / 0.803 / 0.950 | 4.69e-01 | 0.00 | 0.000 |
| 4 | 1 | 1 | flat_prior_bayes | -1.7814 | 0.463 / 0.797 / 0.957 | 3.16e-01 | 0.00 | 0.000 |
| 4 | 1 | 1 | ols_gaussian | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 1.00 | nan |
| 4 | 1 | 1 | ols_student_t | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 1.00 | nan |
| 4 | 1 | 1 | kernel_rolling_origin | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 1.00 | nan |
| 4 | 1 | 1 | kernel_blocked | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 1.00 | nan |
| 4 | 1 | 1 | kernel_leave_one_out | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 1.00 | nan |
| 4 | 1 | 1 | persistence | -83.9373 | 0.560 / 0.720 / 0.823 | 1.31e-02 | 0.00 | nan |
| 4 | 1 | 1 | stability_prior_bayes | -1.4969 | 0.480 / 0.807 / 0.960 | 2.89e-01 | 0.00 | 0.000 |
| 4 | 1 | 5 | matched_reference | -1.5435 | 0.527 / 0.810 / 0.947 | 1.82e-01 | 0.00 | 0.000 |
| 4 | 1 | 5 | flat_prior_bayes | -2.0805 | 0.543 / 0.813 / 0.943 | 3.32e-01 | 0.00 | 0.003 |
| 4 | 1 | 5 | ols_gaussian | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 1.00 | nan |
| 4 | 1 | 5 | ols_student_t | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 1.00 | nan |
| 4 | 1 | 5 | kernel_rolling_origin | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 1.00 | nan |
| 4 | 1 | 5 | kernel_blocked | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 1.00 | nan |
| 4 | 1 | 5 | kernel_leave_one_out | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 1.00 | nan |
| 4 | 1 | 5 | persistence | -27.9805 | 0.660 / 0.817 / 0.890 | 5.83e-04 | 0.00 | nan |
| 4 | 1 | 5 | stability_prior_bayes | -1.5733 | 0.557 / 0.830 / 0.957 | 1.43e-01 | 0.00 | 0.000 |
| 4 | 2 | 1 | matched_reference | -1.4345 | 0.527 / 0.813 / 0.957 | 1.06e-01 | 0.00 | 0.000 |
| 4 | 2 | 1 | flat_prior_bayes | -1.6074 | 0.480 / 0.777 / 0.933 | 3.22e-01 | 0.00 | 0.000 |
| 4 | 2 | 1 | ols_gaussian | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 1.00 | nan |
| 4 | 2 | 1 | ols_student_t | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 1.00 | nan |
| 4 | 2 | 1 | kernel_rolling_origin | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 1.00 | nan |
| 4 | 2 | 1 | kernel_blocked | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 1.00 | nan |
| 4 | 2 | 1 | kernel_leave_one_out | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 1.00 | nan |
| 4 | 2 | 1 | persistence | -2.2900 | 0.613 / 0.793 / 0.913 | 2.35e-02 | 0.00 | nan |
| 4 | 2 | 1 | stability_prior_bayes | -1.4728 | 0.520 / 0.790 / 0.950 | 6.54e-02 | 0.00 | 0.000 |
| 4 | 2 | 5 | matched_reference | -1.6624 | 0.460 / 0.737 / 0.937 | 1.50e-01 | 0.00 | 0.000 |
| 4 | 2 | 5 | flat_prior_bayes | -1.9027 | 0.513 / 0.800 / 0.957 | 9.24e-01 | 0.00 | 0.000 |
| 4 | 2 | 5 | ols_gaussian | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 1.00 | nan |
| 4 | 2 | 5 | ols_student_t | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 1.00 | nan |
| 4 | 2 | 5 | kernel_rolling_origin | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 1.00 | nan |
| 4 | 2 | 5 | kernel_blocked | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 1.00 | nan |
| 4 | 2 | 5 | kernel_leave_one_out | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 1.00 | nan |
| 4 | 2 | 5 | persistence | -2.6490 | 0.737 / 0.867 / 0.947 | 1.67e-06 | 0.00 | nan |
| 4 | 2 | 5 | stability_prior_bayes | -1.6727 | 0.477 / 0.790 / 0.943 | 2.84e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | matched_reference | -1.4194 | 0.533 / 0.797 / 0.953 | 7.01e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | flat_prior_bayes | -1.4945 | 0.507 / 0.793 / 0.947 | 2.36e-01 | 0.00 | 0.000 |
| 4 | 3 | 1 | ols_gaussian | -2.3683 | 0.403 / 0.680 / 0.797 | 1.28e-03 | 0.00 | nan |
| 4 | 3 | 1 | ols_student_t | -1.6970 | 0.507 / 0.807 / 0.973 | 2.10e-01 | 0.00 | nan |
| 4 | 3 | 1 | kernel_rolling_origin | -1.8932 | 0.530 / 0.803 / 0.930 | 1.51e-02 | 1.00 | nan |
| 4 | 3 | 1 | kernel_blocked | -1.8932 | 0.530 / 0.803 / 0.930 | 1.51e-02 | 1.00 | nan |
| 4 | 3 | 1 | kernel_leave_one_out | -4.0389 | 0.400 / 0.640 / 0.800 | 2.34e-04 | 0.00 | nan |
| 4 | 3 | 1 | persistence | -1.8426 | 0.557 / 0.833 / 0.927 | 1.03e-02 | 0.00 | nan |
| 4 | 3 | 1 | stability_prior_bayes | -1.4451 | 0.530 / 0.790 / 0.953 | 7.32e-01 | 0.00 | 0.000 |
| 4 | 3 | 5 | matched_reference | -1.6225 | 0.460 / 0.790 / 0.937 | 5.65e-01 | 0.00 | 0.000 |
| 4 | 3 | 5 | flat_prior_bayes | -1.7219 | 0.503 / 0.850 / 0.977 | 1.48e-01 | 0.00 | 0.000 |
| 4 | 3 | 5 | ols_gaussian | -3.4815 | 0.407 / 0.667 / 0.780 | 4.72e-03 | 0.00 | nan |
| 4 | 3 | 5 | ols_student_t | -1.9729 | 0.500 / 0.783 / 0.957 | 2.63e-01 | 0.00 | nan |
| 4 | 3 | 5 | kernel_rolling_origin | -2.4253 | 0.760 / 0.923 / 0.963 | 4.82e-08 | 1.00 | nan |
| 4 | 3 | 5 | kernel_blocked | -2.4253 | 0.760 / 0.923 / 0.963 | 4.82e-08 | 1.00 | nan |
| 4 | 3 | 5 | kernel_leave_one_out | -2.4253 | 0.760 / 0.923 / 0.963 | 4.82e-08 | 1.00 | nan |
| 4 | 3 | 5 | persistence | -2.4253 | 0.760 / 0.923 / 0.963 | 4.82e-08 | 0.00 | nan |
| 4 | 3 | 5 | stability_prior_bayes | -1.6170 | 0.480 / 0.820 / 0.957 | 6.92e-01 | 0.00 | 0.000 |
| 4 | 5 | 1 | matched_reference | -1.4044 | 0.553 / 0.803 / 0.937 | 8.58e-02 | 0.00 | 0.000 |
| 4 | 5 | 1 | flat_prior_bayes | -1.4532 | 0.550 / 0.823 / 0.937 | 1.35e-01 | 0.00 | 0.000 |
| 4 | 5 | 1 | ols_gaussian | -1.9284 | 0.500 / 0.733 / 0.883 | 2.31e-01 | 0.00 | nan |
| 4 | 5 | 1 | ols_student_t | -1.5376 | 0.540 / 0.800 / 0.967 | 1.31e-01 | 0.00 | nan |
| 4 | 5 | 1 | kernel_rolling_origin | -7.8713 | 0.373 / 0.600 / 0.757 | 1.59e-04 | 0.00 | nan |
| 4 | 5 | 1 | kernel_blocked | -2.0270 | 0.520 / 0.803 / 0.900 | 2.52e-01 | 0.00 | nan |
| 4 | 5 | 1 | kernel_leave_one_out | -1.9081 | 0.473 / 0.720 / 0.840 | 7.63e-02 | 0.00 | nan |
| 4 | 5 | 1 | persistence | -1.7883 | 0.590 / 0.857 / 0.940 | 2.72e-02 | 0.00 | nan |
| 4 | 5 | 1 | stability_prior_bayes | -1.4212 | 0.553 / 0.820 / 0.943 | 1.68e-01 | 0.00 | 0.000 |
| 4 | 5 | 5 | matched_reference | -1.5263 | 0.550 / 0.853 / 0.950 | 1.50e-01 | 0.00 | 0.000 |
| 4 | 5 | 5 | flat_prior_bayes | -1.5991 | 0.583 / 0.867 / 0.963 | 4.89e-02 | 0.00 | 0.000 |
| 4 | 5 | 5 | ols_gaussian | -2.1067 | 0.473 / 0.787 / 0.890 | 2.79e-01 | 0.00 | nan |
| 4 | 5 | 5 | ols_student_t | -1.6910 | 0.560 / 0.847 / 0.950 | 1.10e-01 | 0.00 | nan |
| 4 | 5 | 5 | kernel_rolling_origin | -12.6829 | 0.660 / 0.813 / 0.887 | 1.08e-05 | 1.00 | nan |
| 4 | 5 | 5 | kernel_blocked | -12.6829 | 0.660 / 0.813 / 0.887 | 1.08e-05 | 1.00 | nan |
| 4 | 5 | 5 | kernel_leave_one_out | -12.6829 | 0.660 / 0.813 / 0.887 | 1.08e-05 | 1.00 | nan |
| 4 | 5 | 5 | persistence | -12.6829 | 0.660 / 0.813 / 0.887 | 1.08e-05 | 0.00 | nan |
| 4 | 5 | 5 | stability_prior_bayes | -1.5376 | 0.573 / 0.857 / 0.957 | 7.46e-02 | 0.00 | 0.000 |
| 4 | 10 | 1 | matched_reference | -1.3763 | 0.520 / 0.823 / 0.970 | 9.55e-01 | 0.00 | 0.000 |
| 4 | 10 | 1 | flat_prior_bayes | -1.3846 | 0.530 / 0.840 / 0.970 | 8.63e-01 | 0.00 | 0.000 |
| 4 | 10 | 1 | ols_gaussian | -1.4225 | 0.507 / 0.797 / 0.933 | 9.83e-01 | 0.00 | nan |
| 4 | 10 | 1 | ols_student_t | -1.4200 | 0.530 / 0.837 / 0.960 | 5.66e-01 | 0.00 | nan |
| 4 | 10 | 1 | kernel_rolling_origin | -1.5949 | 0.473 / 0.743 / 0.910 | 1.69e-01 | 0.00 | nan |
| 4 | 10 | 1 | kernel_blocked | -1.6707 | 0.513 / 0.813 / 0.917 | 4.72e-01 | 0.00 | nan |
| 4 | 10 | 1 | kernel_leave_one_out | -1.5466 | 0.457 / 0.723 / 0.923 | 1.15e-01 | 0.00 | nan |
| 4 | 10 | 1 | persistence | -1.6005 | 0.610 / 0.863 / 0.973 | 3.88e-02 | 0.00 | nan |
| 4 | 10 | 1 | stability_prior_bayes | -1.3801 | 0.530 / 0.837 / 0.970 | 9.01e-01 | 0.00 | 0.000 |
| 4 | 10 | 5 | matched_reference | -1.6266 | 0.500 / 0.793 / 0.947 | 1.99e-01 | 0.00 | 0.000 |
| 4 | 10 | 5 | flat_prior_bayes | -1.6531 | 0.513 / 0.800 / 0.953 | 1.55e-01 | 0.00 | 0.000 |
| 4 | 10 | 5 | ols_gaussian | -1.7273 | 0.450 / 0.737 / 0.917 | 8.87e-02 | 0.00 | nan |
| 4 | 10 | 5 | ols_student_t | -1.6798 | 0.473 / 0.783 / 0.943 | 1.54e-01 | 0.00 | nan |
| 4 | 10 | 5 | kernel_rolling_origin | -2.0515 | 0.640 / 0.873 / 0.947 | 3.45e-03 | 1.00 | nan |
| 4 | 10 | 5 | kernel_blocked | -2.0515 | 0.640 / 0.873 / 0.947 | 3.45e-03 | 1.00 | nan |
| 4 | 10 | 5 | kernel_leave_one_out | -2.8286 | 0.363 / 0.570 / 0.767 | 6.28e-06 | 0.00 | nan |
| 4 | 10 | 5 | persistence | -2.1067 | 0.597 / 0.830 / 0.937 | 1.42e-02 | 0.00 | nan |
| 4 | 10 | 5 | stability_prior_bayes | -1.6344 | 0.510 / 0.793 / 0.947 | 2.35e-01 | 0.00 | 0.000 |
| 4 | 20 | 1 | matched_reference | -1.4293 | 0.500 / 0.817 / 0.943 | 4.13e-02 | 0.00 | 0.000 |
| 4 | 20 | 1 | flat_prior_bayes | -1.4428 | 0.480 / 0.807 / 0.943 | 4.69e-02 | 0.00 | 0.000 |
| 4 | 20 | 1 | ols_gaussian | -1.4823 | 0.477 / 0.787 / 0.913 | 4.73e-02 | 0.00 | nan |
| 4 | 20 | 1 | ols_student_t | -1.4747 | 0.483 / 0.820 / 0.947 | 7.97e-02 | 0.00 | nan |
| 4 | 20 | 1 | kernel_rolling_origin | -1.5523 | 0.487 / 0.777 / 0.927 | 4.07e-02 | 0.00 | nan |
| 4 | 20 | 1 | kernel_blocked | -1.5872 | 0.527 / 0.807 / 0.937 | 4.48e-02 | 0.00 | nan |
| 4 | 20 | 1 | kernel_leave_one_out | -1.5920 | 0.443 / 0.757 / 0.913 | 6.87e-03 | 0.00 | nan |
| 4 | 20 | 1 | persistence | -1.6230 | 0.567 / 0.843 / 0.953 | 2.22e-02 | 0.00 | nan |
| 4 | 20 | 1 | stability_prior_bayes | -1.4427 | 0.480 / 0.807 / 0.943 | 5.70e-02 | 0.00 | 0.000 |
| 4 | 20 | 5 | matched_reference | -1.6174 | 0.467 / 0.777 / 0.953 | 9.03e-01 | 0.00 | 0.000 |
| 4 | 20 | 5 | flat_prior_bayes | -1.6179 | 0.487 / 0.783 / 0.960 | 9.07e-01 | 0.00 | 0.000 |
| 4 | 20 | 5 | ols_gaussian | -1.6499 | 0.477 / 0.760 / 0.947 | 7.45e-01 | 0.00 | nan |
| 4 | 20 | 5 | ols_student_t | -1.6307 | 0.487 / 0.800 / 0.953 | 8.61e-01 | 0.00 | nan |
| 4 | 20 | 5 | kernel_rolling_origin | -1.8819 | 0.447 / 0.697 / 0.857 | 1.05e-01 | 0.00 | nan |
| 4 | 20 | 5 | kernel_blocked | -1.9571 | 0.453 / 0.690 / 0.867 | 1.85e-01 | 0.00 | nan |
| 4 | 20 | 5 | kernel_leave_one_out | -1.9473 | 0.423 / 0.673 / 0.840 | 9.79e-02 | 0.00 | nan |
| 4 | 20 | 5 | persistence | -1.9872 | 0.510 / 0.793 / 0.947 | 9.72e-01 | 0.00 | nan |
| 4 | 20 | 5 | stability_prior_bayes | -1.6177 | 0.477 / 0.783 / 0.960 | 9.05e-01 | 0.00 | 0.000 |
