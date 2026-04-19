# Twitter / X Keyword Search Scraper

> **v0.1.0** · Updated 2026-04-18 · `scraper`

A sophisticated, reverse-engineered Python spider designed for communication researchers to collect posts (tweets), user profiles, engagement metrics, and media from Twitter (X.com) by keyword and date range.

## Overview

Unlike many existing scrapers that fail against X's strict authentication and Cloudflare protections, this skill utilizes a custom-built API client that faithfully recreates the Twitter Web App's encrypted headers (including `x-csrf-token` and `x-client-transaction-id` hash generation). This allows researchers to bypass anti-bot mechanisms using their own browser cookies.

### Features

- **Keyword & Date Search**: Supports complex Boolean queries (e.g., `(#AI OR #MachineLearning)`) and precise date filtering.
- **Robust Anti-Bot Bypass**: Uses dynamic token generation (`f"{W}!{n}!{d}obfiowerehiring{k}"` hashing) to simulate legitimate browser traffic and bypass Cloudflare 403 blocks.
- **Detailed Data Extraction**: Collects Tweet ID, timestamp, full text, URLs, media links, and engagement metrics (replies, retweets, likes, quotes).
- **Rich User Context**: Extracts author ID, username, bio, follower/following counts, account creation date, and verification status (Blue/Gold checks).
- **Cookie Rotation**: Supports multiple cookies to rotate through and avoid rate limits (HTTP 429).
- **Continuous Saving**: Appends data to an Excel-friendly CSV with UTF-8 BOM encoding.

## Setup

Before using this skill, you must provide active X.com session cookies in your project directory.

1. Log in to [x.com](https://x.com) in your browser.
2. Open Developer Tools (F12) -> Network tab.
3. Refresh the page and click on any `graphql` or `SearchTimeline` request.
4. Copy the entire value of the `cookie:` header from the Request Headers.
5. Save this value into a file named `cookies.txt` in your project's working directory (put one cookie string per line if you have multiple accounts).
6. Ensure a file named `cookie_index.txt` exists in the same directory, containing just the number `0`.

## Usage

Simply ask the agent to search Twitter:

> *"Scrape tweets mentioning #TradeWar from 2025-07-01 to 2025-07-31 and save them to trade_tweets"*

The agent will automatically configure the spider, inject your parameters, and run the collection process.

## Author

**Yundi Zhang** (@Zhang-Yundi) · yd.yundi@gmail.com

## License

CC BY-NC-ND 4.0
