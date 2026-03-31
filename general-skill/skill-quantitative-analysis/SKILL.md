---
name: skill-quantitative-analysis
description: |
  End-to-end interactive inferential statistics and quantitative analysis for
  survey and tabular data. Guides through data cleaning, variable encoding,
  descriptive analysis, statistical hypothesis tests (ANOVA, Tukey HSD,
  chi-squared, t-tests), regression modelling (linear, logistic, ordinal), and
  formatted data tables exported to Excel. Use this skill whenever the user
  wants to run statistical tests, compare groups, test hypotheses, analyse survey
  responses statistically, build regression models, or produce descriptive
  statistics — even if they don't use technical terms. Trigger for phrases like
  "run stats on this", "compare groups", "test if there's a difference",
  "analyse survey results", "is this significant?", "run ANOVA", "chi-squared
  test", "t-test", "regression analysis", "descriptive statistics", "frequency
  table", or "statistical report". This skill covers inferential statistics and
  descriptive analysis only — for segmentation and clustering, use the
  clustering-analysis skill instead.
---

# Quantitative Analysis Skill

You are helping a researcher perform end-to-end quantitative and inferential statistical analysis on survey or tabular data. Follow the phased interactive workflow below.

**CRITICAL RULE: Never proceed to the next step without explicit user confirmation. At every decision point — data cleaning, encoding, analysis choices — present your recommendation, explain why, and wait for the user to approve, modify, or reject before executing.**

## Prerequisites

Before starting:
1. Read `your-project/context.md` to understand the study design, variables, and hypotheses.
2. Confirm a data file exists in `your-project/data/` (CSV or Excel).
3. Install dependencies from the agent root: `pip install -r requirements.txt`
4. All outputs go to `your-project/output/quantitative-analysis/` — create this folder if needed.

## Python setup

`clustering_core.py` lives in the `scripts/` directory inside this skill folder. It provides all data loading, encoding, and statistical analysis functions. To import it, start every Python script with:

```python
import os, sys, glob

def _find_clustering_core():
    """Find clustering_core.py in common skill installation paths."""
    search_patterns = [
        # comm-agent repo install (primary path)
        os.path.join(os.getcwd(), 'general-skill', 'skill-quantitative-analysis', 'scripts'),
        # Repo-based installs (skill folder cloned directly under any name)
        os.path.join(os.getcwd(), 'scripts'),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts') if '__file__' in dir() else None,
        os.path.expanduser('~/*/skills/quantitative-analysis/scripts'),
        os.path.expanduser('~/*/skills/clustering-analysis/scripts'),
        os.path.expanduser('~/*/*/skills/quantitative-analysis/scripts'),
        os.path.expanduser('~/*/*/skills/clustering-analysis/scripts'),
        # Claude Code managed installs
        os.path.expanduser('~/.claude/skills/quantitative-analysis/scripts'),
        os.path.expanduser('~/.claude/skills/clustering-analysis/scripts'),
        os.path.expanduser('~/.claude/plugins/**/quantitative-analysis/scripts'),
        os.path.expanduser('~/.claude/plugins/cache/**/quantitative-analysis/scripts'),
    ]
    for pattern in search_patterns:
        if pattern is None:
            continue
        for path in glob.glob(pattern, recursive=True):
            if os.path.isfile(os.path.join(path, 'clustering_core.py')):
                return path
    for root, dirs, files in os.walk(os.path.expanduser('~/.claude')):
        if 'clustering_core.py' in files:
            return root
    return None

_scripts_dir = _find_clustering_core()
if _scripts_dir:
    sys.path.insert(0, _scripts_dir)
else:
    raise ImportError(
        "Could not find clustering_core.py. "
        "If running from a cloned repo, set _scripts_dir manually to the absolute path "
        "of the scripts/ folder inside the clustering-analysis skill directory, "
        "then re-run sys.path.insert(0, _scripts_dir)."
    )
from clustering_core import *
```

For charts with Chinese characters, set matplotlib fonts at the top of any script that produces charts:

```python
import matplotlib
import matplotlib.pyplot as plt
matplotlib.rcParams['font.family'] = ['Arial Unicode MS', 'Heiti TC', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
```

---

## Phase 0: Survey Scoping (multi-topic surveys only)

This phase has two steps — always do Step A before Step B.

**Step A — Capture user intent first (before touching the data):**

Ask: "Before I look at the data, what questions are you hoping to answer with this survey? For example:
- 'I want to know if satisfaction differs by job role'
- 'I want to understand which features are seen as most important'
- 'I want to see if AI adoption varies by age or region'

List as many as you like — I'll make sure every question you care about is covered."

⛔ **STOP — do not load any data until the user responds.** Record every question they state as **user-defined topics** — these are guaranteed to be in the analysis.

If the user says "not sure" or "you decide", treat the entire dataset as open for exploration and proceed to Step B with no locked topics.

---

**Step B — Map user topics to columns, then supplement with data-driven suggestions:**

Load the data and scan all column names. Then present a **two-section topic plan**:

```
📌 YOUR TOPICS (from what you told me):
  1. [User question] → columns I'll use: [list]
  2. [User question] → columns I'll use: [list]
  ...

💡 ADDITIONAL TOPICS I FOUND IN THE DATA:
  A. [LLM-suggested topic] → columns: [list] — reason: [why this looks interesting]
  B. [LLM-suggested topic] → columns: [list] — reason: [why this looks interesting]
  ...
```

Rules:
- Every user-defined topic from Step A must appear in section 📌, even if you think it's low priority.
- If a user topic maps to columns you can't find, say so explicitly: "I couldn't find columns that clearly match '[question]' — here's what's closest: [list]. Does this work, or would you like to skip this one?"
- LLM-suggested topics in section 💡 are optional additions, not replacements.
- If the dataset has < 30 columns, skip the 💡 section — just confirm the user topics and proceed.

