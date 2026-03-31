# Changelog

## [agent] - 2026-03-31 (3)

### Added
- `skill-quantitative-analysis` v1.2 — imported from gim-home/studio8researchskills
  Covers end-to-end inferential statistics: ANOVA, Tukey HSD, t-tests, chi-squared,
  linear/logistic/ordinal regression, descriptive analysis, and Excel export

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
