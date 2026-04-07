"""
Douyin (抖音) trending topic scraper.

Modes:
  trending  — fetch the current hot search list (热搜榜)
  topic     — fetch videos under a specific trending topic
  all       — fetch trending list + videos for every topic on it

Usage examples:
  python main.py --mode trending --output-dir "your-project/output/douyin/trending"
  python main.py --mode topic --topic "元宵节" --output-dir "your-project/output/douyin/元宵节"
  python main.py --mode all --output-dir "your-project/output/douyin"
"""

import argparse
import datetime
import json
import os
import random
import sys
import time

import requests
import pandas as pd

# Fix Windows console encoding for Chinese characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------------------
# API endpoints (reverse-engineered from Douyin Android app v8.6.0)
# Device parameters are kept as-is from the original implementation.
# If requests return unexpected responses, the API may have been updated.
# ---------------------------------------------------------------------------
TRENDING_API = (
    "https://aweme-hl.snssdk.com/aweme/v1/hot/search/list/"
    "?detail_list=1"
    "&mac_address=08:00:27:29:D2:F5"
    "&os_api=23"
    "&device_type=MI%205s"
    "&device_platform=android"
    "&ssmix=a"
    "&iid=92152480453"
    "&manifest_version_code=860"
    "&dpi=320"
    "&uuid=008796750074613"
    "&version_code=860"
    "&app_name=aweme"
    "&version_name=8.6.0"
    "&openudid=c055533a0591b2dc"
    "&device_id=69918538596"
    "&resolution=810*1440"
    "&os_version=6.0.1"
    "&language=zh"
    "&device_brand=Xiaomi"
    "&app_type=normal"
    "&ac=wifi"
    "&update_version_code=8602"
    "&aid=1128"
    "&channel=tengxun_new"
)
TOPIC_API = "https://aweme-hl.snssdk.com/aweme/v1/hot/search/video/list/?hotword="

