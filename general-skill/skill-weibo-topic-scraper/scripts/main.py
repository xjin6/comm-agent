"""微博话题爬虫 - 主入口"""

import argparse
import os
from datetime import date

import config
from comment_scraper import CommentScraper
from exporters import (
    export_comments_to_csv,
    export_comments_to_json,
    export_posts_to_csv,
    export_posts_to_json,
    export_profiles_to_csv,
    export_profiles_to_json,
)
from profile_scraper import ProfileScraper
from topic_scraper import TopicScraper
from utils import sanitize_filename, setup_logger
from weibo_client import WeiboClient


def main():
    parser = argparse.ArgumentParser(
        description="微博话题爬虫 - 爬取话题讨论、评论及用户资料"
    )
    parser.add_argument("--topic", required=True, help="话题名称（不含#号）")
    parser.add_argument("--cookie", required=True, help="微博Cookie字符串")
    parser.add_argument(
        "--start-date", default=None,
        help="起始日期 YYYY-MM-DD（指定后按天分段爬取，突破50页限制）",
    )
    parser.add_argument(
        "--end-date", default=None,
        help="结束日期 YYYY-MM-DD（默认今天）",
    )
    parser.add_argument(
        "--output-dir", default=None, help="输出目录（默认 output/话题名）"
    )
    parser.add_argument(
        "--skip-comments", action="store_true", help="跳过评论爬取"
    )
    parser.add_argument(
        "--skip-profiles", action="store_true", help="跳过用户资料爬取"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "both"],
        default="both",
        help="输出格式（默认both）",
    )
    parser.add_argument(
        "--delay-min", type=float, default=3, help="请求最小间隔秒数（默认3）"
    )
    parser.add_argument(
        "--delay-max", type=float, default=7, help="请求最大间隔秒数（默认7）"
    )
    args = parser.parse_args()

    # 解析日期
    start_date = None
    end_date = None
    if args.start_date:
        start_date = date.fromisoformat(args.start_date)
        end_date = date.fromisoformat(args.end_date) if args.end_date else date.today()

    # 输出目录
    output_dir = args.output_dir or os.path.join(
        config.DEFAULT_OUTPUT_DIR, sanitize_filename(args.topic)
    )
    os.makedirs(output_dir, exist_ok=True)

    logger = setup_logger(
        "main", log_file=os.path.join(output_dir, "scraper.log")
    )
    logger.info(f"话题: #{args.topic}#")
    if start_date:
        logger.info(f"日期范围: {start_date} ~ {end_date}")
    logger.info(f"输出目录: {output_dir}")

    # 初始化客户端
    client = WeiboClient(
        cookie=args.cookie,
        delay_range=(args.delay_min, args.delay_max),
    )

    # 增量保存回调
    def on_progress(index, posts):
        if index % config.INCREMENTAL_SAVE_INTERVAL == 0:
            logger.info("增量保存...")
            _save_posts(posts, output_dir, args.format)

    # 1. 爬取话题帖子
    topic_scraper = TopicScraper(client)
    posts = topic_scraper.scrape_topic(
        args.topic,
        start_date=start_date,
        end_date=end_date,
        on_progress=on_progress,
    )

    if not posts:
        logger.warning("未获取到任何微博数据")
        return

    _save_posts(posts, output_dir, args.format)

    # 2. 爬取评论
    comments = []
    if not args.skip_comments:
        comment_scraper = CommentScraper(client)
        comments = comment_scraper.scrape_all_posts_comments(posts)
        if comments:
            _save_comments(comments, output_dir, args.format)

    # 3. 爬取用户资料（发帖人 + 评论人，去重）
    profiles = []
    if not args.skip_profiles:
        user_ids = [p.user_id for p in posts if p.user_id]
        user_ids += [c.user_id for c in comments if c.user_id]
        profile_scraper = ProfileScraper(client)
        profiles = profile_scraper.scrape_profiles(user_ids)
        if profiles:
            _save_profiles(profiles, output_dir, args.format)

    # 打印摘要
    print("\n" + "=" * 50)
    print("爬取完成!")
    print(f"  话题: #{args.topic}#")
    print(f"  微博数量: {len(posts)}")
    if not args.skip_comments:
        print(f"  评论数量: {len(comments)}")
    if not args.skip_profiles:
        print(f"  用户数量: {len(profiles)}")
    print(f"  输出目录: {output_dir}")
    print("=" * 50)


def _save_posts(posts, output_dir, fmt):
    if fmt in ("csv", "both"):
        export_posts_to_csv(posts, os.path.join(output_dir, "posts.csv"))
    if fmt in ("json", "both"):
        export_posts_to_json(posts, os.path.join(output_dir, "posts.json"))


def _save_comments(comments, output_dir, fmt):
    if fmt in ("csv", "both"):
        export_comments_to_csv(comments, os.path.join(output_dir, "comments.csv"))
    if fmt in ("json", "both"):
        export_comments_to_json(comments, os.path.join(output_dir, "comments.json"))


def _save_profiles(profiles, output_dir, fmt):
    if fmt in ("csv", "both"):
        export_profiles_to_csv(
            profiles, os.path.join(output_dir, "profiles.csv")
        )
    if fmt in ("json", "both"):
        export_profiles_to_json(
            profiles, os.path.join(output_dir, "profiles.json")
        )


if __name__ == "__main__":
    main()
