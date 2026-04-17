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

        # Images: search API nests URLs inside info_list[].url
        images = []
        for img in note_card.get("image_list", []):
            url = img.get("url", "")
            if not url:
                # Try info_list → prefer WB_DFT scene
                for info in img.get("info_list", []):
                    if info.get("image_scene") == "WB_DFT":
                        url = info.get("url", "")
                        break
                if not url and img.get("info_list"):
                    url = img["info_list"][0].get("url", "")
            if url:
                images.append(url)

        video_url = ""
        if note_card.get("type") == "video":
            video_url = (
                note_card.get("video", {})
                .get("media", {})
                .get("stream", {})
                .get("h264", [{}])[0]
                .get("master_url", "")
            )

        # Publish time: search API stores it in corner_tag_info
        publish_time = ""
        for tag in note_card.get("corner_tag_info", []):
            if tag.get("type") == "publish_time":
                publish_time = tag.get("text", "")
                break
        if not publish_time:
            import datetime
            ts = note_card.get("time", 0)
            if ts:
                try:
                    v = int(ts)
                    if v > 1e10:
                        v = v // 1000
                    publish_time = datetime.datetime.fromtimestamp(v).isoformat()
                except Exception:
                    publish_time = str(ts)

        def _safe_int(v):
            try:
                return int(str(v).replace(",", "").strip() or 0)
            except Exception:
                return 0

        note_id = raw.get("id") or note_card.get("note_id", "")
        return XHSNote(
            note_id         = note_id,
            note_type       = note_card.get("type", "normal"),
            # search API uses display_title; feed API uses title
            title           = note_card.get("display_title") or note_card.get("title", ""),
            desc            = note_card.get("desc", ""),
            author_id       = author.get("user_id", ""),
            author_name     = author.get("nickname") or author.get("nick_name", ""),
            liked_count     = _safe_int(interact.get("liked_count", 0)),
            collected_count = _safe_int(interact.get("collected_count", 0)),
            comment_count   = _safe_int(interact.get("comment_count", 0)),
            share_count     = _safe_int(interact.get("shared_count") or interact.get("share_count", 0)),
            publish_time    = publish_time,
            last_update     = publish_time,
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
        user = raw.get("user_info", {})
        t = raw.get("create_time", "")
        # Handle both date strings ("2025-04-25") and unix timestamps
        if isinstance(t, (int, float)) and t > 0:
            import datetime
            v = int(t)
            if v > 1e10:
                v = v // 1000
            publish_time = datetime.datetime.fromtimestamp(v).isoformat()
        else:
            publish_time = str(t) if t else ""

        return XHSComment(
            comment_id        = raw.get("id", ""),
            note_id           = note_id,
            user_id           = user.get("user_id", ""),
            user_name         = user.get("nickname", ""),
            content           = raw.get("content", ""),
            like_count        = int(raw.get("like_count", 0) or 0),
            publish_time      = publish_time,
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
