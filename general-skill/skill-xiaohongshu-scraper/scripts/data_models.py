"""
Data models for Xiaohongshu scraped data.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List
import csv
import json
import os


@dataclass
class XHSNote:
    note_id:       str
    note_type:     str          # "normal" | "video"
    title:         str
    desc:          str
    author_id:     str
    author_name:   str
    liked_count:   int
    collected_count: int
    comment_count: int
    share_count:   int
    publish_time:  str          # ISO format
    last_update:   str
    topics:        List[str]    # 话题标签
    image_urls:    List[str]
    video_url:     str
    ip_location:   str
    note_url:      str
    xsec_token:    str = ""


@dataclass
class XHSComment:
    comment_id:   str
    note_id:      str
    user_id:      str
    user_name:    str
    content:      str
    like_count:   int
    publish_time: str
    ip_location:  str
    sub_comment_count: int
    parent_comment_id: str = ""   # empty = top-level


@dataclass
class XHSUser:
    user_id:          str
    nickname:         str
    gender:           str
    location:         str
    description:      str
    followers:        int
    following:        int
    notes_count:      int
    liked_count:      int
    collected_count:  int
    verified:         bool
    verified_reason:  str


# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_note(raw: dict) -> Optional[XHSNote]:
    """Parse a raw note dict from the search or feed API."""
    try:
        note_card = raw.get("note_card", raw)
        interact  = note_card.get("interact_info", {})
        author    = note_card.get("user", {})

        topics = [
            t.get("name", "")
            for t in note_card.get("tag_list", [])
            if t.get("type") == "topic"
        ]

        images = [
            img.get("url", "")
            for img in note_card.get("image_list", [])
            if img.get("url")
        ]

        video_url = ""
        if note_card.get("type") == "video":
            video_url = (
                note_card.get("video", {})
                .get("media", {})
                .get("stream", {})
                .get("h264", [{}])[0]
                .get("master_url", "")
            )

        ts = note_card.get("time", 0)
        last_ts = note_card.get("last_update_time", ts)
        import datetime
        def _ts(t):
            try:
                return datetime.datetime.fromtimestamp(int(t)).isoformat()
            except Exception:
                return str(t)

        note_id = raw.get("id") or note_card.get("note_id", "")
        return XHSNote(
            note_id         = note_id,
            note_type       = note_card.get("type", "normal"),
            title           = note_card.get("title", ""),
            desc            = note_card.get("desc", ""),
            author_id       = author.get("user_id", ""),
            author_name     = author.get("nickname", ""),
            liked_count     = int(interact.get("liked_count", 0) or 0),
            collected_count = int(interact.get("collected_count", 0) or 0),
            comment_count   = int(interact.get("comment_count", 0) or 0),
            share_count     = int(interact.get("share_count", 0) or 0),
            publish_time    = _ts(ts),
            last_update     = _ts(last_ts),
            topics          = topics,
            image_urls      = images,
            video_url       = video_url,
            ip_location     = note_card.get("ip_location", ""),
            note_url        = f"https://www.xiaohongshu.com/explore/{note_id}",
            xsec_token      = raw.get("xsec_token", ""),
        )
    except Exception:
        return None


def parse_comment(raw: dict, note_id: str) -> Optional[XHSComment]:
    try:
        import datetime
        def _ts(t):
            try:
                return datetime.datetime.fromtimestamp(int(t)).isoformat()
            except Exception:
                return str(t)

        user = raw.get("user_info", {})
        return XHSComment(
            comment_id        = raw.get("id", ""),
            note_id           = note_id,
            user_id           = user.get("user_id", ""),
            user_name         = user.get("nickname", ""),
            content           = raw.get("content", ""),
            like_count        = int(raw.get("like_count", 0) or 0),
            publish_time      = _ts(raw.get("create_time", 0)),
            ip_location       = raw.get("ip_location", ""),
            sub_comment_count = int(raw.get("sub_comment_count", 0) or 0),
            parent_comment_id = raw.get("target_comment", {}).get("id", ""),
        )
    except Exception:
        return None


def parse_user(raw: dict) -> Optional[XHSUser]:
    try:
        info = raw.get("basic_info", raw)
        inter = raw.get("interactions", [])
        counts = {i.get("type"): int(i.get("count", 0) or 0) for i in inter}
        return XHSUser(
            user_id         = info.get("user_id", ""),
            nickname        = info.get("nickname", ""),
            gender          = info.get("gender", ""),
            location        = info.get("ip_location", ""),
            description     = info.get("desc", ""),
            followers       = counts.get("fans", 0),
            following       = counts.get("follows", 0),
            notes_count     = counts.get("notes", 0),
            liked_count     = counts.get("liked", 0),
            collected_count = counts.get("collected", 0),
            verified        = bool(raw.get("extra_info", {}).get("verified")),
            verified_reason = raw.get("extra_info", {}).get("verified_reason", ""),
        )
    except Exception:
        return None
