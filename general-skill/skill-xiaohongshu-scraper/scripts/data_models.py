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
            for t in (note_card.get("tag_list") or [])
            if t.get("type") == "topic"
        ]

        # Real API: images have info_list[{image_scene, url}], not a top-level url.
        # Prefer WB_DFT scene; fall back to first available url.
        def _img_url(img: dict) -> str:
            if img.get("url"):
                return img["url"]
            for info in img.get("info_list", []):
                if info.get("image_scene") == "WB_DFT" and info.get("url"):
                    return info["url"]
            for info in img.get("info_list", []):
                if info.get("url"):
                    return info["url"]
            return ""

        images = [_img_url(img) for img in note_card.get("image_list", [])
                  if _img_url(img)]

        # Video URL: direct field, or nested stream structure
        video_url = note_card.get("video_url", "")
        if not video_url and note_card.get("type") == "video":
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
            if not t:
                return ""
            if isinstance(t, str) and len(t) >= 8 and not t.lstrip("-").isdigit():
                return t
            try:
                v = int(t)
                if v == 0:
                    return ""
                if v > 1e10:
                    v = v // 1000
                return datetime.datetime.fromtimestamp(v).isoformat()
            except Exception:
                return str(t)

        note_id = raw.get("id") or note_card.get("note_id", "")
        return XHSNote(
            note_id         = note_id,
            note_type       = note_card.get("type", "normal"),
            # Real API uses display_title; hand-crafted responses use title
            title           = note_card.get("display_title") or note_card.get("title", ""),
            desc            = note_card.get("desc", ""),
            author_id       = author.get("user_id", ""),
            author_name     = author.get("nickname") or author.get("nick_name", ""),
            liked_count     = int(interact.get("liked_count", 0) or 0),
            collected_count = int(interact.get("collected_count", 0) or 0),
            comment_count   = int(interact.get("comment_count", 0) or 0),
            # Real API uses shared_count; hand-crafted responses use share_count
            share_count     = int(interact.get("shared_count") or interact.get("share_count", 0) or 0),
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
    """
    Handles both snake_case (HTTP interception) and camelCase (webpack injection).
    camelCase fields: userInfo, likeCount, ipLocation, subCommentCount,
                      createTime, targetComment
    """
    try:
        # user info — camelCase or snake_case
        user = raw.get("userInfo") or raw.get("user_info", {})

        # timestamp — camelCase or snake_case, ms or s
        t = raw.get("createTime") or raw.get("create_time", "")
        import datetime
        if isinstance(t, (int, float)) and t > 0:
            v = int(t)
            if v > 1e10:
                v = v // 1000
            publish_time = datetime.datetime.fromtimestamp(v).isoformat()
        else:
            publish_time = str(t) if t else ""

        like_count = int(
            raw.get("likeCount") or raw.get("like_count", 0) or 0)
        ip_location = (
            raw.get("ipLocation") or raw.get("ip_location", ""))
        sub_count = int(
            raw.get("subCommentCount") or raw.get("sub_comment_count", 0) or 0)
        parent_id = (
            (raw.get("targetComment") or raw.get("target_comment") or {}).get("id", ""))

        return XHSComment(
            comment_id        = raw.get("id", ""),
            note_id           = note_id,
            user_id           = user.get("userId") or user.get("user_id", ""),
            user_name         = user.get("nickname", ""),
            content           = raw.get("content", ""),
            like_count        = like_count,
            publish_time      = publish_time,
            ip_location       = ip_location,
            sub_comment_count = sub_count,
            parent_comment_id = parent_id,
        )
    except Exception:
        return None


def parse_user(raw: dict) -> Optional[XHSUser]:
    """
    Handles both snake_case (page interception) and camelCase (webpack injection).
    camelCase fields: basicInfo, ipLocation, extraInfo, verifiedReason
    """
    try:
        # Resolve the basic_info block (snake or camel)
        info = raw.get("basic_info") or raw.get("basicInfo") or {}
        uid  = info.get("user_id") or info.get("userId", "")
        if not uid:
            return None          # empty / wrong structure — skip
        inter = raw.get("interactions", [])
        counts = {i.get("type"): int(i.get("count", 0) or 0) for i in inter}
        extra = raw.get("extra_info") or raw.get("extraInfo") or {}
        return XHSUser(
            user_id         = uid,
            nickname        = info.get("nickname", ""),
            gender          = str(info.get("gender", "")),
            location        = info.get("ip_location") or info.get("ipLocation", ""),
            description     = info.get("desc", ""),
            followers       = counts.get("fans", 0),
            following       = counts.get("follows", 0),
            notes_count     = counts.get("notes", 0),
            # webpack uses "interaction" (combined likes+collects); interception splits them
            liked_count     = counts.get("liked") or counts.get("interaction", 0),
            collected_count = counts.get("collected", 0),
            verified        = bool(extra.get("verified")),
            verified_reason = extra.get("verified_reason") or extra.get("verifiedReason", ""),
        )
    except Exception:
        return None
