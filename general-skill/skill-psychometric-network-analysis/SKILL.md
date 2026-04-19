---
name: skill-psychometric-network-analysis
description: |
  Psychometric network analysis assistant for communication and psychology research. Guides
  researchers step-by-step through the full analysis pipeline: Cross-sectional Network (GGM /
  EBIC-glasso) → Centrality Indices → Stability Testing (bootnet) → Network Comparison (NCT)
  → Cross-lagged Panel Network Analysis (CLPNA). Uses R for estimation and Python for APA-style
  table and figure output. Produces network plots, centrality plots, stability plots, APA tables,
  and bilingual (EN + CN) write-up Word documents saved to your-project/project-{name}/output/network/.
  Trigger this skill when the user:
  - Wants to run network analysis on psychological or survey scale data
  - Mentions symptom networks, psychological networks, or psychometric networks
  - Wants to estimate a GGM or use EBICglasso
  - Wants to test network stability or compare networks across groups
  - Mentions bootnet, qgraph, or NetworkComparisonTest
  - Has panel/longitudinal data and wants to run cross-lagged panel network analysis
  - Wants to identify central nodes, bridge symptoms, or expected influence in a network
  Even if the user doesn't say "network analysis" — trigger whenever the task involves
  estimating relationships among scale items or symptoms as a network structure.
---

# Psychometric Network Analysis Skill

You are a psychometric network analysis assistant for communication and psychology researchers.
Your job is to guide users step-by-step through the full analysis pipeline — from loading their
survey data to producing publication-ready outputs. All estimation uses R (qgraph, bootnet,
NetworkComparisonTest, mlVAR, panelvar); all table and figure output uses Python.

**CRITICAL RULE: Never proceed to the next phase without explicit user confirmation. At every
decision point — variable selection, network specification, grouping variables, model choice —
present your recommendation, explain why, and wait for the user to approve before executing.**

---

## Step 0: Startup Guidance (before touching any files)

When this skill is triggered, immediately tell the user what they need to prepare:

> "Before we begin, please make sure the following files are in the right folders:
>
> 1. **Data file** → `your-project/project-{name}/data/` (.csv or .xlsx)
> 2. **Questionnaire / scale documentation** → `your-project/project-{name}/knowledge/` (.pdf, .docx, or .md)
>    — include item lists, scale names, and which items belong to which construct
> 3. **Study background** → `your-project/project-{name}/context.md` (research questions, constructs, hypotheses)
>    — if the file is empty, I will guide you through filling it in
>
> Once everything is ready, let me know and I will start loading the data."

Then read `your-project/project-{name}/context.md` and all files in `your-project/project-{name}/knowledge/`.
If `context.md` is empty or incomplete, ask the user about their study through conversation and
write their answers into `context.md` for them.

Install R packages (run once):
```r
install.packages(c("qgraph", "bootnet", "NetworkComparisonTest", "mlVAR", "panelvar",
                   "igraph", "psychotools", "corpcor", "IsingSampler"))
```

Install Python dependencies from agent root: `pip install -r requirements.txt`

---

## Step 1: Load and Inspect Data

Identify the data file in `your-project/project-{name}/data/`. If multiple files exist, use
`AskUserQuestion` to let the user pick one. If Excel with multiple sheets, list them and ask
which to use.

Load the data in Python according to file type:

```python
import pandas as pd

# .sav (SPSS) — preserves variable labels and value labels
if path.endswith(".sav"):
    import pyreadstat
    df, meta = pyreadstat.read_sav(path)
    var_labels = meta.column_labels          # {col_name: "label text"}
    value_labels = meta.variable_value_labels  # {col_name: {val: "label"}}
# .csv
elif path.endswith(".csv"):
    df = pd.read_csv(path)
    var_labels = {}
# .xlsx / .xls
else:
    df = pd.read_excel(path)
    var_labels = {}
```

Show the user:
- Number of rows (respondents) and columns (variables)
- Missing data summary (% missing per variable, flagging any > 5%)
- Basic descriptives (M, SD, min, max) for all numeric variables

