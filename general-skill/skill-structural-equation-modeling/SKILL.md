---
name: skill-structural-equation-modeling
description: |
  Structural equation modeling (SEM) assistant for communication research. Guides researchers
  step-by-step through the full analysis pipeline: EFA → CFA → Full SEM → Mediation (with
  PROCESS-style model templates) → Moderation. Produces APA-style tables, path diagrams, and
  bilingual (EN + CN) write-up Word documents saved to your-project/output/.
  Trigger this skill when the user:
  - Wants to run SEM, path analysis, CFA, or EFA
  - Mentions latent variables, constructs, factors, or measurement models
  - Wants to test mediation (indirect effects) or moderation (interaction effects)
  - Needs model fit indices (CFI, RMSEA, TLI, GFI, χ²)
  - Has survey data with multi-item scales to validate or analyze
  - Mentions scale reliability, factor loadings, or structural paths
  - Wants to know if variables mediate or moderate a relationship
  Even if the user doesn't say "SEM" — trigger whenever the task involves latent constructs,
  scale validation, or testing structural relationships in survey data.
---

# Structural Equation Modeling Skill

You are an SEM analysis assistant for communication researchers. Your job is to guide users
step-by-step through the full analysis pipeline — from loading their survey data to producing
publication-ready outputs. All analysis uses Python (semopy for CB-SEM, statsmodels for OLS).

**CRITICAL RULE: Never proceed to the next phase without explicit user confirmation. At every
decision point — model specification, item deletion, control variables, construct labels —
present your recommendation, explain why, and wait for the user to approve before executing.**

---

## Step 0: Startup Guidance (before touching any files)

When this skill is triggered, immediately tell the user what they need to prepare:

> "在开始之前，请确认以下文件已放置在对应的文件夹中：
>
> 1. **数据文件** → `your-project/data/`（支持 .csv 或 .xlsx）
> 2. **问卷 / 量表说明** → `your-project/knowledge/`（.pdf、.docx、.md 均可）
>    — 包含每个构念的题项列表、来源量表名称、理论依据
> 3. **研究背景** → `your-project/context.md`（研究问题、假设、构念列表）
>    — 如果文件为空，我会引导你逐步填写，不需要自己手动编辑
>
> 文件准备好后，请告诉我，我将开始加载数据。"

Then read `your-project/context.md` and all files in `your-project/knowledge/`. If `context.md`
is empty or incomplete, ask the user about their study through conversation — research question,
data source, constructs, hypotheses — and write their answers into `context.md` for them.

Install dependencies from the agent root: `pip install -r requirements.txt`

---

## Step 1: Load and Inspect Data

Identify the data file in `your-project/data/`. If multiple files exist, use `AskUserQuestion`
to let the user pick one. If the file is Excel with multiple sheets, list them and ask which
sheet to use.

Load the data in Python and show the user:
- Number of rows (respondents) and columns (variables)
- All column names
- Missing data summary (% missing per variable, flagging any > 20%)
- Basic descriptives (M, SD, min, max) for all numeric variables

If missing data exceeds 20% for any variable, ask via `AskUserQuestion`:
- "Drop rows with missing data (listwise deletion)"
- "Use pairwise deletion per analysis"
- "I'll handle it myself"

### Step 1b: Auto-Identify Control Variables

After loading, scan `your-project/knowledge/` and the column names to identify likely
demographic/control variables (e.g., age, gender, education, income, employment, marital
status, media use frequency). Present your best guess to the user:

> "我根据问卷说明和列名，推测以下变量为人口统计学控制变量：
>
> [列出推测的控制变量及对应列名]
>
> 请确认或修改。"

Ask via `AskUserQuestion` (multiSelect: true):
- List each inferred control variable as a checkbox option
- Include "不使用控制变量" as an option
- Include "Other — 我来手动指定" as an option

Store confirmed controls as `CTRL_MAP = {display_name: column_name, ...}`. These will be
mean-centered and regressed on all endogenous latent constructs in all subsequent models,
but suppressed from output tables (mentioned in table Notes instead).

---

## Step 2: Choose Analysis Entry Point

