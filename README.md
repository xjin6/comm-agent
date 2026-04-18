# Communication Research Agent

An AI-powered research assistant for communication studies — from data collection to paper writing.

Built on [Claude Code](https://claude.ai/claude-code), this agent gives researchers a shared foundation of domain knowledge and reusable skills, while each user works in their own isolated `your-project/` folder.

## Structure

```
comm-agent/
├── CLAUDE.md                       # Agent instructions
├── general-knowledge/              # Shared theory & methods knowledge base
├── general-skill/                  # Reusable research skills (scraping, analysis, etc.)
│   ├── skill-weibo-topic-scraper/
│   ├── skill-xiaohongshu-search-scraper/
│   ├── skill-douyin-trending-topic-scraper/
│   ├── skill-twitter-search-scraper/
│   ├── skill-structural-equation-modeling/
│   ├── skill-quantitative-analysis/
│   └── skill-apa-reference-list/
└── your-project/                   # Your personal workspace — intentionally empty
    └── project-{name}/             # Created by the agent when you start a project
        ├── context.md              # Describe your study here
        ├── data/                   # Your raw data
        ├── knowledge/              # Your literature & notes
        ├── literature/             # Drop PDFs/BIB/RIS here for APA reference generation
        └── output/                 # Agent-generated results
```

## General Knowledge

Foundation files the agent reads when answering theory or methods questions.

| File | Description |
|------|-------------|
| *(none yet)* | |

## General Skills

Standalone, reusable skills for specific research tasks.

| Skill | Version | Description |
|-------|---------|-------------|
| [skill-weibo-topic-scraper](./general-skill/skill-weibo-topic-scraper/) | v0.1.0 | Scrape Sina Weibo topic posts, comments, and user profiles |
| [skill-xiaohongshu-search-scraper](./general-skill/skill-xiaohongshu-search-scraper/) | v0.1.0 | Scrape Xiaohongshu notes, comments, and user profiles by keyword |
| [skill-douyin-trending-topic-scraper](./general-skill/skill-douyin-trending-topic-scraper/) | v0.1.0 | Scrape Douyin trending topics list and videos under specific trending topics |
| [skill-twitter-search-scraper](./general-skill/skill-twitter-search-scraper/) | v0.1.0 | Scrape Twitter / X.com tweets, profiles, and media by keywords and dates |
| [skill-structural-equation-modeling](./general-skill/skill-structural-equation-modeling/) | v0.2.0 | EFA / CFA / Full SEM / Mediation / Moderation with MI optimization, item diagnostics, measurement quality tables, and APA publication tables |
| [skill-sentiment-analysis](./general-skill/skill-sentiment-analysis/) | v0.1.0 | Run LLM-based sentiment and emotion analysis on datasets using academic coding schemes (Ekman, Plutchik, etc.), outputting automated statistical reports |
| [skill-apa-reference-list](./general-skill/skill-apa-reference-list/) | v0.1.0 | Read literature files and generate an APA 7th edition reference list |
| [skill-quantitative-analysis](./general-skill/skill-quantitative-analysis/) | v0.1.0 | End-to-end inferential statistics: ANOVA, t-tests, chi-squared, regression, and descriptive analysis on survey data |

## Getting Started

`your-project/` is intentionally empty — create your own project to get started:

1. Tell the agent: *"Create a project called [name]"* — it will create `your-project/project-{name}/` with the four standard folders (`data/`, `knowledge/`, `literature/`, `output/`) and an empty `context.md`
2. Describe your study and the agent will fill in `context.md` for you
3. Drop your data into `your-project/project-{name}/data/`
4. Drop literature files (PDF, DOCX, BIB, RIS, TXT) into `your-project/project-{name}/literature/`
5. At the start of each session, tell the agent which project you're working on

## Vision

A modular end-to-end research agent that helps communication researchers go from a research question to a publishable paper — handling the tedious parts so researchers can focus on thinking.

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

## License

CC BY-NC-ND 4.0
