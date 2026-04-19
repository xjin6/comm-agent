#!/usr/bin/env Rscript
# sna_analysis.R — Social Network Analysis: igraph construction, community detection,
#                   QAP test, and ggraph visualisation
# Called by the SNA skill with substituted parameters.

suppressPackageStartupMessages({
  library(igraph)
  library(ggraph)
  library(tidygraph)
  library(ggplot2)
  library(RColorBrewer)
  library(scales)
})

# ---------------------------------------------------------------------------
# Parameters (substituted by the skill at runtime)
# ---------------------------------------------------------------------------
GRAPHML_PATH  <- "{GRAPHML_PATH}"   # input: network exported from Python as GraphML
OUTPUT_DIR    <- "{OUTPUT_DIR}"     # e.g. your-project/project-{name}/output/network/sna
LAYOUT        <- "{LAYOUT}"         # "fr" | "kk" | "lgl" | "auto"
IS_DIRECTED   <- {IS_DIRECTED}      # TRUE / FALSE
IS_WEIGHTED   <- {IS_WEIGHTED}      # TRUE / FALSE
COMM_METHOD   <- "{COMM_METHOD}"    # "louvain" | "edge_betweenness" | "label_prop" | "none"
RUN_QAP       <- {RUN_QAP}         # TRUE / FALSE
GRAPHML_PATH2 <- "{GRAPHML_PATH2}"  # second network for comparison (if RUN_QAP)
TOP_N_LABELS  <- {TOP_N_LABELS}     # number of top nodes to label (by pagerank)

dir.create(file.path(OUTPUT_DIR, "figures"), recursive = TRUE, showWarnings = FALSE)

# ---------------------------------------------------------------------------
# 1. Load network
# ---------------------------------------------------------------------------
g <- read_graph(GRAPHML_PATH, format = "graphml")
cat(sprintf("Loaded network: %d nodes, %d edges\n", vcount(g), ecount(g)))

# Auto-select layout if "auto"
if (LAYOUT == "auto") {
  LAYOUT <- if (vcount(g) > 1000) "lgl" else if (vcount(g) < 200) "kk" else "fr"
  cat(sprintf("Auto-selected layout: %s\n", LAYOUT))
}

# ---------------------------------------------------------------------------
# 2. Centrality (computed in Python; igraph recomputes for plotting)
# ---------------------------------------------------------------------------
if (IS_DIRECTED) {
  V(g)$in_degree  <- degree(g, mode = "in")
  V(g)$out_degree <- degree(g, mode = "out")
  V(g)$pagerank   <- page_rank(g, weights = if (IS_WEIGHTED) E(g)$weight else NA)$vector
} else {
  V(g)$degree   <- degree(g)
  V(g)$pagerank <- page_rank(g, weights = if (IS_WEIGHTED) E(g)$weight else NA)$vector
}
V(g)$betweenness <- betweenness(g, weights = if (IS_WEIGHTED) E(g)$weight else NA, normalized = TRUE)

# ---------------------------------------------------------------------------
# 3. Community Detection
# ---------------------------------------------------------------------------
if (COMM_METHOD != "none") {
  g_ud <- if (IS_DIRECTED) as.undirected(g, mode = "collapse") else g

  comm <- switch(COMM_METHOD,
    louvain         = cluster_louvain(g_ud,
                        weights = if (IS_WEIGHTED && !is.null(E(g_ud)$weight)) E(g_ud)$weight else NA),
    edge_betweenness= cluster_edge_betweenness(g_ud),
    label_prop      = cluster_label_prop(g_ud),
    stop(paste("Unknown community method:", COMM_METHOD))
  )

  mod_score <- modularity(comm)
  n_comm    <- length(comm)
  cat(sprintf("Community detection (%s): %d communities, modularity = %.4f\n",
              COMM_METHOD, n_comm, mod_score))

  V(g)$community <- membership(comm)

  # Save membership
  mem_df <- data.frame(node = V(g)$name, community = V(g)$community)
  write.csv(mem_df, file.path(OUTPUT_DIR, "community_membership_r.csv"), row.names = FALSE)

  # Save modularity
  cat(sprintf("modularity,%.6f\nn_communities,%d\n", mod_score, n_comm),
      file = file.path(OUTPUT_DIR, "community_stats.txt"))

} else {
  V(g)$community <- 1
  n_comm <- 1
}

# ---------------------------------------------------------------------------
# 4. Network Plot (Figure1)
# ---------------------------------------------------------------------------
palette <- if (n_comm <= 12) brewer.pal(max(3, n_comm), "Set3") else
           colorRampPalette(brewer.pal(12, "Set3"))(n_comm)

# Identify top nodes to label
pr_vals   <- V(g)$pagerank
threshold <- sort(pr_vals, decreasing = TRUE)[min(TOP_N_LABELS, length(pr_vals))]
V(g)$label_text <- ifelse(pr_vals >= threshold, V(g)$name, "")

tg <- as_tbl_graph(g)