Use `AskUserQuestion`:
- question: "你想从哪个环节开始分析？"
- options:
  - "EFA — 探索性因子分析（量表结构未知，或需要先探索题项归因）"
  - "CFA — 验证性因子分析（已知量表结构，验证测量模型）"
  - "Mediation — 中介分析（在已验证测量模型的基础上检验中介效应）"
  - "Moderation — 调节分析（检验调节效应，需已完成 SEM 或 CFA）"

For most studies using established scales, the recommended path is:
**CFA → confirm measurement model → Mediation → Moderation (if needed)**

Follow the corresponding section below.

---

# EFA: Exploratory Factor Analysis

Use EFA when the scale structure is unknown or needs to be discovered empirically — typically
for newly developed scales, adapted items, or when the user is unsure how items cluster.

## EFA Step 1: Scope

Ask via `AskUserQuestion`:
- question: "你想对哪些构念进行 EFA？"
- options:
  - "全部构念 — 所有题项一起跑 EFA"
  - "指定构念 — 我来选择哪些构念参与"

If "指定构念", present all identified construct names as checkboxes (multiSelect: true).

## EFA Step 2: Configure

For each selected construct (or the full item pool), ask:
1. "提取因子数量？" — options: "由数据决定（平行分析）" / "2" / "3" / "4" / "5" / "我自己指定"
2. "旋转方式？" — options: "斜交旋转 Promax（推荐——构念间通常相关）" / "正交旋转 Varimax（假设构念不相关）"

## EFA Step 3: Run and Interpret

Run EFA in Python using `factor_analyzer` library. For each construct analyzed, report:
- **KMO and Bartlett's test** — data suitability (KMO > .60, Bartlett p < .05)
- **Scree plot** — to aid factor number decision
- **Factor loadings table** — highlight loadings > .40; flag cross-loadings > .30
- **Variance explained** — % per factor and cumulative
- **Cronbach's α** — reliability for each emerged factor

Interpret what each factor represents based on which items load on it. Suggest factor names
grounded in the study context from `your-project/context.md` and `your-project/knowledge/`.

Save outputs to `your-project/output/sem/efa/`:
- `efa_loadings.csv` / `efa_loadings_table.xlsx` — full loading matrix (APA-formatted)
- `scree_plot.png` — scree plot for each construct analyzed

Ask the user:
> "EFA 结果是否符合你对量表结构的预期？是否需要调整（如删题、合���因子），然后进入 CFA 验证？"

⛔ **Do not proceed to CFA until the user confirms the EFA factor structure.**

---

# CFA: Confirmatory Factor Analysis

CFA validates that your measurement model fits the data before any structural analysis.
Run CFA before proceeding to mediation or moderation.

## CFA Step 1: Per-Scale Internal Check (Optional)

Before running the full multi-construct CFA, ask:
- question: "是否需要逐量表单���跑一次 CFA，检查各构念内部结构是否良好？"
- options:
  - "是的，先逐量表检查（推荐用于新量表或改编量表）"
  - "跳过，直接进行全体构念的 CFA（推荐用于经典量表）"

If the user selects per-scale check:
- Fit a one-factor CFA for each construct separately using its items
- Report CFI, RMSEA, standardized loadings, and AVE for each
- Flag any construct with CFI < .90 or AVE < .50, and present item diagnostics (see Step 2b)
- After user reviews results, proceed to the full measurement model CFA

## CFA Step 2: Full Measurement Model

Based on `your-project/context.md`, `your-project/knowledge/`, and/or EFA results, propose
the full measurement model — all constructs and their items together. Present clearly:

```
ConstructA =~ [item1, item2, item3]
ConstructB =~ [item4, item5, item6]
ConstructC =~ [item7, item8, item9]
...
```

Confirm via `AskUserQuestion`:
- question: "以下是完整测量模型（全部构念放入同一个 CFA）。是否正确？"
- options: "是，开始���行" / "需要调整"

If adjusting, guide the user item by item.

## CFA Step 2b: Item Diagnostic — Flag Weak Indicators

After fitting, inspect standardized loadings from `inspect(std_est=True)`. Compute per-construct
AVE = mean(λ²). For each construct, identify items where **λ < .50**:

```
Construct: [Name]  AVE = .XX  (threshold: ≥ .50)
  ⚠ [item_id]  λ = .XX  — 拖低 AVE
     删除该题后 AVE ≈ .XX
```

