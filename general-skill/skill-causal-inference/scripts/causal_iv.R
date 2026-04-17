# IV (Instrumental Variables) Analysis Template
# ── Replace ALL CAPS placeholders with your actual variable/path names ──────
#
# OUTCOME      : outcome variable Y (numeric)
# ENDOG        : endogenous treatment variable X
# INSTRUMENTS  : character vector of instrument variable names
# UNIT_FE      : unit fixed effect variable (e.g., "country", "firm")
# TIME_FE      : time fixed effect variable (e.g., "year")
# COVARS       : exogenous control variables
# DATA_FILE    : relative path to your CSV
# OUTPUT_DIR   : relative path to output folder

pkgs <- c("fixest", "modelsummary", "flextable", "officer", "dplyr", "ggplot2")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, repos = "https://cloud.r-project.org")
  library(p, character.only = TRUE)
}

DATA_FILE   <- "projects/PROJECT_NAME/data/DATA_FILE.csv"
OUTPUT_DIR  <- "projects/PROJECT_NAME/output"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

OUTCOME     <- "OUTCOME"
ENDOG       <- "ENDOG"
INSTRUMENTS <- c("INSTRUMENT1", "INSTRUMENT2")
UNIT_FE     <- "UNIT_FE"
TIME_FE     <- "TIME_FE"
COVARS      <- c("COVAR1", "COVAR2")

# ── 1. Load Data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
df[[UNIT_FE]] <- as.factor(df[[UNIT_FE]])
df[[TIME_FE]] <- as.factor(df[[TIME_FE]])
cat(sprintf("  N rows: %d\n", nrow(df)))

# Drop rows missing any key variable
key_cols <- c(OUTCOME, ENDOG, INSTRUMENTS, COVARS)
df_clean <- df[complete.cases(df[, key_cols]), ]
cat(sprintf("  After dropping NAs: %d rows\n\n", nrow(df_clean)))

covar_str <- paste(COVARS,       collapse = " + ")
instr_str <- paste(INSTRUMENTS,  collapse = " + ")
fe_str    <- paste(c(UNIT_FE, TIME_FE), collapse = " + ")

# ── 2. IV Feasibility Checks ──────────────────────────────────────────────────
cat("=== IV FEASIBILITY CHECKS ===\n\n")

# Check 1: First-stage relevance
cat("-- Check 1: First-stage relevance (F-statistic) --\n")
fs_fml <- as.formula(sprintf("%s ~ %s + %s | %s", ENDOG, instr_str, covar_str, fe_str))
fs <- feols(fs_fml, data = df_clean,
            cluster = as.formula(sprintf("~%s", UNIT_FE)))
fs_f <- as.numeric(fitstat(fs, "f")$f)[1]
cat(sprintf("  First-stage F: %.2f  %s\n\n", fs_f,
            ifelse(fs_f > 10, "PASS ✓", "FAIL — weak instruments")))

# Check 2: Endogeneity (Hausman-Wu via residual augmentation)
cat("-- Check 2: Endogeneity (Hausman-Wu) --\n")
fs_resid <- residuals(fs)
removed  <- abs(fs$obs_selection$obsRemoved)
keep_idx <- setdiff(seq_len(nrow(df_clean)), removed)
df_haus  <- df_clean[keep_idx, ]
df_haus$v_hat <- as.numeric(fs_resid)
haus_fml <- as.formula(
  sprintf("%s ~ %s + v_hat + %s | %s", OUTCOME, ENDOG, covar_str, fe_str))
haus_test <- feols(haus_fml, data = df_haus,
                   cluster = as.formula(sprintf("~%s", UNIT_FE)))
v_coef <- coef(haus_test)["v_hat"]
v_se   <- sqrt(diag(vcov(haus_test)))["v_hat"]
v_p    <- 2 * pt(abs(v_coef / v_se), df = nrow(df_haus) - 1, lower.tail = FALSE)
cat(sprintf("  v_hat p=%.4f  --> %s\n\n", v_p,
            ifelse(v_p < 0.05, "ENDOGENOUS — IV needed ✓", "Exogenous — OLS may suffice")))

# Check 3: Overidentification (Hansen J, only if #instruments > 1)
if (length(INSTRUMENTS) > 1) {
  cat("-- Check 3: Overidentification (Hansen J) --\n")
  iv_base_fml <- as.formula(
    sprintf("%s ~ 1 | %s | %s ~ %s", OUTCOME, fe_str, ENDOG, instr_str))
  iv_base <- feols(iv_base_fml, data = df_clean,
                   cluster = as.formula(sprintf("~%s", UNIT_FE)))
  iv_resid_vec <- residuals(iv_base, type = "response")
  iv_removed   <- abs(iv_base$obs_selection$obsRemoved)
  iv_keep      <- setdiff(seq_len(nrow(df_clean)), iv_removed)
  df_sargan    <- df_clean[iv_keep, ]
  df_sargan$iv_resid <- as.numeric(iv_resid_vec)
  sargan_fml <- as.formula(
    sprintf("iv_resid ~ %s + %s | %s", instr_str, covar_str, fe_str))
  sargan_aux <- feols(sargan_fml, data = df_sargan)
  r2_s  <- fitstat(sargan_aux, "r2")$r2
  j_stat <- nrow(df_sargan) * r2_s
  j_p    <- pchisq(j_stat, df = length(INSTRUMENTS) - 1, lower.tail = FALSE)
  cat(sprintf("  J stat=%.4f  df=%d  p=%.4f  --> %s\n\n",
              j_stat, length(INSTRUMENTS) - 1, j_p,
              ifelse(j_p > 0.05, "PASS ✓", "FAIL — instruments may be invalid")))
} else {
  j_p <- NA
  cat("-- Check 3: Overidentification — skipped (exactly identified) --\n\n")
}

