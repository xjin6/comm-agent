# DID Analysis Template
# ── Replace ALL CAPS placeholders with your actual variable/path names ──────
#
# OUTCOME      : outcome variable (numeric)
# UNIT_ID      : unit identifier (e.g., country, firm, person)
# TIME_VAR     : time period variable (numeric or integer)
# TREATED      : binary treatment group indicator (0/1, time-invariant)
# FIRST_TREAT  : year/period of first treatment (0 = never treated)
# TREAT_PERIOD : the treatment onset period for single-timing DID
# COVAR1 etc.  : pre-treatment covariates
# DATA_FILE    : relative path to your CSV, e.g. "your-project/project-{name}/data/panel.csv"
# OUTPUT_DIR   : relative path to output folder

pkgs <- c("fixest", "did", "modelsummary", "flextable", "officer",
          "ggplot2", "dplyr", "tidyr")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, repos = "https://cloud.r-project.org")
  library(p, character.only = TRUE)
}

DATA_FILE   <- "your-project/project-{name}/data/DATA_FILE.csv"
OUTPUT_DIR  <- "your-project/project-{name}/output/causal-inference"
dir.create(OUTPUT_DIR, showWarnings = FALSE, recursive = TRUE)

OUTCOME      <- "OUTCOME"
UNIT_ID      <- "UNIT_ID"
TIME_VAR     <- "TIME_VAR"
TREATED      <- "TREATED"
FIRST_TREAT  <- "FIRST_TREAT"   # set NA if single-timing DID
TREAT_PERIOD <- 2010            # for single-timing DID only
COVARS       <- c("COVAR1", "COVAR2")  # pre-treatment covariates

# ── 1. Load Data ──────────────────────────────────────────────────────────────
cat("Loading data...\n")
df <- read.csv(DATA_FILE, stringsAsFactors = FALSE)
cat(sprintf("  N rows: %d\n", nrow(df)))

# Create DID interaction term (single timing)
df$treated   <- df[[TREATED]]
df$post      <- as.integer(df[[TIME_VAR]] >= TREAT_PERIOD)
df$treat_post <- df$treated * df$post

# ── 2. Descriptive Statistics Table ──────────────────────────────────────────
cat("Exporting descriptive statistics table...\n")

all_vars <- c(OUTCOME, "treat_post", COVARS)
desc_all <- df %>%
  summarise(across(all_of(all_vars),
                   list(N    = ~sum(!is.na(.)),
                        Mean = ~round(mean(., na.rm = TRUE), 3),
                        SD   = ~round(sd(.,   na.rm = TRUE), 3),
                        Min  = ~round(min(.,  na.rm = TRUE), 3),
                        Max  = ~round(max(.,  na.rm = TRUE), 3)),
                   .names = "{.col}__{.fn}")) %>%
  tidyr::pivot_longer(everything(),
                      names_to  = c("Variable", "Stat"),
                      names_sep = "__") %>%
  tidyr::pivot_wider(names_from = Stat, values_from = value)

ft_desc <- flextable(desc_all) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc <- officer::read_docx()
doc <- flextable::body_add_flextable(doc, ft_desc)
print(doc, target = file.path(OUTPUT_DIR, "table_did_descriptive.docx"))
cat(sprintf("  Saved: %s/table_did_descriptive.docx\n", OUTPUT_DIR))

# ── 3. Parallel Trends Plot ───────────────────────────────────────────────────
cat("Plotting parallel trends...\n")

trend_data <- df %>%
  group_by(across(all_of(c(TIME_VAR, TREATED)))) %>%
  summarise(mean_y = mean(.data[[OUTCOME]], na.rm = TRUE), .groups = "drop") %>%
  rename(time = all_of(TIME_VAR), treated = all_of(TREATED)) %>%
  mutate(Group = ifelse(treated == 1, "Treatment", "Control"))