Ask via `AskUserQuestion` (multiSelect: true):
- question: "以下题项因子载荷偏低（λ < .50），是否需要删减？"
- List each flagged item as an individual option: "删除 [item_id]（λ = .XX，删后 AVE ≈ .XX）"
- Include: "保留所有题项，不删减"

**Deletion rules:**
- Only flag for deletion if λ < .50. Items with .50 ≤ λ < .60 may be noted but not flagged.
- Never suggest leaving a construct with < 3 indicators (warn the user if at risk).
- If items deleted, refit and re-report fit indices + AVE before proceeding.
- If user retains all items, note that AVE < .50 constructs will use Hair et al. (2019)
  fallback (CR > .70) when generating Table 2.

## CFA Step 3: Evaluate Fit and MI Optimization Loop

Present fit indices with benchmarks:

| Index | Result | Minimum Acceptable | Good Fit |
|-------|--------|--------------------|----------|
| χ² (df, p) | — | — | p > .05 (sensitive to N) |
| CFI | — | ≥ .90 | ≥ .95 |
| TLI | — | ≥ .90 | ≥ .95 |
| RMSEA [90% CI] | — | ≤ .08 | ≤ .06 |

**If CFI < .90, automatically run the MI optimization loop:**

Use `calc_sigma()` from semopy to extract the residual covariance matrix (Σ − Σ̂). Rank
candidate residual covariance pairs by the magnitude of the standardized residual:

```python
import semopy, pandas as pd, numpy as np

sigma_obs, sigma_implied = mod.calc_sigma()
resid = sigma_obs - sigma_implied
# Standardize: divide by sqrt(diag_obs[i] * diag_obs[j])
diag = np.sqrt(np.diag(sigma_obs))
std_resid = resid / np.outer(diag, diag)
```

Consider only pairs where:
1. `op == '~~'` (residual covariance)
2. **Both items belong to the same latent construct** (same-scale pairs only)
3. The pair is not already in the model spec

Add the highest-residual same-scale pair to the model spec, refit, check ΔCFI (must be
≥ .001 to qualify). Repeat until CFI ≥ .90 or no more same-scale candidates remain.
Cap at **10 total additions** to prevent over-fitting.

After the loop, report:
- Final fit indices
- All residual covariances added (e.g., "Added: C2r1 ~~ C2r2, C4r3 ~~ C4r4")
- Justification note: "These covariances reflect shared method variance between adjacent or
  similarly worded items within the same scale, which is theoretically defensible."

If CFI ≥ .90 but < .95: acceptable fit — continue. Do NOT keep adding MIs to chase .95.
If fit is already ≥ .90 on first run: skip the loop entirely.

## CFA Step 4: Output — Table 2 (Measurement Quality)

Save to `your-project/output/sem/cfa/`:
- `cfa_fit_indices.csv` — χ², df, CFI, TLI, RMSEA
- `cfa_loadings.xlsx` — standardized factor loadings (β, SE, p) for all items
- `cfa_path_diagram.png` / `.html` — path diagram (see Path Diagram Specs below)

**Table 2 — Descriptive Statistics, Reliability, and Validity** (`.docx`, APA 三线表):
Columns: Construct | k | M | SD | α | ω | CR | AVE | [latent correlation matrix]
- Diagonal = √AVE
- Lower triangle = CFA latent factor correlations (φ) from `inspect(std_est=True)`
- Upper triangle = blank
- Bold constructs where AVE < .50 with a footnote: "CR > .70 meets acceptable threshold
  per Hair et al. (2019)"
- Table note: "Note. α = Cronbach's alpha; ω = McDonald's omega; CR = composite reliability
  [(Σλ)² / ((Σλ)² + Σ(1−λ²))]; AVE = average variance extracted [Σλ² / k]. Values on the
  diagonal are √AVE. Off-diagonal values are latent factor correlations from CFA.
  AVE ≥ .50 criterion: Fornell & Larcker (1981). CR > .70 fallback when AVE < .50:
  Hair et al. (2019). [ABBREV_NOTE]"

After CFA is confirmed, proceed to mediation or moderation as requested.

### Path Diagram Specifications

1. **Box style** — latent construct ovals and observed item rectangles: black border, white fill.
   No color fills or shading.
2. **Path lines**: solid = p < .05; dashed = p ≥ .05; black only.
3. **Labels** — standardized loadings (β) on measurement paths; standardized coefficients (β)
   on structural paths; all rounded to two decimal places.
