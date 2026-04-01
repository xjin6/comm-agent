"""
Xiaohongshu (小红书) topic scraper.
Usage:
  python main.py --keyword "关键词" --cookie "YOUR_COOKIE" [options]
"""

import argparse
import os
import sys
import time

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from xhs_client import XHSClient
from data_models import parse_note, parse_comment, parse_user
from exporters import save_notes, save_comments, save_users


def scrape(keyword: str, cookie: str, max_pages: int, sort: str,
           note_type: int, skip_comments: bool, skip_users: bool,
           output_dir: str, fmt: str, delay_min: float, delay_max: float) -> None:

    client = XHSClient(cookie, delay_min=delay_min, delay_max=delay_max)

    if not client.validate_cookie():
        print("ERROR: Cookie missing required 'a1' field. Please re-extract your cookie.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"Keyword : {keyword}")
    print(f"Sort    : {sort}")
    print(f"Max pages: {max_pages}")
    print(f"Output  : {output_dir}")
    print(f"{'='*60}\n")

    os.makedirs(output_dir, exist_ok=True)

    notes    = []
    comments = []
    users    = {}    # user_id → XHSUser (deduplicated)
    seen_ids = set()

    # ── Phase 1: Collect notes ────────────────────────────────────────────────
    for page in range(1, max_pages + 1):
        print(f"[Page {page}/{max_pages}] Searching '{keyword}'...")
        try:
            resp = client.search_notes(keyword, page=page, sort=sort,
                                       note_type=note_type)
        except Exception as e:
            print(f"  ERROR on page {page}: {e}")
            break

        if resp.get("code") != 0:
            msg = resp.get("msg", "")
            if "登录" in msg or "auth" in msg.lower():
                print("ERROR: Cookie expired — please get a fresh cookie.")
            else:
                print(f"  API error: {msg}")
            break

        items = resp.get("data", {}).get("items", [])
        if not items:
            print("  No more results.")
            break

        new = 0
        for item in items:
            note = parse_note(item)
            if note and note.note_id not in seen_ids:
                notes.append(note)
                seen_ids.add(note.note_id)
                new += 1

        print(f"  Collected {new} new notes (total: {len(notes)})")
        save_notes(notes, output_dir, fmt)   # incremental save

    if not notes:
        print("No notes collected. Exiting.")
        return

    print(f"\nTotal notes collected: {len(notes)}")

    # ── Phase 2: Comments ─────────────────────────────────────────────────────
    if not skip_comments:
        print(f"\nCollecting comments for {len(notes)} notes...")
        for i, note in enumerate(notes, 1):
            print(f"  [{i}/{len(notes)}] Comments for note {note.note_id}...")
            cursor = ""
            page_num = 0
            while True:
                try:
                    resp = client.get_comments(
                        note.note_id, cursor=cursor,
                        xsec_token=note.xsec_token)
                except Exception as e:
                    print(f"    ERROR: {e}")
                    break

                if resp.get("code") != 0:
                    break

                data     = resp.get("data", {})
                raw_cmts = data.get("comments", [])
                for rc in raw_cmts:
                    c = parse_comment(rc, note.note_id)
                    if c:
                        comments.append(c)
                    # Sub-comments (replies)
                    for sub in rc.get("sub_comments", []):
                        sc = parse_comment(sub, note.note_id)
                        if sc:
                            comments.append(sc)

                cursor = data.get("cursor", "")
                page_num += 1
                if not data.get("has_more") or not cursor or page_num >= 10:
                    break

            print(f"    → {len(comments)} comments so far")

        save_comments(comments, output_dir, fmt)

    # ── Phase 3: User profiles ────────────────────────────────────────────────
    if not skip_users:
        author_ids = list({n.author_id for n in notes if n.author_id})
        if comments:
            author_ids += list({c.user_id for c in comments if c.user_id})
        author_ids = list(set(author_ids))

        print(f"\nCollecting profiles for {len(author_ids)} unique users...")
        for i, uid in enumerate(author_ids, 1):
            if uid in users:
                continue
            print(f"  [{i}/{len(author_ids)}] User {uid}...")
            try:
                resp = client.get_user_info(uid)
                if resp.get("code") == 0:
                    u = parse_user(resp.get("data", {}))
                    if u:
                        users[uid] = u
            except Exception as e:
                print(f"    ERROR: {e}")

        save_users(list(users.values()), output_dir, fmt)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"DONE")
    print(f"  Notes    : {len(notes)}")
    print(f"  Comments : {len(comments)}")
    print(f"  Users    : {len(users)}")
    print(f"  Output   : {output_dir}")
    print(f"{'='*60}\n")
    client.close()


def main():
    parser = argparse.ArgumentParser(description="Xiaohongshu topic scraper")
    parser.add_argument("--keyword",       required=True,  help="Search keyword or topic")
    parser.add_argument("--cookie",        required=True,  help="XHS cookie string")
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
