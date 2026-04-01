"""
Export scraped XHS data to CSV and JSON.
"""

import csv
import json
import os
from dataclasses import asdict
from typing import List, Union
from data_models import XHSNote, XHSComment, XHSUser


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None


def save_notes(notes: List[XHSNote], output_dir: str, fmt: str = "both") -> None:
    os.makedirs(output_dir, exist_ok=True)
    rows = [asdict(n) for n in notes]
    if not rows:
        return
    if fmt in ("csv", "both"):
        path = os.path.join(output_dir, "notes.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        print(f"  Saved {len(rows)} notes → {path}")
    if fmt in ("json", "both"):
        path = os.path.join(output_dir, "notes.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"  Saved {len(rows)} notes → {path}")


def save_comments(comments: List[XHSComment], output_dir: str, fmt: str = "both") -> None:
    os.makedirs(output_dir, exist_ok=True)
    rows = [asdict(c) for c in comments]
    if not rows:
        return
    if fmt in ("csv", "both"):
        path = os.path.join(output_dir, "comments.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        print(f"  Saved {len(rows)} comments → {path}")
    if fmt in ("json", "both"):
        path = os.path.join(output_dir, "comments.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"  Saved {len(rows)} comments → {path}")


def save_users(users: List[XHSUser], output_dir: str, fmt: str = "both") -> None:
    os.makedirs(output_dir, exist_ok=True)
    rows = [asdict(u) for u in users]
    if not rows:
        return
    if fmt in ("csv", "both"):
        path = os.path.join(output_dir, "users.csv")
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader(); w.writerows(rows)
        print(f"  Saved {len(rows)} users → {path}")
    if fmt in ("json", "both"):
        path = os.path.join(output_dir, "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"  Saved {len(rows)} users → {path}")
