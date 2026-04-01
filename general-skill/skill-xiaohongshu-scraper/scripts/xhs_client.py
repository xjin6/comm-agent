"""
Xiaohongshu (小红书) API client using Playwright.
Runs a real browser with the user's cookies so all request signing
is handled automatically by XHS's own JavaScript.
"""

import json
import time
import random
from typing import Optional


class XHSClient:
    """Browser-based XHS client via Playwright."""

    SEARCH_API  = "https://edith.xiaohongshu.com/api/sns/web/v1/search/notes"
    COMMENT_API = "https://edith.xiaohongshu.com/api/sns/web/v2/comment/page"
    USER_API    = "https://edith.xiaohongshu.com/api/sns/web/v1/user/otherinfo"
    BASE_URL    = "https://www.xiaohongshu.com"

    def __init__(self, cookie: str, delay_min: float = 3.0, delay_max: float = 7.0,
                 headless: bool = True):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError("Please install playwright: pip install playwright && python -m playwright install chromium")

        self.cookie_str = cookie
        self.delay_min  = delay_min
        self.delay_max  = delay_max
        self.headless   = headless

        self._pw      = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._context = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        )
        self._load_cookies()
        self._page = self._context.new_page()
        # Navigate to XHS so cookies are active and JS is loaded
        self._page.goto(self.BASE_URL, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

    def _load_cookies(self) -> None:
        """Parse cookie string and set in browser context."""
        cookies = []
        for part in self.cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookies.append({
                    "name":   k.strip(),
                    "value":  v.strip(),
                    "domain": ".xiaohongshu.com",
                    "path":   "/",
                })
        self._context.add_cookies(cookies)

    def validate_cookie(self) -> bool:
        return "a1" in self.cookie_str

    def _wait(self) -> None:
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def _api_post(self, url: str, payload: dict) -> dict:
        """Make a POST request through the browser context (handles signing)."""
        self._wait()
        result = self._page.evaluate(
            """async ([url, payload]) => {
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    credentials: 'include',
                    body: JSON.stringify(payload)
                });
                return await resp.json();
            }""",
            [url, payload]
        )
        return result

    def _api_get(self, url: str, params: dict) -> dict:
        """Make a GET request through the browser context."""
        self._wait()
        qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
        full_url = f"{url}?{qs}" if qs else url
        result = self._page.evaluate(
            """async (url) => {
                const resp = await fetch(url, {
                    method: 'GET',
                    credentials: 'include',
                });
                return await resp.json();
            }""",
            full_url
        )
        return result

    def search_notes(self, keyword: str, page: int = 1,
                     sort: str = "general", note_type: int = 0) -> dict:
        payload = {
            "keyword":   keyword,
            "page":      page,
            "page_size": 20,
            "search_id": self._random_id(),
            "sort":      sort,
            "note_type": note_type,
            "ext_flags": [],
        }
        return self._api_post(self.SEARCH_API, payload)

    def get_note_comments(self, note_id: str, cursor: str = "",
                          xsec_token: str = "") -> dict:
        params = {
            "note_id":     note_id,
            "cursor":      cursor,
            "top_comment_id": "",
            "image_formats": "jpg,webp,avif",
            "xsec_token":  xsec_token,
            "xsec_source": "pc_search",
        }
        return self._api_get(self.COMMENT_API, params)

    def get_user_info(self, user_id: str) -> dict:
        return self._api_get(self.USER_API, {"target_user_id": user_id})

    @staticmethod
    def _random_id(length: int = 32) -> str:
        import random, string
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass

    def __del__(self):
        self.close()
