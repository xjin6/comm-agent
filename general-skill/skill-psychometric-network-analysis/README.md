# Psychometric Network Analysis

> **v0.1.0** · Updated 2026-04-17 · `analysis`

A step-by-step psychometric network analysis assistant for communication and psychology researchers. Covers cross-sectional GGM estimation, centrality indices, stability testing, network comparison (NCT), and cross-lagged panel network analysis (CLPNA). Uses R for estimation and Python for APA-style output.

## Features

- **Cross-sectional Network (GGM)** — EBICglasso estimation, spring-layout visualisation, edge weight matrix
- **Centrality Indices** — Strength, Betweenness, Closeness, Expected Influence, Bridge Centrality
- **Stability Testing** — Edge-weight bootstrap + case-dropping bootstrap, CS-coefficients (bootnet)
- **Network Comparison (NCT)** — Global structure and strength tests, edge-specific comparisons across two groups
- **Cross-lagged Panel Network (CLPNA)** — mlVAR for ESM/diary data; panelvar for traditional panel surveys
- **APA output** — Three-line Word tables, bilingual EN/CN write-up documents, 300 dpi network plots

## Output

All results saved under `your-project/project-{name}/output/network/`:

**Cross-sectional Network**

| File | Description |
|------|-------------|
| `network_plot.png` | Spring-layout network plot (300 dpi) |
| `centrality_plot.png` | Centrality index bar chart |
| `stability_edge_plot.png` | Edge-weight bootstrap plot |
| `stability_case_plot.png` | Case-dropping stability plot |
| `edge_weights.csv` | Full edge weight matrix |
| `centrality_indices.csv` | All centrality indices per node |
| `expected_influence.csv` | Expected Influence values |
| `bridge_centrality.csv` | Bridge centrality (if construct groups defined) |
| `cs_coefficients.csv` | CS-coefficients from case-dropping bootstrap |
| `network_object.rds` | Saved R network object for further analysis |

**Network Comparison (NCT)**

| File | Description |
|------|-------------|
| `nct_network_{group}.png` | Network plot per group (300 dpi) |
| `nct_result.rds` | Saved NCT result object |
| `nct_summary.txt` | NCT summary output |

**Cross-lagged Panel Network (CLPNA)**

| File | Description |
|------|-------------|
| `clpna_temporal_network.png` | Temporal (cross-lagged) network — mlVAR |
| `clpna_contemporaneous_network.png` | Contemporaneous network — mlVAR |
| `clpna_between_network.png` | Between-person network — mlVAR |
| `clpna_panelvar_network.png` | Cross-lagged panel network — panelvar |
| `mlvar_temporal_matrix.csv` | Temporal coefficient matrix |
| `mlvar_contemporaneous_matrix.csv` | Contemporaneous coefficient matrix |
| `panelvar_coefficients.csv` | GMM coefficient matrix |

**APA Tables** (saved to `tables/` subfolder)

| File | Description |
|------|-------------|
| `Table1_EdgeWeights.docx` | Non-zero edge weights sorted by absolute weight |
| `Table2_Centrality.docx` | Centrality indices (Strength, Betweenness, Closeness, EI) |
| `Table3_ExpectedInfluence.docx` | Expected Influence 1-step and 2-step raw values |
| `Table4_BridgeCentrality.docx` | Bridge centrality (if construct groups defined) |
| `Table5_Stability.docx` | CS-coefficients with stability interpretation |
| `Table6_NCT.docx` | Network comparison test results (if NCT was run) |

**Figures** (saved to `figures/` subfolder)

| File | Description |
|------|-------------|
| `Figure1_NetworkPlot.png` | Spring-layout network plot (300 dpi) |
| `Figure2_CentralityPlot.png` | Centrality index bar chart |
| `Figure3_StabilityEdge.png` | Edge-weight bootstrap plot |
| `Figure4_StabilityCase.png` | Case-dropping stability plot |
| `Figure5_NCT_Group1.png` | Network plot — Group 1 (if NCT was run) |
| `Figure6_NCT_Group2.png` | Network plot — Group 2 (if NCT was run) |

**Combined Report**

| File | Description |
|------|-------------|
| `network_analysis_report.docx` | Full APA-formatted report combining all tables and figures |

## Quick Start

1. Place your data in `your-project/project-{name}/data/` (CSV or Excel)
2. Place questionnaire/scale docs in `your-project/project-{name}/knowledge/`
3. Install R packages (run once):
   ```r
   install.packages(c("qgraph", "bootnet", "NetworkComparisonTest",
                      "mlVAR", "panelvar", "networktools"))
   ```
4. Install Python dependencies: `pip install -r requirements.txt`
5. Tell the agent: *"Run network analysis on my survey data"* or *"I want to estimate a GGM"*

The agent guides you interactively — it always presents recommendations and waits for your approval before running anything.

## Workflow Phases

| Phase | What happens |
|-------|-------------|
| 0 — Startup | File check, read context.md and knowledge files |
| 1 — Load | Load data, identify node variables, handle missing data |
| 2 — Entry Point | Choose: Cross-sectional / NCT / CLPNA |
| GGM | EBICglasso estimation, edge weight matrix, network plot |
| Centrality | Strength, Betweenness, Closeness, Expected Influence, Bridge |
| Stability | Edge-weight bootstrap + case-dropping bootstrap, CS-coefficients |
| NCT | Per-group networks, global strength test, edge-specific comparisons |
| CLPNA | mlVAR (ESM) or panelvar (panel survey), temporal + contemporaneous networks |
| 3 — Output | Select tables, figures, and write-up documents to generate |

## Core Scripts

| Script | Description |
|--------|-------------|
| `scripts/network_analysis.R` | GGM estimation, centrality, stability, NCT, CLPNA |
| `scripts/network_output.py` | APA three-line Word tables, Excel export, bilingual write-up |

## Key References

- Epskamp, S., & Fried, E. I. (2018). A tutorial on regularized partial correlation networks. *Psychological Methods*, *23*(4), 617–634.
- van Borkulo, C. D., et al. (2022). Comparing network structures on three aspects: A permutation test. *Psychological Methods*, *27*(6), 1033–1043.
- Haslbeck, J. M. B., & Waldorp, L. J. (2018). How well do network models predict observations? On the importance of predictability in network models. *Behavior Research Methods*, *50*(2), 853–861.

## Author

**Sha Qiu** (@sarahqiu-lab) · sarahq2025@gmail.com


## License

CC BY-NC-ND 4.0
