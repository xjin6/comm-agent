# RDD (Regression Discontinuity Design) Analysis Template
# ── Replace ALL CAPS placeholders with your actual variable/path names ──────
#
# OUTCOME    : outcome variable Y
# RUNNING    : continuous running variable (centered at cutoff is conventional)
# CUTOFF     : known threshold value (numeric)
# TREATMENT  : binary treatment indicator (optional; for fuzzy RDD)
# COVARS     : pre-treatment covariates for balance checks
# DATA_FILE  : relative path to your CSV
# OUTPUT_DIR : relative path to output folder

pkgs <- c("rdrobust", "rddensity", "modelsummary", "flextable",
          "officer", "ggplot2", "dplyr")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, repos = "https://cloud.r-project.org")
  library(p, character.only = TRUE)
}

DATA_FILE  <- "your-project/project-{name}/data/DATA_FILE.csv"
OUTPUT_DIR <- "your-project/project-{name}/output/causal-inference"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

OUTCOME   <- "OUTCOME"
RUNNING   <- "RUNNING"
CUTOFF    <- 0          # replace with your actual cutoff
RDD_TYPE  <- "sharp"    # "sharp" or "fuzzy"
TREATMENT <- "TREATMENT"  # only needed for fuzzy RDD
COVARS    <- c("COVAR1", "COVAR2")

# ── 1. Load Data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
cat(sprintf("  N rows: %d\n", nrow(df)))

df_clean <- df[!is.na(df[[RUNNING]]) & !is.na(df[[OUTCOME]]), ]
cat(sprintf("  After dropping NAs: %d rows\n\n", nrow(df_clean)))

y <- df_clean[[OUTCOME]]
x <- df_clean[[RUNNING]]

# ── 2. Manipulation Test (McCrary density) ────────────────────────────────────
cat("=== RDD FEASIBILITY CHECKS ===\n\n")
cat("-- Check 1: McCrary density test (H0: no manipulation) --\n")
rdd_dens <- rddensity(X = x, c = CUTOFF)
summary_dens <- summary(rdd_dens)
print(summary_dens)
dens_p <- rdd_dens$test$p_jk   # two-sided p-value
cat(sprintf("  Density test p=%.4f  --> %s\n\n", dens_p,
            ifelse(dens_p > 0.05, "PASS ✓ (no manipulation)", "WARNING — potential manipulation")))

# Save density plot
png(file.path(OUTPUT_DIR, "fig_rdd_density.png"), width = 800, height = 500)
rdplotdensity(rdd_dens, x, title = "McCrary density test",
              xlabel = RUNNING, CIuniform = TRUE)
dev.off()
cat(sprintf("  Saved: %s/fig_rdd_density.png\n\n", OUTPUT_DIR))

# ── 3. Bandwidth Selection & Main Estimate ────────────────────────────────────
cat("-- Check 2: Bandwidth selection (MSE-optimal) --\n")
if (RDD_TYPE == "sharp") {
  rdd_out <- rdrobust(y = y, x = x, c = CUTOFF,
                      kernel = "triangular", bwselect = "mserd")
} else {
  # Fuzzy RDD: treatment probability jumps at cutoff; instruments crossing
  fuzzy_treat <- df_clean[[TREATMENT]]
  rdd_out <- rdrobust(y = y, x = x, c = CUTOFF,
                      fuzzy = fuzzy_treat,
                      kernel = "triangular", bwselect = "mserd")
}
summary(rdd_out)

bw    <- rdd_out$bws["h", 1]
n_l   <- rdd_out$N_h[1]
n_r   <- rdd_out$N_h[2]
est   <- rdd_out$coef["Conventional", 1]
se    <- rdd_out$se["Conventional", 1]
p_val <- rdd_out$pv["Conventional", 1]
ci_l  <- rdd_out$ci["Robust", 1]
ci_r  <- rdd_out$ci["Robust", 2]
cat(sprintf("\n  Bandwidth h: %.4f\n", bw))
cat(sprintf("  N left: %d  N right: %d\n", n_l, n_r))
cat(sprintf("  Estimate (conventional): %.4f  SE: %.4f  p: %.4f\n", est, se, p_val))
cat(sprintf("  Robust 95%% CI: [%.4f, %.4f]\n\n", ci_l, ci_r))

# ── 4. RDD Visualization ──────────────────────────────────────────────────────
cat("Plotting RDD scatter + polynomial fit...\n")
png(file.path(OUTPUT_DIR, "fig_rdd_main.png"), width = 900, height = 550)
rdplot(y = y, x = x, c = CUTOFF,
       title = "RDD: outcome by running variable",
       x.label = RUNNING, y.label = OUTCOME)
dev.off()
cat(sprintf("  Saved: %s/fig_rdd_main.png\n\n", OUTPUT_DIR))

# ── 5. Robustness Checks ──────────────────────────────────────────────────────
cat("Running robustness checks...\n")

# Bandwidth sensitivity: 0.5×, 1×, 1.5× optimal
rdd_half <- rdrobust(y = y, x = x, c = CUTOFF, h = bw * 0.5)
rdd_one  <- rdd_out
rdd_one5 <- rdrobust(y = y, x = x, c = CUTOFF, h = bw * 1.5)

