#!/usr/bin/env Rscript
# network_analysis.R — Psychometric Network Analysis
# Called by skill-psychometric-network-analysis agent steps
# Usage: Rscript network_analysis.R <mode> <data_path> <output_dir> [options...]
#   mode: ggm | centrality | stability | nct | clpna_mlvar | clpna_panelvar

suppressPackageStartupMessages({
  library(qgraph)
  library(bootnet)
  library(NetworkComparisonTest)
  library(networktools)
  library(igraph)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 3) {
  stop("Usage: Rscript network_analysis.R <mode> <data_path> <output_dir> [json_options]")
}

MODE       <- args[1]
DATA_PATH  <- args[2]
OUTPUT_DIR <- args[3]
OPTS       <- if (length(args) >= 4) fromJSON(args[4]) else list()

dir.create(OUTPUT_DIR, recursive = TRUE, showWarnings = FALSE)

# ── helpers ──────────────────────────────────────────────────────────────────

load_data <- function(path) {
  ext <- tolower(tools::file_ext(path))
  if (ext %in% c("xlsx", "xls")) {
    requireNamespace("readxl", quietly = TRUE)
    readxl::read_excel(path)
  } else {
    read.csv(path, stringsAsFactors = FALSE)
  }
}

save_json <- function(obj, name) {
  write(toJSON(obj, auto_unbox = TRUE, digits = 6, na = "null"),
        file = file.path(OUTPUT_DIR, name))
}

# ── GGM estimation ────────────────────────────────────────────────────────────

run_ggm <- function() {
  dat    <- load_data(DATA_PATH)
  nodes  <- OPTS$node_vars
  gamma  <- if (!is.null(OPTS$gamma)) OPTS$gamma else 0.5

  node_dat <- dat[, nodes, drop = FALSE]
  node_dat <- na.omit(node_dat)

  cor_method <- if (!is.null(OPTS$corMethod)) OPTS$corMethod else "cor_auto"
  net <- estimateNetwork(node_dat,
                         default    = "EBICglasso",
                         tuning     = gamma,
                         corMethod  = cor_method)

  # Save network object
  saveRDS(net, file = file.path(OUTPUT_DIR, "network_object.rds"))

  # Edge weight matrix
  ew <- net$graph
  rownames(ew) <- colnames(ew) <- nodes
  write.csv(as.data.frame(ew),
            file = file.path(OUTPUT_DIR, "edge_weights.csv"))

  # Network plot — cluster coloring when construct_map is provided
  # qgraph groups expects integer index vectors, not node name strings
  groups_list  <- NULL
  group_colors <- NULL
  if (!is.null(OPTS$construct_map)) {
    groups_list <- lapply(OPTS$construct_map, function(node_names) {
      which(nodes %in% node_names)
    })
    names(groups_list) <- names(OPTS$construct_map)
    palette      <- c("#4E79A7","#F28E2B","#E15759","#76B7B2",
                      "#59A14F","#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC")
    group_colors <- palette[seq_len(length(groups_list))]
  }

  png(file.path(OUTPUT_DIR, "network_plot.png"),
      width = 2400, height = 2400, res = 300)
  plot(net,
       layout    = "spring",
       labels    = nodes,
       groups    = groups_list,
       color     = group_colors,
       vsize     = 8,
       esize     = 15,
       posCol    = "#2196F3",
       negCol    = "#F44336",
       title     = "Psychometric Network (EBICglasso)")
  dev.off()

  # Return summary for agent
  n_edges   <- sum(ew[upper.tri(ew)] != 0)
  n_nodes   <- length(nodes)
  density   <- n_edges / (n_nodes * (n_nodes - 1) / 2)

  save_json(list(n_nodes  = n_nodes,
                 n_edges  = n_edges,
                 density  = round(density, 3),
                 gamma    = gamma,
                 n_obs    = nrow(node_dat)),
            "ggm_summary.json")
  message("GGM done. Edges: ", n_edges, " | Density: ", round(density, 3))
}

# ── Centrality ────────────────────────────────────────────────────────────────

run_centrality <- function() {
  net   <- readRDS(file.path(OUTPUT_DIR, "network_object.rds"))
  nodes <- OPTS$node_vars

  # Standard centrality
  ci <- centralityTable(net)
  write.csv(ci, file = file.path(OUTPUT_DIR, "centrality_indices.csv"),
            row.names = FALSE)

  # Expected Influence (accounts for negative edges)
  ei <- expectedInf(net$graph)
  ei_df <- data.frame(node = names(ei$step1),
                      EI_step1 = round(as.numeric(ei$step1), 4),
                      EI_step2 = round(as.numeric(ei$step2), 4))
  write.csv(ei_df, file = file.path(OUTPUT_DIR, "expected_influence.csv"),
            row.names = FALSE)

  # Bridge centrality (requires construct groups)
  if (!is.null(OPTS$construct_map)) {
    communities <- OPTS$construct_map  # named list: construct -> vector of node names
    comm_vec    <- rep(NA, length(nodes))
    names(comm_vec) <- nodes
    for (cname in names(communities)) {
      comm_vec[communities[[cname]]] <- cname
    }
    bc <- bridge(net$graph, communities = comm_vec)
    bc_df <- data.frame(node            = names(bc$`Bridge Strength`),
                        bridge_strength = round(bc$`Bridge Strength`, 4),
                        bridge_between  = round(bc$`Bridge Betweenness`, 4),
                        bridge_close    = round(bc$`Bridge Closeness`, 4),
                        bridge_EI       = round(bc$`Bridge Expected Influence (1-step)`, 4))
    write.csv(bc_df, file = file.path(OUTPUT_DIR, "bridge_centrality.csv"),
              row.names = FALSE)
  }

  # Centrality plot
  cent_scale <- if (!is.null(OPTS$centralityScale)) OPTS$centralityScale else "z-scores"
  png(file.path(OUTPUT_DIR, "centrality_plot.png"),
      width = 2400, height = 1800, res = 300)
  centralityPlot(net,
                 include = c("Strength", "Betweenness", "Closeness",
                             "ExpectedInfluence"),
                 orderBy = "Strength",
                 scale   = cent_scale)
  dev.off()

  message("Centrality done.")
}

# ── Stability (bootnet) ��──────────────────────────────────────────────────────

run_stability <- function() {
  dat    <- load_data(DATA_PATH)
  nodes  <- OPTS$node_vars
  gamma  <- if (!is.null(OPTS$gamma)) OPTS$gamma else 0.5
  nboots <- if (!is.null(OPTS$nboots)) OPTS$nboots else 1000

  node_dat <- dat[, nodes, drop = FALSE]
  node_dat <- na.omit(node_dat)

  cor_method_s <- if (!is.null(OPTS$corMethod)) OPTS$corMethod else "cor_auto"
  net <- estimateNetwork(node_dat, default = "EBICglasso", tuning = gamma,
                         corMethod = cor_method_s)

  # Edge-weight bootstrap
  message("Running edge-weight bootstrap (B=", nboots, ")...")
  boot_edge <- bootnet(net, nBoots = nboots, type = "nonparametric",
                       nCores = max(1, parallel::detectCores() - 1))

  png(file.path(OUTPUT_DIR, "stability_edge_plot.png"),
      width = 2400, height = 1800, res = 300)
  print(plot(boot_edge, labels = FALSE, order = "sample"))
  dev.off()

  # Case-dropping bootstrap
  message("Running case-dropping bootstrap (B=", nboots, ")...")
  boot_case <- bootnet(net, nBoots = nboots, type = "case",
                       statistics = c("Strength", "Betweenness", "Closeness",
                                      "ExpectedInfluence"),
                       nCores = max(1, parallel::detectCores() - 1))

  png(file.path(OUTPUT_DIR, "stability_case_plot.png"),
      width = 2400, height = 1800, res = 300)
  print(plot(boot_case, statistics = c("Strength", "Betweenness", "Closeness",
                                  "ExpectedInfluence")))
  dev.off()

  # CS-coefficients
  cs <- corStability(boot_case)
  cs_df <- data.frame(statistic  = names(cs),
                      CS_coef    = round(unlist(cs), 3))
  write.csv(cs_df, file = file.path(OUTPUT_DIR, "cs_coefficients.csv"),
            row.names = FALSE)

  save_json(list(cs_coefficients = as.list(round(unlist(cs), 3))), "stability_summary.json")
  message("Stability done. CS-coefficients: ")
  print(cs_df)
}

# ── Network Comparison Test ───────────────────────────────────────────────────

run_nct <- function() {
  dat        <- load_data(DATA_PATH)
  nodes      <- OPTS$node_vars
  group_var  <- OPTS$group_var
  group_vals <- OPTS$group_vals   # length-2 vector
  gamma      <- if (!is.null(OPTS$gamma)) OPTS$gamma else 0.5
  it         <- if (!is.null(OPTS$nct_iter)) OPTS$nct_iter else 1000

  g1 <- dat[dat[[group_var]] == group_vals[1], nodes, drop = FALSE]
  g2 <- dat[dat[[group_var]] == group_vals[2], nodes, drop = FALSE]
  g1 <- na.omit(g1)
  g2 <- na.omit(g2)

  net1 <- estimateNetwork(g1, default = "EBICglasso", tuning = gamma)
  net2 <- estimateNetwork(g2, default = "EBICglasso", tuning = gamma)

  # Per-group plots
  for (i in seq_along(group_vals)) {
    net_i  <- list(net1, net2)[[i]]
    label_i <- group_vals[i]
    png(file.path(OUTPUT_DIR, paste0("nct_network_", label_i, ".png")),
        width = 2400, height = 2400, res = 300)
    plot(net_i, layout = "spring", labels = nodes,
         title = paste("Network —", label_i))
    dev.off()
  }

  # NCT — pass raw data frames, not graph matrices
  message("Running NCT (it=", it, ")...")
  nct_result <- NCT(g1, g2,
                    gamma    = gamma,
                    it       = it,
                    test.edges = TRUE,
                    edges    = "all",
                    progressbar = FALSE)

  saveRDS(nct_result, file.path(OUTPUT_DIR, "nct_result.rds"))

  # Text summary
  sink(file.path(OUTPUT_DIR, "nct_summary.txt"))
  print(summary(nct_result))
  sink()

  # JSON summary
  save_json(list(
    group1 = group_vals[1],
    group2 = group_vals[2],
    n_group1 = nrow(g1),
    n_group2 = nrow(g2),
    global_strength_p    = round(nct_result$glstrinv.pval, 4),
    network_structure_p  = round(nct_result$nwinv.pval, 4)
  ), "nct_summary.json")

  message("NCT done.")
}

# ── CLPNA: mlVAR ───────────────────────────────────��─────────────────────────

run_clpna_mlvar <- function() {
  suppressPackageStartupMessages(library(mlVAR))

  dat      <- load_data(DATA_PATH)
  nodes    <- OPTS$node_vars
  id_var   <- OPTS$id_var
  time_var <- OPTS$time_var
  lags     <- if (!is.null(OPTS$lags)) OPTS$lags else 1

  message("Estimating mlVAR model...")
  mlvar_fit <- mlVAR(dat,
                     vars    = nodes,
                     idvar   = id_var,
                     lags    = lags,
                     temporal   = "correlated",
                     contemporaneous = "correlated")

  # Plots
  png(file.path(OUTPUT_DIR, "clpna_temporal_network.png"),
      width = 2400, height = 2400, res = 300)
  plot(mlvar_fit, type = "temporal", labels = nodes,
       title = "Temporal Network (mlVAR)")
  dev.off()

  png(file.path(OUTPUT_DIR, "clpna_contemporaneous_network.png"),
      width = 2400, height = 2400, res = 300)
  plot(mlvar_fit, type = "contemporaneous", labels = nodes,
       title = "Contemporaneous Network (mlVAR)")
  dev.off()

  png(file.path(OUTPUT_DIR, "clpna_between_network.png"),
      width = 2400, height = 2400, res = 300)
  plot(mlvar_fit, type = "between", labels = nodes,
       title = "Between-Person Network (mlVAR)")
  dev.off()

  # Coefficient matrices — mlVAR stores results in $results
  temp_mat <- mlvar_fit$results$Beta[[1]]   # lag-1 temporal (fixed effects)
  cont_mat <- mlvar_fit$results$Theta        # contemporaneous partial correlations
  write.csv(as.data.frame(temp_mat),
            file = file.path(OUTPUT_DIR, "mlvar_temporal_matrix.csv"))
  write.csv(as.data.frame(cont_mat),
            file = file.path(OUTPUT_DIR, "mlvar_contemporaneous_matrix.csv"))

  saveRDS(mlvar_fit, file = file.path(OUTPUT_DIR, "mlvar_fit.rds"))
  message("mlVAR done.")
}

# ── CLPNA: panelvar ───────────────────────────────────────────────────────────

run_clpna_panelvar <- function() {
  suppressPackageStartupMessages(library(panelvar))

  dat      <- load_data(DATA_PATH)
  nodes    <- OPTS$node_vars
  id_var   <- OPTS$id_var
  time_var <- OPTS$time_var
  lags     <- if (!is.null(OPTS$lags)) OPTS$lags else 1

  message("Estimating panelvar (GMM) model...")

  pv_fit <- pvargmm(dependent_vars   = nodes,
                    lags             = lags,
                    transformation   = "fd",
                    data             = dat,
                    panel_identifier = c(id_var, time_var),
                    steps            = "twostep",
                    system_instruments = FALSE)

  saveRDS(pv_fit, file = file.path(OUTPUT_DIR, "panelvar_fit.rds"))

  coef_mat <- coef(pv_fit)
  write.csv(as.data.frame(coef_mat),
            file = file.path(OUTPUT_DIR, "panelvar_coefficients.csv"))

  # Build adjacency matrix from significant coefficients for plot
  # Rows = outcome, cols = predictor (lagged)
  adj <- matrix(0, nrow = length(nodes), ncol = length(nodes),
                dimnames = list(nodes, nodes))
  for (v in nodes) {
    for (pred in nodes) {
      lag_name <- paste0(pred, ".l", lags)
      if (lag_name %in% rownames(coef_mat) && v %in% colnames(coef_mat)) {
        adj[v, pred] <- coef_mat[lag_name, v]
      }
    }
  }

  png(file.path(OUTPUT_DIR, "clpna_panelvar_network.png"),
      width = 2400, height = 2400, res = 300)
  qgraph(t(adj), layout = "circle", labels = nodes,
         directed = TRUE, arrows = TRUE,
         title = "Cross-lagged Panel Network (panelvar GMM)")
  dev.off()

  message("panelvar done.")
}

# ── dispatch ──────────────────────────────────────────────────────────────────

switch(MODE,
  ggm          = run_ggm(),
  centrality   = run_centrality(),
  stability    = run_stability(),
  nct          = run_nct(),
  clpna_mlvar  = run_clpna_mlvar(),
  clpna_panelvar = run_clpna_panelvar(),
  stop("Unknown mode: ", MODE)
)
