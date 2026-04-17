# PSW Analysis Template
# ── Replace ALL CAPS placeholders with your actual variable/path names ──────
#
# OUTCOME    : outcome variable (numeric)
# TREATED    : binary treatment indicator (0/1)
# UNIT_ID    : unit identifier (for clustering SE)
# COVARS     : pre-treatment covariates for propensity score model
# DATA_FILE  : relative path to your CSV
# OUTPUT_DIR : relative path to output folder

pkgs <- c("WeightIt", "cobalt", "estimatr", "modelsummary",
          "flextable", "officer", "ggplot2", "dplyr")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, repos = "https://cloud.r-project.org")
  library(p, character.only = TRUE)
}

DATA_FILE  <- "projects/PROJECT_NAME/data/DATA_FILE.csv"
OUTPUT_DIR <- "projects/PROJECT_NAME/output"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

OUTCOME  <- "OUTCOME"
TREATED  <- "TREATED"
UNIT_ID  <- "UNIT_ID"
COVARS   <- c("COVAR1", "COVAR2", "COVAR3")
ESTIMAND <- "ATE"   # "ATE" or "ATT"

# ── 1. Load Data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
cat(sprintf("  N rows: %d  Treated: %d  Control: %d\n",
            nrow(df), sum(df[[TREATED]] == 1), sum(df[[TREATED]] == 0)))

# ── 2. Estimate Propensity Weights ────────────────────────────────────────────
cat(sprintf("\nEstimating %s weights via IPW...\n", ESTIMAND))
ps_fml <- as.formula(sprintf("%s ~ %s", TREATED, paste(COVARS, collapse = " + ")))
w_out  <- weightit(ps_fml, data = df, method = "ps", estimand = ESTIMAND)
cat(sprintf("  Effective N (treated):  %.1f\n", w_out$effn$treated))
cat(sprintf("  Effective N (control):  %.1f\n", w_out$effn$control))
cat(sprintf("  Max weight: %.3f\n", max(w_out$weights)))

# ── 3. Trim Extreme Weights ───────────────────────────────────────────────────
cat("Trimming weights at 1st/99th percentile...\n")
df$w_raw     <- w_out$weights
df$w_trimmed <- pmin(pmax(df$w_raw,
                          quantile(df$w_raw, 0.01)),
                     quantile(df$w_raw, 0.99))
cat(sprintf("  Pre-trim  max: %.3f  Post-trim max: %.3f\n",
            max(df$w_raw), max(df$w_trimmed)))

# ── 4. Weighted Love Plot (Balance) ──────────────────────────────────────────
cat("\nExporting weighted Love plot...\n")
lp <- love.plot(w_out, threshold = 0.1, abs = TRUE,
                title = sprintf("Covariate balance (PSW, %s weights)", ESTIMAND),
                colors = c("#457B9D", "#E63946"))
ggsave(file.path(OUTPUT_DIR, "fig_psw_balance.png"),
       plot = lp, width = 7, height = 6, dpi = 300)
cat(sprintf("  Saved: %s/fig_psw_balance.png\n", OUTPUT_DIR))

# ── 5. Weighted Outcome Model (lm_robust, CR2 SE) ────────────────────────────
cat("\nRunning weighted outcome model (CR2 SE)...\n")
covar_fml <- paste(COVARS, collapse = " + ")
fit_fml   <- as.formula(sprintf("%s ~ %s + %s", OUTCOME, TREATED, covar_fml))
fit_psw   <- lm_robust(
  fit_fml,
  data      = df,
  weights   = w_trimmed,
  clusters  = df[[UNIT_ID]],
  se_type   = "CR2"
)
print(summary(fit_psw))

# ── 6. Export Word Table ───────────────────────────────────────────────────────
cat("\nExporting regression table...\n")
cm <- c(setNames(TREATED, "Treatment effect (PSW)"),
        setNames(COVARS, COVARS))

ft_psw <- modelsummary(
  list("PSW" = fit_psw),
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map = cm,
  gof_map  = tribble(~raw, ~clean, ~fmt,
                     "nobs",      "Observations", 0,
                     "r.squared", "R²",           3),
  title    = sprintf("Table X. PSW outcome regression (%s weights)", ESTIMAND),
  notes    = paste0("Notes: * p<0.1, ** p<0.05, *** p<0.01. ",
                    "CR2 standard errors clustered at unit level. ",
                    "Weights trimmed at 1st/99th percentile."),
  output   = "flextable"
) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc <- officer::read_docx()
doc <- flextable::body_add_flextable(doc, ft_psw)
print(doc, target = file.path(OUTPUT_DIR, "table_causal_psw.docx"))
cat(sprintf("  Saved: %s/table_causal_psw.docx\n", OUTPUT_DIR))

cat("\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat("PSW ANALYSIS COMPLETE\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("Outputs in: %s\n", OUTPUT_DIR))
cat("  table_causal_psw.docx\n")
cat("  fig_psw_balance.png\n")