# ── 3. Main IV Model ──────────────────────────────────────────────────────────
cat("Running IV models...\n")

iv_fml <- as.formula(
  sprintf("%s ~ %s | %s | %s ~ %s", OUTCOME, covar_str, fe_str, ENDOG, instr_str))
m_iv <- feols(iv_fml, data = df_clean,
              cluster = as.formula(sprintf("~%s", UNIT_FE)))

# ── 4. IV Diagnostics ─────────────────────────────────────────��───────────────
uid_p <- tryCatch(fitstat(m_iv, "ivf")$ivf$p, error = function(e) NA)
cd_f  <- tryCatch({
  mod_nc <- update(m_iv, . ~ ., cluster = NULL, data = df_clean)
  as.numeric(fitstat(mod_nc, "cd")$cd)
}, error = function(e) NA)
kp_f  <- as.numeric(fitstat(m_iv, "f")$f)[1]

# ── 5. First-Stage Scatter Plot ───────────────────────────────────────────────
cat("Plotting first-stage fit...\n")
fs_pred <- predict(fs)
df_fs_plot <- data.frame(fitted = as.numeric(fs_pred),
                          actual = df_clean[keep_idx, ENDOG])
p_fs <- ggplot(df_fs_plot, aes(x = fitted, y = actual)) +
  geom_point(alpha = 0.4, size = 1.5, color = "#457B9D") +
  geom_smooth(method = "lm", color = "#E63946", linewidth = 0.9, se = FALSE) +
  labs(title = "First-stage fit",
       x = sprintf("Fitted %s (instruments + controls)", ENDOG),
       y = sprintf("Actual %s", ENDOG)) +
  theme_bw(base_size = 12) +
  theme(text = element_text(family = "serif"))
ggsave(file.path(OUTPUT_DIR, "fig_iv_firststage.png"),
       plot = p_fs, width = 7, height = 5, dpi = 300)
cat(sprintf("  Saved: %s/fig_iv_firststage.png\n", OUTPUT_DIR))

# ── 6. Export Word Table ───────────────────────────────────────────────────────
cat("Exporting regression table...\n")

fit_endog_name <- paste0("fit_", ENDOG)
cm <- c(setNames(fit_endog_name, ENDOG), setNames(COVARS, COVARS))

fmt3 <- function(x) ifelse(is.na(x), "", sprintf("%.3f", x))

n_countries <- length(unique(df_clean[[UNIT_FE]]))

add_rows_df <- data.frame(
  term     = c("Unit FE", "Time FE", "Controls",
               sprintf("N (%ss)", UNIT_FE),
               "Underidentification test (p)",
               "Cragg-Donald F",
               "Kleibergen-Paap F",
               "Hansen J (p)"),
  `IV`     = c("Yes", "Yes", "Yes",
               as.character(n_countries),
               fmt3(uid_p),
               fmt3(cd_f),
               fmt3(kp_f),
               fmt3(j_p)),
  check.names = FALSE
)
# position: 2×n_coef + n_gof + 1
n_coef <- length(cm)
attr(add_rows_df, "position") <- (2 * n_coef + 2 + 1):(2 * n_coef + 2 + 8)

ft_iv <- modelsummary(
  list("IV" = m_iv),
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map = cm,
  gof_map  = tribble(~raw, ~clean, ~fmt, "nobs", "Observations", 0),
  add_rows = add_rows_df,
  title    = "Table X. Instrumental variable analysis",
  notes    = paste0(
    "Notes: * p<0.1, ** p<0.05, *** p<0.01. ",
    "Standard errors clustered at ", UNIT_FE, " level. ",
    "Cragg-Donald F computed under homoskedastic errors; ",
    "Kleibergen-Paap F computed with clustered errors."
  ),
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
doc <- flextable::body_add_flextable(doc, ft_iv)
print(doc, target = file.path(OUTPUT_DIR, "table_iv.docx"))
cat(sprintf("  Saved: %s/table_iv.docx\n", OUTPUT_DIR))

# ── 7. Summary ───────────────────────────────────────────────��────────────────
cat("\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat("IV ANALYSIS COMPLETE\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("  Y  : %s\n  X  : %s\n  Z  : %s\n  FE : %s + %s\n",
            OUTCOME, ENDOG, paste(INSTRUMENTS, collapse = ", "), UNIT_FE, TIME_FE))
cat("----\n")
cat(sprintf("  First-stage F       : %.2f  %s\n", fs_f,
            ifelse(fs_f > 10, "PASS", "FAIL")))
cat(sprintf("  Endogeneity (Haus.) : p=%.4f  %s\n", v_p,
            ifelse(v_p < 0.05, "Endogenous", "Exogenous")))
if (!is.na(j_p))
  cat(sprintf("  Hansen J            : p=%.4f  %s\n", j_p,
              ifelse(j_p > 0.05, "PASS", "FAIL")))
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("Outputs in: %s\n", OUTPUT_DIR))
cat("  table_iv.docx\n  fig_iv_firststage.png\n")
