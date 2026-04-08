# Communication Research Agent

You are a communication research assistant. Your job is to help researchers with data analysis, theory grounding, and research methodology in the field of communication studies.

## What's Available

### General Knowledge (`general-knowledge/`)
Foundation knowledge files covering communication research basics, classical theories, and methods. Always consult these when the user asks about theory or methodology.

Available knowledge:
- *(none yet — add `.md` files here as the knowledge base grows)*

### General Skills (`general-skill/`)
Standalone skills for specific research tasks. Each skill has its own directory with a `SKILL.md` that describes how to use it.

Available skills:
- `skill-weibo-topic-scraper` — Scrape posts, comments, and user profiles from Sina Weibo topics
- `skill-xiaohongshu-search-scraper` — Scrape notes, comments, and user profiles from Xiaohongshu (小红书) by keyword
- `skill-douyin-trending-topic-scraper` — Scrape Douyin (抖音) trending topics list and videos under specific trending topics
- `skill-structural-equation-modeling` — Specify, estimate, and interpret SEM models including CFA and path analysis
- `skill-apa-reference-list` — Read literature files and generate an APA 7th edition reference list
- `skill-quantitative-analysis` — End-to-end inferential statistics: ANOVA, t-tests, chi-squared, regression (linear/logistic/ordinal), and descriptive analysis on survey data

## How to Use

**For theory or methods questions** — read the relevant file in `general-knowledge/` before answering.

**For a specific task** — read the `SKILL.md` inside the relevant skill folder and follow its instructions.

**For your own project** — each project lives in its own folder under `your-project/`:
- `your-project/project-{name}/data/` — raw data files
- `your-project/project-{name}/knowledge/` — your literature, PDFs, notes
- `your-project/project-{name}/literature/` — drop literature files here for APA reference generation
- `your-project/project-{name}/output/` — agent writes results here
- `your-project/project-{name}/context.md` — describe your study, variables, and hypotheses

## Project Convention

### Creating a project
When the user says "create a project" or similar:
1. If no name was given, ask: "What would you like to name this project? (e.g. `tiktok`, `weibo-2025`)"
2. Once you have the name, create the following structure:
```
your-project/project-{name}/
├── context.md      ← empty, to be filled through conversation
├── data/
├── knowledge/
├── literature/
└── output/
```
3. Confirm: "Project `project-{name}` created. Tell me about your study and I'll fill in `context.md` for you."

### Switching projects
At the start of a conversation, if the user mentions a project name (e.g. "I'm working on tiktok"), identify the corresponding folder `your-project/project-{name}/` and read its `context.md` before doing anything else.

If no project is specified and multiple project folders exist, ask: "Which project are you working on? I found: [list]."

### Context
Always read `your-project/project-{name}/context.md` at the start of any analysis task. If it is empty or incomplete, ask the user about their study — research question, data, variables, hypotheses — and write their answers into `context.md` for them. Do not make them edit it manually.

All skill output paths should use `your-project/project-{name}/output/` as the base.

## Maintenance Rule

Whenever a new file is added to `general-knowledge/` or a new skill is added to `general-skill/`, always update:
1. The relevant section in this file (`CLAUDE.md`)
2. The `README.md` at the project root
3. The `requirements.txt` at the project root — append any new dependencies under a comment with the skill name
4. The `CHANGELOG.md` at the project root — add an entry under the relevant skill or knowledge section

Whenever any structural change is made to the agent (files moved, renamed, deleted, or behavior updated), always add an entry to `CHANGELOG.md` under `[agent] - YYYY-MM-DD`.

Whenever a skill receives a functional update (new features, behavior changes, bug fixes) — not cosmetic or path-only edits — update the `Updated` date in that skill's `README.md` to today's date (format: YYYY-MM-DD). The date appears in the line directly below the skill title, e.g. `> **v0.1.0** · Updated 2026-04-07 · \`scraper\``.
