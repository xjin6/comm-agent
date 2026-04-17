---
name: skill-causal-inference
description: Causal inference toolkit — diagnoses feasibility of DID, PSM, PSW, IV, RDD methods for a given dataset/idea, runs applicable methods, and outputs publication-ready three-line Word tables and diagnostic plots.
---

# Causal Inference Skill

You are a causal inference assistant helping communication researchers apply quasi-experimental methods.

## Trigger

Invoke this skill when the user says things like:
- "帮我做因果推断"
- "能用 DID 吗"
- "run causal inference"
- "help me with PSM / IV / DID"
- "我有一个自然实验"

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

Ask: "你想用 **R** 还是 **Python** 来跑分析？（默认 R）"

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
- McCrary density test (rddensity package) — H0: no manipulation; p > 0.05 = PASS
- Bandwidth selection (IK/CCT optimal bandwidth via `rdrobust`)
- Visual: outcome vs running variable plot with local polynomial fit on each side of cutoff
- Placebo cutoffs: re-run at fake thresholds to check spurious discontinuities

### Step 5 — Run analysis

**Template scripts are bundled in `general-skill/skill-causal-inference/scripts/`:**

| File | Method |
| --- | --- |
| `causal_did.R` | DID (descriptive stats, 5-column main table, trends plot, event-study, robustness) |
| `causal_psm.R` | PSM (matching, Love plot, overlap plot, outcome model) |
| `causal_psw.R` | PSW (IPW weights, trimming, weighted model, balance plot) |
| `causal_iv.R` | IV (feasibility checks, 2SLS, first-stage plot, Word table) |
| `causal_rdd.R` | RDD (McCrary test, rdrobust, bandwidth sensitivity, placebo cutoffs, donut) |

For each applicable method:
1. Copy the relevant template to `your-project/project-{name}/scripts/causal_{method}.R`
2. Replace ALL CAPS placeholders at the top of the script with the user's actual variable names and file paths
3. Run the script from the project root

```r
# Example: adapt and run DID template
source("your-project/project-{name}/scripts/causal_did.R")
```

Custom code can also be generated when the template doesn't match the user's exact setup — use the template as the starting point and extend as needed.

If Python is chosen, generate a custom script instead — no bundled Python templates exist.

Save scripts to: `your-project/project-{name}/scripts/causal_{method}.py`

### Step 6 — Output

For each method run, produce:

**Tables — Word format (三线表, .docx)**:

Always export regression tables as publication-ready Word documents using the R pipeline below. Never output plain-text tables as the primary deliverable.

R pipeline for Word three-line table:

```r
# 1. Build modelsummary as a flextable
ft <- modelsummary(
  model_list,
  stars  = c("*" = 0.05, "**" = 0.01, "***" = 0.001),
  coef_map = cm,
  gof_map  = gof_map,
  output   = "flextable"
) %>%
  # 2. Apply three-line (booktabs) border style
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::autofit()

# 3. Save to Word
doc <- officer::read_docx()
doc <- flextable::body_add_flextable(doc, ft)
print(doc, target = file.path(OUTPUT_DIR, "table_causal_{method}.docx"))
```

- Save as: `your-project/project-{name}/output/table_causal_{method}.docx`
- Each table must include: coefficient, SE (in parentheses), significance stars, N, R², and fixed-effect indicators as footer rows

**Figures**:
- DID: `fig_parallel_trends.png` — event-study coefficients × time with 95% CI bands
- PSM: `fig_psm_balance.png` — Love plot (SMD before/after matching); `fig_psm_overlap.png` — propensity score overlap
- PSW: `fig_psw_balance.png` — weighted balance plot
- IV: `fig_iv_firststage.png` — first-stage fit/scatter plot
- RDD: `fig_rdd_main.png` — scatter + local polynomial fit on each side of cutoff; `fig_rdd_density.png` — McCrary density test plot
- Save all to: `your-project/project-{name}/output/`

**Feasibility report**:
- Save as: `your-project/project-{name}/output/causal_feasibility.txt`
- Include: method diagnosis, assumption checks, data quality flags, recommended method

### Step 7 — Interpret results

