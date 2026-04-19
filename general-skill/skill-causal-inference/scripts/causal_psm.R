# PSM Analysis Template
# ── Replace ALL CAPS placeholders with your actual variable/path names ──────
#
# OUTCOME    : outcome variable (numeric)
# TREATED    : binary treatment indicator (0/1)
# UNIT_ID    : unit identifier (for clustering SE by matched pair/subclass)
# COVARS     : pre-treatment covariates for propensity score model
# DATA_FILE  : relative path to your CSV
# OUTPUT_DIR : relative path to output folder

pkgs <- c("MatchIt", "cobalt", "modelsummary", "flextable", "officer",
          "ggplot2", "dplyr", "sandwich", "lmtest")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, repos = "https://cloud.r-project.org")
  library(p, character.only = TRUE)
}

DATA_FILE  <- "your-project/project-{name}/data/DATA_FILE.csv"
OUTPUT_DIR <- "your-project/project-{name}/output/causal-inference"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

OUTCOME  <- "OUTCOME"
TREATED  <- "TREATED"
UNIT_ID  <- "UNIT_ID"
COVARS   <- c("COVAR1", "COVAR2", "COVAR3")

# ── 1. Load Data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
cat(sprintf("  N rows: %d  Treated: %d  Control: %d\n",
            nrow(df), sum(df[[TREATED]] == 1), sum(df[[TREATED]] == 0)))

# ── 2. Pre-matching Balance Check ─────────────────────────────────────────────
cat("\nPre-matching covariate balance (SMD):\n")
ps_fml <- as.formula(sprintf("%s ~ %s", TREATED, paste(COVARS, collapse = " + ")))
glm_pre <- glm(ps_fml, data = df, family = binomial)
df$ps_pre <- predict(glm_pre, type = "response")
cat(sprintf("  Propensity score range: [%.3f, %.3f]\n",
            min(df$ps_pre), max(df$ps_pre)))

# ── 3. Propensity Score Matching ──────────────────────────────────────────────
cat("\nRunning nearest-neighbor matching (caliper = 0.1 SD logit PS)...\n")
m_out <- matchit(
  ps_fml,
  data     = df,
  method   = "nearest",
  distance = "logit",
  caliper  = 0.1,
  ratio    = 1
)
cat(summary(m_out)$nn)  # matched sample sizes

m_data <- match.data(m_out)
cat(sprintf("  Matched N: %d  Treated: %d  Control: %d\n",
            nrow(m_data), sum(m_data[[TREATED]] == 1), sum(m_data[[TREATED]] == 0)))

# ── 4. Love Plot (Balance After Matching) ─────────────────────────────────────
cat("\nExporting Love plot...\n")
lp <- love.plot(m_out, threshold = 0.1, abs = TRUE,
                title = "Covariate balance: before vs after PSM",
                colors = c("#457B9D", "#E63946"))
ggsave(file.path(OUTPUT_DIR, "fig_psm_balance.png"),
       plot = lp, width = 7, height = 6, dpi = 300)
cat(sprintf("  Saved: %s/fig_psm_balance.png\n", OUTPUT_DIR))

# ── 5. Overlap / Common Support Plot ──────────────────────────────────────────
cat("Exporting overlap plot...\n")
df$ps    <- df$ps_pre
df$Group <- ifelse(df[[TREATED]] == 1, "Treatment", "Control")
p_overlap <- ggplot(df, aes(x = ps, fill = Group)) +
  geom_density(alpha = 0.5) +
  scale_fill_manual(values = c("Treatment" = "#E63946", "Control" = "#457B9D")) +
  labs(title = "Propensity score overlap (common support)",
       x = "Propensity score", y = "Density", fill = NULL) +
  theme_bw(base_size = 12) +
  theme(text = element_text(family = "serif"), legend.position = "bottom")
ggsave(file.path(OUTPUT_DIR, "fig_psm_overlap.png"),
       plot = p_overlap, width = 7, height = 5, dpi = 300)
cat(sprintf("  Saved: %s/fig_psm_overlap.png\n", OUTPUT_DIR))

# ── 6. Outcome Model on Matched Data ──────────────────────────────────────────
cat("\nRunning outcome model on matched data...\n")
covar_fml <- paste(COVARS, collapse = " + ")
fit_fml   <- as.formula(sprintf("%s ~ %s + %s", OUTCOME, TREATED, covar_fml))
fit_psm   <- lm(fit_fml, data = m_data, weights = weights)

# Cluster SE by matched pair (subclass)
fit_psm_se <- coeftest(fit_psm, vcov = vcovCL(fit_psm, cluster = ~subclass))
print(fit_psm_se)

# ── 7. Export Word Table ───────────────────────────────────────────────────────
cat("\nExporting regression table...\n")
cm <- c(setNames(TREATED, "Treatment effect"), setNames(COVARS, COVARS))

ft_psm <- modelsummary(
  list("PSM" = fit_psm),
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map = cm,
  gof_map  = tribble(~raw, ~clean, ~fmt,
                     "nobs",      "Observations", 0,
                     "r.squared", "R²",           3),
  title    = "Table X. PSM outcome regression",
  notes    = "Notes: * p<0.1, ** p<0.05, *** p<0.01. SE clustered by matched pair (subclass).",
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
doc <- flextable::body_add_flextable(doc, ft_psm)
print(doc, target = file.path(OUTPUT_DIR, "table_causal_psm.docx"))
cat(sprintf("  Saved: %s/table_causal_psm.docx\n", OUTPUT_DIR))

cat("\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat("PSM ANALYSIS COMPLETE\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("Outputs in: %s\n", OUTPUT_DIR))
cat("  table_causal_psm.docx\n")
cat("  fig_psm_balance.png\n")
cat("  fig_psm_overlap.png\n")