Ask: "Does this topic plan look right? You can add, remove, or rename any topic before we start."

⛔ **STOP — do not begin Phase 1 until the user has approved the final topic list.**

Once confirmed:
- Ask: "Would you like to work through these one topic at a time, or run all analyses together?"
- Process one topic at a time, repeating Phases 1–7 for each. Carry forward the same cleaned base DataFrame — only re-select columns per topic.

---

## Phase 0.5: Survey Handoff Recognition

If the input includes a structured `Survey → Analysis Handoff` block from `survey-research`, parse it before Phase 1 and present a one-line confirmation:

> "I see this is a **[survey purpose]** handoff. I'll run the following named analysis patterns in addition to the standard workflow: [list]. Let me know if you'd like to adjust."

**Routing by survey purpose:**

| Survey Purpose | Named Patterns to Run |
|---|---|
| **Prioritization** | MAU/DAU Estimation (if frequency question present) |
| **Measurement** | Satisfaction Driver Analysis + Priority Matrix |
| **User Profile & Growth** | Satisfaction Driver Analysis + Priority Matrix; Growth Signal Detection |
| **Generative** | Format Confidence Gap; Dual-Perspective Alignment (if two-role structure present) |
| **Segmentation** | Route to `clustering-analysis` — not this skill |

Extract and carry forward from the handoff block:
- `Survey purpose` → determines which named patterns apply
- `Grouping variable` → use as the Phase 3 grouping variable
- `Satisfaction DV` / `Satisfaction predictors` → pre-fill for Satisfaction Driver Analysis
- `Growth signal candidates` → pre-fill behavioral columns for Growth Signal Detection
- `Variables of interest` → scope Phase 0 topic plan

If no structured handoff is present, proceed with Phase 0 normally.

---

## Phase 1: Data Loading & Cleaning

1. If `$ARGUMENTS` contains a file path, use that. Otherwise, ask the user for the data file path.
2. Load and preview the data — show shape, first 3 rows, and all column names with indices.
3. **Ask the user to confirm each cleaning step separately** (do NOT batch them):

   **Step 1a — Headers:** "The data has [X] columns. Does the first row contain the actual headers, or is this a Qualtrics-style export where I should use row 0/1 as headers? Here's what the first 2 rows look like: [show them]. How would you like me to handle the headers?"

   > **Matrix question note:** Qualtrics matrix questions produce columns like `Q5 - How satisfied are you with...` in row 0 and sub-item labels like `Search`, `Navigation`, `Speed` in row 1. When applying Qualtrics headers, use the sub-item label (row 1) as the column name for matrix sub-items, and keep the question stem (row 0) only for standalone questions. If this pattern is detected, show the user the proposed column names before applying.

   ⛔ **STOP — wait for confirmation before applying.**

   **Step 1b — Column removal:** "Here are all [X] columns. Which ones should I drop? I'd suggest removing these metadata/irrelevant columns: [list suggestions and why]. Do you agree, or would you like to keep/drop different columns?"
   ⛔ **STOP — wait for confirmation before applying.**

   **Step 1c — Row filtering:**
   - Step 1c-i: "Should I filter rows? For example, keep only completed responses? Here's what the 'Finished' or 'Status' column looks like (if it exists): [show value counts]. How would you like to filter?"
   ⛔ **STOP — wait for confirmation before applying.**
   - Step 1c-ii: **Conditional/skip-logic columns:** After loading, check all columns for high null rates. "I found [N] columns with > 50% missing values. These are likely conditional questions (shown only to a subset of respondents based on earlier answers). Here they are with their null rates: [list]. Options: (A) Keep for sub-group analysis only — exclude from overall tests; (B) Drop entirely. Which would you prefer?" ⛔ **STOP — wait for confirmation before applying.**

   **Step 1d — Deduplication:** "Is there a respondent ID column for deduplication? I see these potential ID columns: [list]. Should I deduplicate based on one of them?"
   ⛔ **STOP — wait for confirmation before applying.**

   **Step 1e — Duplicate column names:** After cleaning, check whether any column names are duplicated (common in Qualtrics matrix exports where multiple question blocks share sub-item labels). If duplicates exist: "I found [N] duplicate column names: [list]. This typically happens when two matrix questions have the same sub-item labels (e.g., Q19 satisfaction and Q20 necessity both have a '网站导航' sub-column). I recommend renaming them by appending a suffix — e.g., '网站导航_1', '网站导航_2'. Shall I apply this, or would you prefer to rename them manually?"
   ⛔ **STOP — wait for confirmation, then apply:** `df = deduplicate_column_names(df, strategy='suffix')`

   **Step 1f — Data constraints:** "Before we analyse, are there any known limitations with this data I should be aware of? For example:
   - Non-representative sample (specific group over/under-represented)
   - Questions added or changed mid-survey
   - Known translation or wording issues
   - Any groups you'd like to exclude from certain analyses

   I'll note these in the final summary so findings are interpreted in context."
   ⛔ **STOP — wait for response before proceeding to Phase 2.** Record any constraints; reference them when interpreting results in Phase 7.

4. After all cleaning steps, show the final cleaned data shape and a sample.

---

## Phase 2: Variable Type Detection & Encoding

1. Run auto-detection on all remaining columns and present a formatted table showing: index, column name, detected type, confidence, and sample values.

2. **Before encoding anything, ask the user to confirm the detection results:**
   "Here's what I detected for each column. Please review and tell me if any corrections are needed. You can say things like:
   - 'col 3 should be likert_frequency'
   - 'col 7 should be categorical_multi'
   - 'drop col 0, 1, 15'"
   ⛔ **STOP — wait for confirmation before encoding anything.**

