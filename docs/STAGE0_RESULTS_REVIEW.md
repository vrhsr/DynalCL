# Stage 0 results review (Stage 0.5, Step 1)

Source: `runs/20261009T094047949167Z_separability_9123175bb3` (60 cells, 2337 paired evaluation items per cell). delta = 0.02 nats, as pre-registered in Stage 0. 95% CI = mean +/- 1.96 SE (analytic, paired). r = sd(x_0)/sigma (r = 4 is sigma = 0.25; r = 1 is sigma = 1). Classification is the Stage 0 pre-registered rule. Positive differences favour the first-named predictor.

## (a) Matched Bayesian reference vs the context-only frontier

`frontier_all` = best context-only member on the selection split (flat-prior Bayes in every cell; it is given the true sigma). `frontier_strict` excludes sigma-informed members (it selected OLS Student-t, or OLS Gaussian in 2 cells).

### E-CONT

| r | K | n | h | vs frontier_all: mean (95% CI) | class | vs frontier_strict: mean (95% CI) | class |
|---|---|---|---|---|---|---|---|
| 1 | 0 | 5 | 1 | +0.0760 [+0.0612, +0.0908] | separable | +0.1848 [+0.1619, +0.2077] | separable |
| 1 | 0 | 5 | 5 | +0.1546 [+0.1408, +0.1685] | separable | +0.2186 [+0.1931, +0.2440] | separable |
| 1 | 0 | 20 | 1 | +0.0078 [+0.0027, +0.0129] | equivalent | +0.0371 [+0.0270, +0.0471] | separable |
| 1 | 0 | 20 | 5 | +0.0100 [+0.0053, +0.0147] | equivalent | +0.0276 [+0.0182, +0.0370] | separable |
| 1 | 0 | 80 | 1 | +0.0005 [-0.0010, +0.0020] | equivalent | +0.0095 [+0.0040, +0.0150] | equivalent |
| 1 | 0 | 80 | 5 | +0.0010 [-0.0005, +0.0024] | equivalent | +0.0066 [+0.0017, +0.0114] | equivalent |
| 4 | 0 | 5 | 1 | +0.0355 [+0.0251, +0.0459] | separable | +0.1541 [+0.1324, +0.1758] | separable |
| 4 | 0 | 5 | 5 | +0.0652 [+0.0547, +0.0758] | separable | +0.1544 [+0.1325, +0.1764] | separable |
| 4 | 0 | 20 | 1 | +0.0046 [+0.0005, +0.0088] | equivalent | +0.0368 [+0.0269, +0.0467] | separable |
| 4 | 0 | 20 | 5 | +0.0058 [+0.0024, +0.0093] | equivalent | +0.0284 [+0.0191, +0.0376] | separable |
| 4 | 0 | 80 | 1 | +0.0004 [-0.0009, +0.0017] | equivalent | +0.0092 [+0.0038, +0.0145] | equivalent |
| 4 | 0 | 80 | 5 | +0.0007 [-0.0007, +0.0020] | equivalent | +0.0063 [+0.0015, +0.0111] | equivalent |

### E-LIB

| r | K | n | h | vs frontier_all: mean (95% CI) | class | vs frontier_strict: mean (95% CI) | class |
|---|---|---|---|---|---|---|---|
| 1 | 4 | 5 | 1 | +0.1000 [+0.0823, +0.1178] | separable | +0.2109 [+0.1869, +0.2349] | separable |
| 1 | 4 | 5 | 5 | +0.1569 [+0.1430, +0.1708] | separable | +0.2214 [+0.1961, +0.2466] | separable |
| 1 | 4 | 20 | 1 | +0.0168 [+0.0095, +0.0241] | detectable_below_delta | +0.0460 [+0.0342, +0.0579] | separable |
| 1 | 4 | 20 | 5 | +0.0105 [+0.0050, +0.0160] | equivalent | +0.0319 [+0.0218, +0.0421] | separable |
| 1 | 4 | 80 | 1 | +0.0046 [+0.0011, +0.0081] | equivalent | +0.0094 [+0.0039, +0.0148] | equivalent |
| 1 | 4 | 80 | 5 | +0.0019 [+0.0001, +0.0036] | equivalent | +0.0084 [+0.0038, +0.0130] | equivalent |
| 1 | 16 | 5 | 1 | +0.0926 [+0.0772, +0.1081] | separable | +0.2042 [+0.1818, +0.2265] | separable |
| 1 | 16 | 5 | 5 | +0.1558 [+0.1416, +0.1700] | separable | +0.2245 [+0.1992, +0.2499] | separable |
| 1 | 16 | 20 | 1 | +0.0167 [+0.0106, +0.0228] | detectable_below_delta | +0.0464 [+0.0358, +0.0571] | separable |
| 1 | 16 | 20 | 5 | +0.0134 [+0.0082, +0.0186] | equivalent | +0.0353 [+0.0245, +0.0461] | separable |
| 1 | 16 | 80 | 1 | +0.0024 [+0.0002, +0.0046] | equivalent | +0.0074 [+0.0028, +0.0120] | equivalent |
| 1 | 16 | 80 | 5 | +0.0009 [-0.0015, +0.0032] | equivalent | +0.0073 [+0.0022, +0.0124] | equivalent |
| 1 | 64 | 5 | 1 | +0.0875 [+0.0713, +0.1037] | separable | +0.2035 [+0.1802, +0.2267] | separable |
| 1 | 64 | 5 | 5 | +0.1549 [+0.1408, +0.1690] | separable | +0.2270 [+0.2009, +0.2531] | separable |
| 1 | 64 | 20 | 1 | +0.0148 [+0.0097, +0.0199] | equivalent | +0.0437 [+0.0334, +0.0540] | separable |
| 1 | 64 | 20 | 5 | +0.0102 [+0.0048, +0.0157] | equivalent | +0.0310 [+0.0204, +0.0416] | separable |
| 1 | 64 | 80 | 1 | +0.0009 [-0.0008, +0.0026] | equivalent | +0.0057 [+0.0013, +0.0102] | equivalent |
| 1 | 64 | 80 | 5 | +0.0016 [+0.0003, +0.0029] | equivalent | +0.0096 [+0.0048, +0.0144] | equivalent |
| 1 | 256 | 5 | 1 | +0.0825 [+0.0665, +0.0985] | separable | +0.1943 [+0.1712, +0.2174] | separable |
| 1 | 256 | 5 | 5 | +0.1509 [+0.1371, +0.1647] | separable | +0.2271 [+0.2009, +0.2532] | separable |
| 1 | 256 | 20 | 1 | +0.0085 [+0.0029, +0.0141] | equivalent | +0.0379 [+0.0274, +0.0484] | separable |
| 1 | 256 | 20 | 5 | +0.0113 [+0.0057, +0.0169] | equivalent | +0.0410 [+0.0302, +0.0519] | separable |
| 1 | 256 | 80 | 1 | +0.0005 [-0.0011, +0.0020] | equivalent | +0.0056 [+0.0013, +0.0100] | equivalent |
| 1 | 256 | 80 | 5 | +0.0006 [-0.0010, +0.0021] | equivalent | +0.0079 [+0.0034, +0.0125] | equivalent |
| 4 | 4 | 5 | 1 | +0.0440 [+0.0316, +0.0564] | separable | +0.1643 [+0.1424, +0.1862] | separable |
| 4 | 4 | 5 | 5 | +0.0610 [+0.0519, +0.0700] | separable | +0.1618 [+0.1410, +0.1825] | separable |
| 4 | 4 | 20 | 1 | +0.0126 [+0.0070, +0.0182] | equivalent | +0.0431 [+0.0323, +0.0539] | separable |
| 4 | 4 | 20 | 5 | +0.0060 [+0.0017, +0.0103] | equivalent | +0.0310 [+0.0210, +0.0411] | separable |
| 4 | 4 | 80 | 1 | +0.0037 [+0.0006, +0.0069] | equivalent | +0.0087 [+0.0035, +0.0138] | equivalent |
| 4 | 4 | 80 | 5 | +0.0018 [+0.0002, +0.0033] | equivalent | +0.0086 [+0.0039, +0.0132] | equivalent |
| 4 | 16 | 5 | 1 | +0.0380 [+0.0276, +0.0485] | separable | +0.1564 [+0.1354, +0.1773] | separable |
| 4 | 16 | 5 | 5 | +0.0619 [+0.0521, +0.0717] | separable | +0.1614 [+0.1403, +0.1826] | separable |
| 4 | 16 | 20 | 1 | +0.0128 [+0.0080, +0.0177] | equivalent | +0.0435 [+0.0336, +0.0535] | separable |
| 4 | 16 | 20 | 5 | +0.0089 [+0.0049, +0.0129] | equivalent | +0.0331 [+0.0227, +0.0435] | separable |
| 4 | 16 | 80 | 1 | +0.0019 [-0.0001, +0.0039] | equivalent | +0.0070 [+0.0024, +0.0115] | equivalent |
| 4 | 16 | 80 | 5 | +0.0005 [-0.0017, +0.0028] | equivalent | +0.0071 [+0.0020, +0.0122] | equivalent |
| 4 | 64 | 5 | 1 | +0.0382 [+0.0275, +0.0488] | separable | +0.1621 [+0.1405, +0.1836] | separable |
| 4 | 64 | 5 | 5 | +0.0618 [+0.0519, +0.0717] | separable | +0.1666 [+0.1449, +0.1882] | separable |
| 4 | 64 | 20 | 1 | +0.0109 [+0.0069, +0.0150] | equivalent | +0.0406 [+0.0309, +0.0503] | separable |
| 4 | 64 | 20 | 5 | +0.0069 [+0.0028, +0.0111] | equivalent | +0.0308 [+0.0208, +0.0409] | separable |
| 4 | 64 | 80 | 1 | +0.0006 [-0.0009, +0.0021] | equivalent | +0.0055 [+0.0012, +0.0098] | equivalent |
| 4 | 64 | 80 | 5 | +0.0014 [+0.0002, +0.0026] | equivalent | +0.0096 [+0.0048, +0.0144] | equivalent |
| 4 | 256 | 5 | 1 | +0.0297 [+0.0187, +0.0408] | separable | +0.1480 [+0.1265, +0.1695] | separable |
| 4 | 256 | 5 | 5 | +0.0585 [+0.0484, +0.0686] | separable | +0.1655 [+0.1436, +0.1874] | separable |
| 4 | 256 | 20 | 1 | +0.0060 [+0.0019, +0.0102] | equivalent | +0.0355 [+0.0258, +0.0452] | separable |
| 4 | 256 | 20 | 5 | +0.0082 [+0.0039, +0.0125] | equivalent | +0.0393 [+0.0290, +0.0497] | separable |
| 4 | 256 | 80 | 1 | +0.0003 [-0.0011, +0.0016] | equivalent | +0.0055 [+0.0012, +0.0097] | equivalent |
| 4 | 256 | 80 | 5 | +0.0004 [-0.0009, +0.0018] | equivalent | +0.0080 [+0.0035, +0.0124] | equivalent |

