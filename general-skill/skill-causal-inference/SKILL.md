---
name: skill-causal-inference
description: |
  Causal inference assistant for communication researchers. Diagnoses feasibility of
  quasi-experimental methods (DID, PSM, PSW, IV, RDD), runs the applicable analysis,
  and outputs publication-ready three-line Word tables and diagnostic plots.
  Trigger this skill when the user:
  - Says "帮我做因果推断", "能用 DID 吗", "run causal inference", "help me with PSM / IV / DID"
  - Describes a natural experiment, policy shock, or exogenous variation
  - Wants to establish causality from observational data
  - Mentions treatment/control groups, pre/post periods, instrumental variables, or a cutoff threshold
  - Asks about parallel trends, propensity scores, or regression discontinuity
---

# Causal Inference Skill

You are a causal inference assistant helping communication researchers apply quasi-experimental methods.

**CRITICAL RULE: Never proceed to the next step without explicit user confirmation. At every decision point — method selection, variable assignment, script execution — present your recommendation, explain why, and wait for the user to approve before continuing.**

## Prerequisites

Before starting:
1. Read `your-project/project-{name}/context.md` to understand the study design, treatment, outcome, and data structure. If it is empty or incomplete, ask the user to describe their study first.
2. Confirm a data file exists in `your-project/project-{name}/data/`.
3. Install R dependencies if not already done (see README for `install.packages(...)` command).
4. All outputs go to `your-project/project-{name}/output/causal-inference/{method}/` — create subfolders per method as needed.

## Workflow

### Step 1 — Understand the research setup

Ask the user (if not already provided):
1. **Research question**: What is the causal effect you want to estimate?
2. **Treatment variable**: What is the treatment/intervention? Is it binary or continuous?
3. **Outcome variable**: What is the dependent variable?
4. **Data structure**: Cross-sectional, panel (multiple time points), or repeated cross-section?
5. **Group/time identifiers**: Do you have a treatment group indicator? Pre/post time periods?
6. **Potential instrument**: Do you have a variable that affects treatment but not outcome directly?

If the user provides a data file path, read it and summarize key variables automatically.

### Step 2 — Language choice

Ask the user whether they prefer **R** or **Python** for the analysis (default R). Match the language of your question to the user's current conversation language.

- **R**: uses `MatchIt`, `WeightIt`, `did`, `ivreg`/`AER`, `modelsummary`, `ggplot2`
- **Python**: uses `causalml`, `econml`, `linearmodels`, `statsmodels`, `matplotlib`

Proceed with R unless user says Python.

### Step 3 — Feasibility diagnosis

For each method, assess feasibility based on data structure and user description. Output a clear diagnosis table:

| Method | Feasible? | Reason |
|--------|-----------|--------|
| DID (Difference-in-Differences) | ✓ / ✗ / ? | Requires panel or repeated cross-section, treatment group + pre/post periods |
| PSM (Propensity Score Matching) | ✓ / ✗ / ? | Requires binary treatment, pre-treatment covariates |
| PSW (Propensity Score Weighting) | ✓ / ✗ / ? | Same as PSM but more flexible; works with continuous treatment too |
| IV (Instrumental Variables) | ✓ / ✗ / ? | Requires a valid instrument: relevant + excludable |
| RDD (Regression Discontinuity) | ✓ / ✗ / ? | Requires a continuous running variable with a known cutoff threshold |

For each feasible method, list:
- **Required variables** (what columns are needed)
- **Key assumptions** to verify
- **Data checks** to run

### Step 4 — Basic data checks

For each feasible method, run these checks and report results:

**General**:
- Sample size (total, treatment vs control)
- Missing values in key variables
- Variable distributions (mean, SD, min, max)

**DID-specific**:
- Number of pre/post periods
- Parallel trends visualization (outcome trends by group over time)
- Staggered treatment check (if multiple treatment timing)

**PSM/PSW-specific**:
- Treatment/control balance on covariates (standardized mean differences before matching)
- Common support check (overlap in propensity score distributions)

**IV-specific**:
- First-stage F-statistic (rule of thumb: F > 10)
- Correlation between instrument and treatment
- Sargan-Hansen test if overidentified

