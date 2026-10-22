# Stage 0.6: stage06_noisy_probe (confirmatory)

Manifest SHA-256: fdb46788cd0fddba59cbc995adf7a3f6f410184e299b4dfc5cbecfa8f3f3fa05; config hash 8304d1ab2d37efbfea93fc25ecf37644341450985eb6c55a7d3397bc548f97c4; environment: qualified.

## Critical checks

- integrity: PASS
- tier1: PASS
- calibration: PASS
- numerics: PASS
- reproducibility: PASS
- tier2: PASS

```
{
 "integrity": {
  "details": {
   "R1_distinct_systems": true,
   "R1_vs_R2": "disjoint",
   "R1_vs_selection_63001": "disjoint",
   "R1_vs_stage05_52101": "disjoint",
   "R1_vs_stage05_52102": "disjoint",
   "R2_distinct_systems": true,
   "R2_vs_selection_63001": "disjoint",
   "R2_vs_stage05_52101": "disjoint",
   "R2_vs_stage05_52102": "disjoint"
  },
  "ok": true
 },
 "tier1": {
  "details": {
   "items_compared": 36000,
   "max_abs_diff": 7.993605777301127e-15,
   "tolerance": 1e-09
  },
  "passed": true,
  "tolerance_matches_config": true
 },
 "calibration": {
  "tests": 96,
  "per_test_level": 1.0416666666666666e-05,
  "min_p": 0.04906804749511129
 },
 "numerics": {
  "max_gain_change_node_doubling": 2.6645352591003757e-14,
  "budget": 0.0002
 },
 "reproducibility": {
  "max_abs_diff": 7.993605777301127e-15,
  "tolerance": 1e-10
 },
 "tier2": "PASS"
}
```

## Verdict: **STOP**

- all 18 gains have adjusted upper bound < delta in both replicates

Stricter variant (the same adjacent pair at >= 2 scales; descriptive): False {'h=1': [], 'h=5': []}

Q(h, r): {'h=1|r=0.25': [], 'h=1|r=1.0': [], 'h=1|r=4.0': [], 'h=5|r=0.25': [], 'h=5|r=1.0': [], 'h=5|r=4.0': []}

## Tier-2 zero-noise reproduction: **PASS** (z_crit 3.341, max combined SE 0.00478)

| rep | r | h | Stage 0.6 | Stage 0.5 | combined SE | z |
|---|---|---|---|---|---|---|
| R1 | 0.25 | 1 | +0.0270 | +0.0311 | 0.00185 | -2.20 |
| R1 | 0.25 | 5 | +0.0101 | +0.0101 | 0.00137 | -0.02 |
| R1 | 1.0 | 1 | +0.0234 | +0.0276 | 0.00176 | -2.37 |
| R1 | 1.0 | 5 | +0.0089 | +0.0090 | 0.00136 | -0.07 |
| R1 | 4.0 | 1 | +0.0113 | +0.0149 | 0.00130 | -2.80 |
| R1 | 4.0 | 5 | +0.0050 | +0.0065 | 0.00115 | -1.24 |
| R2 | 0.25 | 1 | +0.0270 | +0.0311 | 0.00183 | -2.22 |
| R2 | 0.25 | 5 | +0.0120 | +0.0101 | 0.00127 | +1.48 |
| R2 | 1.0 | 1 | +0.0235 | +0.0276 | 0.00175 | -2.33 |
| R2 | 1.0 | 5 | +0.0118 | +0.0090 | 0.00123 | +2.23 |
| R2 | 4.0 | 1 | +0.0124 | +0.0149 | 0.00136 | -1.85 |
| R2 | 4.0 | 5 | +0.0092 | +0.0065 | 0.00107 | +2.54 |

## Replicate R1: simultaneous band (c = 2.8987, 20000 draws, relative MC error 0.0065); ok = True 