## (b) Finite library vs continuous-prior Bayes

E-CONT: matched = continuous; the row shows (library - continuous). E-LIB: matched = library; the row shows (library - continuous). 'material' means abs(mean) >= delta.

| condition | r | K | n | h | library - continuous (95% CI) | z | class | material |
|---|---|---|---|---|---|---|---|---|
| E-CONT | 1 | 4 | 5 | 1 | -0.0245 [-0.0340, -0.0150] | -5.1 | separable | YES |
| E-CONT | 1 | 4 | 5 | 5 | -0.0305 [-0.0435, -0.0175] | -4.6 | separable | YES |
| E-CONT | 1 | 4 | 20 | 1 | -0.0273 [-0.0378, -0.0167] | -5.1 | separable | YES |
| E-CONT | 1 | 4 | 20 | 5 | -0.0363 [-0.0518, -0.0209] | -4.6 | separable | YES |
| E-CONT | 1 | 4 | 80 | 1 | -0.0321 [-0.0446, -0.0195] | -5.0 | separable | YES |
| E-CONT | 1 | 4 | 80 | 5 | -0.0519 [-0.0764, -0.0273] | -4.1 | separable | YES |
| E-CONT | 1 | 16 | 5 | 1 | -0.0039 [-0.0074, -0.0004] | -2.2 | equivalent | no |
| E-CONT | 1 | 16 | 5 | 5 | -0.0051 [-0.0092, -0.0009] | -2.4 | equivalent | no |
| E-CONT | 1 | 16 | 20 | 1 | -0.0048 [-0.0088, -0.0008] | -2.3 | equivalent | no |
| E-CONT | 1 | 16 | 20 | 5 | -0.0060 [-0.0110, -0.0010] | -2.4 | equivalent | no |
| E-CONT | 1 | 16 | 80 | 1 | -0.0066 [-0.0109, -0.0022] | -3.0 | equivalent | no |
| E-CONT | 1 | 16 | 80 | 5 | -0.0107 [-0.0190, -0.0025] | -2.6 | equivalent | no |
| E-CONT | 1 | 64 | 5 | 1 | -0.0012 [-0.0032, +0.0007] | -1.3 | equivalent | no |
| E-CONT | 1 | 64 | 5 | 5 | -0.0017 [-0.0034, +0.0001] | -1.9 | equivalent | no |
| E-CONT | 1 | 64 | 20 | 1 | -0.0007 [-0.0022, +0.0008] | -0.9 | equivalent | no |
| E-CONT | 1 | 64 | 20 | 5 | -0.0017 [-0.0032, -0.0002] | -2.2 | equivalent | no |
| E-CONT | 1 | 64 | 80 | 1 | -0.0008 [-0.0018, +0.0003] | -1.4 | equivalent | no |
| E-CONT | 1 | 64 | 80 | 5 | -0.0005 [-0.0014, +0.0004] | -1.2 | equivalent | no |
| E-CONT | 1 | 256 | 5 | 1 | -0.0002 [-0.0017, +0.0013] | -0.2 | equivalent | no |
| E-CONT | 1 | 256 | 5 | 5 | -0.0005 [-0.0013, +0.0003] | -1.2 | equivalent | no |
| E-CONT | 1 | 256 | 20 | 1 | -0.0003 [-0.0013, +0.0007] | -0.6 | equivalent | no |
| E-CONT | 1 | 256 | 20 | 5 | -0.0007 [-0.0014, -0.0000] | -2.0 | equivalent | no |
| E-CONT | 1 | 256 | 80 | 1 | -0.0001 [-0.0007, +0.0004] | -0.4 | equivalent | no |
| E-CONT | 1 | 256 | 80 | 5 | -0.0002 [-0.0007, +0.0004] | -0.6 | equivalent | no |
| E-CONT | 4 | 4 | 5 | 1 | -0.0415 [-0.0559, -0.0271] | -5.6 | separable | YES |
| E-CONT | 4 | 4 | 5 | 5 | -0.0610 [-0.0871, -0.0349] | -4.6 | separable | YES |
| E-CONT | 4 | 4 | 20 | 1 | -0.0294 [-0.0409, -0.0179] | -5.0 | separable | YES |
| E-CONT | 4 | 4 | 20 | 5 | -0.0412 [-0.0600, -0.0225] | -4.3 | separable | YES |
| E-CONT | 4 | 4 | 80 | 1 | -0.0330 [-0.0456, -0.0203] | -5.1 | separable | YES |
| E-CONT | 4 | 4 | 80 | 5 | -0.0525 [-0.0771, -0.0278] | -4.2 | separable | YES |
| E-CONT | 4 | 16 | 5 | 1 | -0.0062 [-0.0106, -0.0017] | -2.7 | equivalent | no |
| E-CONT | 4 | 16 | 5 | 5 | -0.0120 [-0.0209, -0.0032] | -2.7 | equivalent | no |
| E-CONT | 4 | 16 | 20 | 1 | -0.0051 [-0.0092, -0.0009] | -2.4 | equivalent | no |
| E-CONT | 4 | 16 | 20 | 5 | -0.0073 [-0.0133, -0.0013] | -2.4 | equivalent | no |
| E-CONT | 4 | 16 | 80 | 1 | -0.0069 [-0.0112, -0.0026] | -3.1 | equivalent | no |
| E-CONT | 4 | 16 | 80 | 5 | -0.0106 [-0.0189, -0.0024] | -2.5 | equivalent | no |
| E-CONT | 4 | 64 | 5 | 1 | -0.0012 [-0.0029, +0.0006] | -1.3 | equivalent | no |
| E-CONT | 4 | 64 | 5 | 5 | -0.0017 [-0.0034, +0.0001] | -1.9 | equivalent | no |
| E-CONT | 4 | 64 | 20 | 1 | -0.0004 [-0.0017, +0.0009] | -0.6 | equivalent | no |
| E-CONT | 4 | 64 | 20 | 5 | -0.0009 [-0.0021, +0.0003] | -1.4 | equivalent | no |
| E-CONT | 4 | 64 | 80 | 1 | -0.0007 [-0.0017, +0.0003] | -1.4 | equivalent | no |
| E-CONT | 4 | 64 | 80 | 5 | -0.0007 [-0.0016, +0.0002] | -1.6 | equivalent | no |
| E-CONT | 4 | 256 | 5 | 1 | -0.0002 [-0.0015, +0.0010] | -0.3 | equivalent | no |
| E-CONT | 4 | 256 | 5 | 5 | -0.0006 [-0.0016, +0.0003] | -1.3 | equivalent | no |
| E-CONT | 4 | 256 | 20 | 1 | -0.0000 [-0.0008, +0.0008] | -0.0 | equivalent | no |
| E-CONT | 4 | 256 | 20 | 5 | -0.0004 [-0.0010, +0.0002] | -1.2 | equivalent | no |
| E-CONT | 4 | 256 | 80 | 1 | -0.0001 [-0.0006, +0.0004] | -0.4 | equivalent | no |
| E-CONT | 4 | 256 | 80 | 5 | -0.0002 [-0.0007, +0.0003] | -0.8 | equivalent | no |
| E-LIB | 1 | 4 | 5 | 1 | +0.0085 [+0.0030, +0.0141] | +3.0 | equivalent | no |
| E-LIB | 1 | 4 | 5 | 5 | +0.0077 [+0.0030, +0.0125] | +3.2 | equivalent | no |
| E-LIB | 1 | 4 | 20 | 1 | +0.0042 [-0.0002, +0.0085] | +1.9 | equivalent | no |
| E-LIB | 1 | 4 | 20 | 5 | +0.0026 [-0.0009, +0.0062] | +1.5 | equivalent | no |
| E-LIB | 1 | 4 | 80 | 1 | +0.0031 [+0.0003, +0.0059] | +2.2 | equivalent | no |
| E-LIB | 1 | 4 | 80 | 5 | +0.0013 [-0.0001, +0.0027] | +1.8 | equivalent | no |
| E-LIB | 1 | 16 | 5 | 1 | +0.0019 [-0.0008, +0.0045] | +1.4 | equivalent | no |
| E-LIB | 1 | 16 | 5 | 5 | +0.0006 [-0.0020, +0.0033] | +0.5 | equivalent | no |
| E-LIB | 1 | 16 | 20 | 1 | +0.0042 [+0.0019, +0.0066] | +3.6 | equivalent | no |
| E-LIB | 1 | 16 | 20 | 5 | +0.0027 [+0.0009, +0.0046] | +2.9 | equivalent | no |
| E-LIB | 1 | 16 | 80 | 1 | +0.0019 [+0.0003, +0.0035] | +2.4 | equivalent | no |
| E-LIB | 1 | 16 | 80 | 5 | +0.0002 [-0.0016, +0.0020] | +0.2 | equivalent | no |
| E-LIB | 1 | 64 | 5 | 1 | +0.0006 [-0.0011, +0.0024] | +0.7 | equivalent | no |
| E-LIB | 1 | 64 | 5 | 5 | +0.0002 [-0.0013, +0.0018] | +0.3 | equivalent | no |
| E-LIB | 1 | 64 | 20 | 1 | +0.0020 [+0.0008, +0.0032] | +3.3 | equivalent | no |
| E-LIB | 1 | 64 | 20 | 5 | +0.0001 [-0.0012, +0.0014] | +0.1 | equivalent | no |
| E-LIB | 1 | 64 | 80 | 1 | +0.0006 [-0.0002, +0.0013] | +1.5 | equivalent | no |
| E-LIB | 1 | 64 | 80 | 5 | +0.0001 [-0.0005, +0.0007] | +0.5 | equivalent | no |
| E-LIB | 1 | 256 | 5 | 1 | -0.0001 [-0.0016, +0.0014] | -0.1 | equivalent | no |
| E-LIB | 1 | 256 | 5 | 5 | -0.0002 [-0.0011, +0.0008] | -0.3 | equivalent | no |
| E-LIB | 1 | 256 | 20 | 1 | +0.0008 [-0.0002, +0.0018] | +1.6 | equivalent | no |
| E-LIB | 1 | 256 | 20 | 5 | +0.0003 [-0.0005, +0.0012] | +0.8 | equivalent | no |
| E-LIB | 1 | 256 | 80 | 1 | +0.0001 [-0.0003, +0.0005] | +0.5 | equivalent | no |
| E-LIB | 1 | 256 | 80 | 5 | -0.0001 [-0.0005, +0.0003] | -0.3 | equivalent | no |
| E-LIB | 4 | 4 | 5 | 1 | +0.0063 [+0.0011, +0.0115] | +2.4 | equivalent | no |
| E-LIB | 4 | 4 | 5 | 5 | +0.0053 [+0.0013, +0.0094] | +2.6 | equivalent | no |
| E-LIB | 4 | 4 | 20 | 1 | +0.0043 [+0.0008, +0.0078] | +2.4 | equivalent | no |
| E-LIB | 4 | 4 | 20 | 5 | +0.0016 [-0.0014, +0.0046] | +1.1 | equivalent | no |
| E-LIB | 4 | 4 | 80 | 1 | +0.0026 [+0.0001, +0.0051] | +2.0 | equivalent | no |
| E-LIB | 4 | 4 | 80 | 5 | +0.0013 [-0.0000, +0.0026] | +1.9 | equivalent | no |
| E-LIB | 4 | 16 | 5 | 1 | +0.0019 [-0.0007, +0.0046] | +1.5 | equivalent | no |
| E-LIB | 4 | 16 | 5 | 5 | +0.0013 [-0.0011, +0.0037] | +1.1 | equivalent | no |
| E-LIB | 4 | 16 | 20 | 1 | +0.0038 [+0.0016, +0.0059] | +3.3 | equivalent | no |
| E-LIB | 4 | 16 | 20 | 5 | +0.0025 [+0.0007, +0.0044] | +2.6 | equivalent | no |
| E-LIB | 4 | 16 | 80 | 1 | +0.0017 [+0.0002, +0.0032] | +2.2 | equivalent | no |
| E-LIB | 4 | 16 | 80 | 5 | +0.0000 [-0.0017, +0.0018] | +0.0 | equivalent | no |
| E-LIB | 4 | 64 | 5 | 1 | +0.0006 [-0.0009, +0.0021] | +0.8 | equivalent | no |
| E-LIB | 4 | 64 | 5 | 5 | -0.0002 [-0.0016, +0.0013] | -0.2 | equivalent | no |
| E-LIB | 4 | 64 | 20 | 1 | +0.0020 [+0.0009, +0.0030] | +3.5 | equivalent | no |
| E-LIB | 4 | 64 | 20 | 5 | +0.0002 [-0.0010, +0.0013] | +0.3 | equivalent | no |
| E-LIB | 4 | 64 | 80 | 1 | +0.0006 [-0.0001, +0.0013] | +1.6 | equivalent | no |
| E-LIB | 4 | 64 | 80 | 5 | +0.0002 [-0.0004, +0.0007] | +0.7 | equivalent | no |
| E-LIB | 4 | 256 | 5 | 1 | -0.0003 [-0.0015, +0.0009] | -0.5 | equivalent | no |
| E-LIB | 4 | 256 | 5 | 5 | +0.0001 [-0.0008, +0.0010] | +0.3 | equivalent | no |
| E-LIB | 4 | 256 | 20 | 1 | +0.0007 [-0.0002, +0.0015] | +1.5 | equivalent | no |
| E-LIB | 4 | 256 | 20 | 5 | +0.0003 [-0.0004, +0.0011] | +0.8 | equivalent | no |
| E-LIB | 4 | 256 | 80 | 1 | +0.0001 [-0.0003, +0.0005] | +0.5 | equivalent | no |
| E-LIB | 4 | 256 | 80 | 5 | -0.0000 [-0.0004, +0.0003] | -0.2 | equivalent | no |

