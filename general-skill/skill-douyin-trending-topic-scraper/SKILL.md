---
name: skill-douyin-trending-topic-scraper
description: >
  Douyin (抖音) trending topic scraper for academic research — scrapes the hot
  trending list (热搜榜) and/or videos under a specific trending topic by name.
  Collects video descriptions, author info, engagement metrics (likes, comments,
  shares, forwards, downloads), timestamps, and video URLs.
  Use this skill whenever the user wants to collect Douyin data, scrape trending
  topics on Douyin/TikTok China, gather 抖音热搜 data, or analyze Douyin video
  engagement for research purposes.
---

# Douyin Trending Topic Scraper

Scrapes Douyin's trending hot search list (热搜榜) and videos under specific
trending topics. Based on Douyin's mobile API (reverse-engineered). No login
cookie required — the API is accessed directly via mobile app parameters.

> **Note:** These API endpoints were reverse-engineered from the Douyin Android
> app. If you get an error like `API may have changed`, the endpoints may need
> updating. Tell the user and ask if they have an updated API URL.

---

## Step 1 — Choose Mode

Ask the user which mode they want:

| Mode | What it does |
|------|--------------|
| `trending` | Collect the current trending topics list (热搜榜) only — ranks, names, hot values |
| `topic` | Collect videos posted under one specific trending topic |
| `all` | Collect the trending list AND videos for every topic on it (slow — ~30+ topics) |

If the user says something like "给我抓一下今天的热搜" → `trending`.  
If they say "我想要#某话题#下面的视频" → `topic`.  
If they want everything → `all`.

---

## Step 2 — Identify Topic Name (topic mode only)

If mode is `topic`, extract the topic name from the user's message.
- Strip `#` wrappers if present: `#元宵节#` → `元宵节`
- URL decode if needed: `%E5%85%83%E5%AE%B5%E8%8A%82` → `元宵节`
- If vague, ask: "请问你想爬哪个话题？请提供话题名称（不含#）"

---

## Step 3 — Confirm and Run

Confirm the plan with the user, then run the script from the **project root**:

**Mode: trending**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode trending \
  --output-dir "your-project/project-{name}/output/douyin/trending" \
  --format both
```

**Mode: topic**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode topic \
  --topic "话题名称" \
  --output-dir "your-project/project-{name}/output/douyin/话题名称" \
  --format both
```

**Mode: all (trending list + all topic videos)**
```bash
python general-skill/skill-douyin-trending-topic-scraper/scripts/main.py \
  --mode all \
  --output-dir "your-project/project-{name}/output/douyin" \
  --format both \
  --delay-min 3 --delay-max 7
```

**Optional flags:**
- `--format csv` / `--format json` / `--format both` (default: both)
- `--delay-min` / `--delay-max` — seconds between requests in `all` mode (default: 3–7)

---

## Step 4 — Present Results

After the script finishes, report:
- **trending mode**: number of trending topics, date of the list, output file path
- **topic mode**: topic name, number of videos collected, output file path
- **all mode**: number of topics covered, total videos, output directory

Offer next steps: "要对这些数据做分析吗？可以用 skill-quantitative-analysis 继续。"

---

## Output Files

**trending mode** → `trending_YYYY-MM-DD.csv / .json`

| Field | Description |
|-------|-------------|
| rank | Position on hot search list |
| word | Topic name (话题名) |
| hot_value | Hotness score |
| video_count | Number of videos under topic |
| label | Topic label/tag |
| cover_url | Topic cover image URL |

**topic / all mode** → `videos.csv / .json` (one file per topic)

| Field | Description |
|-------|-------------|
| desc | Video description/caption |
| nickname | Author username |
| custom_verify | Author verification label |
| create_time | Post timestamp (YYYY-MM-DD HH:MM:SS) |
| like_count | Number of likes (点赞数) |
| comment_count | Number of comments (评论数) |
| share_count | Number of shares (分享数) |
| forward_count | Number of forwards (转发数) |
| download_count | Number of downloads |
| video_url | Direct video download URL |
| cover_url | Video thumbnail URL |

---

## Error Handling

| Error | Likely cause | Action |
|-------|-------------|--------|
| `API may have changed` | Endpoint outdated | Inform user; ask for updated API URL |
| `Connection refused` / timeout | Network issue or IP blocked | Retry; increase delays |
| Empty `aweme_list` | Topic not found or no videos | Confirm topic name spelling |
| `JSONDecodeError` | Non-JSON response | API endpoint may be dead |

---

## Notes for Academic Use

- No login required — data is from Douyin's public trending API
- Default delay in `all` mode: 3–7 seconds between topic requests
- Video URLs expire quickly — download promptly if needed
- Intended for academic research only; respect platform terms of service
