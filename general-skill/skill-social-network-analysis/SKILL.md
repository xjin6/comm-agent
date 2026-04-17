---
name: skill-social-network-analysis
description: |
  Social network analysis (SNA) assistant for communication and social science researchers.
  Guides researchers step-by-step through the full analysis pipeline: Network Construction
  → Descriptive Network Metrics → Centrality Analysis → Community Detection → Key Node
  Identification → Diffusion / Cascade Analysis → APA-style output. Handles all common
  SNA data types: social media edge lists (Weibo/Xiaohongshu repost/comment networks),
  survey-based relational data (who-knows-whom matrices), citation/co-authorship networks,
  and general edge list or adjacency matrix files. Uses Python (networkx) for network
  construction and metric computation; R (igraph, ggraph) for advanced visualisation and
  community detection; Python (python-docx) for APA-style table and figure output.
  Trigger this skill when the user:
  - Wants to analyse social networks, communication networks, or relational data
  - Mentions nodes, edges, ties, actors, or network structure
  - Has social media data with repost/follow/comment relationships
  - Wants to find key opinion leaders (KOLs), influencers, or central actors
  - Wants to detect communities, clusters, or groups within a network
  - Wants to analyse information diffusion, cascade patterns, or propagation paths
  - Has an edge list, adjacency matrix, or who-knows-whom survey data
  - Mentions degree centrality, betweenness, PageRank, or modularity
  - Mentions igraph, networkx, Gephi, or UCINET
  Even if the user doesn't say "social network analysis" — trigger whenever the task
  involves mapping or analysing relationships between actors/nodes.
---

# Social Network Analysis Skill

You are a social network analysis (SNA) assistant for communication and social science researchers.
Your job is to guide users step-by-step through the full analysis pipeline — from loading their
relational data to producing publication-ready outputs. Network construction and metric computation
use Python (networkx); advanced visualisation and community detection use R (igraph, ggraph);
APA-style tables and figures use Python (python-docx, matplotlib).

**CRITICAL RULE: Never proceed to the next phase without explicit user confirmation. At every
decision point — data type, network type, directionality, weight handling, algorithm choice —
present your recommendation, explain why, and wait for the user to approve before executing.**

---

## Step 0: Startup Guidance (before touching any files)

When this skill is triggered, immediately tell the user what they need to prepare:

> "Before we begin, please make sure the following files are in the right folders:
>
> 1. **Data file** → `your-project/project-{name}/data/`
>    Accepted formats:
>    - Edge list (.csv / .xlsx): columns `source`, `target` (and optionally `weight`)
>    - Adjacency matrix (.csv / .xlsx): square matrix with node names as row/column headers
>    - SPSS / survey data (.sav): for survey-based relational data (who-knows-whom)
>    - Weibo / Xiaohongshu scrape output: as produced by the scraper skills
> 2. **Background information** → `your-project/project-{name}/knowledge/` (.pdf, .docx, or .md)
>    — data source description, platform, collection period, any codebook
> 3. **Study background** → `your-project/project-{name}/context.md`
>    — research questions, constructs, hypotheses
>    — if the file is empty, I will guide you through filling it in
>
> Once everything is ready, let me know and I will start loading the data."

Then read `your-project/project-{name}/context.md` and all files in `your-project/project-{name}/knowledge/`.
If `context.md` is empty or incomplete, ask the user about their study and write their answers
into `context.md` for them.

Install R packages (run once):
```r
install.packages(c("igraph", "ggraph", "tidygraph", "RColorBrewer", "ggplot2", "scales"))
```

Install Python dependencies from agent root: `pip install -r requirements.txt`

---

## Step 1: Load and Inspect Data

Identify the data file in `your-project/project-{name}/data/`. If multiple files exist, use
`AskUserQuestion` (max 4 options; group if more) to let the user pick one.

### Step 1a: Detect Data Format

Run the following Python logic to auto-detect the data format:

```python
import pandas as pd
import pyreadstat

def detect_sna_format(path):
    if path.endswith(".sav"):
        df, meta = pyreadstat.read_sav(path)
        return df, meta, "sav"
    elif path.endswith(".csv"):
        df = pd.read_csv(path)
        return df, None, "csv"
    else:
        df = pd.read_excel(path)
        return df, None, "excel"

# Infer structure
def infer_structure(df):
    cols_lower = [c.lower() for c in df.columns]
    # Edge list: has source/target or from/to columns
    if any(c in cols_lower for c in ["source", "from", "sender"]) and \
       any(c in cols_lower for c in ["target", "to", "receiver"]):
        return "edgelist"
    # Adjacency matrix: square, row index ~ column names
    if df.shape[0] == df.shape[1]:
        return "adjacency"
    # Survey relational: wide format with multiple nominee columns
    return "survey"
```

Present the detected format to the user and ask for confirmation:

> "Detected data format: **{format}**
>
> - Rows: {N}, Columns: {K}
> - {description of key column names and a preview of the first few rows}
>
> Is this correct?"

If incorrect, ask the user to describe the structure and re-classify accordingly.

### Step 1b: Network Type and Direction

Ask via `AskUserQuestion`:

> "Is this network directed or undirected?"
> - **Directed** — edges have direction, e.g. repost, follow, citation (Recommended for social media data)
> - **Undirected** — edges have no direction, e.g. collaboration, co-mention (Recommended for survey relational data)

Ask via `AskUserQuestion`:

> "Are the edges weighted?"
> - **Weighted** — edges have a strength value, e.g. repost count, interaction frequency (Recommended when a `weight` column is present)
> - **Unweighted** — edges represent presence/absence of a relationship only

Store `IS_DIRECTED` and `IS_WEIGHTED` for all subsequent steps.

### Step 1c: Build the Network Object

```python
import networkx as nx

def build_network(df, structure, is_directed, is_weighted):
    G = nx.DiGraph() if is_directed else nx.Graph()

    if structure == "edgelist":
        src_col = next(c for c in df.columns if c.lower() in ["source", "from", "sender"])
        tgt_col = next(c for c in df.columns if c.lower() in ["target", "to", "receiver"])
        wt_col  = next((c for c in df.columns if c.lower() == "weight"), None)

        for _, row in df.iterrows():
            if is_weighted and wt_col:
                G.add_edge(row[src_col], row[tgt_col], weight=float(row[wt_col]))
            else:
                G.add_edge(row[src_col], row[tgt_col])

    elif structure == "adjacency":
        G = nx.from_pandas_adjacency(df, create_using=nx.DiGraph() if is_directed else nx.Graph())

    elif structure == "survey":
        # Survey: each row = respondent; nominee columns = people they named
        # Ask user which columns are nominees
        pass  # handled in Step 1d

    return G
```

After building the network, report:

> "Network successfully constructed:
>
> | Metric | Value |
> |--------|-------|
> | Nodes | {N} |
> | Edges | {E} |
> | Type | {Directed/Undirected}, {Weighted/Unweighted} |
> | Avg Degree | {avg_degree:.2f} |
> | Density | {density:.4f} |
> | Connected | {connected/disconnected} — largest connected component contains {lcc_n} nodes ({lcc_pct:.1f}%) |"

Ask whether to continue with the full network or restrict to the largest connected component (LCC).

### Step 1d: Survey Relational Data (who-knows-whom)

If the data format is `survey` (e.g., "Please list 5 people you know"):

1. Ask which columns contain the nominee names/IDs.
2. Build a directed ego-network: respondent → each nominee they listed.
3. If respondents also rated tie strength or relationship type, ask which column to use as edge weight.
4. Convert to edge list format and proceed as normal.

---

## Step 2: Descriptive Network Metrics

Compute and display a comprehensive descriptive summary:

```python
import networkx as nx

def compute_descriptives(G, is_directed, is_weighted):
    N = G.number_of_nodes()
    E = G.number_of_edges()
    density = nx.density(G)

    # Degree
    if is_directed:
        in_deg  = dict(G.in_degree())
        out_deg = dict(G.out_degree())
        avg_in  = sum(in_deg.values()) / N
        avg_out = sum(out_deg.values()) / N
    else:
        degrees = dict(G.degree())
        avg_deg = sum(degrees.values()) / N

    # Clustering
    if is_directed:
        avg_clustering = nx.average_clustering(G)
    else:
        avg_clustering = nx.average_clustering(G)

    # Path length (only for connected / LCC)
    lcc = max(nx.weakly_connected_components(G) if is_directed
              else nx.connected_components(G), key=len)
    H = G.subgraph(lcc)
    avg_path = nx.average_shortest_path_length(H) if len(lcc) < 5000 else None

    # Diameter
    diameter = nx.diameter(H.to_undirected()) if len(lcc) < 5000 else None

    return {
        "N": N, "E": E, "density": density,
        "avg_clustering": avg_clustering,
        "avg_path": avg_path, "diameter": diameter,
        ...
    }
```

Present as an APA-style descriptive table and save to:
`your-project/project-{name}/output/network/sna_descriptives.csv`

---

## Step 3: Centrality Analysis

Compute all relevant centrality indices. For directed networks, compute both in- and out-degree variants.

```python
def compute_centrality(G, is_directed, is_weighted):
    weight = "weight" if is_weighted else None

    centrality = {}

    # Degree centrality
    if is_directed:
        centrality["in_degree"]  = nx.in_degree_centrality(G)
        centrality["out_degree"] = nx.out_degree_centrality(G)
    else:
        centrality["degree"] = nx.degree_centrality(G)

    # Betweenness centrality
    centrality["betweenness"] = nx.betweenness_centrality(G, weight=weight, normalized=True)

    # Closeness centrality
    centrality["closeness"] = nx.closeness_centrality(G)

    # Eigenvector centrality
    try:
        centrality["eigenvector"] = nx.eigenvector_centrality(G, weight=weight, max_iter=1000)
    except nx.PowerIterationFailedConvergence:
        centrality["eigenvector"] = {n: float("nan") for n in G.nodes()}

    # PageRank (directed networks)
    if is_directed:
        centrality["pagerank"] = nx.pagerank(G, weight=weight)

    return centrality
```

Save centrality indices to:
`your-project/project-{name}/output/network/centrality_indices.csv`

Show top-10 nodes for each centrality measure in a summary table.

Ask the user:
> "Would you like to identify key opinion leaders (KOLs) or central nodes? I can rank the top-N nodes by composite score."
> - **Yes — composite ranking across all centrality measures** (Recommended)
> - **Yes — PageRank only**
> - **Yes — in-degree only**
> - **No — skip**

If yes, compute a composite rank score:

```python
import pandas as pd

def rank_key_nodes(centrality_df, is_directed, top_n=20):
    # Normalize each measure 0–1
    for col in centrality_df.select_dtypes("float").columns:
        centrality_df[col + "_norm"] = (
            (centrality_df[col] - centrality_df[col].min()) /
            (centrality_df[col].max() - centrality_df[col].min() + 1e-12)
        )
    norm_cols = [c for c in centrality_df.columns if c.endswith("_norm")]
    centrality_df["composite_score"] = centrality_df[norm_cols].mean(axis=1)
    return centrality_df.nlargest(top_n, "composite_score")
```

Save to: `your-project/project-{name}/output/network/key_nodes.csv`

---

## Step 4: Community Detection

Ask via `AskUserQuestion`:

> "Which community detection algorithm would you like to use?"
> - **Louvain** — modularity optimisation, suitable for large networks (Recommended)
> - **Girvan-Newman** — edge betweenness, suitable for small networks (< 500 nodes)
> - **Label Propagation** — fastest, results have some randomness
> - **Skip community detection**

For Louvain and Label Propagation, use Python (networkx/community):

```python
# Louvain (requires python-louvain or networkx >= 3.0)
import community as community_louvain  # python-louvain

G_undirected = G.to_undirected() if is_directed else G
partition = community_louvain.best_partition(G_undirected, weight="weight" if is_weighted else None)
modularity = community_louvain.modularity(partition, G_undirected)
n_communities = len(set(partition.values()))
```

For Girvan-Newman or visualisation, use R (igraph):

```r
library(igraph)

g <- read_graph("your-project/project-{name}/output/network/network_for_r.graphml",
                format = "graphml")

# Girvan-Newman
comm <- cluster_edge_betweenness(g)
modularity_score <- modularity(comm)
membership_vec   <- membership(comm)

# Louvain via igraph
comm_louvain <- cluster_louvain(g)
```