## (c) Differences that are small relative to their uncertainty (abs(z) < 2)

361 of 996 paired comparisons in the file have abs(z) < 2:

| condition | r | K | n | h | A - B | mean | SE | z |
|---|---|---|---|---|---|---|---|---|
| E-CONT | 1 | 0 | 20 | 1 | flat_prior_bayes - library_K16 | -0.0030 | 0.0044 | -0.68 |
| E-CONT | 1 | 0 | 20 | 5 | flat_prior_bayes - library_K16 | -0.0040 | 0.0045 | -0.87 |
| E-CONT | 4 | 0 | 20 | 1 | flat_prior_bayes - library_K16 | +0.0004 | 0.0040 | +0.11 |
| E-CONT | 4 | 0 | 20 | 5 | flat_prior_bayes - library_K16 | +0.0015 | 0.0042 | +0.35 |
| E-CONT | 1 | 0 | 80 | 1 | flat_prior_bayes - library_K256 | -0.0004 | 0.0010 | -0.42 |
| E-CONT | 1 | 0 | 80 | 5 | flat_prior_bayes - library_K256 | -0.0008 | 0.0010 | -0.80 |
| E-CONT | 4 | 0 | 20 | 1 | flat_prior_bayes - library_K256 | -0.0046 | 0.0025 | -1.88 |
| E-CONT | 4 | 0 | 80 | 1 | flat_prior_bayes - library_K256 | -0.0003 | 0.0009 | -0.31 |
| E-CONT | 4 | 0 | 80 | 5 | flat_prior_bayes - library_K256 | -0.0004 | 0.0009 | -0.49 |
| E-CONT | 4 | 0 | 5 | 1 | flat_prior_bayes - library_K4 | +0.0060 | 0.0106 | +0.57 |
| E-CONT | 4 | 0 | 5 | 5 | flat_prior_bayes - library_K4 | -0.0042 | 0.0156 | -0.27 |
| E-CONT | 1 | 0 | 80 | 1 | flat_prior_bayes - library_K64 | +0.0002 | 0.0012 | +0.20 |
| E-CONT | 1 | 0 | 80 | 5 | flat_prior_bayes - library_K64 | -0.0004 | 0.0011 | -0.38 |
| E-CONT | 4 | 0 | 20 | 1 | flat_prior_bayes - library_K64 | -0.0042 | 0.0027 | -1.54 |
| E-CONT | 4 | 0 | 80 | 1 | flat_prior_bayes - library_K64 | +0.0003 | 0.0011 | +0.29 |
| E-CONT | 4 | 0 | 80 | 5 | flat_prior_bayes - library_K64 | +0.0001 | 0.0011 | +0.06 |
| E-CONT | 1 | 0 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 1 | frontier_all - library_K16 | -0.0030 | 0.0044 | -0.68 |
| E-CONT | 1 | 0 | 20 | 5 | frontier_all - library_K16 | -0.0040 | 0.0045 | -0.87 |
| E-CONT | 4 | 0 | 20 | 1 | frontier_all - library_K16 | +0.0004 | 0.0040 | +0.11 |
| E-CONT | 4 | 0 | 20 | 5 | frontier_all - library_K16 | +0.0015 | 0.0042 | +0.35 |
| E-CONT | 1 | 0 | 80 | 1 | frontier_all - library_K256 | -0.0004 | 0.0010 | -0.42 |
| E-CONT | 1 | 0 | 80 | 5 | frontier_all - library_K256 | -0.0008 | 0.0010 | -0.80 |
| E-CONT | 4 | 0 | 20 | 1 | frontier_all - library_K256 | -0.0046 | 0.0025 | -1.88 |
| E-CONT | 4 | 0 | 80 | 1 | frontier_all - library_K256 | -0.0003 | 0.0009 | -0.31 |
| E-CONT | 4 | 0 | 80 | 5 | frontier_all - library_K256 | -0.0004 | 0.0009 | -0.49 |
| E-CONT | 4 | 0 | 5 | 1 | frontier_all - library_K4 | +0.0060 | 0.0106 | +0.57 |
| E-CONT | 4 | 0 | 5 | 5 | frontier_all - library_K4 | -0.0042 | 0.0156 | -0.27 |
| E-CONT | 1 | 0 | 80 | 1 | frontier_all - library_K64 | +0.0002 | 0.0012 | +0.20 |
| E-CONT | 1 | 0 | 80 | 5 | frontier_all - library_K64 | -0.0004 | 0.0011 | -0.38 |
| E-CONT | 4 | 0 | 20 | 1 | frontier_all - library_K64 | -0.0042 | 0.0027 | -1.54 |
| E-CONT | 4 | 0 | 80 | 1 | frontier_all - library_K64 | +0.0003 | 0.0011 | +0.29 |
| E-CONT | 4 | 0 | 80 | 5 | frontier_all - library_K64 | +0.0001 | 0.0011 | +0.06 |
| E-CONT | 1 | 0 | 80 | 1 | frontier_strict - library_K16 | -0.0029 | 0.0039 | -0.75 |
| E-CONT | 1 | 0 | 80 | 5 | frontier_strict - library_K16 | +0.0041 | 0.0052 | +0.80 |
| E-CONT | 4 | 0 | 80 | 1 | frontier_strict - library_K16 | -0.0023 | 0.0038 | -0.59 |
| E-CONT | 4 | 0 | 80 | 5 | frontier_strict - library_K16 | +0.0044 | 0.0051 | +0.85 |
| E-CONT | 1 | 0 | 20 | 1 | frontier_strict - library_K4 | -0.0098 | 0.0088 | -1.11 |
| E-CONT | 1 | 0 | 20 | 5 | frontier_strict - library_K4 | +0.0088 | 0.0106 | +0.83 |
| E-CONT | 4 | 0 | 20 | 1 | frontier_strict - library_K4 | -0.0074 | 0.0089 | -0.83 |
| E-CONT | 4 | 0 | 20 | 5 | frontier_strict - library_K4 | +0.0129 | 0.0114 | +1.13 |
| E-CONT | 1 | 0 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.0001 | 0.1675 | +0.00 |
| E-CONT | 1 | 0 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 1 | kernel_blocked - kernel_leave_one_out | -0.0065 | 0.0079 | -0.82 |
| E-CONT | 1 | 0 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0595 | 0.0421 | -1.41 |
| E-CONT | 1 | 0 | 80 | 1 | kernel_blocked - kernel_leave_one_out | +0.0014 | 0.0032 | +0.45 |
| E-CONT | 1 | 0 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0052 | 0.0038 | +1.39 |
| E-CONT | 4 | 0 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0650 | 0.0396 | -1.64 |
| E-CONT | 4 | 0 | 80 | 1 | kernel_blocked - kernel_leave_one_out | -0.0013 | 0.0034 | -0.37 |
| E-CONT | 4 | 0 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0044 | 0.0038 | +1.14 |
| E-CONT | 1 | 0 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -94.7773 | 80.3988 | -1.18 |
| E-CONT | 1 | 0 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0888 | 0.0447 | +1.99 |
| E-CONT | 1 | 0 | 80 | 1 | kernel_rolling_origin - kernel_blocked | -0.0030 | 0.0034 | -0.90 |
| E-CONT | 4 | 0 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0550 | 0.0439 | +1.25 |
| E-CONT | 4 | 0 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0034 | 0.0036 | +0.95 |
| E-CONT | 4 | 0 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0059 | 0.0030 | +1.99 |
| E-CONT | 1 | 0 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -94.7773 | 80.4339 | -1.18 |
| E-CONT | 1 | 0 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 1 | 0 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0293 | 0.0186 | +1.57 |
| E-CONT | 1 | 0 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0016 | 0.0036 | -0.44 |
| E-CONT | 4 | 0 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-CONT | 4 | 0 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0100 | 0.0081 | +1.24 |
| E-CONT | 4 | 0 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0100 | 0.0194 | -0.52 |
| E-CONT | 4 | 0 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0022 | 0.0034 | +0.64 |
| E-CONT | 1 | 0 | 5 | 1 | library_K64 - library_K256 | -0.0011 | 0.0006 | -1.80 |
| E-CONT | 1 | 0 | 5 | 5 | library_K64 - library_K256 | -0.0012 | 0.0008 | -1.52 |
| E-CONT | 1 | 0 | 20 | 1 | library_K64 - library_K256 | -0.0004 | 0.0004 | -0.91 |
| E-CONT | 1 | 0 | 20 | 5 | library_K64 - library_K256 | -0.0009 | 0.0005 | -1.71 |
| E-CONT | 1 | 0 | 80 | 1 | library_K64 - library_K256 | -0.0007 | 0.0004 | -1.69 |
| E-CONT | 1 | 0 | 80 | 5 | library_K64 - library_K256 | -0.0004 | 0.0003 | -1.13 |
| E-CONT | 4 | 0 | 5 | 1 | library_K64 - library_K256 | -0.0009 | 0.0006 | -1.69 |
| E-CONT | 4 | 0 | 5 | 5 | library_K64 - library_K256 | -0.0010 | 0.0007 | -1.45 |
| E-CONT | 4 | 0 | 20 | 1 | library_K64 - library_K256 | -0.0004 | 0.0004 | -0.96 |
| E-CONT | 4 | 0 | 20 | 5 | library_K64 - library_K256 | -0.0005 | 0.0005 | -1.07 |
| E-CONT | 4 | 0 | 80 | 1 | library_K64 - library_K256 | -0.0006 | 0.0004 | -1.52 |
| E-CONT | 4 | 0 | 80 | 5 | library_K64 - library_K256 | -0.0005 | 0.0003 | -1.64 |
| E-CONT | 1 | 0 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0005 | 0.0008 | +0.68 |
| E-CONT | 1 | 0 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0010 | 0.0007 | +1.29 |
| E-CONT | 4 | 0 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0004 | 0.0007 | +0.58 |
| E-CONT | 4 | 0 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0007 | 0.0007 | +0.96 |
| E-CONT | 1 | 0 | 80 | 1 | matched_reference - frontier_all | +0.0005 | 0.0008 | +0.68 |
| E-CONT | 1 | 0 | 80 | 5 | matched_reference - frontier_all | +0.0010 | 0.0007 | +1.29 |
| E-CONT | 4 | 0 | 80 | 1 | matched_reference - frontier_all | +0.0004 | 0.0007 | +0.58 |
| E-CONT | 4 | 0 | 80 | 5 | matched_reference - frontier_all | +0.0007 | 0.0007 | +0.96 |
| E-CONT | 1 | 0 | 5 | 1 | matched_reference - library_K256 | +0.0002 | 0.0008 | +0.22 |
| E-CONT | 1 | 0 | 5 | 5 | matched_reference - library_K256 | +0.0005 | 0.0004 | +1.21 |
| E-CONT | 1 | 0 | 20 | 1 | matched_reference - library_K256 | +0.0003 | 0.0005 | +0.61 |
| E-CONT | 1 | 0 | 20 | 5 | matched_reference - library_K256 | +0.0007 | 0.0004 | +1.96 |
| E-CONT | 1 | 0 | 80 | 1 | matched_reference - library_K256 | +0.0001 | 0.0003 | +0.37 |
| E-CONT | 1 | 0 | 80 | 5 | matched_reference - library_K256 | +0.0002 | 0.0003 | +0.62 |
| E-CONT | 4 | 0 | 5 | 1 | matched_reference - library_K256 | +0.0002 | 0.0006 | +0.35 |
| E-CONT | 4 | 0 | 5 | 5 | matched_reference - library_K256 | +0.0006 | 0.0005 | +1.32 |
| E-CONT | 4 | 0 | 20 | 1 | matched_reference - library_K256 | +0.0000 | 0.0004 | +0.01 |
| E-CONT | 4 | 0 | 20 | 5 | matched_reference - library_K256 | +0.0004 | 0.0003 | +1.20 |
| E-CONT | 4 | 0 | 80 | 1 | matched_reference - library_K256 | +0.0001 | 0.0003 | +0.45 |
| E-CONT | 4 | 0 | 80 | 5 | matched_reference - library_K256 | +0.0002 | 0.0003 | +0.76 |
| E-CONT | 1 | 0 | 5 | 1 | matched_reference - library_K64 | +0.0012 | 0.0010 | +1.27 |
| E-CONT | 1 | 0 | 5 | 5 | matched_reference - library_K64 | +0.0017 | 0.0009 | +1.87 |
| E-CONT | 1 | 0 | 20 | 1 | matched_reference - library_K64 | +0.0007 | 0.0008 | +0.93 |
| E-CONT | 1 | 0 | 80 | 1 | matched_reference - library_K64 | +0.0008 | 0.0005 | +1.42 |
| E-CONT | 1 | 0 | 80 | 5 | matched_reference - library_K64 | +0.0005 | 0.0005 | +1.15 |
| E-CONT | 4 | 0 | 5 | 1 | matched_reference - library_K64 | +0.0012 | 0.0009 | +1.26 |
| E-CONT | 4 | 0 | 5 | 5 | matched_reference - library_K64 | +0.0017 | 0.0009 | +1.89 |
| E-CONT | 4 | 0 | 20 | 1 | matched_reference - library_K64 | +0.0004 | 0.0007 | +0.58 |
| E-CONT | 4 | 0 | 20 | 5 | matched_reference - library_K64 | +0.0009 | 0.0006 | +1.43 |
| E-CONT | 4 | 0 | 80 | 1 | matched_reference - library_K64 | +0.0007 | 0.0005 | +1.36 |
| E-CONT | 4 | 0 | 80 | 5 | matched_reference - library_K64 | +0.0007 | 0.0005 | +1.59 |
| E-LIB | 1 | 16 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0005 | 0.0005 | -1.04 |
| E-LIB | 1 | 16 | 80 | 5 | flat_prior_bayes - continuous_prior_bayes | -0.0007 | 0.0004 | -1.52 |
| E-LIB | 1 | 64 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0003 | 0.0006 | -0.57 |
| E-LIB | 1 | 256 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0004 | 0.0006 | -0.58 |
| E-LIB | 1 | 256 | 80 | 5 | flat_prior_bayes - continuous_prior_bayes | -0.0007 | 0.0006 | -1.05 |
| E-LIB | 4 | 16 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0003 | 0.0004 | -0.67 |
| E-LIB | 4 | 16 | 80 | 5 | flat_prior_bayes - continuous_prior_bayes | -0.0005 | 0.0004 | -1.32 |
| E-LIB | 4 | 64 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0000 | 0.0005 | -0.03 |
| E-LIB | 4 | 256 | 80 | 1 | flat_prior_bayes - continuous_prior_bayes | -0.0002 | 0.0005 | -0.35 |
| E-LIB | 4 | 256 | 80 | 5 | flat_prior_bayes - continuous_prior_bayes | -0.0005 | 0.0005 | -0.88 |
| E-LIB | 1 | 16 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0005 | 0.0005 | -1.04 |
| E-LIB | 1 | 16 | 80 | 5 | frontier_all - continuous_prior_bayes | -0.0007 | 0.0004 | -1.52 |
| E-LIB | 1 | 64 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0003 | 0.0006 | -0.57 |
| E-LIB | 1 | 256 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0004 | 0.0006 | -0.58 |
| E-LIB | 1 | 256 | 80 | 5 | frontier_all - continuous_prior_bayes | -0.0007 | 0.0006 | -1.05 |
| E-LIB | 4 | 16 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0003 | 0.0004 | -0.67 |
| E-LIB | 4 | 16 | 80 | 5 | frontier_all - continuous_prior_bayes | -0.0005 | 0.0004 | -1.32 |
| E-LIB | 4 | 64 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0000 | 0.0005 | -0.03 |
| E-LIB | 4 | 256 | 80 | 1 | frontier_all - continuous_prior_bayes | -0.0002 | 0.0005 | -0.35 |
| E-LIB | 4 | 256 | 80 | 5 | frontier_all - continuous_prior_bayes | -0.0005 | 0.0005 | -0.88 |
| E-LIB | 1 | 4 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 5 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 5 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 20 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 20 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 80 | 1 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 80 | 5 | frontier_all - flat_prior_bayes | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +1.1858 | 1.0051 | +1.18 |
| E-LIB | 1 | 4 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 20 | 1 | kernel_blocked - kernel_leave_one_out | +0.0003 | 0.0067 | +0.05 |
| E-LIB | 1 | 4 | 80 | 1 | kernel_blocked - kernel_leave_one_out | +0.0041 | 0.0030 | +1.34 |
| E-LIB | 1 | 4 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0006 | 0.0034 | +0.17 |
| E-LIB | 1 | 16 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.2265 | 0.2091 | +1.08 |
| E-LIB | 1 | 16 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 20 | 1 | kernel_blocked - kernel_leave_one_out | +0.0188 | 0.0096 | +1.96 |
| E-LIB | 1 | 16 | 80 | 1 | kernel_blocked - kernel_leave_one_out | +0.0005 | 0.0029 | +0.17 |
| E-LIB | 1 | 16 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0040 | 0.0038 | +1.06 |
| E-LIB | 1 | 64 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +1.1636 | 1.0182 | +1.14 |
| E-LIB | 1 | 64 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0576 | 0.0337 | -1.71 |
| E-LIB | 1 | 64 | 80 | 1 | kernel_blocked - kernel_leave_one_out | -0.0042 | 0.0026 | -1.60 |
| E-LIB | 1 | 64 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0023 | 0.0039 | +0.58 |
| E-LIB | 1 | 256 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.0544 | 0.0775 | +0.70 |
| E-LIB | 1 | 256 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 20 | 1 | kernel_blocked - kernel_leave_one_out | +0.0101 | 0.0081 | +1.24 |
| E-LIB | 1 | 256 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0747 | 0.0419 | -1.78 |
| E-LIB | 1 | 256 | 80 | 1 | kernel_blocked - kernel_leave_one_out | -0.0032 | 0.0028 | -1.14 |
| E-LIB | 1 | 256 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0056 | 0.0049 | +1.16 |
| E-LIB | 4 | 4 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.1833 | 0.2296 | +0.80 |
| E-LIB | 4 | 4 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 20 | 1 | kernel_blocked - kernel_leave_one_out | -0.0064 | 0.0067 | -0.95 |
| E-LIB | 4 | 4 | 80 | 1 | kernel_blocked - kernel_leave_one_out | -0.0012 | 0.0025 | -0.48 |
| E-LIB | 4 | 4 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0038 | 0.0036 | +1.06 |
| E-LIB | 4 | 16 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.4225 | 0.2962 | +1.43 |
| E-LIB | 4 | 16 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 20 | 1 | kernel_blocked - kernel_leave_one_out | -0.0011 | 0.0086 | -0.13 |
| E-LIB | 4 | 16 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0420 | 0.0293 | -1.43 |
| E-LIB | 4 | 16 | 80 | 1 | kernel_blocked - kernel_leave_one_out | -0.0032 | 0.0025 | -1.28 |
| E-LIB | 4 | 16 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0043 | 0.0040 | +1.08 |
| E-LIB | 4 | 64 | 5 | 1 | kernel_blocked - kernel_leave_one_out | +0.0325 | 0.1633 | +0.20 |
| E-LIB | 4 | 64 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 20 | 1 | kernel_blocked - kernel_leave_one_out | -0.0018 | 0.0092 | -0.20 |
| E-LIB | 4 | 64 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0111 | 0.0298 | -0.37 |
| E-LIB | 4 | 64 | 80 | 5 | kernel_blocked - kernel_leave_one_out | +0.0036 | 0.0041 | +0.87 |
| E-LIB | 4 | 256 | 5 | 1 | kernel_blocked - kernel_leave_one_out | -0.0224 | 0.2007 | -0.11 |
| E-LIB | 4 | 256 | 5 | 5 | kernel_blocked - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 20 | 1 | kernel_blocked - kernel_leave_one_out | -0.0006 | 0.0084 | -0.07 |
| E-LIB | 4 | 256 | 20 | 5 | kernel_blocked - kernel_leave_one_out | -0.0370 | 0.0346 | -1.07 |
| E-LIB | 1 | 4 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 20 | 1 | kernel_rolling_origin - kernel_blocked | +0.0122 | 0.0066 | +1.83 |
| E-LIB | 1 | 4 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0010 | 0.0036 | +0.28 |
| E-LIB | 1 | 4 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0050 | 0.0028 | +1.78 |
| E-LIB | 1 | 16 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 20 | 1 | kernel_rolling_origin - kernel_blocked | -0.0073 | 0.0085 | -0.87 |
| E-LIB | 1 | 16 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0620 | 0.0439 | +1.41 |
| E-LIB | 1 | 16 | 80 | 1 | kernel_rolling_origin - kernel_blocked | -0.0022 | 0.0038 | -0.57 |
| E-LIB | 1 | 16 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0024 | 0.0030 | +0.83 |
| E-LIB | 1 | 64 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -716.3719 | 708.4180 | -1.01 |
| E-LIB | 1 | 64 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 20 | 1 | kernel_rolling_origin - kernel_blocked | -0.0024 | 0.0087 | -0.27 |
| E-LIB | 1 | 64 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0573 | 0.0353 | +1.62 |
| E-LIB | 1 | 64 | 80 | 1 | kernel_rolling_origin - kernel_blocked | -0.0041 | 0.0037 | -1.10 |
| E-LIB | 1 | 64 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0070 | 0.0035 | +2.00 |
| E-LIB | 1 | 256 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 20 | 1 | kernel_rolling_origin - kernel_blocked | +0.0064 | 0.0082 | +0.79 |
| E-LIB | 1 | 256 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0658 | 0.0459 | +1.43 |
| E-LIB | 1 | 256 | 80 | 1 | kernel_rolling_origin - kernel_blocked | -0.0037 | 0.0035 | -1.06 |
| E-LIB | 1 | 256 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0054 | 0.0042 | +1.31 |
| E-LIB | 4 | 4 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -37.8077 | 31.1990 | -1.21 |
| E-LIB | 4 | 4 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 20 | 1 | kernel_rolling_origin - kernel_blocked | +0.0099 | 0.0076 | +1.30 |
| E-LIB | 4 | 4 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0388 | 0.0305 | +1.27 |
| E-LIB | 4 | 4 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0024 | 0.0035 | +0.69 |
| E-LIB | 4 | 4 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0055 | 0.0028 | +1.96 |
| E-LIB | 4 | 16 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -42.0697 | 21.3152 | -1.97 |
| E-LIB | 4 | 16 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 20 | 1 | kernel_rolling_origin - kernel_blocked | +0.0109 | 0.0092 | +1.18 |
| E-LIB | 4 | 16 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0375 | 0.0323 | +1.16 |
| E-LIB | 4 | 16 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0002 | 0.0033 | +0.07 |
| E-LIB | 4 | 16 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0033 | 0.0028 | +1.17 |
| E-LIB | 4 | 64 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -60.7175 | 42.2483 | -1.44 |
| E-LIB | 4 | 64 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 20 | 1 | kernel_rolling_origin - kernel_blocked | +0.0043 | 0.0092 | +0.46 |
| E-LIB | 4 | 64 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0211 | 0.0303 | +0.70 |
| E-LIB | 4 | 64 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0020 | 0.0036 | +0.57 |
| E-LIB | 4 | 64 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0055 | 0.0030 | +1.87 |
| E-LIB | 4 | 256 | 5 | 1 | kernel_rolling_origin - kernel_blocked | -25.5564 | 18.4033 | -1.39 |
| E-LIB | 4 | 256 | 5 | 5 | kernel_rolling_origin - kernel_blocked | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 20 | 5 | kernel_rolling_origin - kernel_blocked | +0.0564 | 0.0395 | +1.43 |
| E-LIB | 4 | 256 | 80 | 1 | kernel_rolling_origin - kernel_blocked | +0.0037 | 0.0037 | +1.01 |
| E-LIB | 4 | 256 | 80 | 5 | kernel_rolling_origin - kernel_blocked | +0.0012 | 0.0039 | +0.30 |
| E-LIB | 1 | 4 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 4 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0125 | 0.0068 | +1.83 |
| E-LIB | 1 | 4 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0218 | 0.0176 | -1.24 |
| E-LIB | 1 | 4 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0051 | 0.0041 | +1.25 |
| E-LIB | 1 | 4 | 80 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0056 | 0.0035 | +1.60 |
| E-LIB | 1 | 16 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 16 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0114 | 0.0092 | +1.24 |
| E-LIB | 1 | 16 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0345 | 0.0203 | -1.70 |
| E-LIB | 1 | 16 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0017 | 0.0035 | -0.49 |
| E-LIB | 1 | 16 | 80 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0064 | 0.0040 | +1.61 |
| E-LIB | 1 | 64 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -715.2083 | 708.4176 | -1.01 |
| E-LIB | 1 | 64 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 64 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0186 | 0.0093 | +1.99 |
| E-LIB | 1 | 64 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0003 | 0.0232 | -0.01 |
| E-LIB | 1 | 256 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 1 | 256 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0089 | 0.0234 | -0.38 |
| E-LIB | 1 | 256 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0069 | 0.0039 | -1.75 |
| E-LIB | 4 | 4 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -37.6244 | 31.1863 | -1.21 |
| E-LIB | 4 | 4 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 4 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0035 | 0.0068 | +0.51 |
| E-LIB | 4 | 4 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0306 | 0.0193 | -1.59 |
| E-LIB | 4 | 4 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0012 | 0.0036 | +0.33 |
| E-LIB | 4 | 16 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -41.6473 | 21.2898 | -1.96 |
| E-LIB | 4 | 16 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 16 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0098 | 0.0084 | +1.16 |
| E-LIB | 4 | 16 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | -0.0044 | 0.0204 | -0.22 |
| E-LIB | 4 | 16 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0030 | 0.0030 | -0.98 |
| E-LIB | 4 | 16 | 80 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0076 | 0.0042 | +1.81 |
| E-LIB | 4 | 64 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -60.6850 | 42.2144 | -1.44 |
| E-LIB | 4 | 64 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 64 | 20 | 1 | kernel_rolling_origin - kernel_leave_one_out | +0.0024 | 0.0093 | +0.26 |
| E-LIB | 4 | 64 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0100 | 0.0261 | +0.38 |
| E-LIB | 4 | 64 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0060 | 0.0031 | -1.95 |
| E-LIB | 4 | 256 | 5 | 1 | kernel_rolling_origin - kernel_leave_one_out | -25.5788 | 18.3911 | -1.39 |
| E-LIB | 4 | 256 | 5 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0000 | 0.0000 | +0.00 |
| E-LIB | 4 | 256 | 20 | 5 | kernel_rolling_origin - kernel_leave_one_out | +0.0194 | 0.0250 | +0.78 |
| E-LIB | 4 | 256 | 80 | 1 | kernel_rolling_origin - kernel_leave_one_out | -0.0028 | 0.0034 | -0.84 |
| E-LIB | 1 | 4 | 20 | 1 | matched_reference - continuous_prior_bayes | +0.0042 | 0.0022 | +1.88 |
| E-LIB | 1 | 4 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0026 | 0.0018 | +1.45 |
| E-LIB | 1 | 4 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0013 | 0.0007 | +1.78 |
| E-LIB | 1 | 16 | 5 | 1 | matched_reference - continuous_prior_bayes | +0.0019 | 0.0013 | +1.39 |
| E-LIB | 1 | 16 | 5 | 5 | matched_reference - continuous_prior_bayes | +0.0006 | 0.0014 | +0.46 |
| E-LIB | 1 | 16 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0002 | 0.0009 | +0.20 |
| E-LIB | 1 | 64 | 5 | 1 | matched_reference - continuous_prior_bayes | +0.0006 | 0.0009 | +0.73 |
| E-LIB | 1 | 64 | 5 | 5 | matched_reference - continuous_prior_bayes | +0.0002 | 0.0008 | +0.29 |
| E-LIB | 1 | 64 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0001 | 0.0007 | +0.12 |
| E-LIB | 1 | 64 | 80 | 1 | matched_reference - continuous_prior_bayes | +0.0006 | 0.0004 | +1.50 |
| E-LIB | 1 | 64 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0001 | 0.0003 | +0.47 |
| E-LIB | 1 | 256 | 5 | 1 | matched_reference - continuous_prior_bayes | -0.0001 | 0.0008 | -0.09 |
| E-LIB | 1 | 256 | 5 | 5 | matched_reference - continuous_prior_bayes | -0.0002 | 0.0005 | -0.33 |
| E-LIB | 1 | 256 | 20 | 1 | matched_reference - continuous_prior_bayes | +0.0008 | 0.0005 | +1.58 |
| E-LIB | 1 | 256 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0003 | 0.0004 | +0.79 |
| E-LIB | 1 | 256 | 80 | 1 | matched_reference - continuous_prior_bayes | +0.0001 | 0.0002 | +0.49 |
| E-LIB | 1 | 256 | 80 | 5 | matched_reference - continuous_prior_bayes | -0.0001 | 0.0002 | -0.30 |
| E-LIB | 4 | 4 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0016 | 0.0015 | +1.05 |
| E-LIB | 4 | 4 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0013 | 0.0007 | +1.92 |
| E-LIB | 4 | 16 | 5 | 1 | matched_reference - continuous_prior_bayes | +0.0019 | 0.0013 | +1.46 |
| E-LIB | 4 | 16 | 5 | 5 | matched_reference - continuous_prior_bayes | +0.0013 | 0.0012 | +1.10 |
| E-LIB | 4 | 16 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0000 | 0.0009 | +0.04 |
| E-LIB | 4 | 64 | 5 | 1 | matched_reference - continuous_prior_bayes | +0.0006 | 0.0008 | +0.76 |
| E-LIB | 4 | 64 | 5 | 5 | matched_reference - continuous_prior_bayes | -0.0002 | 0.0007 | -0.23 |
| E-LIB | 4 | 64 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0002 | 0.0006 | +0.30 |
| E-LIB | 4 | 64 | 80 | 1 | matched_reference - continuous_prior_bayes | +0.0006 | 0.0004 | +1.63 |
| E-LIB | 4 | 64 | 80 | 5 | matched_reference - continuous_prior_bayes | +0.0002 | 0.0003 | +0.66 |
| E-LIB | 4 | 256 | 5 | 1 | matched_reference - continuous_prior_bayes | -0.0003 | 0.0006 | -0.48 |
| E-LIB | 4 | 256 | 5 | 5 | matched_reference - continuous_prior_bayes | +0.0001 | 0.0005 | +0.29 |
| E-LIB | 4 | 256 | 20 | 1 | matched_reference - continuous_prior_bayes | +0.0007 | 0.0004 | +1.53 |
| E-LIB | 4 | 256 | 20 | 5 | matched_reference - continuous_prior_bayes | +0.0003 | 0.0004 | +0.81 |
| E-LIB | 4 | 256 | 80 | 1 | matched_reference - continuous_prior_bayes | +0.0001 | 0.0002 | +0.54 |
| E-LIB | 4 | 256 | 80 | 5 | matched_reference - continuous_prior_bayes | -0.0000 | 0.0002 | -0.23 |
| E-LIB | 1 | 16 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0009 | 0.0012 | +0.70 |
| E-LIB | 1 | 64 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0009 | 0.0009 | +1.02 |
| E-LIB | 1 | 256 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0005 | 0.0008 | +0.59 |
| E-LIB | 1 | 256 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0006 | 0.0008 | +0.75 |
| E-LIB | 4 | 16 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0019 | 0.0010 | +1.89 |
| E-LIB | 4 | 16 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0005 | 0.0011 | +0.48 |
| E-LIB | 4 | 64 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0006 | 0.0008 | +0.77 |
| E-LIB | 4 | 256 | 80 | 1 | matched_reference - flat_prior_bayes | +0.0003 | 0.0007 | +0.43 |
| E-LIB | 4 | 256 | 80 | 5 | matched_reference - flat_prior_bayes | +0.0004 | 0.0007 | +0.64 |
| E-LIB | 1 | 16 | 80 | 5 | matched_reference - frontier_all | +0.0009 | 0.0012 | +0.70 |
| E-LIB | 1 | 64 | 80 | 1 | matched_reference - frontier_all | +0.0009 | 0.0009 | +1.02 |
| E-LIB | 1 | 256 | 80 | 1 | matched_reference - frontier_all | +0.0005 | 0.0008 | +0.59 |
| E-LIB | 1 | 256 | 80 | 5 | matched_reference - frontier_all | +0.0006 | 0.0008 | +0.75 |
| E-LIB | 4 | 16 | 80 | 1 | matched_reference - frontier_all | +0.0019 | 0.0010 | +1.89 |
| E-LIB | 4 | 16 | 80 | 5 | matched_reference - frontier_all | +0.0005 | 0.0011 | +0.48 |
| E-LIB | 4 | 64 | 80 | 1 | matched_reference - frontier_all | +0.0006 | 0.0008 | +0.77 |
| E-LIB | 4 | 256 | 80 | 1 | matched_reference - frontier_all | +0.0003 | 0.0007 | +0.43 |
| E-LIB | 4 | 256 | 80 | 5 | matched_reference - frontier_all | +0.0004 | 0.0007 | +0.64 |

