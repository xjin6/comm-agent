"""微博 HTTP 客户端，封装请求、速率控制和重试逻辑"""

import random
import time
from typing import Optional

import requests

import config
from utils import setup_logger

logger = setup_logger("weibo_client")


class WeiboClient:
    def __init__(self, cookie: str, delay_range: tuple = None):
        self.session = requests.Session()
        self.session.headers.update(config.DEFAULT_HEADERS)
        self.session.headers["Cookie"] = cookie
        self.delay_range = delay_range or config.DEFAULT_DELAY_RANGE
        self.consecutive_failures = 0

    def get(self, url: str, params: dict = None) -> Optional[requests.Response]:
        """发送GET请求，返回Response对象（非JSON）"""
        for attempt in range(1, config.MAX_RETRIES + 1):
            self._sleep()

            try:
                resp = self.session.get(
                    url, params=params, timeout=config.REQUEST_TIMEOUT,
                    allow_redirects=False,
                )
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_BACKOFF * attempt)
                continue

            # 检测被封/限流
            if resp.status_code in (403, 418, 429):
                logger.warning(f"触发限流 (HTTP {resp.status_code})，暂停 {config.LONG_BLOCK_PAUSE}s...")
                self.consecutive_failures += 1
                if self.consecutive_failures >= 3:
                    logger.error("连续3次被限流，建议更换Cookie或稍后重试")
                    return None
                time.sleep(config.LONG_BLOCK_PAUSE)
                continue

            # 检测登录跳转
            if resp.status_code in (301, 302):
                location = resp.headers.get("Location", "")
                if "passport" in location or "login" in location:
                    logger.error("Cookie已失效，请重新获取Cookie")
                    return None

            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code}，尝试 {attempt}/{config.MAX_RETRIES}")
                if attempt < config.MAX_RETRIES:
                    time.sleep(config.RETRY_BACKOFF * attempt)
                continue

            self.consecutive_failures = 0
            return resp

        logger.error(f"请求失败，已达最大重试次数: {url}")
        return None

    def get_json(self, url: str, params: dict = None) -> Optional[dict]:
        """发送GET请求，返回解析后的JSON"""
        resp = self.get(url, params=params)
        if not resp:
            return None
        try:
            return resp.json()
        except ValueError:
            logger.warning("响应非JSON格式")
            return None

    def _sleep(self):
        delay = random.uniform(*self.delay_range)
        logger.debug(f"等待 {delay:.1f}s...")
        time.sleep(delay)
