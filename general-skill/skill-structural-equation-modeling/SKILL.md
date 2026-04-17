---
name: skill-structural-equation-modeling
description: |
  Structural equation modeling (SEM) assistant for communication research. Guides researchers
  step-by-step through EFA, CFA, full SEM, mediation, and moderation analysis using Python.
  Produces APA-style tables and path diagrams saved to your-project/project-{name}/output/.
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
step-by-step through the analysis — from loading their survey data to producing publication-ready
outputs. All analysis uses Python. The scripts live in `scripts/` alongside this SKILL.md.

## Prerequisites

Before starting, verify:
1. Read `your-project/project-{name}/context.md` — understand the study's constructs, variables, and hypotheses.
   If it's empty or incomplete, ask the user to describe their study first.
   Also read all files in `your-project/project-{name}/knowledge/` — questionnaires, literature notes, and any
   other background materials the user has placed there. Use this to understand the theoretical
   grounding of each construct, the source scales, and any prior validation evidence.
2. Check that a data file exists in `your-project/project-{name}/data/` (CSV or Excel).
3. Install dependencies from the agent root: `pip install -r requirements.txt`

---

# Step 1: Load and Inspect Data

Identify the data file in `your-project/project-{name}/data/`. If multiple files exist, use `AskUserQuestion` to
let the user pick one.

Run the data loader:
```bash
python general-skill/skill-structural-equation-modeling/scripts/load_data.py \
  --file "your-project/project-{name}/data/FILENAME"
```

Show the user:
- Number of rows (respondents) and columns (variables)
- Variable names
- Missing data summary (% missing per variable)
- Basic descriptives (mean, SD, range) for all numeric variables

If missing data exceeds 20% for any variable, flag it and ask how to proceed:
- `AskUserQuestion` options: "Drop rows with missing data" / "Use listwise deletion per analysis" / "I'll handle it myself"

---

# Step 2: Choose Analysis Type

Use `AskUserQuestion` to present analysis options:
- question: "What type of analysis do you want to run?"
- options:
  - "EFA — Exploratory Factor Analysis (I want to discover the factor structure)"
  - "CFA — Confirmatory Factor Analysis (I want to validate a known measurement model)"
  - "Full SEM — Latent variable structural model (measurement + structural paths)"
  - "Mediation — Test whether a variable mediates a relationship"
  - "Moderation — Test whether a variable moderates (conditions) a relationship"

Then follow the corresponding section below.

---

# EFA: Exploratory Factor Analysis

Use this when the user wants to explore how items cluster into factors — typically for scale
development or when the factor structure is unknown.

## EFA Step 1: Configure

Ask (use `AskUserQuestion`):
1. "Which variables/columns do you want to include in the EFA?" — list all numeric columns
   as checkboxes (multiSelect: true)
2. "How many factors to extract?" — options: "Let the data decide (parallel analysis)" /
   "2" / "3" / "4" / "5" / "Other — I'll specify"
3. "Rotation method?" — options: "Oblique / Promax (Recommended — factors likely correlated)" /
   "Orthogonal / Varimax (factors assumed uncorrelated)"

## EFA Step 2: Run

```bash
python general-skill/skill-structural-equation-modeling/scripts/efa_analysis.py \
  --file "your-project/project-{name}/data/FILENAME" \
  --vars "var1,var2,var3,..." \
  --n-factors N \
  --rotation promax \
  --output-dir "your-project/project-{name}/output/sem/efa"
```

## EFA Step 3: Interpret and Output

Present to the user:
- **KMO and Bartlett's test** — confirm data is suitable for EFA (KMO > 0.6, Bartlett p < .05)
- **Scree plot** — helps decide number of factors
- **Factor loadings table** — items and their loadings on each factor (highlight > .40)
- **Variance explained** — % variance per factor and cumulative
- **Cronbach's α** — reliability for each factor's items

Explain what each factor seems to represent based on which items load on it. Suggest factor names
based on the study context from `your-project/project-{name}/context.md`.