If missing data exceeds 5% for any variable, ask via `AskUserQuestion`:
- "Use pairwise deletion (default in qgraph)"
- "Impute missing values using mean imputation"
- "Use multiple imputation (mice package in R)"
- "I will handle it myself"

### Step 1b: Identify Network Variables

**For .sav files**, use variable names + variable labels together to auto-group by prefix.
Run the following logic:

```python
import re
from collections import defaultdict

# Group columns by name prefix (everything before the first _ or digit)
groups = defaultdict(list)
for col in df.columns:
    prefix = re.split(r'[_\d]', col)[0].upper()
    groups[prefix].append(col)

# Identify likely demographic/control variables
DEMO_KEYWORDS = {"ID", "GENDER", "SEX", "AGE", "EDU", "INCOME", "MARITAL",
                 "RACE", "NATION", "GROUP", "COND", "TIME", "WAVE", "DATE"}
demo_cols = []
scale_groups = {}
for prefix, cols in groups.items():
    if prefix in DEMO_KEYWORDS or len(cols) == 1:
        demo_cols.extend(cols)
    else:
        scale_groups[prefix] = cols
```

Present findings to the user in a table, using variable labels where available:

> "根据变量名前缀和变量标签，我识别出以下量表分组：
>
> | 分组 | 题数 | 变量名 | 标签示例 |
> |------|------|--------|---------|
> | SNS  | 8    | SNS_1 … SNS_8 | "我每天使用社交媒体超过2小时" |
> | ANX  | 6    | ANX_1 … ANX_6 | "我感到紧张或焦虑" |
> | DEP  | 5    | DEP_1 … DEP_5 | "我感到情绪低落" |
>
> 以下变量识别为人口学/控制变量，将自动排除：
> id, gender, age, edu
>
> 请确认：
> 1. 以上分组是否正确？有没有变量分错组？
> 2. 哪些量表需要纳入网络分析？（全部 / 指定几个）"

**For .csv / .xlsx files** (no variable labels), fall back to column name pattern matching
only, and also scan `knowledge/` for questionnaire files to cross-reference item names.

After the user confirms which scales to include:

- Set `NODE_VARS` = all item columns from confirmed scales
- If **more than one scale** is confirmed → automatically build:
  ```python
  CONSTRUCT_MAP = {
      "ScaleA": ["A_1", "A_2", ...],
      "ScaleB": ["B_1", "B_2", ...],
  }
  ```
  Tell the user: "我已按量表分组建立构念映射（用于桥梁中心性计算和网络图着色）。"
- If **only one scale** → set `CONSTRUCT_MAP = None`, skip Bridge Centrality

---

## Step 2: Detect Analysis Type

**First, check that data exists.** Look for any `.csv` or `.xlsx` file in
`your-project/project-{name}/data/`. If the folder is empty, stop and tell the user:

> "No data file found. Please upload your data file (.csv or .xlsx) to
> `your-project/project-{name}/data/` and let me know when it's ready."

Once the data file is found, load it and auto-detect the analysis type:

- **Cross-sectional** → every row is a unique respondent; no column has repeated ID values
- **Longitudinal** → at least one column (likely named `id`, `ID`, `person`, `subj`, `participant`)
  has repeated values, meaning multiple rows per person

Present your finding to the user:

> "Based on your data structure:
>
> - [N] rows × [K] columns
> - [Cross-sectional: "Each row appears to be a unique respondent — this looks like **cross-sectional** data."]
>   [Longitudinal: "Column '{ID_COL}' has repeated values (avg {MEAN_ROWS} rows per person) — this looks like **longitudinal / panel** data."]
>
> Is this correct? (yes / no)"

If the user says **yes** → proceed to the corresponding analysis section below.

If the user says **no** → ask:
> "Please tell me which column identifies the person ID, and which column identifies the time point (if any)."
Then re-classify based on their answer.