HEADERS = {
    "User-Agent": (
        "com.ss.android.ugc.aweme/860 "
        "(Linux; U; Android 6.0.1; zh_CN; MI 5s; Build/MXB48T; Cronet/TTHttpClient)"
    ),
    "Accept": "application/json",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def to_time(timestamp: int) -> str:
    if not timestamp:
        return ""
    return str(datetime.datetime.fromtimestamp(timestamp))


def save(df: pd.DataFrame, path_no_ext: str, fmt: str) -> None:
    os.makedirs(os.path.dirname(path_no_ext) or ".", exist_ok=True)
    if fmt in ("csv", "both"):
        p = path_no_ext + ".csv"
        df.to_csv(p, encoding="utf-8-sig", index=False)
        log(f"  Saved → {p}")
    if fmt in ("json", "both"):
        p = path_no_ext + ".json"
        df.to_json(p, orient="records", force_ascii=False, indent=2)
        log(f"  Saved → {p}")


def _get_json(url: str, label: str) -> dict:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        log(f"ERROR: non-JSON response from {label} API — the endpoint may have changed.")
        log(f"  Raw response (first 500 chars): {resp.text[:500]}")
        sys.exit(1)
    except Exception as e:
        log(f"ERROR fetching {label}: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Trending list
# ---------------------------------------------------------------------------

def _parse_trending(data: dict) -> tuple[str, list[dict]]:
    """Return (active_time, list of row dicts)."""
    try:
        active_time = data["data"]["active_time"]
        word_list = data["data"]["word_list"]
    except (KeyError, TypeError):
        log("ERROR: unexpected response structure — API may have changed.")
        log(f"  Keys found: {list(data.keys())}")
        sys.exit(1)

    rows = []
    for item in word_list:
        cover_url = None
        wc = item.get("word_cover")
        if isinstance(wc, dict):
            urls = wc.get("url_list", [])
            cover_url = urls[0] if urls else None
        rows.append({
            "rank":        item.get("position"),
            "word":        item.get("word"),
            "hot_value":   item.get("hot_value"),
            "video_count": item.get("video_count"),
            "label":       item.get("label"),
            "cover_url":   cover_url,
        })
    return active_time, rows


def fetch_trending(output_dir: str, fmt: str) -> list[str]:
    """Fetch trending list. Returns list of topic words."""
    log("Fetching trending topics list (热搜榜)...")
    data = _get_json(TRENDING_API, "trending")
    active_time, rows = _parse_trending(data)
    date = active_time.split(" ")[0]

    log(f"  List updated at : {active_time}")
    log(f"  Topics found    : {len(rows)}")

    os.makedirs(output_dir, exist_ok=True)
    save(pd.DataFrame(rows), os.path.join(output_dir, f"trending_{date}"), fmt)

    print(f"\n{'='*60}", flush=True)
    print(f"  DONE — Trending list", flush=True)
    print(f"  Topics   : {len(rows)}", flush=True)
    print(f"  Updated  : {active_time}", flush=True)
    print(f"  Output   : {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)

    return [r["word"] for r in rows if r.get("word")]


# ---------------------------------------------------------------------------
# Topic videos
# ---------------------------------------------------------------------------

def _parse_videos(data: dict) -> list[dict]:
    try:
        video_list = data["aweme_list"]
    except (KeyError, TypeError):
        log("ERROR: unexpected response structure — API may have changed.")
        log(f"  Keys found: {list(data.keys())}")
        sys.exit(1)

    rows = []
    for info in video_list:
        video_url = None
        try:
            dl_urls = info["video"]["download_addr"]["url_list"]
            video_url = next((u for u in dl_urls if "default" in u), dl_urls[0] if dl_urls else None)
        except (KeyError, TypeError):
            pass

        cover_url = None
        try:
            cover_url = info["video"]["cover"]["url_list"][0]
        except (KeyError, TypeError, IndexError):
            pass

        rows.append({
            "desc":           info.get("desc"),
            "nickname":       info.get("author", {}).get("nickname"),
            "custom_verify":  info.get("author", {}).get("custom_verify"),
            "create_time":    to_time(info.get("create_time", 0)),
            "like_count":     info.get("statistics", {}).get("digg_count"),
            "comment_count":  info.get("statistics", {}).get("comment_count"),
            "share_count":    info.get("statistics", {}).get("share_count"),
            "forward_count":  info.get("statistics", {}).get("forward_count"),
            "download_count": info.get("statistics", {}).get("download_count"),
            "video_url":      video_url,
            "cover_url":      cover_url,
        })
    return rows


def fetch_topic(topic: str, output_dir: str, fmt: str) -> int:
    """Fetch videos for one topic. Returns number of videos collected."""
    log(f"Fetching videos for topic: {topic}")
    url = TOPIC_API + requests.utils.quote(topic)
    data = _get_json(url, f"topic/{topic}")
    rows = _parse_videos(data)

    if not rows:
        log(f"  No videos returned for '{topic}'.")
        return 0

    log(f"  Videos found: {len(rows)}")
    os.makedirs(output_dir, exist_ok=True)
    save(pd.DataFrame(rows), os.path.join(output_dir, "videos"), fmt)

    print(f"\n{'='*60}", flush=True)
    print(f"  DONE — Topic videos", flush=True)
    print(f"  Topic    : {topic}", flush=True)
    print(f"  Videos   : {len(rows)}", flush=True)
    print(f"  Output   : {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)

    return len(rows)


# ---------------------------------------------------------------------------
# All mode: trending list + every topic's videos
# ---------------------------------------------------------------------------

def fetch_all(output_dir: str, fmt: str, delay_min: float, delay_max: float) -> None:
    log("Mode: all — fetching trending list then videos for each topic")

    data = _get_json(TRENDING_API, "trending")
    active_time, trend_rows = _parse_trending(data)
    date = active_time.split(" ")[0]

    # Save trending list
    trend_dir = os.path.join(output_dir, "trending_list")
    os.makedirs(trend_dir, exist_ok=True)
    save(pd.DataFrame(trend_rows), os.path.join(trend_dir, f"trending_{date}"), fmt)
    log(f"  Trending list saved ({len(trend_rows)} topics)")

    topics = [r["word"] for r in trend_rows if r.get("word")]
    total_videos = 0

    for i, topic in enumerate(topics, 1):
        log(f"\n[{i}/{len(topics)}] {topic}")
        topic_dir = os.path.join(output_dir, topic)
        count = fetch_topic(topic, topic_dir, fmt)
        total_videos += count

        if i < len(topics):
            delay = random.uniform(delay_min, delay_max)
            log(f"  Waiting {delay:.1f}s before next topic...")
            time.sleep(delay)

    print(f"\n{'='*60}", flush=True)
    print(f"  ALL DONE", flush=True)
    print(f"  Topics covered : {len(topics)}", flush=True)
    print(f"  Total videos   : {total_videos}", flush=True)
    print(f"  Output         : {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Douyin trending topic scraper")
    parser.add_argument(
        "--mode", required=True, choices=["trending", "topic", "all"],
        help="trending=list only | topic=videos for one topic | all=list + all topic videos"
    )
    parser.add_argument("--topic",      help="Topic name (required for --mode topic)")
    parser.add_argument("--output-dir", required=True, help="Directory to save results")
    parser.add_argument("--format",     default="both", choices=["csv", "json", "both"])
    parser.add_argument("--delay-min",  type=float, default=3.0, help="Min delay between requests (all mode)")
    parser.add_argument("--delay-max",  type=float, default=7.0, help="Max delay between requests (all mode)")
    args = parser.parse_args()

    if args.mode == "trending":
        fetch_trending(args.output_dir, args.format)

    elif args.mode == "topic":
        if not args.topic:
            print("ERROR: --topic is required when --mode topic", file=sys.stderr)
            sys.exit(1)
        fetch_topic(args.topic, args.output_dir, args.format)

    elif args.mode == "all":
        fetch_all(args.output_dir, args.format, args.delay_min, args.delay_max)


if __name__ == "__main__":
    main()