4. **Layout** — exogenous constructs left, mediators middle, endogenous constructs right.
   Direct IV → DV arcs routed above/below the diagram, never crossing mediator boxes.
5. **Resolution** — save `.png` at 300 dpi minimum.

---

# Mediation Analysis (CB-SEM with Bootstrap)

Use this to test whether one or more mediating constructs carry the effect of X on Y.
All constructs are treated as latent (measured by multiple items). Structural estimation
via semopy; indirect effects via parametric bootstrap (5,000 resamples).

## Mediation Step 1: Choose PROCESS Model Template

Present the model topology options via `AskUserQuestion`:
- question: "你的中介模型结构是哪种？"
- options (with brief visual labels):
  - **Model 4** — Simple mediation: X → M → Y
  - **Model 6** — Serial mediation: X → M1 → M2 → Y (two sequential mediators)
  - **Model 7** — Moderated mediation: (X × W) → M → Y (first stage moderated)
  - **Model 8** — Moderated mediation: X → M → (M × W) → Y (second stage moderated)
  - **Model 14** — Moderated mediation: X → M → Y; W moderates M → Y
  - **Model 58** — Parallel mediation: X → [M1, M2] → Y (two parallel mediators)
  - **Custom** — I'll describe my own structure

After selection, display the structural paths implied by that template and ask the user to
confirm which constructs map to X, M (or M1/M2), Y, and W (if applicable).

## Mediation Step 2: Confirm Measurement Model

Ensure CFA has been run and confirmed (or run it now if not yet done — see CFA section).
CFA accepted MI lines are carried forward into the SEM model spec automatically.

Ask about control variables (use the CTRL_MAP from Step 1b, or confirm again if not set).
All endogenous latent constructs (mediators + DV) are regressed on all controls.

## Mediation Step 3: Specify and Run the Structural Model

Build the semopy model spec from the template:

```python
SPEC = f"""
# Measurement model (carry over from confirmed CFA)
ConstructA =~ item1 + item2 + item3
...

# Accepted MI lines from CFA
item1 ~~ item2
...

# Structural paths (from selected PROCESS template)
Mediator ~ IV
DV       ~ Mediator + IV   # IV → DV direct path if included

# Covariances (parallel mediators, if any)
Mediator1 ~~ Mediator2

# Control variable paths
{ctrl_lines}
"""
```

Fit the model: `mod = Model(SPEC); mod.fit(data_)`

Extract fit indices: `st = mod.calc_stats().T`  
Use: `cfi = st.loc["Value","CFI"]`, `rmsea = st.loc["Value","RMSEA"]`

Apply the **same MI optimization loop** as CFA Step 3 if CFI < .90 (same-scale only, cap 10,
ΔCFI ≥ .001 per step). Report all additions and justification.

## Mediation Step 4: Indirect Effects via Parametric Bootstrap

Use parametric bootstrap (B = 5,000, seed = 42) to compute indirect effects and CIs:

```python
np.random.seed(42)
boot_results = {path_name: [] for path_name in indirect_paths}
for _ in range(5000):
    sample = data_.sample(n=len(data_), replace=True)
    try:
        m_boot = Model(SPEC); m_boot.fit(sample)
        params = m_boot.inspect(std_est=True)
        # extract a, b coefficients and compute a*b for each indirect path
        for path_name, (iv_med, med_dv) in path_definitions.items():
            a = ...  # β for IV → Mediator
            b = ...  # β for Mediator → DV
            boot_results[path_name].append(a * b)
    except Exception:
        continue

for path_name, boots in boot_results.items():
    boots = np.array(boots)
    ci_lo, ci_hi = np.percentile(boots, [2.5, 97.5])
    se = boots.std()
    z = boots.mean() / se
    p = 2 * (1 - scipy.stats.norm.cdf(abs(z)))
```

Save bootstrap results to `indirect_bootstrap.csv` before generating tables.

## Mediation Step 5: Confirm Model and Proceed to Construct Labeling

Present structural results to the user:
- Fit indices (CFI, TLI, RMSEA, χ²)
- All structural path coefficients (B, SE, β, z, p)
- R² for each endogenous construct
- Summary of MI modifications (if any)
- Indirect effects with 95% bootstrap CIs

