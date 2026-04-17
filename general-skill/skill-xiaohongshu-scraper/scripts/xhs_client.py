"""
Xiaohongshu (小红书) API client — browser-in-the-loop signing.

Opens a headless Edge browser, navigates to XHS (loads the WASM signing module),
then makes every API call through XHS's own axios instance (webpack module 64732)
so the WASM interceptors sign requests automatically.

Users only need to provide a valid cookie — no manual x-s/x-t copy-paste needed.
"""

import json
import random
import string
import time


# JavaScript injected into the XHS page to call their own axios instance
_JS_CALL = """
async ([method, path, payload]) => {
    try {
        // Access XHS webpack module system
        let req;
        self.webpackChunkxhs_pc_web.push([[Symbol()], {}, (r) => { req = r; }]);
        const http = req(64732).dJ;

        let response;
        if (method === 'POST') {
            response = await http.post(path, payload);
        } else {
            response = await http.get(path, { params: payload });
        }
        return { ok: true, data: response.data };
    } catch(e) {
        return { ok: false, error: e.message, status: e?.response?.status };
    }
}
"""


class XHSClient:
    """Browser-in-the-loop client: uses XHS's own WASM signing automatically."""

    SEARCH_PATH  = "/api/sns/web/v1/search/notes"
    COMMENT_PATH = "/api/sns/web/v2/comment/page"
    USER_PATH    = "/api/sns/web/v1/user/otherinfo"

    # Landing page — just needs to load XHS JS bundle (including WASM)
    LANDING_URL  = "https://www.xiaohongshu.com/explore"

    def __init__(self, cookie: str,
                 delay_min: float = 3.0, delay_max: float = 7.0,
                 headless: bool = True, **kwargs):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Install playwright: pip install playwright && "
                "python -m playwright install chromium")

        self.cookie_str = cookie
        self.delay_min  = delay_min
        self.delay_max  = delay_max

        self._pw = sync_playwright().start()

        # Prefer system Edge Beta; fall back to bundled Chromium
        try:
            self._browser = self._pw.chromium.launch(
                channel="msedge", headless=headless)
        except Exception:
            self._browser = self._pw.chromium.launch(headless=headless)

        self._ctx  = self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
            )
        )
        self._load_cookies()
        self._page = self._ctx.new_page()
        self._ready = False

    # ── Cookie ────────────────────────────────────────────────────────────────

    def _load_cookies(self) -> None:
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
        self._ctx.add_cookies(cookies)

    def validate_cookie(self) -> bool:
        return "a1" in self.cookie_str

    # ── Browser init ──────────────────────────────────────────────────────────

    def _ensure_ready(self) -> None:
        """Navigate to XHS once to load the webpack bundle + WASM."""
        if self._ready:
            return
        print("  [browser] Loading XHS and WASM signing module...")
        self._page.goto(self.LANDING_URL, wait_until="domcontentloaded",
                        timeout=30000)
        # Wait for webpack bundle to fully initialise
        self._page.wait_for_function(
            "() => typeof self.webpackChunkxhs_pc_web !== 'undefined'",
            timeout=15000)
        # Small extra wait for WASM to load
        self._page.wait_for_timeout(3000)
        self._ready = True
        print("  [browser] Ready.")

    def _wait(self) -> None:
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    # ── Signed API call ───────────────────────────────────────────────────────

    def _call(self, method: str, path: str, payload: dict) -> dict:
        self._ensure_ready()
        self._wait()

        full_url = f"https://edith.xiaohongshu.com{path}"
        captured = {}

        def on_response(response):
            if path in response.url:
                try:
                    captured["body"] = response.json()
                except Exception:
                    pass

        self._page.on("response", on_response)
        try:
            self._page.evaluate(_JS_CALL, [method, path, payload])
            # Give network response time to arrive
            self._page.wait_for_timeout(2000)
        finally:
            self._page.remove_listener("response", on_response)

        data = captured.get("body")
        if data is None:
            return {"code": -1, "msg": "No response captured"}
        return data

    # ── Public API ────────────────────────────────────────────────────────────

    def search_notes(self, keyword: str, page: int = 1,
                     sort: str = "general", note_type: int = 0) -> dict:
        sid = "".join(random.choices(string.ascii_lowercase + string.digits, k=21))
        return self._call("POST", self.SEARCH_PATH, {
            "keyword":       keyword,
            "page":          page,
            "page_size":     20,
            "search_id":     sid,
            "sort":          sort,
            "note_type":     note_type,
            "ext_flags":     [],
            "geo":           "",
            "image_formats": ["jpg", "webp", "avif"],
        })

    def get_comments(self, note_id: str, cursor: str = "",
                     xsec_token: str = "") -> dict:
        return self._call("GET", self.COMMENT_PATH, {
            "note_id":        note_id,
            "cursor":         cursor,
            "top_comment_id": "",
            "image_formats":  "jpg,webp,avif",
            "xsec_token":     xsec_token,
            "xsec_source":    "pc_search",
        })

    def get_user_info(self, user_id: str) -> dict:
        return self._call("GET", self.USER_PATH,
                          {"target_user_id": user_id})

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass

    def __del__(self):
        self.close()
