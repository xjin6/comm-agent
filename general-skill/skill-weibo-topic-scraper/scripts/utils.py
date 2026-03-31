"""共享工具函数"""

import html
import logging
import re
from datetime import datetime, timedelta, timezone

# 北京时间 UTC+8
CST = timezone(timedelta(hours=8))


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def strip_html(html_text: str) -> str:
    if not html_text:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", html_text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return text.strip()


def parse_weibo_time(time_str: str) -> str:
    if not time_str:
        return ""

    now = datetime.now(CST)

    # "刚刚"
    if time_str == "刚刚":
        return now.isoformat()

    # "X分钟前"
    m = re.match(r"(\d+)分钟前", time_str)
    if m:
        dt = now - timedelta(minutes=int(m.group(1)))
        return dt.isoformat()

    # "X小时前"
    m = re.match(r"(\d+)小时前", time_str)
    if m:
        dt = now - timedelta(hours=int(m.group(1)))
        return dt.isoformat()

    # "今天 HH:MM"
    m = re.match(r"今天\s*(\d{2}):(\d{2})", time_str)
    if m:
        dt = now.replace(hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0)
        return dt.isoformat()

    # "昨天 HH:MM"
    m = re.match(r"昨天\s*(\d{2}):(\d{2})", time_str)
    if m:
        dt = (now - timedelta(days=1)).replace(
            hour=int(m.group(1)), minute=int(m.group(2)), second=0, microsecond=0
        )
        return dt.isoformat()

    # "MM-DD" (今年)
    m = re.match(r"(\d{2})-(\d{2})", time_str)
    if m and len(time_str) <= 5:
        dt = now.replace(month=int(m.group(1)), day=int(m.group(2)), hour=0, minute=0, second=0, microsecond=0)
        return dt.isoformat()

    # "MM月DD日 HH:MM" (今年) 如 "03月11日 05:59"
    m = re.match(r"(\d{1,2})月(\d{1,2})日\s*(\d{2}):(\d{2})", time_str)
    if m:
        dt = now.replace(
            month=int(m.group(1)), day=int(m.group(2)),
            hour=int(m.group(3)), minute=int(m.group(4)),
            second=0, microsecond=0,
        )
        return dt.isoformat()

    # "YYYY年MM月DD日 HH:MM" 如 "2025年12月18日 12:35"
    m = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{2}):(\d{2})", time_str)
    if m:
        dt = datetime(
            int(m.group(1)), int(m.group(2)), int(m.group(3)),
            int(m.group(4)), int(m.group(5)), tzinfo=CST,
        )
        return dt.isoformat()

    # 标准格式 "Tue Mar 25 10:30:00 +0800 2026"
    try:
        dt = datetime.strptime(time_str, "%a %b %d %H:%M:%S %z %Y")
        return dt.isoformat()
    except ValueError:
        pass

    # 尝试其他常见格式
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(time_str, fmt).replace(tzinfo=CST)
            return dt.isoformat()
        except ValueError:
            continue

    return time_str


def extract_topic_tags(text: str) -> list:
    if not text:
        return []
    return re.findall(r"#(.+?)#", text)


def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", name).strip()