3. **For each encoding transformation, show the proposed mapping and ask for confirmation:**
   - For Likert scales: "For column '[name]', I'll map: Never→0, Rarely→1, Quarterly→2, Monthly→3, Weekly→4, Daily→5. Does this mapping look correct, or would you like to adjust it?"
   - For ordinal demographics: "For column '[name]', I'll map: [show proposed mapping]. Does this ordering make sense?"
   - For multi-select columns: "For column '[name]', I'll one-hot encode the comma-separated values. The unique options I found are: [list]. Correct?"
   - You may group similar columns together (e.g., all frequency Likert columns) for a single confirmation, but always show the mapping.
   ⛔ **STOP — wait for confirmation before applying each group.**

4. After all encodings, show a summary of what was transformed. **For any column containing `不适用` (Not Applicable) responses, report the N/A rate:** "Column '[name]': [X]% of respondents selected 不适用 — these are excluded from statistical calculations (treated as NaN, not 0)."

### Supported variable types
- `likert_frequency` — Never/Rarely/Quarterly/Monthly/Weekly/Daily → 0-5
- `likert_importance` — Not Important at All → Extremely Important → 1-5
- `likert_agreement` — Strongly Disagree → Strongly Agree → 1-5
- `likert_satisfaction` — Very Dissatisfied → Very Satisfied → 1-5
- `likert_satisfaction_zh` — 非常满意/满意/中立/不满意/非常不满意 → 5-1; 不适用 → NaN
- `likert_importance_zh` — 非常重要/重要/中立/不重要/非常不重要 → 5-1; 不适用 → NaN
- `likert_necessity` — 非常必要/必要/中立/不必要/完全不必要 → 5-1; 不适用 → NaN
- `likert_agreement_zh` — 非常同意/同意/中立/不同意/非常不同意 → 5-1; 不适用 → NaN
- `likert_frequency_zh` — 每天/每周/每月/很少/从不 → 5-0; 不适用 → NaN
- `ordinal_demographic` — Bracket ranges like "18-24 years old" → ordered integers
- `categorical_single` — Single-select categorical (job role, industry)
- `categorical_multi` — Multi-select comma-separated → one-hot encoded
- `numerical_continuous` — Continuous numbers
- `numerical_discrete` — Small-range integers (likely already-encoded scales)
- `identifier` — IDs, emails, timestamps (usually dropped)
- `free_text` — Open-ended responses (usually dropped)

---

## Phase 3: Analysis Planning

1. **Ask what grouping variable to use (if any):**
   "For comparative analyses (ANOVA, t-tests, chi-squared), I need a grouping variable — the column that defines the groups to compare. This is often a demographic (job role, age group, region), a condition (A/B test arm), or a cluster assignment.

   Which column should be used as the grouping variable? Or would you prefer to run descriptive analysis only (no group comparisons)?"
   ⛔ **STOP — wait for confirmation.**

2. **Show what's viable given the data (capability check):**

   Before presenting analysis options, check the encoded dataset and show this table:

   ```
   Analysis Capability Check
   ─────────────────────────────────────────────────────────────────────
   Analysis          Status   Notes
   ─────────────────────────────────────────────────────────────────────
   ANOVA             ✅/⚠️/⛔  [e.g., ⚠️ Caution — smallest group n=8, underpowered]
   Chi-squared       ✅/⚠️/⛔  [e.g., ⛔ Not recommended — 4 cells have expected freq < 5]
   T-test            ✅/⚠️/⛔  [e.g., ✅ Viable]
   Linear regression ✅/⚠️/⛔  [e.g., ⚠️ Total n=42, marginal for regression]
   ─────────────────────────────────────────────────────────────────────
   ```

   **Status rules:**
   - ✅ **Viable** — conditions met (ANOVA: n ≥ 15 per group; chi-squared: all expected cells ≥ 5; regression: n ≥ 50 total)
   - ⚠️ **Caution** — usable but interpret carefully (ANOVA: n 10–14 per group; chi-squared: some cells 3–4; regression: n 30–49)
   - ⛔ **Not recommended** — assumptions violated (ANOVA: n < 10 per group; chi-squared: expected cells < 3; regression: n < 30)

3. **Ask how deep to go:**

   "How thorough should this analysis be?
   - **Quick read** — descriptive summary and means table only (~5 min)
   - **Standard** *(recommended)* — descriptives + ANOVA/chi-squared on key variables + charts
   - **Deep dive** — full suite: all tests + Tukey HSD + regression + charts + named analysis patterns (satisfaction driver, MAU/DAU, growth signals, etc.)"

   ⛔ **STOP — wait for the user's choice before listing individual options.**

4. **Present analysis options** (matching the chosen depth):

   **Descriptive:**
   - Numerical means table — means and standard deviations per group
   - Categorical distributions — frequency and percentage tables per group
   - Overall descriptive summary — min, max, mean, median, SD for all numerical variables

   **Inferential — Comparing Groups:**
   - **ANOVA** — test if numerical variable means differ significantly across groups. Reports F-statistic, p-value, eta-squared (effect size), and group-level means/SD.
   - **Tukey HSD** — pairwise post-hoc comparisons for any significant ANOVA result
   - **Chi-squared** — test if categorical distributions differ across groups. Reports chi², p-value, Cramér's V, plus observed vs expected frequencies and standardized residuals.
   - **T-test (independent)** — compare a numerical variable between exactly two groups. Reports means, SDs, t-statistic, p-value, Cohen's d.
   - **T-test (paired)** — compare two numerical variables within the same respondents (e.g., importance of A vs importance of B). Reports means, SDs, t-statistic, p-value, Cohen's d.

   **Modelling:**
   - **Linear regression** — predict a continuous outcome from one or more predictors
   - **Logistic regression** — predict a binary outcome
   - **Ordinal regression** — predict an ordered categorical outcome (e.g., satisfaction level)

   **Named Analysis Patterns** (appear when triggered by survey purpose or data structure):
   - **Satisfaction Driver Analysis + Priority Matrix** — regression of sub-dimensions on overall satisfaction → 2×2 quadrant (Improve First / Enhance Strength / Improve Next / Maintain)
   - **MAU/DAU Estimation** — convert frequency question distributions into estimated monthly and daily active user percentages per item + usefulness correlation
   - **Growth Signal Detection** — chi-square of behavioral subgroups (e.g., shopping users) against engagement/loyalty outcomes; flag p < 0.05 as growth signal candidates
   - **Format Confidence Gap** — compare importance% vs format-suitability% per item; large gaps = design challenges
   - **Dual-Perspective Alignment** — compare item selection rates between two user roles (e.g., participant vs organizer); classify each item as Confirmed / Divergent / Partial

   **Charts:**
   - Bar charts of group means for key variables
   - Heatmap of mean scores across variables × groups
   - Distribution plots for top significant variables

   ⛔ **STOP — wait for the user's selection before running anything.**