p_trend <- ggplot(trend_data, aes(x = time, y = mean_y,
                                   color = Group, group = Group)) +
  geom_line(linewidth = 0.9) +
  geom_point(size = 2) +
  geom_vline(xintercept = TREAT_PERIOD - 0.5,
             linetype = "dashed", color = "grey40") +
  scale_color_manual(values = c("Treatment" = "#E63946", "Control" = "#457B9D")) +
  labs(title = "Outcome trends: treatment vs control",
       x = "Time", y = "Mean outcome", color = NULL) +
  theme_bw(base_size = 12) +
  theme(text = element_text(family = "serif"), legend.position = "bottom")

ggsave(file.path(OUTPUT_DIR, "fig_did_trends.png"),
       plot = p_trend, width = 8, height = 5, dpi = 300)
cat(sprintf("  Saved: %s/fig_did_trends.png\n", OUTPUT_DIR))

# ── 4. Main DID Regression Table (5 columns) ─────────────────────────────────
cat("Running DID models...\n")

covar_fml <- if (length(COVARS) > 0) paste(COVARS, collapse = " + ") else "1"

m1 <- lm(as.formula(sprintf("%s ~ treated + post + treat_post", OUTCOME)), data = df)
m2 <- lm(as.formula(sprintf("%s ~ treated + post + treat_post + %s", OUTCOME, covar_fml)), data = df)
m3 <- feols(as.formula(sprintf("%s ~ post + treat_post + %s | %s", OUTCOME, covar_fml, UNIT_ID)),
            data = df, cluster = as.formula(sprintf("~%s", UNIT_ID)))
m4 <- feols(as.formula(sprintf("%s ~ treat_post + %s | %s + %s", OUTCOME, covar_fml, UNIT_ID, TIME_VAR)),
            data = df, cluster = as.formula(sprintf("~%s", UNIT_ID)))
m5 <- m4   # same spec — Model 5 is baseline for robustness comparisons

model_list <- list("(1)" = m1, "(2)" = m2, "(3)" = m3, "(4)" = m4, "(5)" = m5)

cm_base <- c("treat_post" = "Treat × Post",
             "treated"    = "Treated",
             "post"       = "Post")
cm_covars <- setNames(COVARS, COVARS)
cm <- c(cm_base, cm_covars)

add_rows_df <- data.frame(
  term  = c("Unit FE", "Time FE", "Controls", "Clustered SE"),
  `(1)` = c("No",  "No",  "No",  "No"),
  `(2)` = c("No",  "No",  "Yes", "No"),
  `(3)` = c("Yes", "No",  "Yes", "Yes"),
  `(4)` = c("Yes", "Yes", "Yes", "Yes"),
  `(5)` = c("Yes", "Yes", "Yes", "Yes"),
  check.names = FALSE
)
# Inspect row count first: nrow(modelsummary(model_list, output = "dataframe"))
# then set: attr(add_rows_df, "position") <- (last_row + 1):(last_row + 4)
attr(add_rows_df, "position") <- 13:16   # adjust if coef count differs

ft_main <- modelsummary(
  model_list,
  stars    = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  coef_map = cm,
  gof_map  = tribble(~raw, ~clean, ~fmt,
                     "nobs",      "Observations", 0,
                     "r.squared", "R²",           3),
  add_rows = add_rows_df,
  title    = "Table X. Difference-in-differences estimates",
  notes    = "Notes: * p<0.1, ** p<0.05, *** p<0.01. Standard errors clustered at unit level in models (3)–(5).",
  output   = "flextable"
) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc2 <- officer::read_docx()
doc2 <- flextable::body_add_flextable(doc2, ft_main)
print(doc2, target = file.path(OUTPUT_DIR, "table_did_main.docx"))
cat(sprintf("  Saved: %s/table_did_main.docx\n", OUTPUT_DIR))

# ── 5. Event-Study Plot ───────────────────────────────────────────────────────
cat("Running event-study model...\n")

df$first_treat_val <- df[[FIRST_TREAT]]
df$time_to_treat   <- df[[TIME_VAR]] - df$first_treat_val
df$time_to_treat[is.na(df$first_treat_val)] <- NA

es_fml <- as.formula(
  sprintf("%s ~ i(time_to_treat, ref = -1) + %s | %s + %s",
          OUTCOME, covar_fml, UNIT_ID, TIME_VAR))