| kind | q | h | r | estimate | SE | adjusted lower | adjusted upper |
|---|---|---|---|---|---|---|---|
| gain | 0.755 | 1 | 0.25 | +0.0066 | 0.0003 | +0.0058 | +0.0073 |
| gain | 0.755 | 1 | 1.0 | +0.0063 | 0.0003 | +0.0055 | +0.0070 |
| gain | 0.755 | 1 | 4.0 | +0.0038 | 0.0002 | +0.0032 | +0.0044 |
| gain | 0.755 | 5 | 0.25 | +0.0033 | 0.0003 | +0.0023 | +0.0042 |
| gain | 0.755 | 5 | 1.0 | +0.0031 | 0.0003 | +0.0022 | +0.0041 |
| gain | 0.755 | 5 | 4.0 | +0.0020 | 0.0003 | +0.0012 | +0.0029 |
| gain | 2.56 | 1 | 0.25 | +0.0056 | 0.0002 | +0.0050 | +0.0063 |
| gain | 2.56 | 1 | 1.0 | +0.0055 | 0.0002 | +0.0048 | +0.0061 |
| gain | 2.56 | 1 | 4.0 | +0.0036 | 0.0002 | +0.0030 | +0.0042 |
| gain | 2.56 | 5 | 0.25 | +0.0022 | 0.0002 | +0.0015 | +0.0029 |
| gain | 2.56 | 5 | 1.0 | +0.0021 | 0.0002 | +0.0014 | +0.0028 |
| gain | 2.56 | 5 | 4.0 | +0.0015 | 0.0002 | +0.0008 | +0.0021 |
| gain | 6.5 | 1 | 0.25 | +0.0036 | 0.0002 | +0.0031 | +0.0041 |
| gain | 6.5 | 1 | 1.0 | +0.0035 | 0.0002 | +0.0030 | +0.0040 |
| gain | 6.5 | 1 | 4.0 | +0.0026 | 0.0002 | +0.0022 | +0.0031 |
| gain | 6.5 | 5 | 0.25 | +0.0016 | 0.0002 | +0.0011 | +0.0021 |
| gain | 6.5 | 5 | 1.0 | +0.0016 | 0.0002 | +0.0011 | +0.0021 |
| gain | 6.5 | 5 | 4.0 | +0.0011 | 0.0002 | +0.0007 | +0.0016 |
| increment | 0.755 | 1 | 0.25 | +0.0009 | 0.0002 | +0.0002 | +0.0015 |
| increment | 0.755 | 1 | 1.0 | +0.0009 | 0.0002 | +0.0002 | +0.0016 |
| increment | 0.755 | 1 | 4.0 | +0.0006 | 0.0002 | +0.0001 | +0.0012 |
| increment | 0.755 | 5 | 0.25 | -0.0005 | 0.0002 | -0.0011 | +0.0001 |
| increment | 0.755 | 5 | 1.0 | -0.0004 | 0.0002 | -0.0010 | +0.0002 |
| increment | 0.755 | 5 | 4.0 | +0.0000 | 0.0002 | -0.0005 | +0.0005 |
| increment | 2.56 | 1 | 0.25 | -0.0001 | 0.0003 | -0.0009 | +0.0008 |
| increment | 2.56 | 1 | 1.0 | +0.0001 | 0.0003 | -0.0007 | +0.0010 |
| increment | 2.56 | 1 | 4.0 | +0.0004 | 0.0002 | -0.0003 | +0.0011 |
| increment | 2.56 | 5 | 0.25 | -0.0016 | 0.0003 | -0.0024 | -0.0007 |
| increment | 2.56 | 5 | 1.0 | -0.0014 | 0.0003 | -0.0023 | -0.0005 |
| increment | 2.56 | 5 | 4.0 | -0.0005 | 0.0002 | -0.0012 | +0.0001 |
| increment | 6.5 | 1 | 0.25 | -0.0021 | 0.0003 | -0.0030 | -0.0013 |
| increment | 6.5 | 1 | 1.0 | -0.0019 | 0.0003 | -0.0027 | -0.0010 |
| increment | 6.5 | 1 | 4.0 | -0.0006 | 0.0002 | -0.0013 | +0.0001 |
| increment | 6.5 | 5 | 0.25 | -0.0022 | 0.0004 | -0.0032 | -0.0011 |
| increment | 6.5 | 5 | 1.0 | -0.0019 | 0.0004 | -0.0030 | -0.0009 |
| increment | 6.5 | 5 | 4.0 | -0.0009 | 0.0003 | -0.0017 | -0.0000 |