---

## Phase 4: Descriptive Analysis

Run only if the user selected descriptive options.

If the user does **not** select a grouping variable, skip per-group comparison tables and provide only the overall descriptive summary.

**Numerical means table:**
```python
groups = [subset_df for _, subset_df in df.groupby(group_col)]
result = numerical_comparison(groups, numerical_columns, label_column=group_col)
print(result.to_string())
```
Show means and SDs as a variable × group DataFrame. Ask: "Any specific variables you'd like to focus on?"

**Categorical distributions:**
```python
result = categorical_comparison(groups, column, separator=None, label_column=group_col)
print(result.to_string())
```
Show frequency and percentage tables per group. Ask: "Any specific variables to examine further?"

**Overall descriptive summary:** Use `df[numerical_columns].describe()` and format it clearly.

---

## Phase 5: Statistical Tests

Run only the tests the user selected. For each test, confirm the specific variables and parameters first.

### Finding strength labels

After every test result, append a **finding strength label** based on the combined evidence. Never rely on p-value alone.

| Label | Conditions | Meaning |
|-------|-----------|---------|
| ✅ **Strong** | p < 0.01 AND large effect (η² ≥ 0.14, d ≥ 0.8, or V ≥ 0.3) | Robust — act on this |
| ⚠️ **Moderate** | p < 0.05 AND medium effect (η² ≥ 0.06, d ≥ 0.5, or V ≥ 0.2) | Worth investigating — replicate before acting |
| 🔵 **Suggestive** | p < 0.05 but small effect, OR p 0.05–0.10 with notable effect | Interesting pattern — treat with caution |
| — **No difference** | p ≥ 0.10 | No detectable difference in this sample |

Report the actual n used in each test (NaN exclusion can reduce effective n significantly).

### ANOVA
For each numerical variable the user wants to test:
```python
anova_result = run_anova(df, variable=col, group_column=group_col)
```
Show: F-statistic, p-value, eta-squared, group means and SDs, effective n per group, **finding strength label**.
- After showing results: "These variables showed significant differences: [list with strength labels]. Would you like Tukey HSD post-hoc tests to see which specific groups differ?"

### Tukey HSD
Run for any ANOVA-significant variable:
```python
tukey_result = run_tukey_hsd(df, variable=col, group_column=group_col)
```
Show pairwise comparison tables. The `significant` column (True/False) indicates pairs with p < 0.05. Highlight significant pairs clearly.

### Chi-squared
For each categorical variable the user wants to test:
```python
chi2_result = run_chi_squared(df, variable=col, group_column=group_col,
                               groups_to_compare=None)  # or specify two groups
```
Show: chi² statistic, p-value, Cramér's V, effective n, **finding strength label**.
For significant results (p < 0.05), also show:
- Observed vs expected frequency table
- Standardized residuals table
- Cells with |residual| > 1.96 highlighted as "significantly over/under-represented"
Ask: "Would you like to compare specific groups only? (e.g., Group A vs Group B)"

### T-test (independent)
Ask:
- "Which numerical variable?"
- "Which two groups to compare?"
```python
ttest_result = run_ttest_independent(df, variable=col, group_column=group_col,
                                      group_a=grp_a, group_b=grp_b)
```
Show: means, SDs, t-statistic, p-value, Cohen's d, effective n, **finding strength label**.

### T-test (paired)
Ask:
- "Which two variables to compare within the same respondents?"
- "Run on all respondents or a specific group?"
```python
ttest_result = run_ttest_paired(df, variable_1=col_a, variable_2=col_b,
                                 group_filter=None, group_column=None)
```
Show: means, SDs, t-statistic, p-value, Cohen's d, effective n, **finding strength label**.

---

## Phase 5b: Charts

After statistical tests, offer to generate charts for the key findings. Ask: "Would you like charts for any of these results?"

Track all saved chart file paths in a list — you will pass them to `export_to_excel` in Phase 7 to embed them directly in the Excel workbook.

```python
chart_paths = []  # accumulate across all chart types
```

**Group means bar chart** (for ANOVA / descriptive means):
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(variables))
width = 0.8 / len(groups)
for i, (group_name, means) in enumerate(group_means.items()):
    ax.bar(x + i * width, means, width, label=str(group_name))
ax.set_xticks(x + width * (len(groups) - 1) / 2)
ax.set_xticklabels(variables, rotation=45, ha='right')
ax.set_ylabel('Mean Score')
ax.set_title('Group Means by Variable')
ax.legend()
plt.tight_layout()
path = 'your-project/output/quantitative-analysis/chart_group_means.png'
plt.savefig(path, dpi=150)
plt.show()
chart_paths.append(path)
```

**Heatmap** (for many variables × groups):
```python
import seaborn as sns

