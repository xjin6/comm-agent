---
name: skill-weibo-topic-scraper
description: |
  Sina Weibo topic scraper for academic research — scrapes all posts, comments, and user profiles
  under any Weibo hashtag topic. Guides users step-by-step through login, cookie extraction, topic
  selection, date range configuration, and data collection.
  Trigger this skill when the user:
  - Wants to scrape, crawl, or collect data from Weibo (微博)
  - Mentions Weibo topics (话题), super topics (超话), or trending searches (热搜)
  - Shares a weibo.com or s.weibo.com URL
  - Wants to do sentiment analysis, social media research, or public opinion analysis on Weibo
  - Needs Weibo posts, comments, or user profile data for research
  Even if the user doesn't say "scraper" explicitly, trigger whenever the task involves getting data from Weibo.
---

# Weibo Topic Scraper

You are a Weibo data collection assistant. Your job is to guide users through scraping topic data
from Sina Weibo, including posts, comments, and user profiles. The scraper code lives in the
`scripts/` directory alongside this SKILL.md.

## Prerequisites

Before starting, verify the environment:

1. Locate the skill directory — the folder containing this SKILL.md file. It should also contain
   a `scripts/` directory with `main.py` and other Python files.
2. Check `scripts/main.py` exists. If not, tell the user to clone or download the project first.
3. Install dependencies if needed: `pip install -r requirements.txt` (run from the skill directory)

All `python` commands below run from the skill directory (where SKILL.md lives).

## Workflow

Guide the user through each step. Use the `AskUserQuestion` tool whenever a choice or confirmation
is needed — present a clean selection UI so users can click instead of typing. Minimize free-text
input; prefer structured choices wherever possible.

# Step 1: Identify the Topic

Extract the topic name from whatever the user provides:
- **Topic name** (e.g., "再见爱人") — use directly
- **Weibo URL** (e.g., `s.weibo.com/weibo?q=%23再见爱人%23`) — URL-decode the `q=` parameter, strip `#` marks
- **Vague description** (e.g., "that variety show everyone's talking about") — ask for the specific topic name

After extracting, use `AskUserQuestion` to confirm:
- question: "Is this the correct topic: **#TOPIC_NAME#** ?"
- options: "Yes, that's correct" / "No, let me re-specify"

# Step 2: Get the Cookie

This is the critical step — without a valid cookie, the Weibo API rejects all requests.

First, generate a preview URL so the user can verify the topic exists. URL-encode the topic name
and output a clickable link:

```
https://s.weibo.com/weibo?q=%23TOPIC_NAME_URL_ENCODED%23
```

Tell the user: "Open this link in your browser — make sure you're logged in to Weibo. You should
see search results for your topic. Now follow these steps to get the cookie:"

**Method A: Quick way (Console)**

> 1. With the Weibo page open, press **F12** (Mac: **Cmd+Option+I**) to open Developer Tools
> 2. Click the **Console** tab at the bottom
> 3. Type `document.cookie` and press Enter
> 4. Copy the entire output string and paste it here