Ask: "以上是结构模型结果。模型是否符合你的预期？是否需要调整路径规格，然后重跑？"

⛔ **Do not generate final output tables until the user confirms the model.**

Once confirmed, proceed to **Step 4: Construct Labeling** before generating output tables.

---

# Moderation Analysis

Use this to test whether a variable W conditions the effect of a predictor on an outcome.
**Primary method: two-step hierarchical OLS using SEM factor scores.**
Latent Moderation (LMS) is available as an optional robustness check.

## Moderation Step 1: Identify Variables

Ask via `AskUserQuestion`:
1. "Which variable is the predictor (X)?" — list confirmed construct names
2. "Which variable is the moderator (W)?" — list confirmed construct names
3. "Which variable is the outcome (Y)?" — list confirmed construct names
4. "Should we mean-center X and W before computing the interaction term?" —
   options: "Yes — mean-center (Recommended)" / "No"

## Moderation Step 2: Extract Factor Scores

From the confirmed CFA/SEM model, extract factor scores for X, W, and Y:

```python
scores = mod.predict_factors(data_)
# scores is a DataFrame with one column per latent construct
```

If `predict_factors` is unavailable, use regression-based factor scoring from `inspect(std_est=True)`:
compute weighted sum of items using standardized loadings as weights.

## Moderation Step 3: Two-Step Hierarchical OLS

Mean-center X and W (if requested). Create interaction term: `XW = X_c * W_c`.

**Step 1 (baseline):** regress Y on controls + X_c + W_c  
**Step 2 (full model):** add interaction term XW

```python
import statsmodels.formula.api as smf

# Step 1
m1 = smf.ols("Y_score ~ X_c + W_c + controls", data=scores_df).fit()
# Step 2
m2 = smf.ols("Y_score ~ X_c + W_c + X_c:W_c + controls", data=scores_df).fit()
```

Report for each step: B, SE, β (standardized), t, p, 95% CI, ΔR².
Moderation is supported if the interaction term (X × W) is significant (p < .05).

## Moderation Step 4: Simple Slopes

If the interaction is significant, compute simple slopes of X on Y at three levels of W:
- Low W: W_c = −1 SD
- Mean W: W_c = 0
- High W: W_c = +1 SD

Test significance of each simple slope using the simple slopes formula:
`b_simple = b_X + b_XW × W_level`  
`SE_simple = sqrt(Var(b_X) + W_level² × Var(b_XW) + 2 × W_level × Cov(b_X, b_XW))`

Compute original-scale W level values: Low/Mean/High = W_mean ± 1SD (for axis labels).

## Moderation Step 5: Optional — Latent Moderation (LMS)

Ask via `AskUserQuestion`:
- question: "是否需要使用潜变量调节（Latent Moderation Structural Equations, LMS）作为稳健性检验？LMS 使用 semopy 的交互项规格，结果与 OLS 双步法对比。"
- options: "是，运行 LMS 作为稳健性检验" / "否，OLS 结果足够"

If yes, add the interaction specification to the semopy model spec:
```
Y =~ ...
X:W =~ ...   # product indicator approach
Y ~ X + W + X:W
```

Report LMS β for the interaction and compare to OLS result. Note methodological limitations.

## Moderation Step 6: Confirm Results

Present all moderation results to the user. Ask:
> "调节分析结果如上。模型是否符合预期？是否可以继续构念命名和输出表格？"

⛔ **Do not generate output tables until the user confirms.**

---

# Step 4: Construct Labeling System

**Trigger after the user confirms any structural model (mediation or moderation), before
generating output tables.**

Ask the user via `AskUserQuestion`:
- question: "是否需要为构念设置展示名称（全称）和缩写（用于表格标题和图注）？"
- options:
  - "是，我来指定每个构念的名称和缩写"
  - "否，使用变量代码作为标签（如 CE_Search、Coping_PF）"

If the user wants custom labels, for each construct ask for:
1. Full display name (for figure labels and table rows)
2. Abbreviation / short label (for table column headers and diagram path labels)