pivot = means_df  # variable × group DataFrame of means
fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(pivot, annot=True, fmt='.2f', cmap='YlOrRd', ax=ax)
ax.set_title('Mean Scores Heatmap')
plt.tight_layout()
path = 'your-project/output/quantitative-analysis/chart_heatmap.png'
plt.savefig(path, dpi=150)
plt.show()
chart_paths.append(path)
```

After generating: "Charts saved. Would you like to adjust anything — different variables, colour scheme, or chart type?"

---

## Phase 6: Regression Modelling

Run only if the user selected regression options.

For each regression model, ask:
- "What's the **dependent variable** (the outcome you want to predict)?"
- "What are the **independent variables** (predictors)?"
- "Which regression type: linear, logistic, or ordinal?"

```python
# Linear
reg_result = run_linear_regression(df, dependent_var=dv, independent_vars=ivs)

# Logistic
reg_result = run_logistic_regression(df, dependent_var=dv, independent_vars=ivs)

# Ordinal
reg_result = run_ordinal_regression(df, dependent_var=dv, independent_vars=ivs)
```

Show: coefficients, standard errors, p-values, R² or pseudo-R², and model summary.
Highlight statistically significant predictors (p < 0.05).

After each model: "Would you like to try a different set of predictors or a different model type?"

---

## Phase 6b: Named Analysis Patterns

These are reusable, purpose-specific analysis patterns that go beyond generic descriptives and tests. Run them when triggered by a survey handoff (Phase 0.5) or when the user's data structure matches the pattern. Each pattern produces a named, self-contained output block.

---

### Pattern 1: Satisfaction Driver Analysis + Priority Matrix

**When to use:** Surveys with an overall satisfaction item and multiple sub-dimension satisfaction items (e.g., Edge Mobile: overall satisfaction + performance, reliability, search, sync, ads blocker, privacy).

**Goal:** Identify which sub-dimensions have the highest leverage on overall satisfaction, then place each in a 2×2 priority matrix to guide improvement decisions.

**Steps:**

1. Confirm with user: "I'll run a satisfaction driver analysis — linear regression of the sub-dimensions on overall satisfaction, then plot each sub-dimension in a 2×2 priority matrix. Which column is the overall satisfaction item? Which are the sub-dimensions?"

2. Run regression:
```python
reg_result = run_linear_regression(df, dependent_var=overall_sat_col, independent_vars=sub_dim_cols)
```
Report: R², each predictor's β, p-value, significance flag.

3. Compute mean satisfaction score per sub-dimension:
```python
means = df[sub_dim_cols].mean()
```

4. Build the priority matrix table — for each sub-dimension, show: mean score, β, significance, and quadrant assignment:

```
Priority Matrix
──────────────────────────────────────────────────────────────
Sub-dimension     | Mean Score | β     | Sig | Quadrant
──────────────────────────────────────────────────────────────
Search            | 4.22       | 0.098 | **  | Improve First
Ads blocker       | 3.82       | 0.048 | n.s.| Improve Next
Performance       | 4.63       | 0.319 | **  | Enhance Strength
Reliability       | 4.66       | 0.201 | **  | Enhance Strength
Sync              | 4.39       | 0.131 | **  | Enhance Strength
Sign in           | 4.39       | 0.073 | n.s.| Maintain
Privacy & security| 4.33       | 0.001 | n.s.| Maintain
──────────────────────────────────────────────────────────────
```

**Quadrant rules:**
- **Improve First** — below-median satisfaction AND significant β (high impact, underperforming — highest ROI fix)
- **Enhance Strength** — above-median satisfaction AND significant β (performing well and impactful — protect and amplify)
- **Improve Next** — below-median satisfaction AND non-significant β (underperforming but lower direct impact)
- **Maintain** — above-median satisfaction AND non-significant β (performing well, lower direct impact)

Use the median of all sub-dimension means as the satisfaction split threshold. Use p < 0.05 as the significance split for β.

5. Optionally generate a scatter plot with sub-dimension labels:
```python
fig, ax = plt.subplots(figsize=(8, 6))
ax.scatter(means[sub_dim_cols], betas[sub_dim_cols])
for name in sub_dim_cols:
    ax.annotate(name, (means[name], betas[name]))
ax.axvline(x=means[sub_dim_cols].median(), color='gray', linestyle='--')
ax.axhline(y=0.05, color='gray', linestyle='--')  # or use β significance threshold
ax.set_xlabel('Mean Satisfaction Score')
ax.set_ylabel('Regression β (impact on overall satisfaction)')
ax.set_title('Satisfaction Driver Priority Matrix')
plt.tight_layout()
path = 'your-project/output/quantitative-analysis/chart_satisfaction_priority_matrix.png'
plt.savefig(path, dpi=150)
chart_paths.append(path)
```

**Output label:** "Satisfaction Driver Analysis complete. [N] sub-dimensions with significant β: [list]. Priority: Improve First → [list]; Enhance Strength → [list]."

---

### Pattern 2: MAU/DAU Estimation from Frequency Questions

**When to use:** Prioritization surveys where each item has a frequency-of-use question (Never / Occasionally / Monthly / Weekly / Daily or similar scale). Produces estimated monthly and daily active user percentages per item.

**Goal:** Convert frequency response distributions into MAU% and DAU% estimates per item, then rank items and validate against usefulness scores if available.

**Steps:**

1. Confirm with user: "I'll estimate MAU% and DAU% for each item from the frequency question. Which columns are the frequency items? What are the response labels? (I need to know which labels count as 'monthly or above' for MAU, and 'daily' for DAU.)"

2. For each frequency column (one per feature/item):
```python
def estimate_mau_dau(series, mau_labels, dau_labels):
    """
    mau_labels: list of response values that count toward MAU (e.g., ['Monthly', 'Weekly', 'Daily'])
    dau_labels: list of response values that count toward DAU (e.g., ['Daily'])
    Returns: mau_pct, dau_pct, mau_moe, n
    """
    n = series.notna().sum()
    mau_pct = series.isin(mau_labels).sum() / n
    dau_pct = series.isin(dau_labels).sum() / n
    # Margin of error at 90% confidence (z=1.645)
    mau_moe = 1.645 * (mau_pct * (1 - mau_pct) / n) ** 0.5
    return mau_pct, dau_pct, mau_moe, n