**Method B: From Network tab (if Method A doesn't work or returns incomplete data)**

> 1. With the Weibo page open, press **F12** (Mac: **Cmd+Option+I**) to open Developer Tools
> 2. Click the **Network** tab at the top — **not** Elements, not Sources, specifically **Network**
> 3. Refresh the page (F5 or Cmd+R) so it captures new requests
> 4. In the request list on the left, look for requests that start with `weibo?q=` — these are the
>    actual page requests. **Ignore** static files like `.js`, `.css`, `.png` — those won't have cookies
> 5. Click one of the `weibo?q=` requests
> 6. In the right panel, you'll see **Headers** — scroll down past "General" and "Response Headers"
>    to find **Request Headers**
> 7. Find the line that says **Cookie:** — copy everything after the colon

If the user is confused about which request to click: any request whose name starts with `weibo`
or contains the topic name is correct. Requests named `bootstrap.js`, `vue.min.js`, `katex.min.js`
etc. are static resources and typically won't carry the user's cookie.

**Validate the cookie:** Check that it contains a `SUB=` field. If missing, the user likely isn't
logged in or copied it incorrectly — ask them to retry.

**Important:** Warn the user that cookies expire (typically hours to days). If the scraper reports
an expired cookie mid-run, they'll need to get a fresh one. The browser can stay open or closed —
once the cookie string is copied, it works independently of the browser.

# Step 3: Set the Date Range

Use `AskUserQuestion` to determine the scope:
- question: "What time range do you want to scrape?"
- options:
  - "Just today" — quick test with today's data
  - "Last 7 days" — recent week of discussions
  - "Last 30 days" — recent month of discussions
  - "Custom range" — I'll pick the start and end dates

If "Custom range" is selected, guide the user through date selection with `AskUserQuestion` step
by step (no free-text typing needed):

1. Ask **start year**:
   - question: "Start year?"
   - options: list recent years, e.g. "2024" / "2025" / "2026"

2. Ask **start month**:
   - question: "Start month?"
   - options: "Jan (1)" / "Feb (2)" / "Mar (3)" / "Apr (4)" — show 4 at a time, group logically
     (Q1, Q2, Q3, Q4). If the user needs a month not shown, they can use "Other".

3. Ask **end year** and **end month** in the same way. If start and end are likely the same year,
   pre-select it and only ask for the end month.

Compute start_date as the 1st of the start month, end_date as the last day of the end month.

If the range spans more than 1 month, use `AskUserQuestion` to recommend batching:
- question: "This covers multiple months. How should we handle it?"
- options:
  - "Monthly batches (Recommended)" — one month at a time, safer if cookie expires, smaller files
  - "All at once" — scrape the entire range in a single run

# Step 4: Confirm Options

Use `AskUserQuestion` with `multiSelect: true` to let the user pick what to collect:
- question: "What data do you want to collect? (Posts are always included)"
- multiSelect: true
- options:
  - "Comments" — all comments under each post
  - "User profiles" — profile data for all posters and commenters

Then use `AskUserQuestion` for output format:
- question: "What output format?"
- options:
  - "Both CSV + JSON (Recommended)" — CSV for Excel/SPSS, JSON for Python/R
  - "CSV only" — spreadsheet-friendly
  - "JSON only" — full nested data for programmatic analysis

# Step 5: Run the Scraper

Output data should be saved to the user's Desktop, not inside the skill directory. Use this path:
```
~/Desktop/output-weibo-topic-scraper/TOPIC_NAME/
```

For monthly batches, add the month:
```
~/Desktop/output-weibo-topic-scraper/TOPIC_NAME/2025-01/
```

Assemble and execute the command:

```bash
python scripts/main.py \
  --topic "TOPIC_NAME" \
  --cookie "USER_COOKIE" \
  --start-date YYYY-MM-DD \
  --end-date YYYY-MM-DD \
  --output-dir ~/Desktop/output-weibo-topic-scraper/TOPIC_NAME \
  --format both \
  --delay-min 3 --delay-max 7
```

Optional flags:
- `--skip-comments` — skip comment scraping
- `--skip-profiles` — skip user profile scraping

Run in the background and report progress to the user periodically.

# Step 6: Present Results

When complete, show the user a summary:
- Number of posts collected
- Number of comments (if scraped)
- Number of unique user profiles (if scraped)
- Output file locations and sizes

Explain the data structure:
- **posts.csv/json** — Post ID, user, content, timestamp, reposts/comments/likes, images, topic tags, source device
- **comments.csv/json** — Comment ID, post ID, user, content, timestamp, likes, reply-to relationship
- **users.csv/json** — User ID, nickname, gender, location, bio, follower/following counts, verification status
- Posts and comments link via `post_id`; all tables link to users via `user_id`

Then use `AskUserQuestion` for next steps:
- question: "What would you like to do next?"
- options:
  - "Scrape another month" — continue with the next time period
  - "Scrape a different topic" — start over with a new topic
  - "I'm done" — all data collected

## Error Handling

- **Cookie expired** ("Cookie已失效" in logs) — guide the user to get a fresh cookie, resume from where it stopped
- **Rate limited** ("触发限流" in logs) — the scraper auto-pauses and retries; if persistent, suggest increasing delays (`--delay-min 5 --delay-max 10`)
- **High volume day** (hits 50-page limit) — the scraper automatically subdivides by hour; no user action needed

## Important Notes

- Request interval is 3-7 seconds by default to avoid IP bans. Don't let users set it lower than 2 seconds.
- Cookies are login credentials — remind users not to share them with third parties.
- This tool is intended for academic research purposes.
- Weibo search returns a maximum of 50 pages per query. The scraper works around this by splitting
  queries into daily and hourly time windows, but a hard ceiling of ~500 posts per hour-long window
  exists. For extremely viral topics, some peak-hour data may be truncated.
