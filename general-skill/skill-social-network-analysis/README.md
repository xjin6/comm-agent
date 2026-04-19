# Social Network Analysis

> **v0.1.0** · Updated 2026-04-17 · `analysis`

A step-by-step social network analysis assistant for communication and social science researchers. Covers network construction from all common data formats, descriptive metrics, centrality analysis, community detection, key node (KOL) identification, information diffusion/cascade analysis, and network comparison. Uses Python (networkx) for computation and R (igraph, ggraph) for visualisation, with APA-style Word output.

## Features

- **Network Construction** — Handles edge lists, adjacency matrices, survey relational data (who-knows-whom), and social media scrape output (Weibo/Xiaohongshu). Directed/undirected, weighted/unweighted.
- **Descriptive Metrics** — Nodes, edges, density, average degree, clustering coefficient, average path length, diameter
- **Centrality Analysis** — Degree (in/out), Betweenness, Closeness, Eigenvector, PageRank
- **Key Node Identification** — Composite ranking across centrality measures; KOL/influencer extraction
- **Community Detection** — Louvain, Girvan-Newman, Label Propagation; modularity score
- **Diffusion / Cascade Analysis** — BFS cascade trees, depth, width, structural virality (Goel et al., 2016)
- **Network Comparison** — Structural metrics comparison across two groups; QAP significance test
- **APA output** — Three-line Word tables, 300 dpi network plots, Gephi `.gexf` export

## Output

All results saved under `your-project/project-{name}/output/network/sna/`:

**Tables** (saved to `tables/` subfolder)

| File | Description |
|------|-------------|
| `Table1_Descriptives.docx` | Network-level descriptive statistics |
| `Table2_Centrality.docx` | Centrality indices for all nodes |
| `Table3_KeyNodes.docx` | Top-N key nodes by composite score |
| `Table4_Community.docx` | Community detection results and modularity |
| `Table5_Diffusion.docx` | Cascade/diffusion analysis results (if run) |

**Figures** (saved to `figures/` subfolder)

| File | Description |
|------|-------------|
| `Figure1_NetworkPlot.png` | Full network plot (300 dpi, node size = PageRank, colour = community) |
| `Figure2_CentralityPlot.png` | Top-20 nodes bar chart by centrality measure |
| `Figure3_DegreeDistribution.png` | Degree distribution plot |
| `Figure4_CommunityStructure.png` | Community-highlighted network (if detected) |
| `Figure5_DiffusionCascade.png` | Cascade tree visualisation (if diffusion analysis run) |

**Combined Report**

| File | Description |
|------|-------------|
| `sna_report.docx` | Full APA-formatted report combining all tables and figures |

**Data Exports**

| File | Description |
|------|-------------|
| `network_gephi.gexf` | Gephi-ready export with all node/edge attributes |
| `descriptives.csv` | Network-level descriptive statistics |
| `centrality_indices.csv` | All centrality measures per node |
| `key_nodes.csv` | Top-N key nodes with composite score |
| `community_membership.csv` | Community assignment per node |
| `diffusion_analysis.csv` | Cascade analysis results (if run) |

## Quick Start

1. Place your data in `your-project/project-{name}/data/` (edge list CSV, adjacency matrix, `.sav`, or scraper output)
2. Place any codebook or data documentation in `your-project/project-{name}/knowledge/`
3. Install R packages (run once):
   ```r
   install.packages(c("igraph", "ggraph", "tidygraph", "RColorBrewer", "ggplot2", "scales", "sna"))
   ```
4. Install Python dependencies: `pip install -r requirements.txt`
5. Tell the agent: *"Run social network analysis on my data"* or *"I want to find key opinion leaders in this network"*

The agent guides you interactively — it always presents recommendations and waits for your approval before running anything.

## Supported Data Formats

| Format | Description |
|--------|-------------|
| Edge list CSV | Columns: `source`, `target` (optional: `weight`) |
| Adjacency matrix CSV | Square matrix, node names as row/column headers |
| SPSS `.sav` | Survey-based relational data (who-knows-whom) |
| Weibo scraper output | Repost/comment network from `skill-weibo-topic-scraper` |
| Xiaohongshu scraper output | Comment/interaction network from `skill-xiaohongshu-search-scraper` |

## Workflow Phases

| Phase | What happens |
|-------|-------------|
| 0 — Startup | File check, read context.md and knowledge files |
| 1 — Load | Detect data format, build network object, report basic stats |
| 2 — Descriptives | Density, clustering, path length, diameter |
| 3 — Centrality | Degree, Betweenness, Closeness, Eigenvector, PageRank |
| 4 — Community | Louvain / Girvan-Newman / Label Propagation, modularity |
| 5 — Visualisation | ggraph network plot, degree distribution, community plot |
| 6 — Diffusion | Cascade trees, depth/width, structural virality (optional) |
| 7 — Output | Tables, figures, Gephi export, combined report |

## Core Scripts

| Script | Description |
|--------|-------------|
| `scripts/sna_analysis.R` | igraph network construction, community detection, QAP test, ggraph plots |
| `scripts/sna_output.py` | APA three-line Word tables, centrality CSV export, Gephi .gexf export |

## Key References

- Freeman, L. C. (1978). Centrality in social networks conceptual clarification. *Social Networks*, *1*(3), 215–239.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, *2008*(10), P10008.
- Goel, S., Anderson, A., Hofman, J., & Watts, D. J. (2016). The structural virality of online diffusion. *Management Science*, *62*(1), 180–196.
- Borgatti, S. P., Mehra, A., Brass, D. J., & Labianca, G. (2009). Network analysis in the social sciences. *Science*, *323*(5916), 892–895.

## Author

**Sha Qiu** (@sarahqiu-lab) · sarahq2025@gmail.com

## License

CC BY-NC-ND 4.0
