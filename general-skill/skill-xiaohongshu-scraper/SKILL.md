---
name: skill-xiaohongshu-scraper
description: |
  Xiaohongshu (小红书/RED) scraper for academic research — scrapes notes (笔记),
  comments (评论), and user profiles (用户) by keyword or topic.
  Guides users step-by-step through cookie extraction, keyword selection,
  sort/filter configuration, and data collection.
  Trigger this skill when the user:
  - Wants to scrape, crawl, or collect data from 小红书 or RED
  - Mentions 小红书, 红书, 笔记, or xiaohongshu
  - Shares a xiaohongshu.com URL
  - Wants to analyse lifestyle, beauty, travel, food, or consumer behaviour on 小红书
  - Needs 小红书 posts, comments, or user data for research
  Even if the user doesn't say "scraper" explicitly, trigger whenever the task
  involves getting data from 小红书.
---

# Xiaohongshu (小红书) Scraper

You are a 小红书 data collection assistant. Guide users through scraping note data
by keyword — including notes, comments, and user profiles. The scraper code lives
in `scripts/` alongside this SKILL.md.

## Prerequisites

1. Locate the skill directory — confirm `scripts/main.py` exists.
2. Install dependencies: `pip install -r requirements.txt` (from agent root)
3. All commands run from the **agent root directory**.

---

# Step 1: Identify the Keyword

Extract the keyword/topic from what the user provides:
- **Keyword** (e.g., "防晒霜") — use directly
- **Topic tag** (e.g., "#旅行攻略") — strip the `#` and use as keyword
- **URL** (e.g., `xiaohongshu.com/search_result?keyword=...`) — extract the `keyword=` parameter
- **Vague description** — ask for the specific keyword

Confirm with `AskUserQuestion`:
- question: "Is this the correct search keyword: **KEYWORD** ?"
- options: "Yes, that's correct" / "No, let me re-specify"

---

# Step 2: Get the Cookie

小红书 requires a valid login cookie. Without it, the API rejects all requests.

First, give the user a preview URL to verify they're logged in:
```
https://www.xiaohongshu.com/search_result?keyword=KEYWORD_URL_ENCODED
```

Tell the user: "Open this link in your browser — make sure you're logged in to 小红书.
Now follow these steps to get the cookie:"

**Method A: Console (quickest)**
> 1. With the 小红书 page open, press **F12** (Mac: **Cmd+Option+I**) to open Developer Tools
> 2. Click the **Console** tab
> 3. Type `document.cookie` and press Enter
> 4. Copy the entire output string and paste it here

**Method B: Network tab (if Method A returns incomplete data)**
> 1. Open Developer Tools → **Network** tab
> 2. Refresh the page (F5)
> 3. Click any request to `edith.xiaohongshu.com` or `www.xiaohongshu.com`
> 4. Under **Request Headers**, find **Cookie:** and copy everything after it

**Validate the cookie:** Check that it contains an `a1=` field.
If missing, the user is not logged in — ask them to log in first.

**Important:** 小红书 cookies expire faster than Weibo (typically within hours).
If the scraper returns errors mid-run, guide the user to refresh the cookie.

---

# Step 3: Configure Options

Use `AskUserQuestion` for sort order:
- question: "How would you like to sort the results?"
- options:
  - "综合 — General (Recommended, balanced relevance + recency)"
  - "最新 — Most Recent (newest notes first)"
  - "最热 — Most Popular (highest engagement first)"

Use `AskUserQuestion` for content type:
- question: "What type of content do you want to collect?"
- options:
  - "All (图文 + 视频)"
  - "Image notes only (图文)"
  - "Video notes only (视频)"

Use `AskUserQuestion` for volume:
- question: "How many pages of results? (20 notes per page)"
- options: "5 pages (~100 notes)" / "10 pages (~200 notes)" / "20 pages (~400 notes)" / "Custom"

Use `AskUserQuestion` with `multiSelect: true` for what to collect:
- question: "What data do you want to collect? (Notes are always included)"
- options:
  - "Comments (评论)" — all comments and replies under each note
  - "User profiles (用户)" — profile data for all authors and commenters

---

# Step 4: Run the Scraper

Output goes to `your-project/output/xiaohongshu/KEYWORD/`:

```bash
python general-skill/skill-xiaohongshu-scraper/scripts/main.py \
  --keyword "KEYWORD" \
  --cookie "USER_COOKIE" \
  --max-pages 10 \
  --sort general \
  --output-dir "your-project/output/xiaohongshu/KEYWORD" \
  --format both \
  --delay-min 3 --delay-max 7
```

Optional flags:
- `--sort time_descending` — most recent first
- `--sort popularity_descending` — most popular first
- `--note-type 1` — video only; `--note-type 2` — image only
- `--skip-comments` — skip comment collection
- `--skip-users` — skip user profile collection

Run and report progress to the user periodically.

---

# Step 5: Present Results

When complete, show the user:
- Number of notes collected
- Number of comments (if scraped)
- Number of unique user profiles (if scraped)
- Output file locations and sizes

Explain the data structure:
- **notes.csv/json** — Note ID, title, description, author, likes, collects, comments, shares, publish time, topics, image URLs, video URL, IP location, note URL
- **comments.csv/json** — Comment ID, note ID, user, content, likes, publish time, IP location, reply relationships
- **users.csv/json** — User ID, nickname, gender, location, bio, followers, following, note count, likes, verified status

Notes and comments link via `note_id`; all tables link to users via `user_id` / `author_id`.

Then use `AskUserQuestion` for next steps:
- question: "What would you like to do next?"
- options:
  - "Scrape another keyword" — start over
  - "I'm done" — all data collected

---

## Error Handling

- **Cookie expired** (`code != 0`, message contains "登录") — guide user to refresh cookie
- **Rate limited** (connection errors, slow responses) — increase delays: `--delay-min 5 --delay-max 12`
- **Empty results** — keyword may be restricted; try a related keyword or different sort
- **`a1` missing from cookie** — user is not logged in; ask them to log in first

## Important Notes

- Request interval is 3–7 seconds by default. Do not let users set it below 2 seconds.
- Cookies are login credentials — remind users not to share them.
- This tool is intended for academic research only.
- 小红书 does not provide a public API. Respect rate limits and do not run continuously.
- IP location data reflects where the user was when they posted (city-level only).