Outputs saved to `your-project/project-{name}/output/sem/efa/`:
- `efa_loadings.csv` — full loading matrix
- `efa_loadings_table.xlsx` — APA-formatted table
- `scree_plot.png` — scree plot

Ask: "Does this factor structure make sense for your study? Would you like to proceed to CFA
to confirm this structure?"

---

# CFA: Confirmatory Factor Analysis

Use this when the user has a hypothesized measurement model — typically after EFA, or when
using established scales from the literature.

## CFA Step 1: Specify the Measurement Model

Based on `your-project/project-{name}/context.md` and/or EFA results, propose which items load onto which latent
constructs. Present the proposed model to the user using `AskUserQuestion` to confirm:
- question: "Here is the proposed measurement model. Does this look right?"
- Show the model clearly: "Factor1 → [item1, item2, item3]", etc.
- options: "Yes, run it" / "No, I want to adjust"

If adjusting, guide the user item by item.

## CFA Step 2: Run

```bash
python general-skill/skill-structural-equation-modeling/scripts/sem_analysis.py \
  --file "your-project/project-{name}/data/FILENAME" \
  --model-type cfa \
  --model "MODEL_SPEC" \
  --output-dir "your-project/project-{name}/output/sem/cfa"
```

Model spec format (semopy syntax):
```
Factor1 =~ item1 + item2 + item3
Factor2 =~ item4 + item5 + item6
```

## CFA Step 2b: Item Diagnostic — Flag Weak Indicators

