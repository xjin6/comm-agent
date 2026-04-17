"""数据模型定义"""

from dataclasses import dataclass, field


@dataclass
class WeiboPost:
    post_id: str = ""
    user_id: str = ""
    user_nickname: str = ""
    content: str = ""
    publish_time: str = ""
    reposts_count: int = 0
    comments_count: int = 0
    likes_count: int = 0
    images: list = field(default_factory=list)
    video_url: str = ""
    topic_tags: list = field(default_factory=list)
    source_device: str = ""
    raw_json: dict = field(default_factory=dict)

    def to_dict(self, include_raw: bool = False) -> dict:
        d = {
            "post_id": self.post_id,
            "user_id": self.user_id,
            "user_nickname": self.user_nickname,
            "content": self.content,
            "publish_time": self.publish_time,
            "reposts_count": self.reposts_count,
            "comments_count": self.comments_count,
            "likes_count": self.likes_count,
            "images": "; ".join(self.images),
            "video_url": self.video_url,
            "topic_tags": "; ".join(self.topic_tags),
            "source_device": self.source_device,
        }
        if include_raw:
            d["raw_json"] = self.raw_json
        return d


@dataclass
class WeiboComment:
    comment_id: str = ""
    post_id: str = ""
    user_id: str = ""
    user_nickname: str = ""
    content: str = ""
    publish_time: str = ""
    likes_count: int = 0
    reply_to_comment_id: str = ""
    reply_to_user: str = ""
    source_device: str = ""
    raw_json: dict = field(default_factory=dict)

    def to_dict(self, include_raw: bool = False) -> dict:
        d = {
            "comment_id": self.comment_id,
            "post_id": self.post_id,
            "user_id": self.user_id,
            "user_nickname": self.user_nickname,
            "content": self.content,
            "publish_time": self.publish_time,
            "likes_count": self.likes_count,
            "reply_to_comment_id": self.reply_to_comment_id,
            "reply_to_user": self.reply_to_user,
            "source_device": self.source_device,
        }
        if include_raw:
            d["raw_json"] = self.raw_json
        return d


@dataclass
class UserProfile:
    user_id: str = ""
    nickname: str = ""
    gender: str = ""
    location: str = ""
    description: str = ""
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    verified_reason: str = ""
    avatar_url: str = ""
    profile_url: str = ""
    raw_json: dict = field(default_factory=dict)

    def to_dict(self, include_raw: bool = False) -> dict:
        d = {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "gender": self.gender,
            "location": self.location,
            "description": self.description,
            "followers_count": self.followers_count,
            "following_count": self.following_count,
            "posts_count": self.posts_count,
            "verified": self.verified,
            "verified_reason": self.verified_reason,
            "avatar_url": self.avatar_url,
            "profile_url": self.profile_url,
        }
        if include_raw:
            d["raw_json"] = self.raw_json
        return d
