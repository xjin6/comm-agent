"""数据导出模块：CSV 和 JSON"""

import csv
import json


def _write_csv(rows: list, filepath: str) -> None:
    if not rows:
        return
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_posts_to_csv(posts: list, filepath: str) -> None:
    _write_csv([p.to_dict(include_raw=False) for p in posts], filepath)


def export_posts_to_json(posts: list, filepath: str) -> None:
    rows = [p.to_dict(include_raw=True) for p in posts]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def export_comments_to_csv(comments: list, filepath: str) -> None:
    _write_csv([c.to_dict(include_raw=False) for c in comments], filepath)


def export_comments_to_json(comments: list, filepath: str) -> None:
    rows = [c.to_dict(include_raw=True) for c in comments]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def export_profiles_to_csv(profiles: list, filepath: str) -> None:
    _write_csv([p.to_dict(include_raw=False) for p in profiles], filepath)


def export_profiles_to_json(profiles: list, filepath: str) -> None:
    rows = [p.to_dict(include_raw=True) for p in profiles]
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