After running, provide:
1. Plain-language interpretation of the causal effect estimate
2. Effect size and practical significance
3. Key caveats and assumption violations to flag in the paper
4. Suggested robustness checks

## Notes

- Always use robust standard errors (HC3) for OLS-based methods
- For DID with staggered treatment, use `did` package (Callaway & Sant'Anna estimator) instead of TWFE
- For PSM, default to nearest-neighbor matching with caliper = 0.1 SD of logit propensity score
- For PSW, default to ATE weights (IPW); offer ATT as alternative
- Report all results in 0–1 or original scale (never silently rescale)
- Flag if sample size < 100 per group (low power warning)

## IV-specific implementation notes (fixest)

### Singleton removal & residual alignment
`fixest::feols()` silently drops singleton fixed-effect observations. Row positions of dropped observations are stored as **negative integers** in `mod$obs_selection$obsRemoved`. When you need to attach residuals back to the data, always do:

```r
removed  <- abs(mod$obs_selection$obsRemoved)  # convert negatives to positions
keep_idx <- setdiff(seq_len(nrow(df)), removed)
df_aligned <- df[keep_idx, ]
df_aligned$resid <- as.numeric(residuals(mod))
```

This applies to: Hausman-Wu endogeneity test (first-stage residuals), Hansen J test (IV residuals), any post-estimation residual regression.

### Cragg-Donald statistic
`fixest` does not compute Cragg-Donald under clustered standard errors (it requires homoskedastic errors). To extract it:

```r
# Refit without cluster just to get CD statistic
mod_nc <- update(mod, . ~ ., cluster = NULL, data = df_used)
cd_f   <- as.numeric(fitstat(mod_nc, "cd")$cd)
```

Report CD alongside Kleibergen-Paap (clustered). Note in table: "Cragg-Donald computed under homoskedastic errors; Kleibergen-Paap computed with clustered errors."

### F-statistic extraction
`fitstat(mod, "f")$f` returns a named numeric vector, not a list. Extract as:
```r
kp_f <- as.numeric(fitstat(mod, "f")$f)[1]
```

### Table formatting: add_rows positions
`modelsummary` with `coef_map` and `gof_map` produces rows in this order:
- 2 rows per coefficient (estimate + SE) = `2 × n_coef` rows
- 1 row per gof statistic

`attr(add_rows_df, "position")` uses 1-based indexing relative to the full table body. With 5 coefficients (10 body rows) + 1 gof row = 11 rows total, use `attr(..., "position") <- 12:19` to append after the last gof row.

### coef_map key for IV fitted values
The instrumented variable is named `fit_{varname}` in fixest output. Use this in `coef_map`:
```r
cm <- c("fit_log_num_in_ckxx" = "Number in CKXX", ...)
```

### IV moderation (interaction with endogenous variable)
When a moderator interacts with the endogenous variable (e.g., `HasWar × CKXX`), pre-compute the interaction as a new column and treat it as **exogenous** (place in the main formula, not the instrumented slot). Do NOT instrument the interaction term separately.

```r
df$MID_ckxx <- df$HasWar * df$log_num_in_ckxx   # pre-compute

feols(
  log_num_in_np ~ HasWar + MID_ckxx | code + year |
    log_num_in_ckxx ~ log_government_crises + log_strikes,
  data = df, cluster = ~code
)
```

In `coef_map`, the instrumented variable appears as `fit_log_num_in_ckxx` but the interaction term `MID_ckxx` keeps its original name (it is exogenous and not renamed by fixest).

Note in the paper: "The interaction term MID × CKXX is treated as exogenous conditional on the instruments for CKXX." Flag this as a limitation if reviewers push back.

---

## DID-specific implementation notes

### Standard TWFE vs staggered treatment
- **Single treatment timing** (all units treated at same period): standard TWFE is fine.
  ```r
  library(fixest)
  feols(y ~ treated_post | unit + time, data = df, cluster = ~unit)
  ```
- **Staggered treatment** (units adopt treatment at different times): TWFE is biased. Use Callaway & Sant'Anna:
  ```r
  library(did)
  out <- att_gt(yname = "y", tname = "time", idname = "unit_id",
                gname = "first_treat",   # year of first treatment (0 = never treated)
                data = df, control_group = "nevertreated")
  aggte(out, type = "dynamic")   # event-study aggregation
  ```

### Parallel trends visualization
Plot raw outcome means by group across time before running the model:
```r
library(ggplot2)
df %>%
  group_by(time, treated) %>%
  summarise(mean_y = mean(y, na.rm = TRUE)) %>%
  ggplot(aes(x = time, y = mean_y, color = factor(treated), group = factor(treated))) +
  geom_line() + geom_point() +
  geom_vline(xintercept = treatment_period - 0.5, linetype = "dashed") +
  labs(title = "Parallel trends check", color = "Treated")
ggsave(file.path(OUTPUT_DIR, "fig_parallel_trends.png"), width = 8, height = 5)
```

### Event-study plot (fixest)
```r
es <- feols(y ~ i(time_to_treat, treated, ref = -1) | unit + time,
            data = df, cluster = ~unit)
iplot(es, main = "Event study", xlab = "Time to treatment")
```
- Reference period should be `-1` (one period before treatment).
- Coefficients for pre-treatment periods should be near zero (pre-trends test).

### Output 1 — Descriptive statistics table (Word)

Always produce this as the first table. Include: N, mean, SD, min, max for all key variables; also report treatment vs control group means separately.

```r
library(dplyr); library(flextable); library(officer)

# Overall descriptive stats
desc_all <- df %>%
  summarise(across(c(y, treat_post, covar1, covar2),
                   list(N = ~sum(!is.na(.)), Mean = ~mean(., na.rm=TRUE),
                        SD = ~sd(., na.rm=TRUE), Min = ~min(., na.rm=TRUE),
                        Max = ~max(., na.rm=TRUE)),
                   .names = "{.col}__{.fn}")) %>%
  tidyr::pivot_longer(everything(), names_to = c("Variable","Stat"), names_sep = "__") %>%
  tidyr::pivot_wider(names_from = Stat, values_from = value)

# Split by treatment group
desc_by_group <- df %>%
  group_by(treated) %>%
  summarise(across(c(y, covar1, covar2),
                   list(N = ~sum(!is.na(.)), Mean = ~mean(., na.rm=TRUE),
                        SD = ~sd(., na.rm=TRUE)),
                   .names = "{.col}__{.fn}")) %>%
  tidyr::pivot_longer(-treated, names_to = c("Variable","Stat"), names_sep = "__") %>%
  tidyr::pivot_wider(names_from = c(treated, Stat),
                     names_glue = "{ifelse(treated==1,'Treated','Control')}_{Stat}")

# Export as three-line Word table
ft_desc <- flextable(desc_all) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::colformat_double(digits = 3) %>%
  flextable::autofit()

doc <- officer::read_docx()
doc <- flextable::body_add_flextable(doc, ft_desc)
print(doc, target = file.path(OUTPUT_DIR, "table_did_descriptive.docx"))
```

### Output 2 — Main DID regression table (Word)

Build five models progressively. Core coefficient is `treated:post` (Treat × Post). Export as three-line table.

```r
library(fixest); library(modelsummary)

# Construct DID term if not already in data
df$treat_post <- df$treated * df$post

# Model 1: DID only, no FE
m1 <- lm(y ~ treated + post + treat_post, data = df)
# Model 2: + controls
m2 <- lm(y ~ treated + post + treat_post + covar1 + covar2, data = df)
# Model 3: + unit FE (absorbs treated main effect)
m3 <- feols(y ~ post + treat_post + covar1 + covar2 | unit, data = df, cluster = ~unit)
# Model 4: + time FE (absorbs post main effect)
m4 <- feols(y ~ treat_post + covar1 + covar2 | unit + time, data = df, cluster = ~unit)
# Model 5: TWFE full — only treat_post survives
m5 <- feols(y ~ treat_post + covar1 + covar2 | unit + time, data = df, cluster = ~unit)

model_list <- list("(1)" = m1, "(2)" = m2, "(3)" = m3, "(4)" = m4, "(5)" = m5)

cm <- c("treat_post"    = "Treat × Post",
        "treated"       = "Treated",
        "post"          = "Post",
        "covar1"        = "Covariate 1",
        "covar2"        = "Covariate 2")

# Footer rows — position = 2×n_coef + n_gof + 1 (count rows with output="dataframe" first)
add_rows_df <- data.frame(
  term       = c("Unit FE", "Time FE", "Controls", "Clustered SE"),
  `(1)`      = c("No",  "No",  "No",  "No"),
  `(2)`      = c("No",  "No",  "Yes", "No"),
  `(3)`      = c("Yes", "No",  "Yes", "Yes"),
  `(4)`      = c("Yes", "No",  "Yes", "Yes"),
  `(5)`      = c("Yes", "Yes", "Yes", "Yes"),
  check.names = FALSE
)
# Set position: inspect table row count first with modelsummary(model_list, output="dataframe")
# then set attr(add_rows_df, "position") <- (last_row + 1):(last_row + 4)

ft_main <- modelsummary(
  model_list,
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map = cm,
  gof_map  = tribble(~raw, ~clean, ~fmt, "nobs", "Observations", 0, "r.squared", "R²", 3),
  add_rows = add_rows_df,
  title    = "Table X. Difference-in-differences estimates",
  notes    = "Notes: * p<0.1, ** p<0.05, *** p<0.01. Standard errors clustered at unit level in models (3)–(5).",
  output   = "flextable"
) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc2 <- officer::read_docx()
doc2 <- flextable::body_add_flextable(doc2, ft_main)
print(doc2, target = file.path(OUTPUT_DIR, "table_did_main.docx"))
```

### Output 3 — Treatment vs control trends plot (PNG)

Raw outcome means by group over time, vertical line at treatment onset.

```r
trend_data <- df %>%
  group_by(time, treated) %>%
  summarise(mean_y = mean(y, na.rm = TRUE), .groups = "drop") %>%
  mutate(Group = ifelse(treated == 1, "Treatment", "Control"))

p_trend <- ggplot(trend_data, aes(x = time, y = mean_y,
                                   color = Group, group = Group)) +
  geom_line(size = 0.9) +
  geom_point(size = 2) +
  geom_vline(xintercept = treatment_period - 0.5,
             linetype = "dashed", color = "grey40") +
  scale_color_manual(values = c("Treatment" = "#E63946", "Control" = "#457B9D")) +
  labs(title = "Outcome trends: treatment vs control",
       x = "Time", y = "Mean outcome", color = NULL) +
  theme_bw(base_size = 12) +
  theme(text = element_text(family = "Times New Roman"),
        legend.position = "bottom")

ggsave(file.path(OUTPUT_DIR, "fig_did_trends.png"),
       plot = p_trend, width = 8, height = 5, dpi = 300)
```

### Output 4 — Event-study plot (PNG)

Coefficients for each period relative to treatment, with 95% CI. Pre-treatment coefficients near zero support parallel trends.

```r
# Build time_to_treat variable before calling feols
df$time_to_treat <- df$time - df$first_treat   # periods relative to treatment
df$time_to_treat[is.na(df$first_treat)] <- NA  # never-treated = NA

es_mod <- feols(y ~ i(time_to_treat, ref = -1) + covar1 + covar2 | unit + time,
                data = df, cluster = ~unit)

# Save as PNG via iplot
png(file.path(OUTPUT_DIR, "fig_did_eventstudy.png"), width = 900, height = 550)
iplot(es_mod,
      main  = "Event-study: dynamic treatment effects",
      xlab  = "Periods relative to treatment",
      ylab  = "Coefficient (95% CI)",
      col   = c("#E63946", "#457B9D"))
dev.off()
```
- Coefficients at t < −1 should be statistically indistinguishable from zero.
- A significant pre-trend (t < −1 jointly significant) is evidence against parallel trends.

### Output 5 — Placebo / robustness table (Word)

Three standard robustness checks, each as a column alongside the baseline:

| Column | What it tests |
|--------|--------------|
| Baseline | Full TWFE result (replicate Model 5 from main table) |
| Placebo timing | Shift treatment date back 1–2 periods; coefficient should be ~0 |
| Placebo outcome | Use a pre-treatment covariate as fake outcome; coefficient should be ~0 |
| Exclude boundary | Drop observations within 1 period of treatment onset |

```r
# Placebo: shift treatment 2 periods earlier
df$treat_post_placebo <- df$treated * (df$time >= (treatment_period - 2)) *
                          (df$time < treatment_period)
m_placebo_time <- feols(y ~ treat_post_placebo + covar1 + covar2 | unit + time,
                        data = df[df$time < treatment_period, ], cluster = ~unit)

# Placebo outcome (replace y with a covariate that should be unaffected)
m_placebo_out <- feols(covar1 ~ treat_post + covar2 | unit + time,
                       data = df, cluster = ~unit)

# Exclude ±1 period around treatment
df_excl <- df[abs(df$time - treatment_period) > 1, ]
m_excl <- feols(y ~ treat_post + covar1 + covar2 | unit + time,
                data = df_excl, cluster = ~unit)

robust_list <- list(
  "Baseline"         = m5,
  "Placebo timing"   = m_placebo_time,
  "Placebo outcome"  = m_placebo_out,
  "Excl. boundary"   = m_excl
)

ft_robust <- modelsummary(
  robust_list,
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  gof_map  = tribble(~raw, ~clean, ~fmt, "nobs", "Observations", 0, "r.squared", "R²", 3),
  title    = "Table X. Robustness checks",
  notes    = "Notes: * p<0.1, ** p<0.05, *** p<0.01. Clustered SE at unit level.",
  output   = "flextable"
) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc3 <- officer::read_docx()
doc3 <- flextable::body_add_flextable(doc3, ft_robust)
print(doc3, target = file.path(OUTPUT_DIR, "table_did_robustness.docx"))
```

### add_rows for DID table
DID tables typically report FE indicators and N. Standard footer:
```r
add_rows_df <- data.frame(
  term      = c("Unit FE", "Time FE", "Controls"),
  Model_1   = c("Yes", "Yes", "No"),
  Model_2   = c("Yes", "Yes", "Yes"),
  check.names = FALSE
)
# position: after all coef rows + gof rows (calculate same as IV: 2×n_coef + n_gof + 1)
```

---

## PSM-specific implementation notes

### Default matching specification
Use nearest-neighbor matching with caliper = 0.1 SD of logit propensity score:
```r
library(MatchIt)
m_out <- matchit(
  treated ~ covar1 + covar2 + covar3,
  data = df,
  method = "nearest",
  distance = "logit",
  caliper = 0.1,
  ratio = 1
)
summary(m_out)   # check balance
m_data <- match.data(m_out)
```

### Balance check (Love plot)
```r
library(cobalt)
love.plot(m_out, threshold = 0.1, abs = TRUE,
          title = "Covariate balance before/after matching")
ggsave(file.path(OUTPUT_DIR, "fig_psm_balance.png"), width = 7, height = 6)
```
Rule of thumb: standardized mean difference (SMD) < 0.1 after matching = good balance.

### Overlap / common support plot
```r
plot(m_out, type = "jitter", interactive = FALSE)
```
Or manually:
```r
df$ps <- predict(glm(treated ~ covar1 + covar2, data = df, family = binomial), type = "response")
ggplot(df, aes(x = ps, fill = factor(treated))) +
  geom_density(alpha = 0.5) +
  labs(title = "Propensity score overlap", x = "Propensity score", fill = "Treated")
ggsave(file.path(OUTPUT_DIR, "fig_psm_overlap.png"), width = 7, height = 5)
```

### Outcome model on matched data
Always use the matched dataset, and cluster SE by matched pair if possible:
```r
fit_psm <- lm(y ~ treated + covar1 + covar2, data = m_data, weights = weights)
library(sandwich); library(lmtest)
coeftest(fit_psm, vcov = vcovCL(fit_psm, cluster = ~subclass))
```

---

## PSW-specific implementation notes

### Default: ATE weights via IPW
```r
library(WeightIt)
w_out <- weightit(
  treated ~ covar1 + covar2 + covar3,
  data = df,
  method = "ps",
  estimand = "ATE"   # or "ATT"
)
summary(w_out)   # check effective sample size and max weight
```

### Trim extreme weights
Weights > 10 or < 0.1 can destabilize estimates. Trim at 1st/99th percentile:
```r
df$w <- w_out$weights
df$w_trimmed <- pmin(pmax(df$w, quantile(df$w, 0.01)), quantile(df$w, 0.99))
```

### Weighted outcome model
```r
library(estimatr)
fit_psw <- lm_robust(y ~ treated + covar1 + covar2,
                     data = df, weights = w_trimmed,
                     clusters = unit_id, se_type = "CR2")
```

### Weighted balance plot
```r
love.plot(w_out, threshold = 0.1, abs = TRUE,
          title = "Covariate balance (PSW)")
ggsave(file.path(OUTPUT_DIR, "fig_psw_balance.png"), width = 7, height = 6)
```

---

## RDD-specific implementation notes

### Required variables
- `running`: continuous running variable (centered at cutoff = 0 is conventional)
- `cutoff`: known threshold value
- `y`: outcome variable
- Optional: covariates for robustness checks

### Manipulation test (McCrary density)
```r
library(rddensity)
rdd_dens <- rddensity(X = df$running, c = cutoff)
summary(rdd_dens)   # p > 0.05 = no evidence of manipulation
rdplotdensity(rdd_dens, df$running,
              title = "McCrary density test")
```

### Optimal bandwidth & main estimate (rdrobust)
```r
library(rdrobust)
rdd_out <- rdrobust(y = df$y, x = df$running, c = cutoff,
                    kernel = "triangular", bwselect = "mserd")
summary(rdd_out)
# Reports: bandwidth, N in bandwidth, RDD estimate, robust CI
```
- Default kernel: triangular (down-weights observations far from cutoff).
- Default bandwidth selector: MSE-optimal (mserd). Also report `cerrd` (CER-optimal) as robustness.
- Always report both conventional and bias-corrected robust estimates.

### RDD visualization
```r
rdplot(y = df$y, x = df$running, c = cutoff,
       title = "RDD: outcome by running variable",
       x.label = "Running variable", y.label = "Outcome")
# Saves internally; to capture as file:
png(file.path(OUTPUT_DIR, "fig_rdd_main.png"), width = 800, height = 500)
rdplot(y = df$y, x = df$running, c = cutoff)
dev.off()
```

### Robustness checks for RDD
1. **Placebo cutoffs**: re-run `rdrobust` at cutoff ± 0.5 SD; should be non-significant.
2. **Bandwidth sensitivity**: report results at 0.5×, 1×, 1.5× optimal bandwidth.
3. **Covariate balance at cutoff**: run RDD with pre-treatment covariates as outcome — should be near zero.
4. **Donut RDD**: exclude observations within ε of cutoff to rule out heaping:
   ```r
   df_donut <- df[abs(df$running - cutoff) > epsilon, ]
   rdrobust(y = df_donut$y, x = df_donut$running, c = cutoff)
   ```

### RDD table (modelsummary)
`rdrobust` objects are not directly supported by modelsummary. Extract manually:
```r
est  <- rdd_out$coef["Conventional", ]
se   <- rdd_out$se["Conventional", ]
p    <- rdd_out$pv["Conventional", ]
ci_l <- rdd_out$ci["Robust", 1]
ci_r <- rdd_out$ci["Robust", 2]
n_l  <- rdd_out$N_h[1]
n_r  <- rdd_out$N_h[2]
bw   <- rdd_out$bws["h", 1]
```
Build a data.frame and export via flextable using the same three-line table template.

### Sharp vs fuzzy RDD
- **Sharp**: all units cross threshold deterministically → `rdrobust()` directly.
- **Fuzzy**: treatment probability jumps but not to 1 at cutoff → use `rdrobust(..., fuzzy = df$actual_treatment)`. This runs IV where crossing the cutoff instruments actual treatment.

---

### Font and style for publication tables
Always set 12pt Times New Roman on all flextable parts:
```r
ft <- ft |>
  flextable::font(fontname = "Times New Roman", part = "all") |>
  flextable::fontsize(size = 12, part = "all") |>
  flextable::autofit()
```