| cell (q, h, r) | G+ | I+ | G- | NEG | SUPPORTED |
|---|---|---|---|---|---|
| 0.755|1|0.25 | False | True | True | False | False |
| 0.755|1|1.0 | False | True | True | False | False |
| 0.755|1|4.0 | False | True | True | False | False |
| 0.755|5|0.25 | False | False | True | False | False |
| 0.755|5|1.0 | False | False | True | False | False |
| 0.755|5|4.0 | False | False | True | False | False |
| 2.56|1|0.25 | False | False | True | False | False |
| 2.56|1|1.0 | False | False | True | False | False |
| 2.56|1|4.0 | False | False | True | False | False |
| 2.56|5|0.25 | False | False | True | False | False |
| 2.56|5|1.0 | False | False | True | False | False |
| 2.56|5|4.0 | False | False | True | False | False |
| 6.5|1|0.25 | False | False | True | False | False |
| 6.5|1|1.0 | False | False | True | False | False |
| 6.5|1|4.0 | False | False | True | False | False |
| 6.5|5|0.25 | False | False | True | False | False |
| 6.5|5|1.0 | False | False | True | False | False |
| 6.5|5|4.0 | False | False | True | False | False |

## Replicate R2: simultaneous band (c = 2.9085, 20000 draws, relative MC error 0.0075); ok = True 