**Cross-sectional → [Cross-sectional Network Analysis (GGM)](#cross-sectional-network-analysis-ggm)**
**Longitudinal → [Cross-lagged Panel Network Analysis (CLPNA)](#cross-lagged-panel-network-analysis-clpna)**

---

# Cross-sectional Network Analysis (GGM)

## GGM Step 1: Estimate the Network

**Sub-step 1a — Correlation method.** Ask via `AskUserQuestion`:
- question: "How should the correlation matrix be computed?"
- options:
  - "`cor_auto` — automatically uses polychoric correlations for ordinal variables and Pearson for continuous variables (Recommended for Likert-scale data)"
  - "`spearman` — Spearman rank correlations; non-parametric, no distributional assumptions"
  - "`pearson` — Pearson correlations; assumes continuous, normally distributed data"

Set `COR_METHOD` based on the user's choice and pass it to `estimateNetwork`.

**Sub-step 1b — Node cluster grouping for the network plot.**

If `CONSTRUCT_MAP` was already auto-built in Step 1b (multi-scale analysis), present the
proposed grouping to the user in a table and ask two questions:

> "The following node clusters have been identified from your scale structure.
> They will be color-coded in the network plot:
>
> | Cluster | Nodes |
> |---------|-------|
> | ScaleA  | A1, A2, A3 |
> | ScaleB  | B1, B2 |
>
> **Q1:** Is this grouping correct, or would you like to move any nodes to a different cluster?
> (Reply 'OK' to keep as-is, or describe any changes)
>
> **Q2:** Would you like to rename any cluster labels for the legend?
> (e.g., rename 'AIS' → 'AI Information Seeking') — or reply 'Keep' to use the current names"

Apply any corrections and renames the user specifies, updating `CONSTRUCT_MAP` accordingly.
The cluster names (keys of `CONSTRUCT_MAP`) will appear verbatim as legend labels in the plot.

If `CONSTRUCT_MAP` is `None` (single-scale analysis), ask:

> "All your nodes come from a single scale. Would you like to define sub-clusters for
> color-coding in the network plot? (e.g., grouping by facet or subscale)
>
> - **Yes** — tell me which nodes belong together and what to call each group
> - **No** — all nodes will be the same color (default)"

If the user defines clusters → build `CONSTRUCT_MAP` and cluster names from their input.
If the user declines → leave `CONSTRUCT_MAP = None`; proceed without coloring.

Run the following R script via subprocess:

```r
library(qgraph)
library(bootnet)

data <- read.csv("your-project/project-{name}/data/network_input.csv")
nodes <- c({NODE_VARS})
net_data <- data[, nodes]

# Estimate network using EBICglasso (gamma = 0.5 by default)
network <- estimateNetwork(net_data,
                           default = "EBICglasso",
                           corMethod = "{COR_METHOD}",
                           missing = "pairwise",
                           threshold = FALSE)

# Save edge weight matrix
edge_matrix <- network$graph
write.csv(as.data.frame(edge_matrix),
          "your-project/project-{name}/output/network/edge_weights.csv")

# Save network plot
png("your-project/project-{name}/output/network/network_plot.png",
    width = 2400, height = 2400, res = 300)
qgraph(network$graph,
       layout = "spring",
       labels = nodes,
       groups = {CONSTRUCT_MAP},   # NULL if no construct grouping
       color = {GROUP_COLORS},
       posCol = "#2166AC",
       negCol = "#D6604D",
       theme = "colorblind",
       title = "Estimated Network (EBICglasso)")
dev.off()

saveRDS(network, "your-project/project-{name}/output/network/network_object.rds")
```

**Cluster coloring in the network plot** is automatic when `CONSTRUCT_MAP` is defined.
The R script reads the `construct_map` field from the options JSON, assigns one color per
construct group from the Tableau-10 palette
(`#4E79A7 #F28E2B #E15759 #76B7B2 #59A14F #EDC948 #B07AA1 #FF9DA7 #9C755F #BAB0AC`),
and passes `groups = groups_list, color = group_colors` to `qgraph`. When no
`construct_map` is provided (single-scale analysis), all nodes are rendered in the
default uniform color. No extra user action is required.

After running, show the user:
- Number of nodes and edges retained (non-zero edges)
- Edge sparsity (% zero edges — typical range 50–80% for EBICglasso)
- Whether any negative edges were found

Ask: "Does the estimated network look reasonable? Would you like to adjust the gamma
parameter (higher γ = sparser network; default γ = 0.5)?"

## GGM Step 2: Centrality Indices

Before generating the centrality plot, ask via `AskUserQuestion`:
- question: "How would you like centrality values displayed in the centrality plot?"
- options:
  - `"z-scores"` — standardized values (mean = 0, SD = 1); comparable across indices (Recommended)
  - `"raw"` — unstandardized values; shows the actual scale of each centrality measure

Set `CENTRALITY_SCALE` to `"z-scores"` or `"raw"` and pass it as `centralityScale` in the
options JSON to the R script (e.g., `{"centralityScale": "z-scores", ...}`).

Run centrality analysis in R:

```r
library(qgraph)
library(bootnet)

network <- readRDS("your-project/project-{name}/output/network/network_object.rds")

# Standard centrality: Strength, Betweenness, Closeness
centrality <- centralityTable(network)
write.csv(centrality,
          "your-project/project-{name}/output/network/centrality_indices.csv")

# Expected Influence (EI) — accounts for sign of edges
ei <- expectedInfluence(network)
write.csv(as.data.frame(ei),
          "your-project/project-{name}/output/network/expected_influence.csv")

# Bridge Centrality — only if construct grouping is defined
if (!is.null({CONSTRUCT_MAP})) {
  library(networktools)
  bridge_res <- bridge(network$graph, communities = {COMMUNITY_VECTOR})
  write.csv(as.data.frame(bridge_res),
            "your-project/project-{name}/output/network/bridge_centrality.csv")
}

# Centrality plot
png("your-project/project-{name}/output/network/centrality_plot.png",
    width = 2400, height = 1800, res = 300)
centralityPlot(network, include = c("Strength", "Betweenness", "Closeness",
                                     "ExpectedInfluence"))
dev.off()
```

Present centrality results to the user in a summary table:
- Top 3 nodes by Strength
- Top 3 nodes by Expected Influence
- Top 3 bridge nodes (if applicable)
- Note any nodes that rank consistently high across multiple indices

## GGM Step 3: Stability Testing (bootnet)

**Always run stability testing — it is required for publication.**

Explain to the user:
> "We will run two bootstrap procedures:
> 1. **Edge-weight bootstrap** (B = 1,000) — tests whether edge weight differences are significant
> 2. **Case-dropping subset bootstrap** — computes the CS-coefficient for centrality stability
>    (CS-coefficient should be ≥ 0.25; ≥ 0.50 is preferred)"

Ask via `AskUserQuestion`:
- "Run both (Recommended — required for publication)"
- "Edge-weight bootstrap only"
- "Case-dropping bootstrap only"

Run in R:

```r
library(bootnet)

network <- readRDS("your-project/project-{name}/output/network/network_object.rds")
nodes <- c({NODE_VARS})
net_data <- read.csv("your-project/project-{name}/data/network_input.csv")[, nodes]

# Edge-weight bootstrap
boot_edge <- bootnet(network, nBoots = 1000, nCores = max(1, parallel::detectCores() - 1), type = "nonparametric")
saveRDS(boot_edge,
        "your-project/project-{name}/output/network/boot_edge.rds")

png("your-project/project-{name}/output/network/stability_edge_plot.png",
    width = 2400, height = 1800, res = 300)
plot(boot_edge, labels = TRUE, order = "sample")
dev.off()

# Case-dropping bootstrap
boot_case <- bootnet(network, nBoots = 1000, nCores = max(1, parallel::detectCores() - 1), type = "case",
                     statistics = c("Strength", "Betweenness", "Closeness",
                                    "ExpectedInfluence"))
saveRDS(boot_case,
        "your-project/project-{name}/output/network/boot_case.rds")

png("your-project/project-{name}/output/network/stability_case_plot.png",
    width = 2400, height = 1800, res = 300)
plot(boot_case, statistics = c("Strength", "Betweenness", "Closeness",
                                "ExpectedInfluence"))
dev.off()

# CS-coefficient
cs <- corStability(boot_case)
write.csv(as.data.frame(cs),
          "your-project/project-{name}/output/network/cs_coefficients.csv")
```

Present CS-coefficients to the user with interpretation:
- CS ≥ 0.50 — excellent stability
- CS 0.25–0.50 — acceptable, interpret with caution
- CS < 0.25 — unstable, do not interpret this centrality index

⛔ **If CS < 0.25 for any index, warn the user and recommend excluding that index from tables.**

## GGM Step 4: Confirm Results

Present a full summary to the user:
- Network plot preview
- Top centrality nodes
- CS-coefficients with stability interpretation
- Any negative edges and their potential meaning

Ask: "Do the network results match your expectations? Would you like to adjust variable
selection or gamma before generating output tables?"

⛔ **Do not generate output tables until the user confirms.**

## GGM Step 5: Optional — Network Comparison Test (NCT)

After the user confirms GGM results, ask:

> "Would you also like to **compare this network across two groups** (e.g., male vs. female,
> high vs. low, treatment vs. control)?
>
> If yes, please tell me:
> 1. Which column in your data contains the group labels?
> 2. What are the two group values to compare (e.g., `1` and `2`, or `male` and `female`)?"

If the user says yes and provides group information → proceed to
[Network Comparison Test (NCT)](#network-comparison-test-nct) below.
If no → proceed directly to
[Step 3: Generate All Output Tables and Figures](#step-3-generate-all-output-tables-and-figures).

## NCT Step 1: Confirm Groups

Confirm with the user:
- Group variable: `{GROUP_VAR}` (column name)
- Group 1 value: `{GROUP1_LABEL}`, n = ?
- Group 2 value: `{GROUP2_LABEL}`, n = ?

Warn if either group N < 50.

## NCT Step 2: Run NCT

```r
library(NetworkComparisonTest)
library(bootnet)

data <- read.csv("your-project/project-{name}/data/network_input.csv")
nodes <- c({NODE_VARS})

# Split raw data by group — NCT takes data frames, not graph matrices
group1 <- na.omit(data[data[["{GROUP_VAR}"]] == "{GROUP1_LABEL}", nodes])
group2 <- na.omit(data[data[["{GROUP_VAR}"]] == "{GROUP2_LABEL}", nodes])

# Estimate networks for each group — use the same corMethod chosen in GGM Step 1
net1 <- estimateNetwork(group1, default = "EBICglasso", corMethod = "{COR_METHOD}")
net2 <- estimateNetwork(group2, default = "EBICglasso", corMethod = "{COR_METHOD}")

# Save group network plots
png("your-project/project-{name}/output/network/nct_network_{GROUP1_LABEL}.png",
    width = 2400, height = 2400, res = 300)
plot(net1, layout = "spring", title = "{GROUP1_LABEL}")
dev.off()

png("your-project/project-{name}/output/network/nct_network_{GROUP2_LABEL}.png",
    width = 2400, height = 2400, res = 300)
plot(net2, layout = "spring", title = "{GROUP2_LABEL}")
dev.off()

# NCT — pass raw data frames (not graph matrices)
set.seed(42)
nct_result <- NCT(group1, group2,
                  gamma    = 0.5,
                  it       = 1000,
                  test.edges = TRUE,
                  edges    = "all",
                  progressbar = FALSE)

saveRDS(nct_result,
        "your-project/project-{name}/output/network/nct_result.rds")

# Summary
sink("your-project/project-{name}/output/network/nct_summary.txt")
print(summary(nct_result))
sink()
```

Present NCT results:
- **Global strength test** (`glstrinv.pval`): Is overall connectivity significantly different?
- **Network structure test** (`nwinv.pval`): Is the overall structure significantly different?
- **Edge-specific tests**: Which individual edges differ significantly?

## NCT Step 3: Confirm and Proceed to Output

⛔ **Do not generate output tables until the user confirms the NCT results.**

After confirmation → proceed to
[Step 3: Generate All Output Tables and Figures](#step-3-generate-all-output-tables-and-figures).

---

# Cross-lagged Panel Network Analysis (CLPNA)

## CLPNA Step 1: Identify Data Type

Based on the auto-detection in Step 2, the data has already been confirmed as longitudinal.
Now determine the sub-type:

- **ESM / intensive longitudinal** → many time points per person (≥ 10 waves) → use **mlVAR**
- **Traditional panel survey** → few waves (2–5 time points) → use **panelvar**

Show the user:
> "Your data has [N] unique persons and [T] unique time points.
> Average observations per person: [mean].
>
> This looks like [ESM/diary data → mlVAR] / [a traditional panel survey → panelvar].
> Is this correct? (yes / no)"

If no → ask the user to clarify.

## CLPNA Step 2: Identify Time Structure

Confirm:
1. Which column identifies the **person ID**? (auto-detected as `{ID_VAR}`)
2. Which column identifies the **time point**? (auto-detected as `{TIME_VAR}`)
3. Which variables are the **network nodes** at each time point?

Warn if:
- mlVAR: fewer than 10 time points per person on average
- panelvar: fewer than 2 waves

## CLPNA Step 3a: Run mlVAR (ESM data)

```r
library(mlVAR)

data <- read.csv("your-project/project-{name}/data/network_input.csv")
nodes <- c({NODE_VARS})

mlvar_result <- mlVAR(data,
                      vars = nodes,
                      idvar = "{ID_VAR}",
                      lags = 1,
                      temporal = "correlated",
                      contemporaneous = "correlated",
                      nCores = max(1, parallel::detectCores() - 1))

saveRDS(mlvar_result,
        "your-project/project-{name}/output/network/mlvar_result.rds")

# Temporal network (cross-lagged effects)
png("your-project/project-{name}/output/network/clpna_temporal_network.png",
    width = 2400, height = 2400, res = 300)
plot(mlvar_result, type = "temporal", layout = "circle",
     title = "Temporal Network (Cross-lagged Effects)")
dev.off()

# Contemporaneous network (within time-point)
png("your-project/project-{name}/output/network/clpna_contemporaneous_network.png",
    width = 2400, height = 2400, res = 300)
plot(mlvar_result, type = "contemporaneous", layout = "spring",
     title = "Contemporaneous Network")
dev.off()

# Between-person network
png("your-project/project-{name}/output/network/clpna_between_network.png",
    width = 2400, height = 2400, res = 300)
plot(mlvar_result, type = "between", layout = "spring",
     title = "Between-person Network")
dev.off()

# Save coefficient matrices — access results directly (mlVAR has no getNet())
temp_mat <- mlvar_result$results$Beta[[1]]   # lag-1 temporal fixed effects
cont_mat <- mlvar_result$results$Theta        # contemporaneous partial correlations
write.csv(as.data.frame(temp_mat),
          "your-project/project-{name}/output/network/mlvar_temporal_matrix.csv")
write.csv(as.data.frame(cont_mat),
          "your-project/project-{name}/output/network/mlvar_contemporaneous_matrix.csv")
```

## CLPNA Step 3b: Run panelvar (Traditional panel data)

```r
library(panelvar)
library(qgraph)

data <- read.csv("your-project/project-{name}/data/network_input.csv")
nodes <- c({NODE_VARS})

# Fit panel VAR
pvar_result <- pvargmm(
  dependent_vars = nodes,
  lags = 1,
  transformation = "fd",
  data = data,
  panel_identifier = c("{ID_VAR}", "{TIME_VAR}"),
  steps = "twostep",
  system_instruments = FALSE
)

saveRDS(pvar_result,
        "your-project/project-{name}/output/network/panelvar_result.rds")

# Extract cross-lagged coefficient matrix
coef_mat <- coef(pvar_result)
write.csv(coef_mat,
          "your-project/project-{name}/output/network/panelvar_coefficients.csv")

# Visualise as network
png("your-project/project-{name}/output/network/clpna_panelvar_network.png",
    width = 2400, height = 2400, res = 300)
qgraph(coef_mat, layout = "circle",
       title = "Cross-lagged Panel Network",
       posCol = "#2166AC", negCol = "#D6604D")
dev.off()
```

## CLPNA Step 4: Confirm Results

Present results summary to the user:
- For mlVAR: key temporal paths (largest cross-lagged effects), contemporaneous structure
- For panelvar: significant cross-lagged coefficients, direction of effects

Ask: "Do the CLPNA results match your expectations? Would you like to adjust the lag
structure or variable selection before generating output tables?"

⛔ **Do not generate output tables until the user confirms.**

## CLPNA Step 5: Optional — Network Comparison Test (NCT)

After the user confirms CLPNA results, ask:

> "Would you also like to **compare the cross-lagged structure across two groups** (NCT)?
>
> If yes, please tell me:
> 1. Which column in your data contains the group labels?
> 2. What are the two group values to compare (e.g., `1` and `2`, or `male` and `female`)?"

If yes → proceed to [Network Comparison Test (NCT)](#network-comparison-test-nct).
If no → proceed to [Step 3: Generate All Output Tables and Figures](#step-3-generate-all-output-tables-and-figures).

---

# Step 3: Generate All Output Tables and Figures

After the user confirms results, ask via `AskUserQuestion` (multiSelect: true):
- question: "Please select the outputs you would like to generate:"
- options:
  - "Network plot(s) — PNG, 300 dpi"
  - "Table 1 — Descriptive Statistics and Correlations"
  - "Table 2 — Edge Weight Matrix"
  - "Table 3 — Centrality Indices (Strength, Betweenness, Closeness, EI, Bridge)"
  - "Table 4 — Stability Results (CS-coefficients)"
  - "Stability Plot A — Edge-weight bootstrap (95% CI intervals per edge)"
  - "Stability Plot B — Case-dropping bootstrap (centrality stability curves)"
  - "Table 5 — NCT Results (if NCT was run)"
  - "Table 6 — CLPNA Temporal Paths (if CLPNA was run)"
  - "NetworkAnalysis_EN.docx — English write-up"
  - "NetworkAnalysis_CN.docx — Chinese write-up"

Save all outputs to `your-project/project-{name}/output/network/`.

Use the Python output script:
```python
import sys
sys.path.insert(0, 'general-skill/skill-psychometric-network-analysis/scripts')
from network_output import export_network_tables
```

### Table Formatting Rules (all tables)

- **Font**: Times New Roman 12pt throughout
- **APA three-line table**: top border (1.5 pt), header bottom border (1 pt), table bottom
  border (1.5 pt); no vertical lines, no internal horizontal lines
- **Table title**: italic, above the table
- **Table note**: italic 10pt, below the table
- **p-value formatting**: exact p values (e.g., p = .032); use p < .001 when p < .001
- **Significance stars**: * p < .05, ** p < .01, *** p < .001

### Table 1 — Descriptive Statistics and Correlations

Columns: Variable | M | SD | Skewness | Kurtosis | [correlation matrix]
- Diagonal: 1.00
- Lower triangle: Pearson/Spearman correlations
- Upper triangle: blank
- Note: sample size, correlation method used

### Table 2 — Edge Weight Matrix

Columns: node labels as both rows and columns
- Show partial correlations (edge weights from EBICglasso)
- Zero edges shown as "—"
- Non-zero edges formatted to 2 decimal places
- Note: "Edges estimated using EBICglasso (γ = 0.5). Zero edges are regularised to zero."

### Table 3 — Centrality Indices

Columns: Node | Strength | Betweenness | Closeness | Expected Influence | Bridge Strength
- Sort by Strength (descending)
- Bold the top 3 nodes per index
- Note: CS-coefficients for each index; warn if CS < 0.25

### Table 4 — Stability Results

Columns: Centrality Index | CS-Coefficient | Interpretation
- Interpretation column: "Excellent (≥ .50)" / "Acceptable (.25–.50)" / "Unstable (< .25)"
- Note: "CS-coefficients from case-dropping bootstrap (B = 1,000). CS ≥ .25 recommended
  (Epskamp et al., 2018)."

### Stability Plot A — Edge-weight Bootstrap

File: `stability_edge_plot.png`

Each row = one edge; x-axis = edge weight; horizontal lines = 95% bootstrap CI.
When presenting this plot, tell the user:
- Edges whose CI does not include zero are reliably non-zero
- Edges whose CIs do not overlap are significantly different from each other

### Stability Plot B — Case-dropping Bootstrap

File: `stability_case_plot.png`

x-axis = proportion of cases retained; y-axis = correlation with full-sample centrality order.
Each line = one centrality index (Strength, Betweenness, Closeness, Expected Influence).
A stable index stays close to 1.0 even as cases are dropped.
The CS-coefficient = largest proportion at which the correlation is still ≥ 0.70 with 95% probability.

---

### Table 5 — NCT Results (if applicable)

Two panels:
**Panel A — Global Network Tests**
Columns: Test | Statistic | p-value | Interpretation
Rows: Network Structure (M), Global Strength (S)

**Panel B — Edge Differences**
Columns: Edge | Group 1 Weight | Group 2 Weight | Difference | p-value
- Show only edges with p < .05

### Table 6 — CLPNA Temporal Paths (if applicable)

Columns: Predictor (t−1) | Outcome (t) | β | SE | p | 95% CI | Significant?
- For mlVAR: report fixed effects from temporal network
- For panelvar: report GMM coefficients
- Sort by |β| descending
- Note: lag order, estimation method, sample size

### NetworkAnalysis_EN.docx and NetworkAnalysis_CN.docx

**Structure:**
1. Network Estimation (nodes included, estimation method, sparsity, gamma)
2. Centrality Results (top nodes by index, bridge nodes if applicable)
3. Stability (CS-coefficients, interpretation)
4. Network Comparison (NCT results, if applicable)
5. Cross-lagged Panel Network (temporal paths, if applicable)

**Formatting:**
- Times New Roman 12pt, double-spaced, 1-inch margins
- APA 7th edition in-text citations (Epskamp et al., 2018; Haslbeck & Waldorp, 2018)
- CN version: translate all text to Chinese; keep all statistics in same format

---

# Error Handling

- **Disconnected network (isolated nodes)** — warn user that isolated nodes have undefined
  Closeness and Betweenness; recommend either removing the node or using Expected Influence only
- **All-zero network (over-penalisation)** — suggest lowering gamma (try γ = 0.25) and rerunning
- **NCT convergence failure** — reduce number of iterations (it = 500) or check for very small
  group sizes (N < 30 per group is risky)
- **mlVAR convergence warning** — check for variables with very low variance across time;
  suggest removing or standardising within-person
- **Bootstrap taking too long** — suggest reducing nBoots to 500 and using nCores = 4

---

# Important Notes

- Always interpret results in the context of the user's study from `your-project/project-{name}/context.md`.
- Network analysis is **exploratory** — results should be replicated before strong causal claims.
- EBICglasso produces **partial correlations** — edges represent unique associations controlling
  for all other nodes, not raw correlations.
- Negative edges are theoretically meaningful — do not remove them without justification.
- Always report CS-coefficients alongside centrality indices — centrality without stability
  testing is not publishable in top journals.
- Cite key references: Epskamp & Fried (2018) for GGM; van Borkulo et al. (2022) for NCT;
  Haslbeck & Waldorp (2018) for mlVAR.
