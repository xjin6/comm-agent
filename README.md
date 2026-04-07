# Communication Research Agent

An AI-powered research assistant for communication studies — from data collection to paper writing.

Built on [Claude Code](https://claude.ai/claude-code), this agent gives researchers a shared foundation of domain knowledge and reusable skills, while each user works in their own isolated `your-project/` folder.

## Structure

```
comm-agent/
├── general-knowledge/        # Shared theory & methods knowledge base
├── general-skill/            # Reusable research skills (scraping, analysis, etc.)
├── your-project/             # Your personal workspace (not shared)
│   ├── project-tiktok/       # One folder per project
│   │   ├── context.md        # Describe your study here
│   │   ├── data/             # Your raw data
│   │   ├── knowledge/        # Your literature & notes
│   │   ├── literature/       # Drop PDFs/BIB/RIS here for APA reference generation
│   │   └── output/           # Agent-generated results
│   └── project-weibo/        # Another project
│       └── ...
└── CLAUDE.md                 # Agent instructions
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
| [skill-structural-equation-modeling](./general-skill/skill-structural-equation-modeling/) | v0.1.0 | Specify, estimate, and interpret SEM models including CFA and path analysis |
| [skill-apa-reference-list](./general-skill/skill-apa-reference-list/) | v0.1.0 | Read literature files and generate an APA 7th edition reference list |
| [skill-quantitative-analysis](./general-skill/skill-quantitative-analysis/) | v0.1.0 | End-to-end inferential statistics: ANOVA, t-tests, chi-squared, regression, and descriptive analysis on survey data |

## Getting Started

1. Tell the agent: *"Create a project called [name]"* — it will create `your-project/project-{name}/` with all the required folders
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
