---
name: skill-twitter-search-scraper
description: Scrape, crawl, and search Twitter / X.com tweets, profiles, and media by keywords and dates. This skill automates a complex, authenticated Python spider to collect tweets and export them to a CSV file. Use this skill whenever the user asks to "scrape Twitter," "crawl X," "search tweets," "collect Twitter data," "download tweets about [topic]," or any variation of extracting posts from Twitter/X.
---




# Twitter / X.com Keyword Search Scraper

This skill automates a robust, reverse-engineered Python spider that searches Twitter/X by keyword and date range, collecting detailed tweet data (text, metrics, media links, user info) and exporting it to CSV.

The spider relies on authenticated endpoints and requires active X.com session cookies to function.

## Workflow

When the user invokes this skill, follow these steps strictly in order:

### 1. Identify Target Parameters

Determine the following parameters from the user's prompt:
- `keyword`: The search query (can be complex, e.g., `(#AI OR #MachineLearning)`)
- `start_date`: e.g., `2025-01-01`
- `end_date`: e.g., `2025-01-31`
- `save_file_name`: The prefix for the output CSV file (e.g., `ai_tweets`).

If any of these are missing, **ask the user** to provide them before proceeding.

### 2. Check for Cookies

The spider *strictly requires* valid X.com cookies to bypass API restrictions. X's search endpoints are not accessible anonymously anymore.

Check the current working directory for:
1. `cookies.txt` (Contains valid X.com cookies, one per line)
2. `cookie_index.txt` (Contains an integer, usually `0`, tracking the current cookie in rotation)

**If these files do NOT exist, or if the user asks if there is another way:**
Tell the user explicitly:
> "To scrape Twitter/X, you *must* provide valid session cookies. X has locked down anonymous search access, so the script needs to act as a logged-in user to fetch data.
>
> **How to get cookies:**
> 1. Log in to x.com in your browser.
> 2. Open Developer Tools (F12) -> Network tab.
> 3. Refresh the page or perform a search.
> 4. Click any `graphql` or `SearchTimeline` request.
> 5. Look for the `cookie:` header in the Request Headers, copy its entire value.
> 6. Save it to a file named `cookies.txt` in this directory (if you have multiple accounts, put one cookie string per line).
>
> Also, create a file named `cookie_index.txt` containing the number `0`."

Do NOT attempt to run the script without these files. Wait for the user to confirm they have created them.

### 3. Check and Install Dependencies

Ensure `pandas` and `requests` are installed in the user's Python environment.
Run `pip show pandas requests`. If missing, run `pip install pandas requests`.

### 4. Prepare and Run the Script

The base spider script is provided in the bundled resources. Do not rewrite the entire script unless debugging. Instead:
1. Copy the script from `<skill_dir>/scripts/spider.py` to the current working directory as `twitter_spider_runner.py`.
2. Use the `Edit` tool to modify the `if __name__ == '__main__':` block at the bottom of the copied script to inject the user's parameters (`keyword`, `start_date`, `end_date`, `saveFileName`).
3. Run the script using `python3 twitter_spider_runner.py`.

### 5. Report Results

Once the script finishes (or if it crashes), report the status to the user. If successful, tell them where the CSV file is saved and briefly describe the columns available in the output data.

---

## Troubleshooting

- **429 Too Many Requests**: The script handles this by rotating cookies. If it runs out of cookies, it will prompt the user.
- **AuthenticationError**: The cookie is expired or invalid. Tell the user to get a fresh cookie from their browser.
- **Empty CSV / No Results**: Check if the keyword is too narrow or the date range is invalid. X's search can be finicky with complex Boolean queries.