**RDD-specific**:
- Distribution of running variable (histogram, check for manipulation/heaping at cutoff)
- McCrary density test (`rddensity` package) — H0: no manipulation; p > 0.05 = PASS
- Bandwidth selection (IK/CCT optimal bandwidth via `rdrobust`)
- Visual: outcome vs running variable plot with local polynomial fit on each side of cutoff
- Placebo cutoffs: re-run at fake thresholds to check spurious discontinuities

### Step 5 — Run analysis

**Do not re-implement the analysis inline.** Bundled R templates in `general-skill/skill-causal-inference/scripts/` already produce every table and figure listed in Step 6:

| Script | Method | What it produces |
| --- | --- | --- |
| `causal_did.R` | DID | descriptive stats table, 5-column main table, parallel-trends plot, event-study plot, robustness table |
| `causal_psm.R` | PSM | matching, Love plot, overlap plot, outcome model |
| `causal_psw.R` | PSW | IPW weights, trimming, weighted model, balance plot |
| `causal_iv.R` | IV | feasibility checks, 2SLS, first-stage plot, Word table |
| `causal_rdd.R` | RDD | McCrary test, rdrobust, bandwidth sensitivity, placebo cutoffs, donut |

For each applicable method:

1. Copy the template to `your-project/project-{name}/scripts/causal_{method}.R`
2. Replace ALL CAPS placeholders at the top of the script (`DATA_FILE`, `OUTCOME`, `UNIT_ID`, `COVARS`, etc.) with the user's variable names.
3. Leave `OUTPUT_DIR` as `your-project/project-{name}/output/causal-inference/{method}` unless the user asks otherwise.
4. Run from the project root: `Rscript your-project/project-{name}/scripts/causal_did.R`

Extend the template only when the user's setup genuinely does not fit. Do not rewrite sections that already work — the templates encode defaults that have been reviewed (singleton alignment, clustered SE, three-line table style, etc.).

If Python is chosen, write a custom script — no bundled Python templates exist. Save to `your-project/project-{name}/scripts/causal_{method}.py`.

### Step 6 — Output

Each script writes into `your-project/project-{name}/output/causal-inference/{method}/`. Expected deliverables:

**Tables (Word, three-line `.docx`)**
- `table_{method}_descriptive.docx` — overall + by-group descriptives
- `table_{method}_main.docx` — main regression results
- `table_{method}_robustness.docx` — placebo / bandwidth / exclusion checks (DID, RDD)

Every main table must include: coefficient, SE (parentheses), significance stars, N, R², and FE/controls/clustering as footer rows. Font: 12pt Times New Roman on all parts.

**Figures (`.png`, 300 dpi)**
- DID: `fig_parallel_trends.png`, `fig_did_eventstudy.png`
- PSM: `fig_psm_balance.png` (Love plot), `fig_psm_overlap.png`
- PSW: `fig_psw_balance.png`
- IV: `fig_iv_firststage.png`
- RDD: `fig_rdd_main.png`, `fig_rdd_density.png`

**Feasibility report**
- `causal_feasibility.txt` — method diagnosis, assumption checks, data-quality flags, recommended method

### Step 7 — Interpret results

After running, provide:
1. Plain-language interpretation of the causal effect estimate
2. Effect size and practical significance
3. Key caveats and assumption violations to flag in the paper
4. Suggested robustness checks

## Defaults