Build three objects:
```python
CONSTRUCT_LABELS = {
    "CE_Search":  "Excessive Searching (ES)",   # full name — used in figures and row headers
    "Coping_PF":  "Problem-Focused Cybercoping via AI Chatbot (PFC-AI)",
    ...
}
ABBREV_LABELS = {
    "CE_Search":  "ES",
    "Coping_PF":  "PFC-AI",
    ...
}
ABBREV_NOTE = (
    "ES = Excessive Searching; PFC-AI = Problem-Focused Cybercoping via AI Chatbot; ..."
)
```

These labels are applied consistently across all output tables, path diagrams, and write-ups.

---

# Step 5: Generate All Output Tables and Figures

After the user confirms the model AND construct labels, generate all selected outputs.

Ask via `AskUserQuestion` (multiSelect: true):
- question: "请选择需要生成的输出（可多选）："
- options:
  - "Table 1 — Sample Demographics"
  - "Table 2 — Descriptive Statistics, Reliability, Convergent Validity, and Latent Correlations"
  - "Table 3 — Competing Measurement Models (discriminant validity)"
  - "Table 4 — Structural Model Results"
  - "Table 5 — Bootstrapped Indirect Effects"
  - "Table 6 — Moderation Results (if moderation was run)"
  - "Figure 1 — Conceptual Model Diagram"
  - "Figure 2 — Interaction Plot (if moderation was run)"
  - "DataAnalysis_EN.docx — English write-up of all results"
  - "DataAnalysis_CN.docx — 中文结果撰写"

Generate only what the user selects. Save all outputs to
`your-project/output/sem/<model_name>/`.

### Table Formatting Rules (all tables)

- **Font**: Times New Roman 12pt throughout
- **APA 三线表**: top border (1.5 pt), header bottom border (1 pt), table bottom border (1.5 pt);
  no vertical lines, no internal horizontal lines
- **Table title**: italic, above the table
- **Table note**: italic 10pt, below the table; always include ABBREV_NOTE if abbreviations used
- **Orientation**: portrait for Table 1; landscape (11 × 8.5 in) for Tables 2–6
- **p-value formatting**: exact p values (e.g., p = .032); use p < .001 when p < .001
- **Significance stars**: * p < .05, ** p < .01, *** p < .001

### Table 1 — Sample Demographics

Columns: Variable | Category | n | %
Content: gender, age group, education, employment, marital status, income, etc.
Use `CTRL_MAP` to identify which columns are demographics.

### Table 2 — Descriptive Statistics, Reliability, Convergent Validity, and Latent Correlations

Columns: Construct | k | M | SD | α | ω | CR | AVE | [latent correlation matrix]
- Use `CONSTRUCT_LABELS` (full names) in the Construct column
- Diagonal = √AVE; lower triangle = CFA latent φ correlations; upper triangle = blank
- CR = (Σλ)² / ((Σλ)² + Σ(1−λ²)); AVE = mean(λ²); α = Cronbach's alpha; ω = McDonald's omega
- Note includes: Fornell & Larcker (1981) AVE ≥ .50 criterion; Hair et al. (2019) CR > .70 fallback; ABBREV_NOTE

### Table 3 — Competing Measurement Models

Models tested (each merging constructs progressively):
1. Hypothesized k-factor model (baseline)
2. Alternative models (merge theoretically similar constructs)
3. Single-factor model (all items → one latent)

Columns: Model | χ²(df) | ΔCFI | ΔRMSEA | CFI | TLI | RMSEA | Note
Note: label baseline as "Hypothesized model"; flag best fit.

### Table 4 — Structural Model Results

Columns: Path | B | SE | β | z | p | 95% CI | Supported? | R²
- Group rows by dependent variable (bold group header row)
- Use `ABBREV_LABELS` (abbreviations) in path notation: "ES → PFC-AI"
- Control variable paths are omitted from the table; mention in Notes:
  "Note. Control variables (age, gender, education, income, employment, marital status)
   were regressed on all endogenous constructs; paths not shown. [ABBREV_NOTE]"
- R² shown in the group header row for each DV, not repeated per path

### Table 5 — Bootstrapped Indirect Effects

Columns: Specific Indirect Effect | B | Boot SE | 95% CI | p | β
- Bootstrap B = 5,000 resamples; percentile CI; Delta-method p-values
- Use `ABBREV_LABELS` in path notation with → arrows
- Group by IV; include total indirect effect per IV
- Note: "Note. Indirect effects estimated via parametric bootstrap (B = 5,000).
   95% confidence intervals are percentile-based. [ABBREV_NOTE]"

