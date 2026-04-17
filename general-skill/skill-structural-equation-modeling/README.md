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

All results saved to `your-project/project-{name}/output/sem/`:

| File | Description |
|------|-------------|
| `sem_structural.png` | Clean publication-ready structural model (constructs only) |
| `sem_path_diagram.png` | Full AMOS-style diagram with items, error terms, β, SE |
| `sem_interactive.html` | Interactive viewer — drag nodes, toggle modes, export PNG |
| `sem_structural_paths.xlsx` | APA-formatted structural path table |
| `sem_fit_indices.csv` | Model fit summary (χ², CFI, TLI, RMSEA) |

## Quick Start

```bash
# Install dependencies (from agent root)
pip install -r requirements.txt

# Run SEM
python general-skill/skill-structural-equation-modeling/scripts/sem_analysis.py \
  --file "your-project/project-{name}/data/survey.xlsx" \
  --model-type sem \
  --model "
Factor1 =~ item1 + item2 + item3
Factor2 =~ item4 + item5 + item6
Factor2 ~ Factor1
" \
  --output-dir "your-project/project-{name}/output/sem/my_model"
```

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/load_data.py` | Load CSV/Excel, print descriptives and missing data |
| `scripts/efa_analysis.py` | Run EFA with parallel analysis and scree plot |
| `scripts/sem_analysis.py` | CFA, full SEM, mediation, moderation |
| `scripts/interactive_diagram.py` | Generate interactive Cytoscape.js HTML diagram |

## Interactive Diagram

Open `sem_interactive.html` in any browser:

- **Click a construct** → direction picker appears (↑↓←→ + Auto) to rotate items around the oval
- **Full Model / Structural Only** toggle — show/hide items and error terms
- **β Standardized / B Unstandardized** toggle — switch all edge labels live
- **Drag constructs** — items and errors move with them
- **Export PNG** — downloads current view at 2.5× resolution

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

## License

CC BY-NC-ND 4.0
