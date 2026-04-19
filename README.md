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
│   ├── skill-apa-reference-list/
│   ├── skill-causal-inference/
│   ├── skill-sentiment-analysis/
│   ├── skill-social-network-analysis/
│   └── skill-psychometric-network-analysis/
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
| [skill-twitter-search-scraper](./general-skill/skill-twitter-search-scraper/) | v0.1.0 | Scrape Twitter/X tweets, profiles, and media by keyword and date range |
| [skill-structural-equation-modeling](./general-skill/skill-structural-equation-modeling/) | v0.4.0 | EFA / CFA / Full SEM / Mediation (PROCESS templates) / Moderation with bootstrap CI, MI optimization, and APA tables |
| [skill-apa-reference-list](./general-skill/skill-apa-reference-list/) | v0.1.0 | Read literature files and generate an APA 7th edition reference list |
| [skill-quantitative-analysis](./general-skill/skill-quantitative-analysis/) | v0.1.0 | End-to-end inferential statistics: ANOVA, t-tests, chi-squared, regression, and descriptive analysis on survey data |
| [skill-causal-inference](./general-skill/skill-causal-inference/) | v0.1.0 | Quasi-experimental causal methods: DID, PSM, PSW, IV, RDD with R templates and APA Word tables |
| [skill-sentiment-analysis](./general-skill/skill-sentiment-analysis/) | v0.1.0 | In-session LLM-based sentiment/emotion coding for tabular text data |
| [skill-social-network-analysis](./general-skill/skill-social-network-analysis/) | v0.1.0 | SNA pipeline: network construction, centrality, community detection, QAP comparison |
| [skill-psychometric-network-analysis](./general-skill/skill-psychometric-network-analysis/) | v0.1.0 | GGM / EBIC-glasso estimation, bootnet stability, NCT comparison, cross-lagged panel networks |

## Getting Started

`your-project/` is intentionally empty — create your own project to get started:

1. Tell the agent: *"Create a project called [name]"* — it will create `your-project/project-{name}/` with the four standard folders (`data/`, `knowledge/`, `literature/`, `output/`) and an empty `context.md`
2. Describe your study and the agent will fill in `context.md` for you
3. Drop your data into `your-project/project-{name}/data/`
4. Drop literature files (PDF, DOCX, BIB, RIS, TXT) into `your-project/project-{name}/literature/`
5. At the start of each session, tell the agent which project you're working on

## Vision

A modular end-to-end research agent that helps communication researchers go from a research question to a publishable paper — handling the tedious parts so researchers can focus on thinking.

## Authors

Sorted by number of general skills authored or co-authored.

**Xin Jin** (@xjin6) · Microsoft · xjin6@outlook.com · 6 skills
**Sha Qiu** (@sarahqiu-lab) · University of Macau · sarahq2025@gmail.com · 3 skills
**Yundi Zhang** (@Zhang-Yundi) · Fudan University · yd.yundi@gmail.com · 2 skills
**Lihan Yan** (@Lihan-YAN) · Nanjing University · Lihan-YAN@users.noreply.github.com · 1 skill
**Xingjian Wang** (@W-Klaus) · Tsinghua University
**Qianying Ye** (@qianyingye) · The Hong Kong Polytechnic University

## License

CC BY-NC-ND 4.0
