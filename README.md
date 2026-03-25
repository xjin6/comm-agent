# Weibo Topic Scraper

A Python scraper for collecting Sina Weibo (新浪微博) topic data for academic research. Scrapes posts, comments, and user profiles under any hashtag topic.

## Features

- **Posts**: ID, content, timestamp, reposts/comments/likes, images, video, topic tags, source device
- **Comments**: Including nested replies (楼中楼), with reply-to relationships
- **User Profiles**: Nickname, gender, location, bio, followers, verification status
- **Smart Pagination**: Auto-detects page count, splits by day/hour to bypass the 50-page search limit
- **Incremental Saving**: Data saved periodically so nothing is lost if interrupted
- **Rate Limiting**: Built-in random delays and retry logic to avoid IP bans

## Output

Three relational tables (CSV + JSON):

| File | Description | Key Fields |
|------|-------------|------------|
| `posts.csv/json` | Topic posts | post_id, user_id, content, publish_time, reposts/comments/likes |
| `comments.csv/json` | Post comments | comment_id, post_id, user_id, reply_to_comment_id |
| `users.csv/json` | User profiles | user_id, nickname, gender, location, followers_count, verified |

Tables link via `post_id` and `user_id`.

## Quick Start

### 1. Install

```bash
git clone https://github.com/YOUR_USERNAME/skill-weibo-topic-scraper.git
cd skill-weibo-topic-scraper
pip install -r requirements.txt
```

### 2. Get Your Cookie

1. Open **weibo.com** in your browser and log in
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Type `document.cookie` and press Enter
5. Copy the output

### 3. Run

```bash
python scripts/main.py \
  --topic "话题名" \
  --cookie "YOUR_COOKIE" \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--topic` | Topic name (without # marks) | Required |
| `--cookie` | Weibo cookie string | Required |
| `--start-date` | Start date (YYYY-MM-DD) | None (no date filter) |
| `--end-date` | End date (YYYY-MM-DD) | Today |
| `--skip-comments` | Skip comment scraping | False |
| `--skip-profiles` | Skip user profile scraping | False |
| `--format` | Output format: csv, json, both | both |
| `--output-dir` | Output directory | output/topic_name/ |
| `--delay-min` | Min request interval (seconds) | 3 |
| `--delay-max` | Max request interval (seconds) | 7 |

## Claude Code Skill

This project includes a [Claude Code](https://claude.com/claude-code) skill that provides an interactive guided experience. To install:

```bash
ln -s /path/to/skill-weibo-topic-scraper ~/.claude/skills/weibo-scraper
```

Then just tell Claude something like "help me scrape a Weibo topic" and it will guide you through the entire process.

## How It Works

1. **Search via s.weibo.com** — uses the desktop search with cookie authentication
2. **Date segmentation** — splits queries by day to bypass the 50-page-per-query limit
3. **Hourly fallback** — if a single day exceeds 50 pages, auto-splits into 24 hourly queries
4. **Page detection** — reads the actual page count from HTML instead of blindly paginating
5. **Comments via AJAX API** — uses `weibo.com/ajax/statuses/buildComments` with cursor-based pagination
6. **Profile via AJAX API** — uses `weibo.com/ajax/profile/info` with in-memory caching

## Limitations

- Weibo search returns max 50 pages (~500 posts) per query. Time segmentation works around this, but at the hourly level there's a hard ceiling of ~500 posts per hour.
- Cookies expire after hours to days. For long scraping jobs, you may need to refresh your cookie.
- The `timescope` parameter only supports hour-level granularity. Minute-level filtering is not supported by Weibo's API.

## Author

**Xin Jin** — xjin6@outlook.com

## License

MIT