- Robust standard errors: **HC3** for OLS-based methods.
- Staggered DID: use `did::att_gt` (Callaway & Sant'Anna), not TWFE.
- PSM: nearest-neighbor, **caliper = 0.1** SD of logit propensity score, 1:1 ratio.
- PSW: ATE (IPW) weights by default, offer ATT as alternative. **Trim at 1st/99th percentile** of weights.
- Report results on the original scale — never silently rescale.
- Flag low-power warning if N < 100 per group.

## Method-specific gotchas

These are easy-to-miss issues Claude must remember when editing or extending the templates.

### IV (`causal_iv.R`, uses `fixest`)

- **Singleton removal**: `feols()` silently drops singleton FE observations. Dropped row positions are stored as **negative integers** in `mod$obs_selection$obsRemoved`. When attaching residuals back to data (Hausman-Wu, Hansen J, post-estimation residual regressions), always recover alignment:
  ```r
  removed  <- abs(mod$obs_selection$obsRemoved)
  df_used  <- df[setdiff(seq_len(nrow(df)), removed), ]
  ```
- **Cragg-Donald** requires homoskedastic errors. `fixest` won't compute it under clustered SE. Refit once without clustering just to extract it:
  ```r
  mod_nc <- update(mod, . ~ ., cluster = NULL, data = df_used)
  cd_f   <- as.numeric(fitstat(mod_nc, "cd")$cd)
  ```
  Report Cragg-Donald alongside Kleibergen-Paap (clustered) and footnote the difference.
- **F-statistic** extraction: `fitstat(mod, "f")$f` is a named numeric vector, not a list. Use `as.numeric(...)[1]`.
- **`add_rows` position**: `modelsummary` with `coef_map`+`gof_map` produces `2 × n_coef` coefficient rows plus 1 row per gof entry. Append footer rows after the last gof row: `attr(add_rows_df, "position") <- (last_row + 1):(last_row + n_footer)`.
- **Instrumented coefficient name**: appears as `fit_{varname}` in fixest output. Key your `coef_map` with that prefix (e.g. `"fit_log_x" = "X"`).
- **IV moderation**: if a moderator interacts with the endogenous variable (e.g. `Moderator × X`), pre-compute `df$MX <- df$Moderator * df$X` and put `MX` in the **exogenous** side of the formula. Do **not** instrument the interaction separately. Footnote: "The interaction term is treated as exogenous conditional on the instruments for X."

### DID (`causal_did.R`, uses `fixest`, `did`)

- **Single-timing TWFE** is fine: `feols(y ~ treat_post | unit + time, data = df, cluster = ~unit)`.
- **Staggered treatment** (units treated at different times): TWFE is biased. Use Callaway-Sant'Anna:
  ```r
  att <- did::att_gt(yname = "y", tname = "time", idname = "unit_id",
                     gname = "first_treat",
                     data = df, control_group = "nevertreated")
  did::aggte(att, type = "dynamic")
  ```
- **Parallel trends** check: plot raw outcome means by group pre-treatment; pre-treatment event-study coefficients should be statistically indistinguishable from zero. Reference period = `-1`.
- Robustness columns to report: baseline, placebo timing, placebo outcome, exclude boundary periods.

### PSM (`causal_psm.R`, uses `MatchIt`, `cobalt`)

- Default: `method = "nearest"`, `distance = "logit"`, `caliper = 0.1`, `ratio = 1`.
- Success criterion: SMD < 0.1 on all covariates after matching (check `love.plot(m_out, threshold = 0.1)`).
- Outcome model on matched data must weight by `m_data$weights` and cluster SE by `subclass` (matched pair).

### PSW (`causal_psw.R`, uses `WeightIt`, `estimatr`)

- Default `estimand = "ATE"`; offer `"ATT"` when the user cares specifically about effect on the treated.
- Trim weights to the 1st/99th percentile before fitting the outcome model.
- Use `estimatr::lm_robust(..., weights = w_trimmed, clusters = unit_id, se_type = "CR2")` for standard errors.

### RDD (`causal_rdd.R`, uses `rddensity`, `rdrobust`)

- **Manipulation test first**: `rddensity(df$running, c = cutoff)` — require p > 0.05.
- Defaults: `kernel = "triangular"`, `bwselect = "mserd"`. Always report both conventional and bias-corrected robust estimates.
- Required robustness: placebo cutoffs at ±0.5 SD, bandwidth sensitivity at 0.5×/1×/1.5× optimal, covariate balance at cutoff, donut RDD excluding observations near the threshold.
- **Sharp vs fuzzy**: use `rdrobust(..., fuzzy = df$actual_treatment)` if treatment probability jumps but does not go to 1 at the cutoff.
- `rdrobust` objects are not supported by `modelsummary`. Extract `$coef`, `$se`, `$pv`, `$ci`, `$N_h`, `$bws` manually and build a `flextable` using the same three-line style the other methods use.