## (d) Population-knowledge gain G = (S_model - S_ctx)/(S_matched - S_ctx)

Ill-conditioned (abs(denominator) < 3 SE or < delta) in 96 of 192 rows. The denominator is matched - frontier. Ill-conditioned rows by (condition, r, n), counted over models and frontier types:

| condition | r | n | ill-conditioned rows | denominator range |
|---|---|---|---|---|
| E-CONT | 1 | 5 | 0/16 | +0.0760 .. +0.2186 |
| E-CONT | 1 | 20 | 8/16 | +0.0078 .. +0.0371 |
| E-CONT | 1 | 80 | 16/16 | +0.0005 .. +0.0095 |
| E-CONT | 4 | 5 | 0/16 | +0.0355 .. +0.1544 |
| E-CONT | 4 | 20 | 8/16 | +0.0046 .. +0.0368 |
| E-CONT | 4 | 80 | 16/16 | +0.0004 .. +0.0092 |
| E-LIB | 1 | 5 | 0/16 | +0.0825 .. +0.2271 |
| E-LIB | 1 | 20 | 8/16 | +0.0085 .. +0.0464 |
| E-LIB | 1 | 80 | 16/16 | +0.0005 .. +0.0096 |
| E-LIB | 4 | 5 | 0/16 | +0.0297 .. +0.1666 |
| E-LIB | 4 | 20 | 8/16 | +0.0060 .. +0.0435 |
| E-LIB | 4 | 80 | 16/16 | +0.0003 .. +0.0096 |

