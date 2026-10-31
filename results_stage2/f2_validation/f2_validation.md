# F2 reference validation

Overall: PASS; 117 statistical tests, per-test level 8.55e-05 (family 0.01); one-sided z_crit 3.76

| check | n | r | smallest p / smallest z (vs) | pass |
|---|---|---|---|---|
| optimality | 5 | 0.25 | 5.36 (LIB-64) | True |
| optimality | 5 | 1.0 | 5.48 (LIB-64) | True |
| optimality | 5 | 4.0 | 5.49 (LIB-64) | True |
| optimality | 10 | 0.25 | 7.48 (LIB-64) | True |
| optimality | 10 | 1.0 | 5.03 (LIB-64) | True |
| optimality | 10 | 4.0 | 8.89 (LIB-64) | True |
| optimality | 20 | 0.25 | 9.39 (LIB-16) | True |
| optimality | 20 | 1.0 | 2.84 (LIB-16) | True |
| optimality | 20 | 4.0 | 6.40 (LIB-64) | True |
| calibration | 5 | 0.25 | 0.0171 | True |
| calibration | 5 | 1.0 | 0.192 | True |
| calibration | 5 | 4.0 | 0.0641 | True |
| calibration | 10 | 0.25 | 0.162 | True |
| calibration | 10 | 1.0 | 0.255 | True |
| calibration | 10 | 4.0 | 0.13 | True |
| calibration | 20 | 0.25 | 0.0563 | True |
| calibration | 20 | 1.0 | 0.268 | True |
| calibration | 20 | 4.0 | 0.022 | True |

Structural: matched_guard True, leakage True, spectral_radius True