size_aes <- if (IS_DIRECTED) "pagerank" else "pagerank"
edge_aes  <- if (IS_WEIGHTED && !is.null(E(g)$weight)) aes(alpha = weight) else aes()

p_network <- ggraph(tg, layout = LAYOUT) +
  geom_edge_link(edge_aes, colour = "grey70", arrow = if (IS_DIRECTED)
    grid::arrow(length = unit(2, "mm"), type = "closed") else NULL,
    end_cap = circle(2, "mm"), show.legend = FALSE) +
  geom_node_point(aes(size = pagerank, colour = as.factor(community))) +
  geom_node_text(aes(label = label_text), repel = TRUE, size = 2.5, colour = "black") +
  scale_colour_manual(values = palette, name = "Community") +
  scale_size_continuous(range = c(1, 8), name = "PageRank") +
  theme_graph(base_family = "sans") +
  labs(title = "Social Network",
       subtitle = sprintf("N = %d nodes, E = %d edges · Layout: %s · Communities: %d",
                          vcount(g), ecount(g), LAYOUT, n_comm))

ggsave(file.path(OUTPUT_DIR, "figures", "Figure1_NetworkPlot.png"),
       p_network, width = 12, height = 10, dpi = 300)
cat("Saved Figure1_NetworkPlot.png\n")

# ---------------------------------------------------------------------------
# 5. Degree Distribution Plot (Figure3)
# ---------------------------------------------------------------------------
deg_vec <- if (IS_DIRECTED) degree(g, mode = "in") else degree(g)
deg_df  <- data.frame(degree = deg_vec)

p_deg <- ggplot(deg_df, aes(x = degree)) +
  geom_histogram(bins = 30, fill = "#4292C6", colour = "white") +
  scale_x_continuous(name = if (IS_DIRECTED) "In-Degree" else "Degree") +
  scale_y_continuous(name = "Count") +
  theme_classic(base_size = 13) +
  labs(title = "Degree Distribution")

ggsave(file.path(OUTPUT_DIR, "figures", "Figure3_DegreeDistribution.png"),
       p_deg, width = 8, height = 5, dpi = 300)
cat("Saved Figure3_DegreeDistribution.png\n")

# ---------------------------------------------------------------------------
# 6. Community Structure Plot (Figure4) — only if communities detected
# ---------------------------------------------------------------------------
if (COMM_METHOD != "none" && n_comm > 1) {
  p_comm <- ggraph(tg, layout = LAYOUT) +
    geom_edge_link(colour = "grey80", alpha = 0.4, show.legend = FALSE) +
    geom_node_point(aes(colour = as.factor(community), size = pagerank)) +
    scale_colour_manual(values = palette, name = "Community") +
    scale_size_continuous(range = c(1, 6), guide = "none") +
    theme_graph(base_family = "sans") +
    labs(title = "Community Structure",
         subtitle = sprintf("Modularity = %.4f · %d communities", mod_score, n_comm))

  ggsave(file.path(OUTPUT_DIR, "figures", "Figure4_CommunityStructure.png"),
         p_comm, width = 12, height = 10, dpi = 300)
  cat("Saved Figure4_CommunityStructure.png\n")
}

# ---------------------------------------------------------------------------
# 7. QAP Network Comparison (optional)
# ---------------------------------------------------------------------------
if (RUN_QAP && GRAPHML_PATH2 != "") {
  if (!requireNamespace("sna", quietly = TRUE)) {
    stop("Package 'sna' is required for QAP. Install with: install.packages('sna')")
  }
  library(sna)

  g2  <- read_graph(GRAPHML_PATH2, format = "graphml")
  adj1 <- as.matrix(as_adjacency_matrix(g,  sparse = FALSE))
  adj2 <- as.matrix(as_adjacency_matrix(g2, sparse = FALSE))

  # Align node sets
  all_nodes <- union(rownames(adj1), rownames(adj2))
  expand_adj <- function(adj, nodes) {
    m <- matrix(0, nrow = length(nodes), ncol = length(nodes),
                dimnames = list(nodes, nodes))
    m[rownames(adj), colnames(adj)] <- adj
    m
  }
  adj1 <- expand_adj(adj1, all_nodes)
  adj2 <- expand_adj(adj2, all_nodes)

  qap_res <- qaptest(list(adj1, adj2), gcor, g1 = 1, g2 = 2, reps = 1000)
  cat(sprintf("QAP: r = %.4f, p (one-tail) = %.4f\n", qap_res$testval, qap_res$pgreq))

  qap_df <- data.frame(
    statistic = "QAP_correlation",
    r         = round(qap_res$testval, 4),
    p_geq     = round(qap_res$pgreq,   4),
    p_leq     = round(qap_res$pleeq,   4),
    n_perms   = 1000
  )
  write.csv(qap_df, file.path(OUTPUT_DIR, "qap_result.csv"), row.names = FALSE)
  cat("Saved qap_result.csv\n")
}

cat("sna_analysis.R complete.\n")