Immediately after fitting, inspect the standardized loadings and compute per-construct AVE.
For each construct, identify any item where **λ < .50** (i.e., the item explains less than 25%
of its factor's variance), as these are the primary drivers of low AVE.

Present a diagnostic summary to the user for each flagged item:

```
Construct: [Name]  AVE = .XX  (threshold: ≥ .50)
  ⚠ [item_id]  λ = .XX  — this item is pulling AVE down.
     Removing it would raise AVE to approximately .XX.
```

To estimate post-deletion AVE, recompute: AVE = mean(λ²) excluding that item.

Then ask the user via `AskUserQuestion`:
- question: "The items above have low factor loadings (λ < .50), dragging AVE down. Would you like to remove any?"
- options (multiSelect: true — list each flagged item individually, e.g.):
  - "Remove [item_id] (λ = .XX, post-deletion AVE ≈ .XX)"
  - "Keep all items, no deletion"

**Rules for deletion:**
- Only suggest deletion if λ < .50. Items with .50 ≤ λ < .60 may be noted but not flagged
  for deletion unless the user asks.
- Never suggest deleting an item that would leave a construct with fewer than 3 indicators,
  unless the construct originally had only 3 items (in which case warn the user that deletion
  risks under-identification).
- If the user chooses to delete one or more items, refit the CFA with the updated spec and
  re-report fit indices and AVE before proceeding to Step 3.
- If the user chooses to retain all items, continue to Step 3 with the original model.
  Note in the output that AVE < .50 will be addressed via the Hair et al. (2019) fallback
  (CR > .70 as acceptable alternative) when generating Table 2.

## CFA Step 3: Evaluate Fit and Auto-Optimize via Modification Indices

Present fit indices with benchmarks:

| Index | Result | Minimum Acceptable | Good Fit |
|-------|--------|--------------------|----------|
| χ² (df, p) | — | — | p > .05 (sensitive to N) |
| CFI | — | ≥ .90 | ≥ .95 |
| TLI | — | ≥ .90 | ≥ .95 |
| RMSEA [90% CI] | — | ≤ .08 | ≤ .06 |

**If CFI < .90, automatically run the MI optimization loop:**

1. Retrieve modification indices from semopy:
   ```python
   mis = semopy.calc_mi(mod)
   # mis is a DataFrame with columns: lval, op, rval, mi (modification index value)
   ```
2. Sort by `mi` descending. Consider only residual covariance suggestions (`op == '~~'`)
   where **both variables belong to the same latent construct** (same-scale pairs only).
   Do NOT add cross-construct residual covariances — that would compromise discriminant validity.
3. Add the highest-MI same-scale residual covariance to the model spec, refit, and check CFI.
4. Repeat — adding one parameter per iteration — until **CFI ≥ .90** or no more
   same-scale MI candidates remain.
5. Cap at a maximum of **10 added residual covariances** across all constructs to prevent
   over-fitting. If CFI still < .90 after 10 additions, stop and report the best result reached.

**After the loop, report to the user:**
- Final fit indices
- List of all residual covariances added (e.g., "Added: C2r1 ~~ C2r2, C4r3 ~~ C4r4")
- Theoretical justification note: "These covariances reflect shared method variance between
  adjacent or similarly worded items within the same scale, which is theoretically defensible."

**If CFI ≥ .90 but < .95**, note this as acceptable fit and continue. Do not keep adding MIs
just to chase .95 — over-modification inflates fit artificially.

**If fit is already ≥ .90 on first run**, skip the loop entirely and proceed.

## CFA Step 4: Output

Outputs saved to `your-project/project-{name}/output/sem/cfa/`:
- `cfa_fit_indices.csv` — model fit summary (χ², df, CFI, TLI, RMSEA)
- `cfa_parameters.xlsx` — APA-formatted factor loadings table (with β, SE, p)
- `cfa_path_diagram.png` — publication-quality path diagram (300 dpi); see **Path Diagram Specifications** below
- `cfa_path_diagram.html` — interactive version of the same diagram for exploration
- `cfa_measurement_quality.docx` — **APA-formatted Word table** containing per-construct:
  - k (number of items), M, SD
  - Cronbach's α, McDonald's ω
  - CR (composite reliability = (Σλ)² / [(Σλ)² + Σ(1−λ²)])
  - AVE (average variance extracted = Σλ² / k), √AVE on diagonal
  - Latent correlation matrix (lower triangle) from the CFA model
  - Table note citing Fornell & Larcker (1981) for AVE ≥ .50 criterion and
    Hair et al. (2019) for the CR > .70 fallback when AVE < .50

### Path Diagram Specifications (CFA)

Apply the following rules when generating `cfa_path_diagram.png` and `.html`:

1. **Box style** — all latent construct ovals and observed item rectangles use a black border
   with white fill. No color fills, gradients, or shading of any kind.
2. **Path lines**:
   - **Solid line** — factor loading is statistically significant (p < .05)
   - **Dashed line** — factor loading is non-significant (p ≥ .05)
   - Line color: black only
3. **Labels** — standardized loadings (β) displayed on each path, rounded to two decimal places.
4. **Layout** — latent constructs arranged in a single row or column; items fan out from their
   factor. Avoid path crossings where possible.
5. **Resolution** — save `.png` at 300 dpi minimum for print submission.

---

# Full SEM: Latent Variable Structural Model

Full SEM combines a measurement model (CFA) with structural paths between latent constructs.
Use this after confirming the measurement model via CFA.

## SEM Step 1: Specify Structural Paths

Based on `your-project/project-{name}/context.md` hypotheses, propose the structural model. Clearly show:
- Which latent constructs predict which others (e.g., "MediaUse → Attitude")
- Direction of all paths

Confirm with user via `AskUserQuestion`.

## SEM Step 2: Run

```bash
python general-skill/skill-structural-equation-modeling/scripts/sem_analysis.py \
  --file "your-project/project-{name}/data/FILENAME" \
  --model-type sem \
  --model "MODEL_SPEC" \
  --output-dir "your-project/project-{name}/output/sem/full_sem"
```

Model spec adds structural paths to the CFA spec:
```
Factor1 =~ item1 + item2 + item3
Factor2 =~ item4 + item5 + item6
Factor2 ~ Factor1
```

## SEM Step 3: Evaluate, Optimize, and Interpret

Report the same fit indices as CFA (CFI, TLI, RMSEA). Apply the **same MI optimization loop**
described in CFA Step 3 if CFI < .90:
- Only add residual covariances within the same scale
- Cap at 10 total additions
- Stop once CFI ≥ .90

Then present:
- Structural path coefficients (B, SE, β, z, p, 95% CI) — are hypothesized paths significant?
- R² for each endogenous construct — how much variance is explained?
- List any MI-based modifications made, with theoretical justification

## SEM Step 4: Core Outputs

Always save the following to `your-project/project-{name}/output/sem/<model_name>/`:
- `sem_fit_indices.csv` — model fit summary (χ², df, CFI, TLI, RMSEA)
- `sem_structural_paths.xlsx` — structural path estimates (B, SE, β, z, p)
- `sem_path_diagram.png` — publication-quality path diagram (300 dpi); see **Path Diagram Specifications** below
- `sem_path_diagram.html` — interactive version for exploration
- `sem_r_squared.csv` — R² for each endogenous construct
- `sem_measurement_quality.docx` — APA Word table: k, M, SD, α, ω, CR, AVE, latent correlation
  matrix (√AVE on diagonal, lower triangle = CFA latent correlations)

### Path Diagram Specifications (SEM)

Apply the following rules when generating `sem_path_diagram.png` and `.html`:

1. **Box style** — all latent construct ovals and observed item rectangles use a black border
   with white fill. No color fills, gradients, or shading of any kind.
2. **Path lines**:
   - **Solid line** — path is statistically significant (p < .05)
   - **Dashed line** — path is non-significant (p ≥ .05)
   - Line color: black only
3. **Labels** — standardized coefficients (β) on structural paths; standardized loadings on
   measurement paths; all rounded to two decimal places.
4. **Direct IV → DV paths** (when the model includes a direct effect from an exogenous
   variable to the final outcome, bypassing mediators):
   - Route this path as a **curved arc** (concave above or below the diagram) or as a
     **right-angle bent line** that travels above or below the main diagram area.
   - The arc/bent line must **not cross or overlap** mediator boxes or the mediating paths
     between them. Choose above vs. below based on whichever side is less crowded.
5. **Layout** — place exogenous constructs on the left, mediators in the middle, endogenous
   constructs on the right. Keep the main causal flow left-to-right so direct-path arcs
   have a clear route around the diagram.
6. **Resolution** — save `.png` at 300 dpi minimum for print submission.

## SEM Step 5: APA Publication Tables (Optional — Ask First)

After the core outputs are saved, ask the user:

> "The model has finished running. Would you like to generate APA-formatted tables for journal submission? The following tables are available:"

Present as a **multiSelect** `AskUserQuestion`:
- question: "Select the APA result tables to generate (multi-select):"
- options:
  - **Table 1 — Sample Demographics**
    Descriptive statistics for demographic variables. Columns: Variable | n | %.
    Content: gender, age group, education level, employment status, marital status, income, etc.
  - **Table 2 — Descriptive Statistics, Reliability, Convergent Validity, and Latent Correlations**
    Measurement model quality summary. Columns: Construct | k | M | SD | α | ω | CR | AVE | latent correlation matrix.
    Diagonal = √AVE; lower triangle = CFA latent correlations; upper triangle left blank.
    Notes cite Fornell & Larcker (1981) and Hair et al. (2019).
  - **Table 3 — Competing Measurement Models**
    Competing measurement model comparison table for demonstrating construct discriminant validity.
    Columns: Model | χ²(df) | CFI | TLI | RMSEA | GFI.
    Progressively merge from the hypothesized multi-factor model to a single-factor null model, comparing fit index changes.
  - **Table 4 — Structural Model Results**
    Core structural path results. Columns: Path | B | SE | β | z | p | 95% CI | Support | R².
    Grouped by dependent variable (each group has a header row); control variable paths are not listed but noted in table footnotes.
  - **Table 5 — Bootstrapped Indirect Effects**
    Bootstrap mediation test table (2,000 resamples).
    Columns: Specific Indirect Effect | B | Boot SE | 95% CI | p | β.
    Grouped by independent variable, including each specific indirect path and total indirect effect.

Generate only the tables the user selects. Save all selected tables to
`your-project/project-{name}/output/sem/<model_name>/` as `.docx` files using:
- APA three-line table format
- Times New Roman 12pt throughout
- Landscape orientation (11 × 8.5 inches) for wide tables (Tables 2–5)
- Portrait orientation for Table 1

After generating, list the saved file paths so the user can open them directly.

---

# Mediation Analysis

Use this to test whether variable M mediates the effect of X on Y. Works with both observed
and latent variables.

## Mediation Step 1: Identify Variables

Ask via `AskUserQuestion`:
1. "Which variable is the predictor (X)?" — list columns
2. "Which variable is the mediator (M)?" — list columns
3. "Which variable is the outcome (Y)?" — list columns
4. "Are any of these latent constructs (measured by multiple items)?" — Yes / No

If latent: ask user to specify which items belong to each construct.

## Mediation Step 2: Run

```bash
python general-skill/skill-structural-equation-modeling/scripts/sem_analysis.py \
  --file "your-project/project-{name}/data/FILENAME" \
  --model-type mediation \
  --x "X_VAR" --m "M_VAR" --y "Y_VAR" \
  --bootstrap 5000 \
  --output-dir "your-project/project-{name}/output/sem/mediation"
```

## Mediation Step 3: Interpret

Report:
- **Direct effect** (c'): X → Y controlling for M
- **Indirect effect** (a×b): X → M → Y
- **Total effect** (c): X → Y
- **Bootstrap 95% CI** for indirect effect — if CI excludes 0, mediation is supported
- **Type of mediation**: full (c' not sig) / partial (c' sig) / no mediation

## Mediation Step 4: Output

Outputs saved to `your-project/project-{name}/output/sem/mediation/`:
- `mediation_results.xlsx` — APA-formatted table of all effects
- `mediation_path_diagram.png` — path diagram with a, b, c, c' coefficients

---

# Moderation Analysis

Use this to test whether variable W conditions the effect of X on Y (interaction effect).

## Moderation Step 1: Identify Variables

Ask via `AskUserQuestion`:
1. "Which variable is the predictor (X)?" — list columns
2. "Which variable is the moderator (W)?" — list columns
3. "Which variable is the outcome (Y)?" — list columns
4. "Should we mean-center X and W before creating the interaction term?" —
   options: "Yes (Recommended)" / "No"

## Moderation Step 2: Run

```bash
python general-skill/skill-structural-equation-modeling/scripts/sem_analysis.py \
  --file "your-project/project-{name}/data/FILENAME" \
  --model-type moderation \
  --x "X_VAR" --w "W_VAR" --y "Y_VAR" \
  --center \
  --output-dir "your-project/project-{name}/output/sem/moderation"
```

## Moderation Step 3: Interpret

Report:
- **Main effect of X** on Y
- **Main effect of W** on Y
- **Interaction effect (X×W)** on Y — if significant, moderation is supported
- **Simple slopes**: effect of X on Y at low (−1 SD), mean, and high (+1 SD) of W
- **Johnson-Neyman interval**: range of W where X's effect is significant

## Moderation Step 4: Output

Outputs saved to `your-project/project-{name}/output/sem/moderation/`:
- `moderation_results.xlsx` — APA-formatted regression table
- `interaction_plot.png` — interaction plot showing simple slopes

---

# Error Handling

- **Convergence failure** — suggest checking for multicollinearity, reducing model complexity,
  or using a different estimator (MLR instead of ML)
- **Negative variance (Heywood case)** — flag the problematic indicator, suggest removing it
  or constraining the variance
- **Poor fit (CFI < .90)** — automatically run MI optimization loop (same-scale residual
  covariances only, max 10 additions). Report all added parameters and their MI values.
  If CFI still < .90 after exhausting same-scale candidates, flag to user and ask whether
  to consider cross-scale MIs (with strong theoretical caution) or simplify the model
- **Small sample** (N < 200) — warn that SEM requires adequate sample size; suggest bootstrapping

---

# Important Notes

- Always interpret results in the context of the user's study from `your-project/project-{name}/context.md`.
- Report standardized coefficients (β) in tables and diagrams; unstandardized (B) in footnotes.
- Use APA 7th edition table formatting for all outputs.
- Remind users that SEM results are correlational — caution against causal language unless
  the study design supports it.