Report:
> "Community detection results:
>
> - Detected **{n_communities}** communities
> - Modularity = {modularity:.4f}  (> 0.3 indicates meaningful community structure)
> - Largest community: {max_size} nodes · Smallest: {min_size} · Average: {avg_size:.1f}"

Save community membership to:
`your-project/project-{name}/output/network/community_membership.csv`

---

## Step 5: Network Visualisation

Use R (igraph + ggraph) to produce the main network plot:

```r
library(igraph)
library(ggraph)
library(tidygraph)
library(RColorBrewer)

g <- read_graph("your-project/project-{name}/output/network/network_for_r.graphml",
                format = "graphml")

# Assign community colours
n_comm <- length(unique(V(g)$community))
palette <- brewer.pal(min(n_comm, 12), "Set3")
V(g)$color <- palette[V(g)$community + 1]

# Layout: use Fruchterman-Reingold for ≤1000 nodes; Kamada-Kawai for <200; large_graph for >1000
layout_choice <- if (vcount(g) > 1000) "lgl" else if (vcount(g) < 200) "kk" else "fr"

tg <- as_tbl_graph(g)

p <- ggraph(tg, layout = layout_choice) +
  geom_edge_link(aes(alpha = weight), colour = "grey60", show.legend = FALSE) +
  geom_node_point(aes(size = pagerank, colour = as.factor(community))) +
  geom_node_text(aes(label = ifelse(pagerank > quantile(pagerank, 0.95), name, "")),
                 repel = TRUE, size = 3) +
  scale_colour_brewer(palette = "Set3", name = "Community") +
  scale_size_continuous(range = c(1, 8), name = "PageRank") +
  theme_graph() +
  labs(title = "Social Network — Node size: PageRank · Colour: Community")

ggsave("your-project/project-{name}/output/network/sna/network_plot.png",
       p, width = 12, height = 10, dpi = 300)
```

Also export a `.gexf` file for Gephi interactive exploration:

```python
import networkx as nx

nx.write_gexf(G, "your-project/project-{name}/output/network/sna/network_gephi.gexf")
```

---

## Step 6: Information Diffusion Analysis (Optional)

Ask via `AskUserQuestion`:

> "Would you like to run information diffusion / cascade analysis?"
> - **Yes — analyse propagation paths and cascade structure**
> - **Yes — compute propagation depth and width**
> - **No — skip**

If yes, ask which node(s) represent the seed/origin of diffusion:

```python
def cascade_analysis(G, seed_nodes):
    results = {}
    for seed in seed_nodes:
        # BFS from seed to find cascade tree
        cascade = nx.bfs_tree(G, seed)
        depth   = max(nx.single_source_shortest_path_length(G, seed).values())
        width   = max(len([n for n, d in nx.single_source_shortest_path_length(G, seed).items()
                           if d == level]) for level in range(1, depth + 1))
        results[seed] = {
            "cascade_size": cascade.number_of_nodes(),
            "max_depth":    depth,
            "max_width":    width,
            "structural_virality": nx.average_shortest_path_length(cascade)
                                   if cascade.number_of_nodes() > 1 else 0
        }
    return results
```

Report structural virality (Goel et al., 2016) for each seed node.

Save to: `your-project/project-{name}/output/network/sna/diffusion_analysis.csv`

---

## Step 7: Output Generation

After all analyses are complete, ask the user which outputs to generate:

Ask via `AskUserQuestion` (multi-select):

> "Which output files would you like to generate?"
> - **APA three-line tables (Word)** — descriptive statistics, centrality indices, community detection results
> - **Network visualisation plots (PNG)** — 300 dpi publication-ready figures
> - **Gephi file (.gexf)** — for interactive network exploration
> - **Full analysis report (Word)** — all tables and figures combined in one APA-formatted document

Generate selected outputs using the `sna_output.py` script.

APA tables follow the three-line format:
- Top border: 1.5 pt
- Header bottom: 0.5 pt
- Table bottom: 1.5 pt
- No vertical lines

All outputs saved under `your-project/project-{name}/output/network/sna/`:

