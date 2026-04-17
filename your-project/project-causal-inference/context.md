# Project: causal-inference

## Research Overview
Quasi-experimental causal inference methods applied to historical and communication research datasets.

## Current Dataset
**panel_data_update.csv** — County-year panel (Zhou & Wang, SSRN 5244337)
- Unit: U.S. county × year (1800–1920), N ≈ 20,957 after cleaning
- DV: `white_sup_ratio` — prevalence of racist narratives in newspapers
- Treatment: `ln_slave_after` = ln(slave_ratio) × post-1865 (continuous DID)
- FE: county + year; optional pre-rebellion trend × year

## Methods Applied
- Continuous DID (window 1860–1870 and full sample 1800–1920)
- Parallel trends event-study (10-year bins)
- Pre-trend test (pre-1865 only)

## Reference
Zhou, Z. & Wang, C. (2025). SSRN 5244337.
