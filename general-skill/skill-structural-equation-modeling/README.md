# Structural Equation Modeling

> **v0.4.0** · Updated 2026-04-17 · `analysis`

A step-by-step SEM assistant for communication researchers. Covers EFA, CFA, full latent variable SEM, mediation, and moderation analysis using Python. Produces APA-style tables, static AMOS-style path diagrams, and an interactive HTML viewer.

## Features

- **EFA** — Exploratory factor analysis with parallel analysis, scree plot, Cronbach's α
- **CFA** — Confirmatory factor analysis with full fit evaluation and modification indices
- **Full SEM** — Latent variable structural model combining measurement + structural paths
- **Mediation** — Indirect effects with bootstrap confidence intervals
- **Moderation** — Interaction effects with simple slopes and Johnson-Neyman interval
- **Interactive diagram** — Drag-and-drop HTML viewer with mode/coefficient toggles and PNG export

## Output

All results saved under `your-project/project-{name}/output/sem/`:

**EFA** (`output/sem/efa/`)

| File | Description |
|------|-------------|
| `efa_loadings.csv` / `efa_loadings_table.xlsx` | Full factor loading matrix (APA-formatted) |
| `scree_plot.png` | Scree plot for each construct analyzed |

**CFA** (`output/sem/cfa/`)

| File | Description |
|------|-------------|
| `cfa_fit_indices.csv` | χ², df, CFI, TLI, RMSEA |
| `cfa_loadings.xlsx` | Standardized factor loadings (β, SE, p) |
| `cfa_path_diagram.png` / `.html` | Path diagram — static and interactive |

**Full SEM / Mediation / Moderation** (`output/sem/<model_name>/`)

| File | Description |
|------|-------------|
| `indirect_bootstrap.csv` | Raw bootstrap results for indirect effects |
| `Figure1_ConceptualModel.png` | Conceptual path diagram (300 dpi) |
| `Figure2_InteractionPlot.png` | Simple slopes interaction plot (300 dpi) |
| `Table1_Demographics.docx` | Sample demographics (APA three-line) |
| `Table2_Reliability.docx` | Descriptive statistics, reliability, convergent validity, latent correlations |
| `Table3_CompetingModels.docx` | Competing measurement models (discriminant validity) |
| `Table4_StructuralPaths.docx` | Structural model path coefficients |
| `Table5_IndirectEffects.docx` | Bootstrapped indirect effects (B = 5,000) |
| `Table6_Moderation.docx` | Hierarchical OLS regression + simple slopes |
| `DataAnalysis_EN.docx` | Full English results write-up (APA 7th) |
| `DataAnalysis_CN.docx` | Full Chinese results write-up |

## Quick Start

1. Place your data in `your-project/project-{name}/data/` (CSV or Excel)
2. Place questionnaire/scale docs in `your-project/project-{name}/knowledge/`
3. Describe your study in `your-project/project-{name}/context.md` (or let the agent fill it in)
4. Install dependencies: `pip install -r requirements.txt`
5. Tell the agent: *"Run SEM on my survey data"* or *"I need to do CFA and mediation analysis"*

The agent guides you interactively through each phase — it always presents recommendations and waits for your approval before running anything.

## Workflow Phases

| Phase | What happens |
|-------|-------------|
| 0 — Startup | File check, load context and knowledge, identify control variables |
| 1 — Load | Load data, review columns, sample size, missing data |
| 2 — Entry Point | Choose: EFA / CFA / Mediation / Moderation |
| EFA | Parallel analysis, scree plot, factor loadings, Cronbach's α |
| CFA | Full measurement model, fit indices, MI optimization loop, AVE/CR |
| Mediation | PROCESS-style model templates, bootstrap indirect effects (B = 5,000) |
| Moderation | Two-step hierarchical OLS, simple slopes, optional LMS robustness check |
| 4 — Labeling | Set full names and abbreviations for constructs |
| 5 — Output | Select tables, figures, and write-up documents to generate |

## Core Scripts

| Script | Description |
|--------|-------------|
| `scripts/load_data.py` | Load CSV/Excel, print descriptives and missing data summary |
| `scripts/efa_analysis.py` | EFA with parallel analysis, scree plot, and Cronbach's α |
| `scripts/sem_analysis.py` | CFA (with MI optimization), full SEM, mediation (bootstrap), moderation (hierarchical OLS) |
| `scripts/interactive_diagram.py` | Generate interactive Cytoscape.js HTML path diagram |

## Interactive Diagram

Open `sem_interactive.html` in any browser:

- **Click a construct** → direction picker appears (↑↓←→ + Auto) to rotate items around the oval
- **Full Model / Structural Only** toggle — show/hide items and error terms
- **β Standardized / B Unstandardized** toggle — switch all edge labels live
- **Drag constructs** — items and errors move with them
- **Export PNG** — downloads current view at 2.5× resolution

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

**Sha Sarah QIU** · sarahq2025@gmail.com

## License

CC BY-NC-ND 4.0