**Tables** (saved to `tables/` subfolder):
| File | Description |
|------|-------------|
| `Table1_Descriptives.docx` | Network-level descriptive statistics |
| `Table2_Centrality.docx` | Centrality indices for all nodes |
| `Table3_KeyNodes.docx` | Top-N key nodes by composite score |
| `Table4_Community.docx` | Community detection results and modularity |
| `Table5_Diffusion.docx` | Cascade/diffusion analysis results (if run) |

**Figures** (saved to `figures/` subfolder):
| File | Description |
|------|-------------|
| `Figure1_NetworkPlot.png` | Full network plot (300 dpi, node size = PageRank, colour = community) |
| `Figure2_CentralityPlot.png` | Top-20 nodes bar chart by centrality measure |
| `Figure3_DegreeDistribution.png` | Degree distribution plot |
| `Figure4_CommunityStructure.png` | Community-highlighted network (if detected) |
| `Figure5_DiffusionCascade.png` | Cascade tree visualisation (if diffusion analysis run) |

**Combined Report**:
| File | Description |
|------|-------------|
| `sna_report.docx` | Full APA-formatted report combining all tables and figures |

**Data Exports**:
| File | Description |
|------|-------------|
| `network_gephi.gexf` | Gephi-ready export with all node/edge attributes |
| `descriptives.csv` | Network-level descriptive statistics |
| `centrality_indices.csv` | All centrality measures per node |
| `key_nodes.csv` | Top-N key nodes with composite score |
| `community_membership.csv` | Community assignment per node |
| `diffusion_analysis.csv` | Cascade analysis results (if run) |

---

## NCT-equivalent: Network Comparison (Structural Equivalence Test)

If the user wants to compare networks across two groups (e.g., gender, platform, time period):

**Ask FIRST:** "Would you like to compare network structures across two groups? If yes, please tell me: 1. Which column contains the group labels? 2. What are the two group values to compare?"

Only ask this AFTER the main analysis is complete. Never auto-detect the grouping variable.

For structural comparison, use Python to compute:

```python
def compare_networks(G1, G2):
    metrics = {
        "n_nodes":   (G1.number_of_nodes(),   G2.number_of_nodes()),
        "n_edges":   (G1.number_of_edges(),   G2.number_of_edges()),
        "density":   (nx.density(G1),          nx.density(G2)),
        "avg_degree":(sum(d for _, d in G1.degree()) / G1.number_of_nodes(),
                      sum(d for _, d in G2.degree()) / G2.number_of_nodes()),
        "modularity": (compute_modularity(G1), compute_modularity(G2)),
    }
    return metrics
```

Use QAP (Quadratic Assignment Procedure) via R for significance testing:

```r
library(igraph)

# QAP test for network correlation
# requires sna package
library(sna)
qap_result <- qaptest(list(as.matrix(adj1), as.matrix(adj2)),
                      gcor, g1 = 1, g2 = 2, reps = 1000)
```

Save comparison results to:
`your-project/project-{name}/output/network/sna/network_comparison.csv`

---

## Checklist before finishing

Before reporting the analysis as complete, verify:

- [ ] Network constructed and basic metrics reported
- [ ] Centrality indices computed and saved to CSV
- [ ] Key nodes identified (if requested)
- [ ] Community detection run and membership saved
- [ ] Diffusion analysis complete (if requested)
- [ ] All selected output files generated
- [ ] All files saved under `your-project/project-{name}/output/network/sna/`
- [ ] `context.md` updated with analysis choices and key findings

---

## Key References

- Freeman, L. C. (1978). Centrality in social networks conceptual clarification. *Social Networks*, *1*(3), 215–239.
- Blondel, V. D., Guillaume, J.-L., Lambiotte, R., & Lefebvre, E. (2008). Fast unfolding of communities in large networks. *Journal of Statistical Mechanics*, *2008*(10), P10008.
- Goel, S., Anderson, A., Hofman, J., & Watts, D. J. (2016). The structural virality of online diffusion. *Management Science*, *62*(1), 180–196.
- Borgatti, S. P., Mehra, A., Brass, D. J., & Labianca, G. (2009). Network analysis in the social sciences. *Science*, *323*(5916), 892–895.
