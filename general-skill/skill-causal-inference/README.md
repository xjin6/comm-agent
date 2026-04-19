# skill-causal-inference

> **v0.1.0** · Updated 2026-04-20 · `analysis`

Diagnoses feasibility of quasi-experimental causal inference methods (DID, PSM, PSW, IV, RDD) for a given dataset or research idea, runs applicable methods, and outputs publication-ready three-line Word tables and diagnostic plots. Supports both R (default) and Python.

## Trigger

Say "帮我做因果推断", "能用 DID 吗", "run causal inference", or describe a natural experiment.

## Methods covered

| Method | R packages | Python packages |
| --- | --- | --- |
| DID (Difference-in-Differences) | `fixest`, `did` (Callaway & Sant'Anna) | `linearmodels` |
| PSM (Propensity Score Matching) | `MatchIt`, `cobalt` | `causalml` |
| PSW (Propensity Score Weighting) | `WeightIt`, `estimatr` | `causalml` |
| IV (Instrumental Variables) | `fixest` (feols 2SLS) | `linearmodels` |
| RDD (Regression Discontinuity) | `rdrobust`, `rddensity` | `rdrobust` (Python port) |

## Workflow

1. Understand research setup (outcome, treatment, data structure)
2. Feasibility diagnosis — outputs a table of ✓ / ✗ / ? per method
3. Data checks — parallel trends, F-stat, McCrary density, common support, etc.
4. Run analysis — generates and executes R (or Python) script
5. Export outputs — Word tables + PNG figures
6. Interpret results — plain-language causal interpretation + robustness suggestions

## Output

Files saved to `your-project/project-{name}/output/causal-inference/`:

| Path | Description |
| --- | --- |
| `causal_feasibility.txt` | Method diagnosis and assumption check report |
| `did/table_did_descriptive.docx` | Descriptive statistics (overall + by treatment group) |
| `did/table_did_main.docx` | Main DID regression table (5-column progressive) |
| `did/table_did_robustness.docx` | Placebo and robustness checks |
| `did/fig_did_trends.png` | Treatment vs control raw outcome trends |
| `did/fig_did_eventstudy.png` | Event-study plot with 95% CI |
| `psm/table_causal_psm.docx` | PSM outcome regression table |
| `psm/fig_psm_balance.png` | Love plot (SMD before/after matching) |
| `psm/fig_psm_overlap.png` | Propensity score overlap |
| `psw/table_causal_psw.docx` | PSW outcome regression table |
| `psw/fig_psw_balance.png` | Weighted balance plot |
| `iv/table_iv.docx` | IV regression table (2SLS) |
| `iv/fig_iv_firststage.png` | First-stage fit scatter |
| `rdd/table_rdd_main.docx` | RDD estimates table |
| `rdd/fig_rdd_main.png` | RDD scatter + local polynomial fit |
| `rdd/fig_rdd_density.png` | McCrary density test plot |

Scripts saved to `your-project/project-{name}/scripts/causal_{method}.R`.

## Installation

```bash
ln -sf /absolute/path/to/comm-agent/general-skill/skill-causal-inference ~/.claude/skills/skill-causal-inference
```

## R dependencies

```r
install.packages(c(
  "fixest", "did", "MatchIt", "WeightIt", "cobalt", "estimatr",
  "rdrobust", "rddensity",
  "modelsummary", "flextable", "officer",
  "ggplot2", "dplyr", "tidyr", "sandwich", "lmtest"
))
```

## Author

**Lihan Yan** (@Lihan-YAN) · Lihan-YAN@users.noreply.github.com

## License

CC BY-NC-ND 4.0