es_mod <- feols(es_fml, data = df, cluster = as.formula(sprintf("~%s", UNIT_ID)))

png(file.path(OUTPUT_DIR, "fig_did_eventstudy.png"), width = 900, height = 550)
iplot(es_mod,
      main = "Event-study: dynamic treatment effects",
      xlab = "Periods relative to treatment onset",
      ylab = "Coefficient (95% CI)")
dev.off()
cat(sprintf("  Saved: %s/fig_did_eventstudy.png\n", OUTPUT_DIR))

# ── 6. Robustness / Placebo Table ────────────────────────────────────────────
cat("Running robustness checks...\n")

# Placebo timing: shift treatment 2 periods earlier (pre-treatment window only)
df$treat_post_placebo <- df$treated *
  as.integer(df[[TIME_VAR]] >= (TREAT_PERIOD - 2)) *
  as.integer(df[[TIME_VAR]] < TREAT_PERIOD)
m_placebo_time <- feols(
  as.formula(sprintf("%s ~ treat_post_placebo + %s | %s + %s",
                     OUTCOME, covar_fml, UNIT_ID, TIME_VAR)),
  data = df[df[[TIME_VAR]] < TREAT_PERIOD, ],
  cluster = as.formula(sprintf("~%s", UNIT_ID)))

# Placebo outcome: use first covariate as fake outcome
m_placebo_out <- feols(
  as.formula(sprintf("%s ~ treat_post + %s | %s + %s",
                     COVARS[1], covar_fml, UNIT_ID, TIME_VAR)),
  data = df, cluster = as.formula(sprintf("~%s", UNIT_ID)))

# Exclude observations within 1 period of treatment onset
df_excl <- df[abs(df[[TIME_VAR]] - TREAT_PERIOD) > 1, ]
m_excl <- feols(
  as.formula(sprintf("%s ~ treat_post + %s | %s + %s",
                     OUTCOME, covar_fml, UNIT_ID, TIME_VAR)),
  data = df_excl, cluster = as.formula(sprintf("~%s", UNIT_ID)))

robust_list <- list(
  "Baseline"       = m5,
  "Placebo timing" = m_placebo_time,
  "Placebo outcome"= m_placebo_out,
  "Excl. boundary" = m_excl
)

ft_robust <- modelsummary(
  robust_list,
  stars   = c("*" = 0.1, "**" = 0.05, "***" = 0.01),
  gof_map = tribble(~raw, ~clean, ~fmt,
                    "nobs",      "Observations", 0,
                    "r.squared", "R²",           3),
  title   = "Table X. Robustness checks",
  notes   = "Notes: * p<0.1, ** p<0.05, *** p<0.01. Clustered SE at unit level.",
  output  = "flextable"
) %>%
  flextable::border_remove() %>%
  flextable::hline_top(border = officer::fp_border(width = 1.5), part = "header") %>%
  flextable::hline(i = 1, border = officer::fp_border(width = 0.75), part = "header") %>%
  flextable::hline_bottom(border = officer::fp_border(width = 1.5), part = "body") %>%
  flextable::font(fontname = "Times New Roman", part = "all") %>%
  flextable::fontsize(size = 12, part = "all") %>%
  flextable::autofit()

doc3 <- officer::read_docx()
doc3 <- flextable::body_add_flextable(doc3, ft_robust)
print(doc3, target = file.path(OUTPUT_DIR, "table_did_robustness.docx"))
cat(sprintf("  Saved: %s/table_did_robustness.docx\n", OUTPUT_DIR))

cat("\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat("DID ANALYSIS COMPLETE\n")
cat(paste(rep("=", 60), collapse = ""), "\n")
cat(sprintf("Outputs in: %s\n", OUTPUT_DIR))
cat("  table_did_descriptive.docx\n")
cat("  table_did_main.docx\n")
cat("  table_did_robustness.docx\n")
cat("  fig_did_trends.png\n")
cat("  fig_did_eventstudy.png\n")