Well-conditioned G values (frontier_all baseline):

| condition | r | K | n | h | model | G +/- SE |
|---|---|---|---|---|---|---|
| E-CONT | 4 | 0 | 5 | 1 | library_K4 | -0.169 +/- 0.318 |
| E-CONT | 4 | 0 | 5 | 1 | library_K16 | 0.825 +/- 0.082 |
| E-CONT | 4 | 0 | 5 | 1 | library_K64 | 0.967 +/- 0.030 |
| E-CONT | 4 | 0 | 5 | 1 | library_K256 | 0.994 +/- 0.019 |
| E-CONT | 4 | 0 | 5 | 5 | library_K4 | 0.065 +/- 0.236 |
| E-CONT | 4 | 0 | 5 | 5 | library_K16 | 0.815 +/- 0.075 |
| E-CONT | 4 | 0 | 5 | 5 | library_K64 | 0.975 +/- 0.015 |
| E-CONT | 4 | 0 | 5 | 5 | library_K256 | 0.990 +/- 0.008 |
| E-LIB | 4 | 4 | 5 | 1 | continuous_prior_bayes | 0.857 +/- 0.044 |
| E-LIB | 4 | 4 | 5 | 5 | continuous_prior_bayes | 0.913 +/- 0.029 |
| E-LIB | 4 | 16 | 5 | 1 | continuous_prior_bayes | 0.949 +/- 0.030 |
| E-LIB | 4 | 16 | 5 | 5 | continuous_prior_bayes | 0.978 +/- 0.019 |
| E-LIB | 4 | 64 | 5 | 1 | continuous_prior_bayes | 0.985 +/- 0.018 |
| E-LIB | 4 | 64 | 5 | 5 | continuous_prior_bayes | 1.003 +/- 0.012 |
| E-LIB | 4 | 256 | 5 | 1 | continuous_prior_bayes | 1.010 +/- 0.022 |
| E-LIB | 4 | 256 | 5 | 5 | continuous_prior_bayes | 0.998 +/- 0.008 |
| E-CONT | 1 | 0 | 5 | 1 | library_K4 | 0.677 +/- 0.086 |
| E-CONT | 1 | 0 | 5 | 1 | library_K16 | 0.949 +/- 0.027 |
| E-CONT | 1 | 0 | 5 | 1 | library_K64 | 0.984 +/- 0.014 |
| E-CONT | 1 | 0 | 5 | 1 | library_K256 | 0.998 +/- 0.010 |
| E-CONT | 1 | 0 | 5 | 5 | library_K4 | 0.803 +/- 0.047 |
| E-CONT | 1 | 0 | 5 | 5 | library_K16 | 0.967 +/- 0.014 |
| E-CONT | 1 | 0 | 5 | 5 | library_K64 | 0.989 +/- 0.006 |
| E-CONT | 1 | 0 | 5 | 5 | library_K256 | 0.997 +/- 0.003 |
| E-LIB | 1 | 4 | 5 | 1 | continuous_prior_bayes | 0.915 +/- 0.022 |
| E-LIB | 1 | 4 | 5 | 5 | continuous_prior_bayes | 0.951 +/- 0.014 |
| E-LIB | 1 | 16 | 5 | 1 | continuous_prior_bayes | 0.980 +/- 0.013 |
| E-LIB | 1 | 16 | 5 | 5 | continuous_prior_bayes | 0.996 +/- 0.009 |
| E-LIB | 1 | 64 | 5 | 1 | continuous_prior_bayes | 0.993 +/- 0.009 |
| E-LIB | 1 | 64 | 5 | 5 | continuous_prior_bayes | 0.998 +/- 0.005 |
| E-LIB | 1 | 256 | 5 | 1 | continuous_prior_bayes | 1.001 +/- 0.009 |
| E-LIB | 1 | 256 | 5 | 5 | continuous_prior_bayes | 1.001 +/- 0.003 |

