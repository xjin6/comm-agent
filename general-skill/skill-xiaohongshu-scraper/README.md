# Xiaohongshu (小红书) Scraper

A Python scraper for collecting 小红书 (RED) note data for academic research. Scrapes notes (笔记), comments (评论), and user profiles (用户) by keyword search.

## Features

- **Notes**: ID, title, description, author, likes/collects/comments/shares, publish time, topic tags, image/video URLs, IP location
- **Comments**: Including nested replies, with reply-to relationships
- **User Profiles**: Nickname, gender, location, bio, followers, verified status
- **Sort options**: 综合 (general) | 最新 (newest) | 最热 (most popular)
- **Content filter**: All | Image notes | Video notes
- **Incremental saving**: Data saved after each page — nothing lost if interrupted
- **Rate limiting**: Built-in random delays to avoid bans

## Output

Three relational tables (CSV + JSON) saved to `your-project/output/xiaohongshu/KEYWORD/`:

| File | Description | Key Fields |
|------|-------------|------------|
| `notes.csv/json` | Notes | note_id, author_id, title, desc, liked_count, collected_count, comment_count, publish_time, topics, ip_location |
| `comments.csv/json` | Comments + replies | comment_id, note_id, user_id, content, like_count, parent_comment_id |
| `users.csv/json` | User profiles | user_id, nickname, gender, location, followers, verified |

Tables link via `note_id` and `user_id`.

## Quick Start

### 1. Install

```bash
pip install -r requirements.txt   # from agent root
```

### 2. Get Your Cookie

1. Open **xiaohongshu.com** in your browser and log in
2. Press **F12** → **Console** tab
3. Type `document.cookie` and press Enter
4. Copy the output — confirm it contains `a1=`

### 3. Run

```bash
python general-skill/skill-xiaohongshu-scraper/scripts/main.py \
  --keyword "防晒霜" \
  --cookie "YOUR_COOKIE" \
  --max-pages 10 \
  --output-dir "your-project/output/xiaohongshu/防晒霜"
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--keyword` | Search keyword | Required |
| `--cookie` | 小红书 cookie string | Required |
| `--max-pages` | Max pages to scrape (20 notes/page) | 10 |
| `--sort` | `general` / `time_descending` / `popularity_descending` | `general` |
| `--note-type` | 0=all, 1=video, 2=image | 0 |
| `--skip-comments` | Skip comment collection | False |
| `--skip-users` | Skip user profile collection | False |
| `--format` | `csv` / `json` / `both` | `both` |
| `--output-dir` | Output directory | Required |
| `--delay-min` | Min request interval (seconds) | 3.0 |
| `--delay-max` | Max request interval (seconds) | 7.0 |

## Differences from Weibo Scraper

| Feature | Weibo | 小红书 |
|---------|-------|--------|
| Auth field | `SUB=` in cookie | `a1=` in cookie |
| Search unit | Topic (话题) | Keyword / topic tag |
| Cookie lifetime | Hours to days | Hours (refresh more often) |
| Content types | Posts + comments | Notes (图文/视频) + comments |
| Max results | ~500/hour (paginated by time) | ~200–400/keyword (paginated by page) |

## Scripts

| Script | Description |
|--------|-------------|
| `scripts/main.py` | Main entry point — orchestrates the full scraping workflow |
| `scripts/xhs_client.py` | API client — cookie auth, request signing, rate limiting |
| `scripts/data_models.py` | Data classes and API response parsers |
| `scripts/exporters.py` | CSV and JSON export functions |

## Author

**Xin Jin** — xjin6@outlook.com

## License

MIT
