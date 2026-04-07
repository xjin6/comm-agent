# Quantitative Analysis

> **v0.1.0** · Updated 2026-03-31 · `analysis`

End-to-end interactive inferential statistics for survey and tabular data. Guides through data cleaning, variable encoding, hypothesis tests, regression modelling, and Excel export — with user confirmation at every decision point.

## Features

- **Descriptive statistics** — means, SDs, frequencies, missing data summary
- **Hypothesis tests** — ANOVA + Tukey HSD, t-tests (independent/paired), chi-squared
- **Regression** — linear, logistic, and ordinal regression with effect sizes
- **Visualisation** — group mean charts, heatmaps, priority matrices
- **Excel export** — multi-sheet workbook with results, charts, and raw data

## Output

All results saved to `your-project/output/quantitative-analysis/`:

| File | Description |
|------|-------------|
| `quantitative_analysis_results.xlsx` | Multi-sheet workbook with all results and embedded charts |
| `results.docx` | APA-format Word document — Times New Roman 12pt, three-line tables |
| `chart_group_means.png` | Group comparison bar chart |
| `chart_heatmap.png` | Correlation/response heatmap |

## Quick Start

1. Place your data in `your-project/data/` (CSV or Excel)
2. Tell the agent: *"Run stats on my survey data"* or *"Compare groups on satisfaction"*

The agent will guide you through each phase interactively — it always presents recommendations and waits for your approval before running anything.

## Workflow Phases

| Phase | What happens |
|-------|-------------|
| 0 — Scoping | Understand your research questions before touching data |
| 1 — Load | Load data, review columns and sample size |
| 2 — Clean | Handle missing values, filter rows, drop irrelevant columns |
| 3 — Encode | Recode Likert scales, ordinal variables, multi-select columns |
| 4 — Describe | Descriptive statistics and frequency tables |
| 5 — Test | ANOVA, t-tests, chi-squared based on variable types |
| 6 — Regression | Linear, logistic, or ordinal regression |
| 7 — Export | Results and charts to Excel |

## Core Library

| Script | Description |
|--------|-------------|
| `scripts/quantitative_core.py` | Data loading, encoding, and all statistical analysis functions |
| `scripts/word_export.py` | APA three-line table Word export — Times New Roman 12pt, three-line borders |

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

## License

CC BY-NC-ND 4.0