bw_results <- data.frame(
  Bandwidth = c("0.5× optimal", "1× optimal (baseline)", "1.5× optimal"),
  h         = round(c(bw * 0.5, bw, bw * 1.5), 4),
  N_left    = c(rdd_half$N_h[1], rdd_one$N_h[1], rdd_one5$N_h[1]),
  N_right   = c(rdd_half$N_h[2], rdd_one$N_h[2], rdd_one5$N_h[2]),
  Estimate  = round(c(rdd_half$coef[1], rdd_one$coef[1], rdd_one5$coef[1]), 4),
  SE        = round(c(rdd_half$se[1],   rdd_one$se[1],   rdd_one5$se[1]),   4),
  p         = round(c(rdd_half$pv[1],   rdd_one$pv[1],   rdd_one5$pv[1]),   4)
)
cat("\n  Bandwidth sensitivity:\n")
print(bw_results)

# Placebo cutoffs: ± 0.5 SD of running variable
sd_x <- sd(x, na.rm = TRUE)
placebo_low  <- CUTOFF - 0.5 * sd_x
placebo_high <- CUTOFF + 0.5 * sd_x

# Only run placebo on the side away from treatment boundary
tryCatch({
  rdd_placebo_lo <- rdrobust(y = y, x = x, c = placebo_low)
  rdd_placebo_hi <- rdrobust(y = y, x = x, c = placebo_high)
  cat(sprintf("\n  Placebo cutoff (c − 0.5 SD = %.3f): est=%.4f  p=%.4f  %s\n",
              placebo_low, rdd_placebo_lo$coef[1], rdd_placebo_lo$pv[1],
              ifelse(rdd_placebo_lo$pv[1] > 0.05, "PASS ✓", "WARNING")))
  cat(sprintf("  Placebo cutoff (c + 0.5 SD = %.3f): est=%.4f  p=%.4f  %s\n",
              placebo_high, rdd_placebo_hi$coef[1], rdd_placebo_hi$pv[1],
              ifelse(rdd_placebo_hi$pv[1] > 0.05, "PASS ✓", "WARNING")))
}, error = function(e) cat("  Placebo cutoffs could not be estimated.\n"))

# Donut RDD: exclude ε around cutoff (default ε = 0.05 × SD)
epsilon <- 0.05 * sd_x
df_donut <- df_clean[abs(x - CUTOFF) > epsilon, ]
y_d <- df_donut[[OUTCOME]]
x_d <- df_donut[[RUNNING]]
tryCatch({
  rdd_donut <- rdrobust(y = y_d, x = x_d, c = CUTOFF)
  cat(sprintf("\n  Donut RDD (ε=%.4f): est=%.4f  p=%.4f\n",
              epsilon, rdd_donut$coef[1], rdd_donut$pv[1]))
}, error = function(e) cat("  Donut RDD could not be estimated.\n"))

# ── 6. Export Word Table ───────────────────────────────────────────────────────
cat("\nExporting RDD table...\n")

# Manual extraction (rdrobust is not supported by modelsummary directly)
rdd_df <- data.frame(
  Term         = c(RUNNING, "Robust 95% CI", "Bandwidth (h)",
                   "N (left)", "N (right)", "Kernel"),
  Estimate     = c(sprintf("%.4f", est),
                   sprintf("[%.4f, %.4f]", ci_l, ci_r),
                   sprintf("%.4f", bw),
                   as.character(n_l),
                   as.character(n_r),
                   "Triangular"),
  SE_p         = c(sprintf("(%.4f)\n p = %.4f", se, p_val),
                   "", "", "", "", "")
)
names(rdd_df) <- c("", "RDD estimate", "SE / p")

ft_rdd <- flextable(rdd_df) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::set_caption(caption = "Table X. Regression discontinuity estimates") %>%
  flextable::add_footer_lines(
    paste0("Notes: Estimates based on local polynomial regression with triangular kernel. ",
           "Bias-corrected robust confidence intervals reported. ",
           sprintf("Cutoff = %.4f.", CUTOFF))
  ) %>%
  flextable::autofit()

doc <- officer::read_docx()
doc <- flextable::body_add_flextable(doc, ft_rdd)
print(doc, target = file.path(OUTPUT_DIR, "table_rdd_main.docx"))
cat(sprintf("  Saved: %s/table_rdd_main.docx\n", OUTPUT_DIR))

# ── 7. Summary ─────��──────────────────────────────────────────────────────────
cat("\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat("RDD ANALYSIS COMPLETE\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("  Y       : %s\n  Running : %s\n  Cutoff  : %s\n  Type    : %s\n",
            OUTCOME, RUNNING, CUTOFF, RDD_TYPE))
cat("----\n")
cat(sprintf("  McCrary density test    : p=%.4f  %s\n", dens_p,
            ifelse(dens_p > 0.05, "PASS", "WARNING")))
cat(sprintf("  Bandwidth (MSE-optimal) : %.4f\n", bw))
cat(sprintf("  RDD estimate            : %.4f  (SE=%.4f  p=%.4f)\n", est, se, p_val))
cat(sprintf("  Robust 95%% CI          : [%.4f, %.4f]\n", ci_l, ci_r))
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("Outputs in: %s\n", OUTPUT_DIR))
cat("  table_rdd_main.docx\n  fig_rdd_main.png\n  fig_rdd_density.png\n")
