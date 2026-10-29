# F3 short-context separability map (map; seed role f3_map)

Validity: VALID

* i_node_doubling: pass {"max_abs_nats": 4.440892098500626e-15, "tolerance": 1e-06}
* iii_library_vs_independent_kalman: pass {"max_abs_nats": 5.10702591327572e-15, "tolerance": 1e-10}
* iv_disjointness: pass {"held_coefficients_equal_to_an_atom": 0}
* ii_q0_vs_stage1A_map: pass {"z": {"2": -0.18268924914086493, "3": -2.1850225256053193, "5": -0.10141590764697718}, "bound": 4.0, "stage1A": {"2": [0.041463025258438084, 0.0004153198590822218], "3": [0.0358503734529325, 0.000384906876526067], "5": [0.02743305619981977, 0.00033115009100145897]}}

## Q1-type: HELD pop vs stab, largest n with IDENTIFIABLE (n in 2..9; '-' none)

| q | h | r = 0.25 | r = 1 | r = 4 |
|---|---|---|---|---|
| 0.0 | 1 | 7 | 5 | - |
| 0.0 | 5 | - | - | - |
| 0.755 | 1 | 2 | 2 | - |
| 0.755 | 5 | - | - | - |
| 2.56 | 1 | - | - | - |
| 2.56 | 5 | - | - | - |
| 6.5 | 1 | - | - | - |
| 6.5 | 5 | - | - | - |

## Q2-type: library cells marked IDENTIFIABLE (count of (r, n) cells out of 24, per q, h, K)

| set / pair | q | h | K=2 | K=4 | K=16 | K=64 |
|---|---|---|---|---|---|---|
| HELD pop-lib | 0.0 | 1 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 0.0 | 5 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 0.755 | 1 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 0.755 | 5 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 2.56 | 1 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 2.56 | 5 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 6.5 | 1 | 0 | 0 | 0 | 0 |
| HELD pop-lib | 6.5 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 0.0 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 0.0 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 0.755 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 0.755 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 2.56 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 2.56 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 6.5 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-pop | 6.5 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 0.0 | 1 | 0 | 0 | 4 | 5 |
| INLIB lib-stab | 0.0 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 0.755 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 0.755 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 2.56 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 2.56 | 5 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 6.5 | 1 | 0 | 0 | 0 | 0 |
| INLIB lib-stab | 6.5 | 5 | 0 | 0 | 0 | 0 |

2496 decision cells; per-cell two-sided level about 0.0027, so about 6.7 cells could be mis-marked by chance (no global correction; the map guides design only).