## Baseline performance (mean log score, E-CONT)

| r | n | h | matched | flat-prior | OLS-t | kernel RO | persistence |
|---|---|---|---|---|---|---|---|
| 1 | 5 | 1 | -1.4591 | -1.5351 | -1.6439 | -97.1089 | -1.7871 |
| 1 | 5 | 5 | -1.5631 | -1.7177 | -1.7816 | -275.8187 | -275.8187 |
| 1 | 20 | 1 | -1.4276 | -1.4354 | -1.4647 | -1.5430 | -1.6289 |
| 1 | 20 | 5 | -1.5554 | -1.5654 | -1.5829 | -1.8319 | -1.9023 |
| 1 | 80 | 1 | -1.4390 | -1.4396 | -1.4471 | -1.4837 | -1.6493 |
| 1 | 80 | 5 | -1.5774 | -1.5783 | -1.5839 | -1.6060 | -1.9162 |
| 4 | 5 | 1 | -0.0634 | -0.0988 | -0.2175 | -9.3056 | -0.4064 |
| 4 | 5 | 5 | -0.1696 | -0.2348 | -0.3240 | -922.8314 | -922.8314 |
| 4 | 20 | 1 | -0.0385 | -0.0431 | -0.0753 | -0.1556 | -0.2468 |
| 4 | 20 | 5 | -0.1668 | -0.1726 | -0.1952 | -0.4625 | -0.5379 |
| 4 | 80 | 1 | -0.0510 | -0.0514 | -0.0589 | -0.0953 | -0.2618 |
| 4 | 80 | 5 | -0.1904 | -0.1910 | -0.1966 | -0.2217 | -0.5304 |
