"""评论爬取模块 - 桌面版 AJAX API"""

from typing import Optional

from data_models import WeiboComment
from utils import parse_weibo_time, setup_logger, strip_html
from weibo_client import WeiboClient

logger = setup_logger("comment_scraper")

COMMENTS_API = "https://weibo.com/ajax/statuses/buildComments"


class CommentScraper:
    def __init__(self, client: WeiboClient):
        self.client = client

    def scrape_all_posts_comments(self, posts: list) -> list:
        """爬取多个帖子的所有评论"""
        all_comments = []
        total = len(posts)

        logger.info(f"开始爬取 {total} 个帖子的评论")

        for i, post in enumerate(posts, 1):
            if post.comments_count == 0:
                continue

            comments = self._scrape_post_comments(post.post_id)
            all_comments.extend(comments)

            logger.info(
                f"帖子 {i}/{total} (mid={post.post_id}): "
                f"预期{post.comments_count}条, 实际爬到{len(comments)}条"
            )

        logger.info(f"评论爬取完成，共{len(all_comments)}条")
        return all_comments

    def _scrape_post_comments(self, post_id: str) -> list:
        """爬取单个帖子的全部评论（含子评论）"""
        comments = []
        max_id = 0

        while True:
            params = {
                "id": post_id,
                "is_reload": 1,
                "is_show_bulletin": 2,
                "is_mix": 0,
                "count": 20,
                "flow": 0,
            }
            if max_id:
                params["max_id"] = max_id

            data = self.client.get_json(COMMENTS_API, params=params)
            if not data:
                break

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                comment = self._parse_comment(item, post_id)
                comments.append(comment)

                # 子评论（楼中楼）
                sub_items = item.get("comments", [])
                for sub in sub_items:
                    sub_comment = self._parse_comment(
                        sub, post_id, parent_comment_id=str(item.get("id", ""))
                    )
                    comments.append(sub_comment)

            max_id = data.get("max_id", 0)
            if not max_id:
                break

        return comments

    def _parse_comment(
        self, item: dict, post_id: str, parent_comment_id: str = ""
    ) -> WeiboComment:
        user = item.get("user", {}) or {}

        # 回复对象
        reply_to_comment_id = parent_comment_id
        reply_to_user = ""
        reply_info = item.get("reply_comment")
        if reply_info:
            reply_to_comment_id = str(reply_info.get("id", parent_comment_id))
            reply_user = reply_info.get("user", {}) or {}
            reply_to_user = reply_user.get("screen_name", "")

        return WeiboComment(
            comment_id=str(item.get("id", "")),
            post_id=post_id,
            user_id=str(user.get("id", "")),
            user_nickname=user.get("screen_name", ""),
            content=item.get("text_raw", "") or strip_html(item.get("text", "")),
            publish_time=parse_weibo_time(item.get("created_at", "")),
            likes_count=int(item.get("like_counts", 0)),
            reply_to_comment_id=reply_to_comment_id,
            reply_to_user=reply_to_user,
            source_device=strip_html(item.get("source", "")),
            raw_json=item,
        )
