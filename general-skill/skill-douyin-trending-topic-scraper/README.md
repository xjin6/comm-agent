# Douyin Trending Topic Scraper

> **v0.1.0** · Updated 2026-04-07 · `scraper`

A Python scraper for collecting Douyin trending topic data for academic research. Scrapes the hot search list and videos posted under specific trending topics.

## Features

- **Trending List**: Topic ranks, names, hot values, video counts
- **Topic Videos**: Description, author info, engagement metrics, timestamps, video URLs
- **Three modes**: Trending list only / single topic / all trending topics at once
- **No login required**: Uses Douyin's mobile API — no cookie setup needed
- **Incremental saving**: Results saved as collected

## Output

**Trending list** → `trending_YYYY-MM-DD.csv / .json`

| File | Description | Key Fields |
|------|-------------|------------|
| `trending_YYYY-MM-DD.csv/json` | Hot search list | rank, word, hot_value, video_count, label |

**Topic videos** → `videos.csv / .json` (one per topic folder)

| File | Description | Key Fields |
|------|-------------|------------|
| `videos.csv/json` | Videos under a topic | desc, nickname, custom_verify, create_time, like_count, comment_count, share_count, forward_count, download_count, video_url |

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt   # from agent root
```

### 2. Run

**Collect today's trending list:**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode trending \
  --output-dir "your-project/project-{name}/output/douyin/trending"
```

**Collect videos for one topic:**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode topic \
  --topic "元宵节" \
  --output-dir "your-project/project-{name}/output/douyin/元宵节"
```

**Collect everything (trending list + all topic videos):**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode all \
  --output-dir "your-project/project-{name}/output/douyin"
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--mode` | `trending` / `topic` / `all` | Required |
| `--topic` | Topic name, no `#` marks (required for `topic` mode) | — |
| `--output-dir` | Output directory | Required |
| `--format` | `csv` / `json` / `both` | `both` |
| `--delay-min` | Min interval between requests, seconds (`all` mode) | 3.0 |
| `--delay-max` | Max interval between requests, seconds (`all` mode) | 7.0 |

## How It Works

The scraper calls Douyin's internal mobile API (reverse-engineered from the Android app). No browser automation or login is required — requests are made directly with mobile app headers and device parameters.

- **Trending API**: `aweme/v1/hot/search/list/` — returns the current hot search list with ranks and hot values
- **Topic API**: `aweme/v1/hot/search/video/list/` — returns videos posted under a specific trending topic

> **Note:** These endpoints were originally reverse-engineered from Douyin v8.6.0 (2020). If requests return unexpected responses, the API may have been updated.

## Comparison with Other Scrapers

| Feature | Douyin | Weibo | Xiaohongshu |
|---------|--------|-------|-------------|
| Auth required | No | Cookie (`SUB=`) | Cookie (`a1=`) |
| Data type | Videos | Posts + comments | Notes (image/video) |
| Trending support | Yes | No | No |
| Comment scraping | No | Yes | Yes |
| User profiles | No | Yes | Yes |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/main.py` | Main entry point — trending list, topic videos, or all-in-one |

## Author

**Xin Jin** (@xjin6) · xjin6@outlook.com

## License

CC BY-NC-ND 4.0
