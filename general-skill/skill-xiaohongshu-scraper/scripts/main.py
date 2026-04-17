"""
Xiaohongshu (小红书) topic scraper.
Usage:
  python main.py --keyword "关键词" --cookie "YOUR_COOKIE" [options]
"""

import argparse
import os
import sys
import time
import datetime

# Fix Windows console encoding for Chinese characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from xhs_client import XHSClient
from data_models import parse_note, parse_comment, parse_user
from exporters import save_notes, save_comments, save_users


def log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def progress_bar(current: int, total: int, width: int = 30) -> str:
    filled = int(width * current / total) if total else 0
    bar = "#" * filled + "-" * (width - filled)
    pct = int(100 * current / total) if total else 0
    return f"[{bar}] {current}/{total} ({pct}%)"


def scrape(keyword: str, cookie: str, max_pages: int, sort: str,
           note_type: int, skip_comments: bool, skip_users: bool,
           output_dir: str, fmt: str, delay_min: float, delay_max: float) -> None:

    log("Launching browser with WASM signing...")
    client = XHSClient(cookie, delay_min=delay_min, delay_max=delay_max)

    if not client.validate_cookie():
        log("ERROR: Cookie missing required 'a1' field. Please re-extract your cookie.")
        sys.exit(1)

    print(f"\n{'='*60}", flush=True)
    print(f"  Keyword  : {keyword}", flush=True)
    print(f"  Sort     : {sort}", flush=True)
    print(f"  Pages    : {max_pages}  (~{max_pages * 15} notes)", flush=True)
    print(f"  Comments : {'yes' if not skip_comments else 'skip'}", flush=True)
    print(f"  Users    : {'yes' if not skip_users else 'skip'}", flush=True)
    print(f"  Output   : {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)

    os.makedirs(output_dir, exist_ok=True)

    notes    = []
    comments = []
    users    = {}
    seen_ids = set()
    start_time = time.time()

    # ── Phase 1: Notes ────────────────────────────────────────────────────────
    log(f"PHASE 1/3 — Collecting notes ({max_pages} pages)")
    for page in range(1, max_pages + 1):
        log(f"  {progress_bar(page - 1, max_pages)}  Page {page}/{max_pages} — navigating...")
        try:
            resp = client.search_notes(keyword, page=page, sort=sort,
                                       note_type=note_type)
        except Exception as e:
            log(f"  ERROR on page {page}: {e}")
            break

        if resp.get("code") != 0:
            msg = resp.get("msg", "")
            if "登录" in msg or "auth" in msg.lower() or "301" in str(resp.get("code")):
                log("ERROR: Cookie expired — please get a fresh cookie.")
            else:
                log(f"  Error response: {msg}")
            break

        items = resp.get("data", {}).get("items", [])
        if not items:
            log("  No more results.")
            break

        new = 0
        for item in items:
            note = parse_note(item)
            if note and note.note_id not in seen_ids:
                notes.append(note)
                seen_ids.add(note.note_id)
                new += 1

        elapsed = time.time() - start_time
        log(f"  {progress_bar(page, max_pages)}  +{new} notes  |  total: {len(notes)}  |  elapsed: {elapsed:.0f}s")
        save_notes(notes, output_dir, fmt)

    if not notes:
        log("No notes collected. Exiting.")
        return

    log(f"Phase 1 done — {len(notes)} notes collected.")

    # ── Phase 2: Comments ─────────────────────────────────────────────────────
    if not skip_comments:
        log(f"\nPHASE 2/3 — Collecting comments for {len(notes)} notes")
        for i, note in enumerate(notes, 1):
            log(f"  {progress_bar(i, len(notes))}  note {i}/{len(notes)}: {note.title[:25]}...")
            cursor = ""
            page_num = 0
            note_cmts = 0
            while True:
                try:
                    resp = client.get_comments(
                        note.note_id, cursor=cursor,
                        xsec_token=note.xsec_token)
                except Exception as e:
                    log(f"    ERROR: {e}")
                    break

                if resp.get("code") != 0:
                    break

                data     = resp.get("data", {})
                raw_cmts = data.get("comments", [])
                for rc in raw_cmts:
                    c = parse_comment(rc, note.note_id)
                    if c:
                        comments.append(c)
                        note_cmts += 1
                    for sub in rc.get("sub_comments", []):
                        sc = parse_comment(sub, note.note_id)
                        if sc:
                            comments.append(sc)
                            note_cmts += 1

                cursor = data.get("cursor", "")
                page_num += 1
                if not data.get("has_more") or not cursor or page_num >= 10:
                    break

            log(f"    got {note_cmts} comments  |  running total: {len(comments)}")

        save_comments(comments, output_dir, fmt)
        log(f"Phase 2 done — {len(comments)} comments collected.")

    # ── Phase 3: User profiles ────────────────────────────────────────────────
    if not skip_users:
        author_ids = list({n.author_id for n in notes if n.author_id})
        if comments:
            author_ids += list({c.user_id for c in comments if c.user_id})
        author_ids = list(set(author_ids))

        log(f"\nPHASE 3/3 — Collecting profiles for {len(author_ids)} unique users")
        for i, uid in enumerate(author_ids, 1):
            if uid in users:
                continue
            log(f"  {progress_bar(i, len(author_ids))}  user {i}/{len(author_ids)}: {uid}")
            try:
                resp = client.get_user_info(uid)
                if resp.get("code") == 0:
                    u = parse_user(resp.get("data", {}))
                    if u:
                        users[uid] = u
                        log(f"    OK: {u.nickname}")
            except Exception as e:
                log(f"    ERROR: {e}")

        save_users(list(users.values()), output_dir, fmt)
        log(f"Phase 3 done — {len(users)} user profiles collected.")

    # ── Summary ───────────────────────────────────────────────────────────────
    elapsed = time.time() - start_time
    print(f"\n{'='*60}", flush=True)
    print(f"  DONE  (total time: {elapsed:.0f}s)", flush=True)
    print(f"  Notes    : {len(notes)}", flush=True)
    print(f"  Comments : {len(comments)}", flush=True)
    print(f"  Users    : {len(users)}", flush=True)
    print(f"  Output   : {output_dir}", flush=True)
    print(f"{'='*60}\n", flush=True)
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Xiaohongshu topic scraper")
    parser.add_argument("--keyword",       required=True,  help="Search keyword or topic")
    parser.add_argument("--cookie",        required=True,  help="XHS cookie string (only a1= and web_session= are required)")
    parser.add_argument("--max-pages",     type=int, default=10, help="Max search pages (20 notes/page)")
    parser.add_argument("--sort",          default="general",
                        choices=["general", "time_descending", "popularity_descending"])
    parser.add_argument("--note-type",     type=int, default=0,
                        help="0=all, 1=video, 2=image")
    parser.add_argument("--skip-comments", action="store_true")
    parser.add_argument("--skip-users",    action="store_true")
    parser.add_argument("--output-dir",    required=True)
    parser.add_argument("--format",        default="both", choices=["csv", "json", "both"])
    parser.add_argument("--delay-min",     type=float, default=3.0)
    parser.add_argument("--delay-max",     type=float, default=7.0)
    args = parser.parse_args()

    scrape(
        keyword       = args.keyword,
        cookie        = args.cookie,
        max_pages     = args.max_pages,
        sort          = args.sort,
        note_type     = args.note_type,
        skip_comments = args.skip_comments,
        skip_users    = args.skip_users,
        output_dir    = args.output_dir,
        fmt           = args.format,
        delay_min     = args.delay_min,
        delay_max     = args.delay_max,
    )


if __name__ == "__main__":
    main()
