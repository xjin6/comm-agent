# Changelog

## [agent] - 2026-04-18

### Added
- `skill-twitter-search-scraper` v0.1.0 — scrape Twitter / X.com tweets, profiles, and media by keywords and dates with cookie-based auth

---

## [agent] - 2026-04-12 (2)

### Added
- `CLAUDE.md` — Git Convention section: require explicit Author+Committer via env vars, GitHub ID as author name, correct gh account switching, no Claude co-author trailers
- `CLAUDE.md` — Skill Installation Convention section: symlink `general-skill/skill-{name}` → `~/.claude/skills/skill-{name}` only; no project-level installs

---

## [agent] - 2026-04-12

### Changed
- `your-project/` cleared — removed all sample/test project folders; folder is now intentionally empty
- `README.md` updated — Getting Started section explicitly states `your-project/` is empty by design; directory tree simplified to a single `project-{name}/` template
- Removed `your-project/README.md` — project creation flow consolidated into root README only
- `CLAUDE.md` reviewed and tightened:
  - Added fallback for empty `general-knowledge/` — answer from training knowledge if no file exists
  - Added empty-project-folder handling — agent prompts user to create a project when `your-project/` is empty
  - Removed redundant folder structure listing from "How to Use"; now references Project Convention section
  - Maintenance Rule: explicitly names `## What's Available` as the section to update; clarifies `requirements.txt` format as Python pip (`package>=version`)

---

## [agent] - 2026-04-08

### Changed
- `skill-structural-equation-modeling` v0.1.0 → v0.2.0 — MI optimization loop (auto-adds
  same-scale residual covariances until CFI ≥ .90), item diagnostic (flags λ < .50),
  measurement quality table (α, ω, CR, AVE, latent correlations), optional APA publication
  tables (demographics, validity, competing models, structural paths, bootstrap mediation),
  updated path diagram specs (black/white, solid/dashed significance lines)

---

## [agent] - 2026-04-07

### Added
- `skill-douyin-trending-topic-scraper` v0.1.0 — scrape Douyin trending topics list (热搜榜)
  and videos under specific topics; three modes: trending / topic / all;
  no login required; outputs rank, hot value, video count, engagement metrics to CSV/JSON

---

## [agent] - 2026-04-01

### Added
- `skill-xiaohongshu-search-scraper` v0.1.0 — scrape notes, comments, and user profiles
  from 小红书 by keyword; cookie-based auth, sort/filter options, incremental saving

---

## [agent] - 2026-03-31 (3)

### Added
- `skill-quantitative-analysis` v1.2 — end-to-end inferential statistics: ANOVA, Tukey HSD,
  t-tests, chi-squared, linear/logistic/ordinal regression, descriptive analysis, and Excel export

---

## [agent] - 2026-03-31 (2)

### Changed
- `skill-apa-reference-list` — upgraded metadata extraction to three-method pipeline: (1) DOI → CrossRef API lookup, (2) PDF DocInfo/XMP parsing via pymupdf/pypdf, (3) PDF content reading; skill now merges all three and picks the most reliable result per field

## [agent] - 2026-03-31

### Added
- `skill-apa-reference-list` — new skill that reads files from `your-project/literature/` and generates an APA 7th edition reference list; supports PDF, DOCX, TXT, BIB, and RIS formats; outputs to conversation and `your-project/output/apa_references.md`
- `your-project/literature/` folder for dropping literature files before running the APA skill

---

## [agent] - 2026-03-29 (3)

### Added
- `skill-structural-equation-modeling` — full skill with step-by-step workflow for EFA, CFA,
  full SEM, mediation, and moderation analysis
- Bundled scripts: `load_data.py`, `efa_analysis.py`, `sem_analysis.py`
- All outputs write to `your-project/output/sem/`

## [agent] - 2026-03-29 (2)

### Added
- `skill-structural-equation-modeling` — new skill scaffold for SEM, CFA, and path analysis

---

## [agent] - 2026-03-29

### Added
- `your-project/` folder with `data/`, `knowledge/`, `output/` subfolders for per-user workspaces
- `your-project/context.md` template for users to describe their study
- Root-level `LICENSE`, `requirements.txt`, `CHANGELOG.md` (consolidated from skill level)
- `.gitignore` rules to keep `your-project/data/`, `your-project/knowledge/`, `your-project/output/` contents untracked

### Changed
- Skill output now writes to `your-project/output/` instead of `~/Desktop/`
- `skill-weibo-topic-scraper` commands now run from agent root directory
- `CLAUDE.md` updated with project folder convention, context.md workflow, and maintenance rules
- `README.md` updated to reflect full agent structure

### Removed
- Skill-level `LICENSE`, `requirements.txt`, `CHANGELOG.md`, `.gitignore` from `skill-weibo-topic-scraper`

---

## skill-weibo-topic-scraper

### [0.1.0] - 2026-03-26

#### Added
- Initial release
- Topic post scraping via s.weibo.com with cookie authentication
- Comment scraping via AJAX API with cursor-based pagination
- User profile scraping with in-memory caching
- Smart pagination: auto-detects page count from HTML
- Date segmentation (day → hour) to bypass 50-page search limit
- Incremental saving to prevent data loss on interruption
- CSV + JSON dual output with UTF-8 BOM for Excel compatibility
- Claude Code skill with step-by-step guided workflow
