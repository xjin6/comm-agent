# Communication Research Agent

An AI-powered research assistant for communication studies — from data collection to paper writing.

Built on [Claude Code](https://claude.ai/claude-code), this agent gives researchers a shared foundation of domain knowledge and reusable skills, while each user works in their own isolated `your-project/` folder.

## Structure

```
comm-agent/
├── general-knowledge/   # Shared theory & methods knowledge base
├── general-skill/       # Reusable research skills (scraping, analysis, etc.)
├── your-project/             # Your personal workspace (not shared)
│   ├── context.md       # Describe your study here
│   ├── data/            # Your raw data
│   ├── knowledge/       # Your literature & notes
│   ├── literature/      # Drop PDFs/BIB/RIS here for APA reference generation
│   └── output/          # Agent-generated results
└── CLAUDE.md            # Agent instructions
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
| [skill-xiaohongshu-scraper](./general-skill/skill-xiaohongshu-scraper/) | v0.1.0 | Scrape Xiaohongshu (小红书) notes, comments, and user profiles by keyword |
| [skill-structural-equation-modeling](./general-skill/skill-structural-equation-modeling/) | v0.1.0 | Specify, estimate, and interpret SEM models including CFA and path analysis |
| [skill-apa-reference-list](./general-skill/skill-apa-reference-list/) | v0.1.0 | Read literature files and generate an APA 7th edition reference list |
| [skill-quantitative-analysis](./general-skill/skill-quantitative-analysis/) | v1.2 | End-to-end inferential statistics: ANOVA, t-tests, chi-squared, regression, and descriptive analysis on survey data |

## Getting Started

1. Fill in `your-project/context.md` with your study overview, research questions, and variables
2. Drop your data into `your-project/data/`
3. Put your literature and notes in `your-project/knowledge/`
4. Drop literature files (PDF, DOCX, BIB, RIS, TXT) into `your-project/literature/` for APA reference generation
5. Ask the agent to help — it will read your context automatically

## Vision

A modular end-to-end research agent that helps communication researchers go from a research question to a publishable paper — handling the tedious parts so researchers can focus on thinking.

## Author

**Xin Jin** — xjin6@outlook.com

## License

MIT
