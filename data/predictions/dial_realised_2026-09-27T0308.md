# Realised-mask dial comparators on the placement 2026-09-27T030805Z (Deviation 60 part (7))

Lists day3_dial_refs.json; snapshot `ibm_phoenix_2026-09-27T030805Z.csv`; code 17473f678fb1788f5b611fdf2cff7dbc522d9fc2 (dev60-h7-analysis) + the Deviation 60 part (7) code committed with these files + 0f76200c64d2b28c6b34a2d3587340b56b754a5a (dev62-repackage: data, Deviation 62 placement rule); generated 2026-10-04T16:26:20Z; command `python scripts/redraw_dial_points.py --joblist data/joblists/paper1/day3_dial_refs.json`; sampler {'n_samples': 2000000, 'seed': 0, 'chunk': 25000}.

The shared-mask estimators estimate the off-diagonal moment over each probe's realised masks; these values are the comparators of H5 / H6 (sigma = sampling error). The mixture rows are recorded beside them and are not used in any test.

| probe | rung | L | dial | p | seed | k = L variance (realised +/- s.e.) | mixture | ratio | Var[C_mix] (realised +/- s.e.) | mixture | Dev 33 floor grad: realised / mixture | Dev 33 floor cost: realised / mixture |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dial_p0.25_L8_kL_n100 | n100 | 8 | reset | 0.25 | 24991001 | 2.1696e-03 +/- 1.6e-05 | 2.0805e-03 | 1.043 | 4.7656e-03 +/- 2.1e-05 | 3.6160e-03 | 7.1500e-04 / 1.1033e-03 | 3.1566e-03 / 2.2126e-03 |
| dial_p0.25_L8_kL_n40 | n40 | 8 | reset | 0.25 | 21991001 | 1.4357e-03 +/- 1.0e-05 | 2.1706e-03 | 0.661 | 1.9483e-03 +/- 1.1e-05 | 3.5933e-03 | 3.8728e-04 / 1.1838e-03 | 6.5700e-04 / 2.2043e-03 |
| dephasing_dial_p0.5_L8_kL | n60 | 8 | dephase | 0.5 | 22991001 | 1.7314e-05 +/- 1.1e-06 | 1.5551e-05 | 1.113 | 1.7524e-05 +/- 1.1e-06 | 1.6405e-05 |  / 7.5398e-03 |  / 1.5077e-02 |
| dial_p0.25_L8_kL | n60 | 8 | reset | 0.25 | 22991001 | 1.9692e-03 +/- 8.7e-06 | 2.0502e-03 | 0.960 | 3.3881e-03 +/- 1.1e-05 | 3.5684e-03 | 1.1754e-03 / 1.0893e-03 | 2.3518e-03 / 2.1764e-03 |
| dial_p0.5_L8_kL | n60 | 8 | reset | 0.5 | 22991001 | 7.0415e-03 +/- 1.3e-05 | 9.7514e-03 | 0.722 | 1.8789e-02 +/- 2.8e-05 | 1.8312e-02 | 4.8152e-03 / 7.5398e-03 | 1.5621e-02 / 1.5077e-02 |
| dial_p0.25_L12_kL | n60 | 12 | reset | 0.25 | 23001001 | 1.9385e-03 +/- 1.1e-05 | 2.0465e-03 | 0.947 | 2.7693e-03 +/- 1.2e-05 | 3.5625e-03 | 6.9157e-04 / 1.0893e-03 | 1.2998e-03 / 2.1764e-03 |
| dial_p0.5_L12_kL | n60 | 12 | reset | 0.5 | 23001001 | 7.2264e-03 +/- 1.3e-05 | 9.7514e-03 | 0.741 | 1.7226e-02 +/- 2.5e-05 | 1.8312e-02 | 4.4502e-03 / 7.5398e-03 | 1.3540e-02 / 1.5077e-02 |