| kind | q | h | r | estimate | SE | adjusted lower | adjusted upper |
|---|---|---|---|---|---|---|---|
| gain | 0.755 | 1 | 0.25 | +0.0069 | 0.0003 | +0.0062 | +0.0077 |
| gain | 0.755 | 1 | 1.0 | +0.0065 | 0.0003 | +0.0058 | +0.0072 |
| gain | 0.755 | 1 | 4.0 | +0.0039 | 0.0002 | +0.0033 | +0.0045 |
| gain | 0.755 | 5 | 0.25 | +0.0039 | 0.0003 | +0.0030 | +0.0048 |
| gain | 0.755 | 5 | 1.0 | +0.0037 | 0.0003 | +0.0027 | +0.0046 |
| gain | 0.755 | 5 | 4.0 | +0.0026 | 0.0003 | +0.0018 | +0.0033 |
| gain | 2.56 | 1 | 0.25 | +0.0058 | 0.0002 | +0.0051 | +0.0065 |
| gain | 2.56 | 1 | 1.0 | +0.0056 | 0.0002 | +0.0049 | +0.0062 |
| gain | 2.56 | 1 | 4.0 | +0.0036 | 0.0002 | +0.0030 | +0.0041 |
| gain | 2.56 | 5 | 0.25 | +0.0027 | 0.0002 | +0.0021 | +0.0034 |
| gain | 2.56 | 5 | 1.0 | +0.0026 | 0.0002 | +0.0020 | +0.0033 |
| gain | 2.56 | 5 | 4.0 | +0.0019 | 0.0002 | +0.0013 | +0.0025 |
| gain | 6.5 | 1 | 0.25 | +0.0036 | 0.0002 | +0.0031 | +0.0041 |
| gain | 6.5 | 1 | 1.0 | +0.0036 | 0.0002 | +0.0031 | +0.0041 |
| gain | 6.5 | 1 | 4.0 | +0.0026 | 0.0002 | +0.0021 | +0.0030 |
| gain | 6.5 | 5 | 0.25 | +0.0018 | 0.0002 | +0.0013 | +0.0023 |
| gain | 6.5 | 5 | 1.0 | +0.0017 | 0.0002 | +0.0012 | +0.0022 |
| gain | 6.5 | 5 | 4.0 | +0.0013 | 0.0002 | +0.0009 | +0.0018 |
| increment | 0.755 | 1 | 0.25 | +0.0011 | 0.0002 | +0.0005 | +0.0018 |
| increment | 0.755 | 1 | 1.0 | +0.0012 | 0.0002 | +0.0005 | +0.0019 |
| increment | 0.755 | 1 | 4.0 | +0.0007 | 0.0002 | +0.0002 | +0.0012 |
| increment | 0.755 | 5 | 0.25 | -0.0004 | 0.0002 | -0.0010 | +0.0003 |
| increment | 0.755 | 5 | 1.0 | -0.0004 | 0.0002 | -0.0010 | +0.0002 |
| increment | 0.755 | 5 | 4.0 | -0.0002 | 0.0002 | -0.0006 | +0.0003 |
| increment | 2.56 | 1 | 0.25 | -0.0000 | 0.0003 | -0.0008 | +0.0008 |
| increment | 2.56 | 1 | 1.0 | +0.0003 | 0.0003 | -0.0005 | +0.0011 |
| increment | 2.56 | 1 | 4.0 | +0.0004 | 0.0002 | -0.0003 | +0.0010 |
| increment | 2.56 | 5 | 0.25 | -0.0015 | 0.0003 | -0.0024 | -0.0007 |
| increment | 2.56 | 5 | 1.0 | -0.0014 | 0.0003 | -0.0022 | -0.0006 |
| increment | 2.56 | 5 | 4.0 | -0.0009 | 0.0002 | -0.0015 | -0.0002 |
| increment | 6.5 | 1 | 0.25 | -0.0022 | 0.0003 | -0.0030 | -0.0013 |
| increment | 6.5 | 1 | 1.0 | -0.0017 | 0.0003 | -0.0025 | -0.0009 |
| increment | 6.5 | 1 | 4.0 | -0.0006 | 0.0002 | -0.0013 | +0.0001 |
| increment | 6.5 | 5 | 0.25 | -0.0025 | 0.0003 | -0.0035 | -0.0015 |
| increment | 6.5 | 5 | 1.0 | -0.0023 | 0.0003 | -0.0033 | -0.0013 |
| increment | 6.5 | 5 | 4.0 | -0.0014 | 0.0003 | -0.0022 | -0.0006 |

| cell (q, h, r) | G+ | I+ | G- | NEG | SUPPORTED |
|---|---|---|---|---|---|
| 0.755|1|0.25 | False | True | True | False | False |
| 0.755|1|1.0 | False | True | True | False | False |
| 0.755|1|4.0 | False | True | True | False | False |
| 0.755|5|0.25 | False | False | True | False | False |
| 0.755|5|1.0 | False | False | True | False | False |
| 0.755|5|4.0 | False | False | True | False | False |
| 2.56|1|0.25 | False | False | True | False | False |
| 2.56|1|1.0 | False | False | True | False | False |
| 2.56|1|4.0 | False | False | True | False | False |
| 2.56|5|0.25 | False | False | True | False | False |
| 2.56|5|1.0 | False | False | True | False | False |
| 2.56|5|4.0 | False | False | True | False | False |
| 6.5|1|0.25 | False | False | True | False | False |
| 6.5|1|1.0 | False | False | True | False | False |
| 6.5|1|4.0 | False | False | True | False | False |
| 6.5|5|0.25 | False | False | True | False | False |
| 6.5|5|1.0 | False | False | True | False | False |
| 6.5|5|4.0 | False | False | True | False | False |

Descriptive only: n-curves (n_curves.csv), the pooled L-gains (pooled_descriptive.csv) and the noise-naive secondary baselines (naive_secondary.csv; noise-misspecified).
