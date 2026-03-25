"""话题帖子爬取模块 - 桌面版 s.weibo.com，支持按日期分段突破50页限制"""

import re
from datetime import date, timedelta

from bs4 import BeautifulSoup

import config
from data_models import WeiboPost
from utils import extract_topic_tags, parse_weibo_time, setup_logger
from weibo_client import WeiboClient

logger = setup_logger("topic_scraper")

MAX_PAGES_PER_QUERY = 50  # 微博搜索单次查询最多50页


class TopicScraper:
    def __init__(self, client: WeiboClient):
        self.client = client
        self.seen_post_ids: set = set()

    def scrape_topic(
        self,
        topic_name: str,
        start_date: date = None,
        end_date: date = None,
        on_progress=None,
    ) -> list:
        """
        爬取话题全部帖子。
        如果指定了日期范围，按天分段爬取以突破50页限制。
        如果不指定日期，则只爬默认结果（最多50页）。
        """
        query = f"#{topic_name}#"

        if start_date and end_date:
            return self._scrape_by_date_range(
                query, start_date, end_date, on_progress
            )
        else:
            posts, _ = self._scrape_pages(query, on_progress=on_progress)
            return posts

    def _scrape_by_date_range(
        self, query: str, start_date: date, end_date: date, on_progress=None
    ) -> list:
        """按天分段爬取；如果某天爬满50页，自动按小时细分重爬"""
        posts = []
        current = start_date
        total_days = (end_date - start_date).days + 1

        logger.info(
            f"开始按日期分段爬取: {start_date} ~ {end_date} (共{total_days}天)"
        )

        day_index = 0
        while current <= end_date:
            day_index += 1
            date_str = current.strftime("%Y-%m-%d")
            timescope = f"custom:{date_str}-0:{date_str}-23"

            logger.info(f"[{day_index}/{total_days}] 爬取 {date_str}...")

            day_posts, hit_limit = self._scrape_pages(
                query, timescope=timescope, date_label=date_str
            )

            if hit_limit:
                # 该天数据量超过50页上限，按小时细分重爬
                logger.info(
                    f"[{day_index}/{total_days}] {date_str} 触及50页上限 "
                    f"({len(day_posts)}条)，按小时细分重爬..."
                )
                # 清除这天已爬的帖子ID，让小时分段重新爬
                day_post_ids = {p.post_id for p in day_posts}
                self.seen_post_ids -= day_post_ids
                day_posts = self._scrape_by_hours(query, date_str)

            posts.extend(day_posts)

            logger.info(
                f"[{day_index}/{total_days}] {date_str}: {len(day_posts)}条, 累计{len(posts)}条"
            )

            if on_progress:
                on_progress(day_index, posts)

            current += timedelta(days=1)

        logger.info(f"全部日期爬取完成，共{len(posts)}条微博")
        return posts

    def _scrape_by_hours(self, query: str, date_str: str) -> list:
        """将某天拆成24个小时分别爬取"""
        posts = []
        for hour in range(24):
            timescope = f"custom:{date_str}-{hour}:{date_str}-{hour}"
            label = f"{date_str} {hour:02d}:00"

            hour_posts, _ = self._scrape_pages(
                query, timescope=timescope, date_label=label
            )
            posts.extend(hour_posts)

            if hour_posts:
                logger.info(f"    {label}: {len(hour_posts)}条")

        return posts

    def _get_total_pages(self, soup) -> int:
        """从HTML分页栏读取总页数"""
        page_links = soup.select(".s-scroll a")
        if not page_links:
            return 1
        # 最后一个分页链接的文本，如 "第6页"
        last_text = page_links[-1].get_text(strip=True)
        m = re.search(r"\d+", last_text)
        return int(m.group()) if m else 1

    def _scrape_pages(
        self, query: str, timescope: str = None, date_label: str = "",
        on_progress=None,
    ) -> tuple:
        """
        爬取单个查询条件下的所有页。
        先从第1页读取总页数，精确翻页，不浪费请求。
        返回 (posts列表, 总页数是否达到50页上限)。
        """
        posts = []
        total_pages = None
        prefix = f"{date_label} " if date_label else ""

        for page in range(1, MAX_PAGES_PER_QUERY + 1):
            # 如果已知总页数，超出则停止
            if total_pages is not None and page > total_pages:
                break

            params = {"q": query, "page": page}
            if timescope:
                params["timescope"] = timescope

            resp = self.client.get(
                f"{config.SEARCH_BASE_URL}{config.SEARCH_PATH}", params=params
            )

            if not resp:
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # 第1页时读取总页数
            if page == 1:
                total_pages = self._get_total_pages(soup)
                logger.info(f"  {prefix}共{total_pages}页")

            cards = soup.select('div[action-type="feed_list_item"]')

            if not cards:
                break

            new_count = 0
            for card in cards:
                mid = card.get("mid", "")
                if not mid or mid in self.seen_post_ids:
                    continue

                self.seen_post_ids.add(mid)
                post = self._parse_card(card)
                posts.append(post)
                new_count += 1

            logger.info(f"  {prefix}第{page}/{total_pages}页: 新增{new_count}条")

            if on_progress and not timescope:
                on_progress(page, posts)

        hit_limit = (total_pages is not None and total_pages >= MAX_PAGES_PER_QUERY)
        return posts, hit_limit

    def _parse_card(self, card) -> WeiboPost:
        mid = card.get("mid", "")

        # 用户信息
        name_el = card.select_one(".name")
        user_nickname = name_el.get("nick-name", "") if name_el else ""
        user_id = ""
        if name_el:
            href = name_el.get("href", "")
            m = re.search(r"weibo\.com/(\d+)", href)
            if m:
                user_id = m.group(1)

        # 正文 - 优先取完整版
        full_el = card.select_one('p[node-type="feed_list_content_full"]')
        short_el = card.select_one('p[node-type="feed_list_content"]')
        if full_el:
            content = full_el.get_text(strip=True)
        elif short_el:
            content = short_el.get_text(strip=True)
        else:
            content = ""

        # 时间和来源
        from_el = card.select_one(".from")
        publish_time = ""
        source_device = ""
        if from_el:
            links = from_el.select("a")
            if len(links) >= 1:
                publish_time = parse_weibo_time(links[0].get_text(strip=True))
            if len(links) >= 2:
                source_device = links[1].get_text(strip=True)

        # 互动数据：转发、评论、点赞
        acts = card.select(".card-act li a")
        reposts_count = 0
        comments_count = 0
        likes_count = 0
        if len(acts) >= 1:
            reposts_count = self._parse_count(acts[0].get_text(strip=True))
        if len(acts) >= 2:
            comments_count = self._parse_count(acts[1].get_text(strip=True))
        if len(acts) >= 3:
            likes_count = self._parse_count(acts[2].get_text(strip=True))

        # 图片
        images = []
        media_el = card.select_one('div[node-type="feed_list_media_prev"]')
        if media_el:
            for img in media_el.select("img"):
                src = img.get("src", "")
                if src:
                    if src.startswith("//"):
                        src = "https:" + src
                    images.append(src)

        # 视频
        video_url = ""
        video_el = card.select_one(
            'div[node-type="feed_list_media_prev"] .WB_video'
        )
        if video_el:
            video_url = video_el.get("action-data", "")

        # 话题标签
        topic_tags = extract_topic_tags(content)

        return WeiboPost(
            post_id=mid,
            user_id=user_id,
            user_nickname=user_nickname,
            content=content,
            publish_time=publish_time,
            reposts_count=reposts_count,
            comments_count=comments_count,
            likes_count=likes_count,
            images=images,
            video_url=video_url,
            topic_tags=topic_tags,
            source_device=source_device,
            raw_json={},
        )

    @staticmethod
    def _parse_count(text: str) -> int:
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else 0