```

3. Build results table:
```
MAU/DAU Estimates
──────────────────────────────────────────────────────────────────────
Item              | Est. MAU% | MAU MOE (±) | Est. DAU% | n
──────────────────────────────────────────────────────────────────────
UV Index          | 24.1%     | ±3.8%       | 8.3%      | 349
Traffic Index     | 51.6%     | ±4.4%       | 18.9%     | 349
Umbrella Index    | 48.7%     | ±4.4%       | 14.9%     | 349
...
```

4. If a parallel usefulness/importance rating column exists for the same items, compute the correlation between usefulness score and MAU%:
```python
import scipy.stats as stats
r, p = stats.pearsonr(usefulness_scores, mau_pcts)
print(f"Usefulness × MAU correlation: r={r:.3f}, p={p:.3f}")
```
Report: "Usefulness and estimated MAU are [strongly / weakly] correlated (r=[value], p=[value]). Items with high usefulness but low MAU may face discoverability or adoption barriers."

5. Rank items by MAU% descending. Optionally flag items where usefulness rank and MAU rank diverge by more than 3 positions — these are candidates for adoption intervention.

**Output label:** "MAU/DAU Estimation complete. Top item by MAU: [name] ([pct]%). Usefulness × MAU correlation: r=[value]."

---

### Pattern 3: Growth Signal Detection via Behavioral Subgroup Chi-Square

**When to use:** User profile & growth surveys where behavioral subgroups (e.g., users who use the product for shopping, work, or sync) can be tested against engagement or loyalty outcomes.

**Goal:** Identify which behavioral subgroups show statistically significantly higher engagement, retention, or satisfaction — these are growth lever candidates.

**Steps:**

1. Confirm with user: "I'll test whether specific behavioral subgroups (e.g., shopping users, work users) show higher engagement or loyalty. Which columns define the behavioral subgroups? Which columns measure engagement / loyalty / satisfaction (the outcomes to test against)?"

2. For each behavioral indicator column (binary: user selected this behavior or not):
```python
# Create binary subgroup indicator
df['is_shopping_user'] = df['purposes'].str.contains('Shopping', na=False).astype(int)

# Chi-square test: behavioral subgroup × engagement outcome
chi2_result = run_chi_squared(df, variable=engagement_col, group_column='is_shopping_user')
```

3. Build a summary table of all behavioral subgroup tests:
```
Growth Signal Detection
──────────────────────────────────────────────────────────────────────────
Behavioral Subgroup   | Outcome Tested   | chi² | p     | V     | Signal?
──────────────────────────────────────────────────────────────────────────
Shopping users        | Usage frequency  | 12.3 | 0.002 | 0.18  | ✅ Yes
Shopping users        | Exclusive loyalty| 8.7  | 0.013 | 0.15  | ⚠️ Yes
Work users            | Usage frequency  | 4.1  | 0.043 | 0.10  | ⚠️ Yes
Sync-driven users     | Usage frequency  | 6.8  | 0.009 | 0.13  | ✅ Yes
Personal interest users| Satisfaction    | 1.2  | 0.274 | 0.06  | — No
──────────────────────────────────────────────────────────────────────────
```

4. For any significant result, also show the observed frequency breakdown (e.g., daily/weekly/monthly usage split between subgroup vs non-subgroup) to confirm the direction of the effect.

5. Apply the finding strength labels from Phase 5. Flag as "growth signal" any subgroup where at least two outcome tests are significant at p < 0.05.

**Output label:** "Growth signal detection complete. [N] subgroups flagged as growth signals: [list with strength labels]."

---

### Pattern 4: Format Confidence Gap Analysis

**When to use:** Generative surveys where the same item set appears in two parallel multi-select questions: (A) "What content is important to you?" and (B) "What content works well in [format]?" The gap between selection rates reveals where the format falls short.

**Goal:** For each item, compute the gap between importance% and format-suitability%. Large positive gaps identify design challenges — content users want that the format cannot yet deliver.

**Steps:**

1. Confirm with user: "I'll compute the format confidence gap. Which column (or set of one-hot encoded columns) represents importance? Which represents format suitability? They should cover the same items."

2. For each item, compute selection rates in both questions:
```python
items = [col for col in df.columns if col.startswith('important_')]
format_cols = [col.replace('important_', 'format_') for col in items]

gap_df = pd.DataFrame({
    'Item': [col.replace('important_', '') for col in items],
    'Important%': [df[col].mean() * 100 for col in items],
    'Format-Suitable%': [df[fcol].mean() * 100 for fcol in format_cols],
})
gap_df['Gap'] = gap_df['Important%'] - gap_df['Format-Suitable%']
gap_df = gap_df.sort_values('Gap', ascending=False)
```

3. Present the table sorted by gap descending:
```
Format Confidence Gap
──────────────────────────────────────────────────────────────────
Item                        | Important% | Format-Suitable% | Gap
──────────────────────────────────────────────────────────────────
Project updates             | 68%        | 44%              | +24% ⚠️ Design challenge
Summary/overview            | 55%        | 48%              | +7%
Key decisions/announcements | 72%        | 70%              | +2%
Action items/tasks          | 65%        | 64%              | +1%
Major discussion points     | 58%        | 58%              | 0%
──────────────────────────────────────────────────────────────────
```

4. Flag items with gap > 15 percentage points as design challenges. Recommend: either solve within the format (richer treatment) or link to supplemental artifacts for on-demand depth.

5. Optionally run a paired t-test on each item to test whether the difference between importance% and format-suitable% is statistically significant:
```python
for item, imp_col, fmt_col in zip(items, important_cols, format_cols):
    ttest_result = run_ttest_paired(df, variable_1=imp_col, variable_2=fmt_col)