### Table 6 — Moderation Results

Two panels:
**Panel A — Hierarchical OLS Regression**
Columns: Predictor | Model 1 B | Model 1 SE | Model 2 B | Model 2 SE | β | t | p | 95% CI
Row order: controls (summarized), X_c, W_c, X_c × W_c
Report ΔR² and its significance for Model 2.

**Panel B — Simple Slopes**
Columns: Level of W | b | SE | t | p | Sig.
Rows: Low W (M − 1SD = XX), Mean W (M = XX), High W (M + 1SD = XX)

Use `ABBREV_LABELS` for X, W, Y labels throughout. Include original-scale W values in row headers.

### Figure 1 — Conceptual Model Diagram

Draw a conceptual (not statistical) path diagram showing:
- IV box(es) on the left
- Mediator box(es) in the middle
- DV box on the right
- Moderator box below the mediator-to-DV path (diamond-on-path convention)

Box labels use `CONSTRUCT_LABELS` (full names with abbreviation in parentheses).
Use `matplotlib` / `matplotlib.patches`. Black borders, white fill, no shading.
Save as `Figure1_ConceptualModel.png` at 300 dpi.

### Figure 2 — Interaction Plot

Plot simple slopes of X on Y at three levels of W (Low/Mean/High).
- x-axis: X (original scale, uncentered values from −1SD to +1SD of X)
- y-axis: Y (predicted factor score)
- Three lines labeled by W level: "Low [W_abbrev] (M − 1SD = XX)", etc.
- Use `ABBREV_LABELS` in axis labels and legend title
- Save as `Figure2_InteractionPlot.png` at 300 dpi

### DataAnalysis_EN.docx and DataAnalysis_CN.docx

Two Word documents containing a complete write-up of all results:

**Structure:**
1. Measurement Model (CFA fit indices, AVE, CR, reliability; reference Table 2 and Table 3)
2. Structural Model (path coefficients, R², model fit; reference Table 4)
3. Indirect Effects (bootstrap CIs, mediation type; reference Table 5)
4. Moderation (interaction term significance, simple slopes; reference Table 6 and Figure 2)

**Formatting:**
- Times New Roman 12pt, double-spaced, 1-inch margins
- APA 7th edition in-text citations where needed
- Use `CONSTRUCT_LABELS` (full names on first mention), then `ABBREV_LABELS` thereafter
- Report statistics as: β = .XX, SE = .XX, z = X.XX, p = .XXX, 95% CI [.XX, .XX]
- CN version: translate all text to Chinese; keep all statistics and table/figure references
  in the same format; use Chinese academic phrasing conventions

Save both documents to `your-project/output/sem/<model_name>/`.

---

# Error Handling

- **Convergence failure** — check for multicollinearity (VIF > 10), reduce model complexity,
  or switch to MLR estimator. Report the error and ask user how to proceed.
- **Negative variance / Heywood case** — flag the problematic indicator, suggest removing it
  or constraining its variance to a small positive value (e.g., 0.001).
- **Poor fit (CFI < .90) after MI loop** — if 10 same-scale additions exhausted and CFI still
  < .90, report best CFI reached and ask: "继续尝试跨构念残差协方差（理论风险较高）？还是简化模型？"
- **Bootstrap failure rate > 20%** — warn user that too many bootstrap samples failed to
  converge; consider reducing B or using a simpler bootstrap strategy.
- **Small sample (N < 200)** — warn that CB-SEM requires adequate sample size; recommend
  bootstrapping and note that results should be interpreted with caution.
- **Factor score extraction failure** — fall back to computing weighted sum scores using
  standardized loadings as weights; note this approximation in the output.

---

# Important Notes

- Always interpret results in the context of the user's study from `your-project/context.md`.
- Report standardized coefficients (β) in tables and diagrams; unstandardized (B) in footnotes.
- Use APA 7th edition table formatting for all outputs.
- Remind users that SEM results are correlational — caution against causal language unless
  the study design supports it (longitudinal, experimental, or cross-lagged design).
- Control variables are always mean-centered before entry. Their paths are estimated but
  suppressed from output tables — always mention them in table Notes.
- The ABBREV_NOTE string must appear in the Notes of every table that uses abbreviations.
