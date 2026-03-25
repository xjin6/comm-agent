"""用户个人资料爬取模块 - 桌面版 AJAX API"""

from typing import Optional

import config
from data_models import UserProfile
from utils import setup_logger
from weibo_client import WeiboClient

logger = setup_logger("profile_scraper")

GENDER_MAP = {"m": "male", "f": "female"}


class ProfileScraper:
    def __init__(self, client: WeiboClient):
        self.client = client
        self.cache: dict = {}

    def scrape_profiles(self, user_ids: list) -> list:
        unique_ids = list(dict.fromkeys(user_ids))  # 去重并保持顺序
        profiles = []
        total = len(unique_ids)

        logger.info(f"开始爬取 {total} 个用户资料")

        for i, uid in enumerate(unique_ids, 1):
            if uid in self.cache:
                profiles.append(self.cache[uid])
                continue

            profile = self._scrape_one(uid)
            if profile:
                self.cache[uid] = profile
                profiles.append(profile)
                logger.info(f"用户 {i}/{total}: {profile.nickname} ({uid})")
            else:
                logger.warning(f"用户 {i}/{total}: 获取失败 ({uid})")

        logger.info(f"用户资料爬取完成，成功 {len(profiles)}/{total}")
        return profiles

    def _scrape_one(self, user_id: str) -> Optional[UserProfile]:
        # weibo.com 桌面版 AJAX API
        data = self.client.get_json(
            config.PROFILE_BASE_URL,
            params={"uid": user_id},
        )
        if not data:
            return None

        user_info = data.get("data", {}).get("user", {})
        if not user_info:
            return None

        return UserProfile(
            user_id=str(user_info.get("id", "")),
            nickname=user_info.get("screen_name", ""),
            gender=GENDER_MAP.get(user_info.get("gender", ""), "unknown"),
            location=user_info.get("location", ""),
            description=user_info.get("description", ""),
            followers_count=int(user_info.get("followers_count", 0)),
            following_count=int(user_info.get("friends_count", 0)),
            posts_count=int(user_info.get("statuses_count", 0)),
            verified=bool(user_info.get("verified", False)),
            verified_reason=user_info.get("verified_reason", ""),
            avatar_url=user_info.get("avatar_hd", ""),
            profile_url=user_info.get("profile_url", ""),
            raw_json=user_info,
        )