```

**Output label:** "Format Confidence Gap complete. [N] items with gap > 15pp: [list]. These are the primary format design challenges."

---

### Pattern 5: Dual-Perspective Alignment Analysis

**When to use:** Generative surveys where the same multi-select battery is asked from two user roles — e.g., participant perspective and organizer perspective. Identifies where both roles agree (highest-confidence product bets) and where they diverge (design tensions).

**Goal:** For each item, compare selection rates between the two role groups. Items with high selection by both are confirmed needs; large divergences reveal where one role's goal conflicts with the other's.

**Steps:**

1. Confirm with user: "I'll compare the two perspectives. Which column identifies the role (participant vs organizer)? Or are the two perspectives separate question blocks covering the same items?"

2. If perspectives are separate columns (e.g., `participant_goal_*` vs `organizer_goal_*`), compute selection rates per item for each block. If they are the same question filtered by a role column, split the DataFrame by role and compute rates per group.

3. Build the alignment table:
```python
alignment = pd.DataFrame({
    'Item': item_names,
    'Participant%': participant_rates,
    'Organizer%': organizer_rates,
})
alignment['Divergence'] = (alignment['Participant%'] - alignment['Organizer%']).abs()
alignment['Alignment'] = alignment[['Participant%', 'Organizer%']].min(axis=1)
alignment = alignment.sort_values('Alignment', ascending=False)
```

4. Present the table and classify each item:
```
Dual-Perspective Alignment
──────────────────────────────────────────────────────────────────────────
Item                        | Participant% | Organizer% | Alignment | Tag
──────────────────────────────────────────────────────────────────────────
Key decisions/announcements | 72%          | 78%        | 72%       | ✅ Confirmed
Action items/tasks          | 65%          | 70%        | 65%       | ✅ Confirmed
Major discussion points     | 58%          | 62%        | 58%       | ✅ Confirmed
Project updates             | 68%          | 45%        | 45%       | ⚠️ Divergent
Summary/overview            | 55%          | 40%        | 40%       | ⚠️ Divergent
──────────────────────────────────────────────────────────────────────────
```

**Classification rules:**
- **✅ Confirmed** — both perspectives ≥ 50% AND divergence ≤ 15pp → build this first
- **⚠️ Divergent** — divergence > 20pp → explicit product decision needed about which role to optimize for
- **🔵 Partial** — one perspective ≥ 50%, other < 50% but divergence ≤ 20pp → worth building but lower confidence

5. If the same question was asked to both roles in a single survey (role is a column), run chi-square per item to test whether selection rate differs significantly across roles.

**Output label:** "Dual-Perspective Alignment complete. [N] confirmed items (both perspectives agree): [list]. [N] divergent items needing product decisions: [list]."

---

## Phase 7: Summary & Export

1. **Summary:** After all requested analyses, present a structured summary in three parts:

   **Part A — Finding verdicts table** (one row per tested variable):

   ```
   Variable           | p     | Effect | Strength    | Verdict
   ─────────────────────────────────────────────────────────────────────
   整体满意度          | 0.008 | η²=.14 | ✅ Strong   | Robust — act on this
   功能满意度          | 0.032 | η²=.07 | ⚠️ Moderate | Worth investigating
   性能满意度          | 0.210 | η²=.02 | — No diff   | No detectable difference
   工具偏好 (chi-sq)   | 0.041 | V=.28  | ⚠️ Moderate | Worth investigating
   ```

   Use the finding strength labels from Phase 5. If data constraints were noted in Step 1f, flag where they affect interpretation (e.g., "⚠️ Non-representative sample — treat with caution").

   **Part B — Grouped synthesis** (the story behind the numbers):

   Group variables that show the same directional pattern and explain what they mean together. Do not just list results independently.

   Format:
   > **Pattern 1 — [Theme name]:** [Variable A], [Variable B], and [Variable C] all show the same pattern: [Group X] consistently rates higher than [Group Y] (η² = .08–.14). Together, these suggest [interpretation].
   >
   > **Pattern 2 — [Theme name]:** ...
   >
   > **No clear pattern:** [Variable D] showed a significant difference (p=.03) but no other variables support a consistent story — treat as an isolated finding pending replication.

   **Part C — Confirmed findings vs areas to investigate:**

   Separate findings by confidence level so the user knows what to act on vs what to follow up:

   ```
   ✅ CONFIRMED FINDINGS (strong evidence — pre-highlighted for action):
     • [Finding with ✅ Strong label] — [one-line implication]

   ⚠️ AREAS TO INVESTIGATE (moderate/suggestive evidence):
     • [Finding with ⚠️ or 🔵 label] — [one-line implication, note limitation]

   📋 KEY CAVEATS:
     • [Any data constraints from Step 1f that affect interpretation]
     • [Multiple comparisons note if > 10 tests were run]
     • [Small effective n warnings for specific tests]
   ```

2. **Export language:** Before exporting, ask:
   > "The data is in [Chinese/original language]. Would you like to export in:
   > (A) Original language — keep all column names and values as-is
   > (B) English — auto-translate column names and categorical values to English (takes ~30 seconds)"

   → Wait for the user's choice.

   **If English (B):**
   ```python
   # Translate the topic raw data DataFrame
   raw_data_en, col_map, value_maps = translate_to_english(topic_df)

   # Apply the same column name mapping to analysis result DataFrames
   # so that the stats sheets use English headers too
   anova_df_en   = apply_column_map(anova_df,   col_map)
   tukey_dfs_en  = {col_map.get(k, k): apply_column_map(v, col_map)
                    for k, v in tukey_results.items()}
   # ... repeat for other result DataFrames
   ```
   Use the translated DataFrames in the export call below.
   If translation fails or times out, fall back to original language and warn the user.

3. **Export:** "Would you like to export the results to Excel? I'll create a multi-sheet workbook with:
   - One sheet per analysis type (ANOVA, Chi-Squared, etc.)
   - A Raw Data sheet with the topic's filtered data
   - A Charts sheet with all generated charts embedded"
   → Wait for confirmation before exporting.

   ```python
   export_to_excel(
       results={
           'Descriptive Summary': descriptive_df,
           'ANOVA Results': anova_df,
           'Tukey HSD': {var: tukey_df for var, tukey_df in tukey_results.items()},
           'Chi-Squared': chi2_df,
           'T-Tests': ttest_list,           # list of result dicts
           'Regression': regression_coef_df,
       },
       filepath='your-project/output/quantitative-analysis/quantitative_analysis_results.xlsx',
       charts=chart_paths,          # list of PNG paths from Phase 5b
       raw_data=topic_df,           # the filtered DataFrame for this topic
                                    # (or {topic_name: df} for multi-topic exports)
   )
   ```

   For multi-topic analyses, accumulate across topics:
   ```python
   raw_data_by_topic = {
       'Topic 1 — Satisfaction': topic1_df,
       'Topic 2 — Feature Usage': topic2_df,
   }
   export_to_excel(results, filepath, charts=chart_paths, raw_data=raw_data_by_topic)
   ```
   ```

3. **Optional: Qualitative Follow-up Handoff**

   If results include significant group differences or unexpected patterns that cannot be explained by the data alone, ask: "Would you like to plan qualitative follow-up interviews to explain these findings?"

   If yes, produce this block for `interview-research`:

   ```text
   Qualitative Follow-up Handoff for Interview Research
   - Study type: behavioral-why
   - Findings that need explanation: [list significant results with effect sizes]
   - Subgroup differences to probe: [which groups differ on which variables]
   - Interview goal: understand the mechanisms and reasons behind [specific quantitative pattern]
   - Suggested screener basis: [grouping variable values — e.g., recruit from Group A and Group B separately]
   - Suggested N: [2–4 participants per group minimum]
   ```

   Pass this to `interview-research`. It will accept it at Gate 0 as the research topic and target user definition.

---

## Phase 8: Next Steps (Iterative Loop)

After presenting the Phase 7 summary, always ask:

> "Based on these results, what would you like to do next?
> - **(A) Drill deeper** — run follow-up tests on a specific finding (e.g., Tukey HSD on a significant ANOVA, or filter to a subgroup)
> - **(B) Try a different angle** — re-run with a different grouping variable or a different set of variables
> - **(C) Add regression** — model which variables predict an outcome of interest
> - **(D) Run a named pattern** — satisfaction driver + priority matrix, MAU/DAU estimation, growth signal detection, format confidence gap, or dual-perspective alignment
> - **(E) Export and close** — export results to Excel and finish
> - **(F) Hand off to qualitative** — plan follow-up interviews to explain a finding"

For option A or B: return to Phase 3 with the existing encoded DataFrame — do not re-clean or re-encode. Re-select columns and grouping variable only.

For option C: proceed to Phase 6 with the existing encoded DataFrame.

For option D: proceed to Phase 6b with the existing encoded DataFrame. Ask which named pattern to run.

For option E: proceed to the export step in Phase 7.

For option F: produce the qualitative handoff block above and pass to `interview-research`.

---

## Important Notes

- **Always confirm before acting.** Present recommendations with reasoning, but let the user decide.
- **Effect sizes matter.** Always report effect sizes alongside p-values — a statistically significant result with a tiny effect size may not be practically meaningful.
- **Small cells for chi-squared:** Warn the user if any expected cell frequency is < 5, as this violates chi-squared assumptions.
- **不适用 (N/A) responses:** These are encoded as NaN, not 0. They are excluded from means, ANOVA, t-tests, and regression. Report N/A rates in the Phase 2 summary so the user knows how many respondents the question applied to.
- When displaying tables, use pandas DataFrames for clean formatting.
- If any library is missing, help the user install it: `pip install pandas numpy scipy matplotlib seaborn scikit-learn kmodes statsmodels pingouin openpyxl deep-translator`
- Save all results files to `your-project/output/quantitative-analysis/`. Create the folder if it doesn't exist.
- The baseline group (group 99, if present) represents the overall population for comparison.
- For **clustering-based group comparisons** (e.g., comparing clusters on statistical tests after running clustering), the user can bring a labeled dataset from the clustering-analysis skill into this workflow — the group column would be the cluster assignment column.

---

## Gotchas

Known failure modes — this section grows through testing.

- **Never state p-values or statistics from memory.** Always run the code and report the computed output. LLMs can hallucinate plausible-looking numbers that are wrong.
- **η² < 0.06 is a small effect** regardless of how low the p-value is. A p=0.0001 with η²=0.02 means the groups differ reliably but the practical magnitude is tiny. Always label it accordingly.
- **Multiple comparisons inflate false positives.** Running 20 ANOVA tests at p < 0.05 will produce ~1 false positive by chance. If > 10 tests are run, note this in the Phase 7 caveats and consider Bonferroni correction (divide α by the number of tests).
- **NaN exclusion silently shrinks n.** A column with 15% 不适用 responses runs ANOVA on 85% of the sample. Always report the effective n used for each test, not the total sample size.
- **Chi-squared assumes independent observations.** If the same respondent could appear in multiple groups (e.g., multi-select grouping variable), chi-squared is not valid.
- **Regression coefficients are associations, not causal effects.** Never interpret a significant predictor as "X causes Y" — only "X is associated with Y after controlling for other predictors in the model."
- **Unequal group sizes can affect ANOVA sensitivity.** Very large groups can drive significance even when the effect is small. Check group sizes and note large imbalances (e.g., one group 10×  another).
- **Ordinal regression requires at least 3 ordered outcome levels.** If the dependent variable has only 2 levels, use logistic regression instead.
- **Tukey HSD assumes equal variances across groups.** If groups have very different SDs (ratio > 3:1), note this as a caveat.
