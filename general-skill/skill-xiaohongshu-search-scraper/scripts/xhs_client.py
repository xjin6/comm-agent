"""
Xiaohongshu (小红书) scraper — navigate + click + intercept.

Opens a browser (auto-detected from the system), navigates to the XHS
search results page, and for each note:
  1. Intercepts the search/notes API response for the basic note list.
  2. Clicks each note card — this triggers:
       - /api/sns/web/v1/feed  (full note detail: desc, time, ip, tags, video)
       - /api/sns/web/v2/comment/page  (first page of comments)
  3. Uses webpack injection (req(64732).dJ) with the page's xsec_token to
     paginate through all comment pages.
  4. Goes back to the search results before clicking the next note.

get_comments() returns data from the in-memory cache built during search_notes().
get_user_info() navigates to the user profile and intercepts the user API.

Browser auto-detection order: Edge → Chrome → Edge Beta → Chrome Beta →
Edge Dev → Edge Canary → bundled Chromium (requires `playwright install chromium`).
Pass browser="msedge" / "chrome" / etc. to override.
"""

import json
import time
import random
import urllib.parse

_BROWSER_CHANNELS = [
    "msedge",
    "chrome",
    "msedge-beta",
    "chrome-beta",
    "msedge-dev",
    "msedge-canary",
]

# Webpack injection: call comment API with cursor (camelCase response)
_JS_COMMENT = """async ([note_id, xsec, cursor]) => {
    try {
        let req;
        window.webpackChunkxhs_pc_web.push([[Symbol()], {}, (r) => { req = r; }]);
        const http = req(64732).dJ;
        const r = await http.get("/api/sns/web/v2/comment/page", {params: {
            note_id, cursor: cursor || "", top_comment_id: "",
            image_formats: "jpg,webp,avif",
            xsec_token: xsec, xsec_source: "pc_search"
        }});
        return {ok: true, r};
    } catch(e) { return {ok: false, err: e.message}; }
}"""

# Webpack injection: call sub-comment API for a comment
_JS_SUB_COMMENT = """async ([note_id, comment_id, xsec, cursor]) => {
    try {
        let req;
        window.webpackChunkxhs_pc_web.push([[Symbol()], {}, (r) => { req = r; }]);
        const http = req(64732).dJ;
        const r = await http.get("/api/sns/web/v2/comment/sub/page", {params: {
            note_id, root_comment_id: comment_id, cursor: cursor || "",
            image_formats: "jpg,webp,avif",
            xsec_token: xsec, xsec_source: "pc_search"
        }});
        return {ok: true, r};
    } catch(e) { return {ok: false, err: e.message}; }
}"""

# Webpack injection: fetch user profile data without page navigation
_JS_USER = """async ([user_id]) => {
    try {
        let req;
        window.webpackChunkxhs_pc_web.push([[Symbol()], {}, (r) => { req = r; }]);
        const http = req(64732).dJ;
        const r = await http.get("/api/sns/web/v1/user/otherinfo", {params: {
            target_user_id: user_id,
            image_formats: "jpg,webp,avif"
        }});
        return {ok: true, r};
    } catch(e) { return {ok: false, err: e.message}; }
}"""


def _detect_channel(pw) -> str | None:
    for channel in _BROWSER_CHANNELS:
        try:
            b = pw.chromium.launch(channel=channel, headless=True)
            b.close()
            return channel
        except Exception:
            continue
    return None


def _ua_for_channel(channel: str | None) -> str:
    """Return a realistic User-Agent string matching the detected browser."""
    base = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36")
    if channel and "msedge" in channel:
        return base + " Edg/147.0.0.0"
    # Chrome, Chrome-beta, bundled Chromium — plain Chrome UA
    return base


class XHSClient:

    BASE_URL = "https://www.xiaohongshu.com"

    def __init__(self, cookie: str,
                 delay_min: float = 3.0, delay_max: float = 7.0,
                 browser: str = "auto", headless: bool = True, **kwargs):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Install playwright:  pip install playwright\n"
                "If you have Microsoft Edge or Google Chrome, no further setup needed.\n"
                "If you have no browser installed, also run:\n"
                "  python -m playwright install chromium")

        self.cookie_str = cookie
        self.delay_min  = delay_min
        self.delay_max  = delay_max

        self._pw = sync_playwright().start()

        if browser == "auto":
            channel = _detect_channel(self._pw)
            if channel:
                print(f"  [browser] Auto-detected: {channel}")
                self._browser = self._pw.chromium.launch(channel=channel, headless=headless)
            else:
                print("  [browser] No system browser found — using bundled Chromium.")
                channel = None
                try:
                    self._browser = self._pw.chromium.launch(headless=headless)
                except Exception:
                    self._pw.stop()
                    raise RuntimeError(
                        "No browser available.\n"
                        "Run: python -m playwright install chromium")
        else:
            channel = browser
            print(f"  [browser] Using: {browser}")
            self._browser = self._pw.chromium.launch(channel=browser, headless=headless)

        self._ctx = self._browser.new_context(
            user_agent=_ua_for_channel(channel)
        )
        self._load_cookies()
        self._page = self._ctx.new_page()

        # Cache: note_id → {"comments": [...], "has_more": False, "cursor": ""}
        self._comment_cache: dict = {}
        self._search_url: str | None = None

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

    def _wait(self) -> None:
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def _short_wait(self) -> None:
        time.sleep(random.uniform(1.5, 2.5))

    # ── Network capture ───────────────────────────────────────────────────────

    def _capture_api(self, url_fragment: str, action,
                     timeout_ms: int = 12000) -> dict | None:
        captured = {}
        def on_response(response):
            if url_fragment in response.url and "captured" not in captured:
                try:
                    captured["data"] = response.json()
                except Exception:
                    pass
        self._page.on("response", on_response)
        try:
            action()
            deadline = time.time() + timeout_ms / 1000
            while "data" not in captured and time.time() < deadline:
                self._page.wait_for_timeout(200)
        finally:
            self._page.remove_listener("response", on_response)
        return captured.get("data")

    # ── xsec_token extraction ─────────────────────────────────────────────────

    def _xsec_from_url(self) -> str:
        try:
            qs = urllib.parse.urlparse(self._page.url).query
            return urllib.parse.parse_qs(qs).get("xsec_token", [""])[0]
        except Exception:
            return ""

    # ── Comment pagination via webpack injection ──────────────────────────────

    def _fetch_all_comments(self, note_id: str, xsec: str,
                            initial_comments: list,
                            initial_cursor: str,
                            initial_has_more,
                            max_pages: int = 10) -> list:
        """
        Starting from the already-captured first page, paginate all comment
        pages using webpack injection.  Returns the merged comment list.
        """
        all_cmts = list(initial_comments)
        cursor    = initial_cursor
        has_more  = initial_has_more
        page_num  = 0

        while has_more and cursor and page_num < max_pages:
            self._short_wait()
            result = self._page.evaluate(_JS_COMMENT, [note_id, xsec, cursor])
            if not result or not result.get("ok"):
                break
            r        = result.get("r", {})
            new_cmts = r.get("comments", [])
            if not new_cmts:
                break
            all_cmts.extend(new_cmts)
            cursor   = r.get("cursor", "")
            has_more = r.get("hasMore", False)
            page_num += 1

        return all_cmts

    def _expand_sub_comments(self, note_id: str, xsec: str,
                              comments: list) -> list:
        """
        For every comment:
        - Normalise initial sub-comments (snake_case sub_comments → camelCase subComments).
        - For comments with subCommentHasMore=True, paginate and append remaining sub-comments.
        """
        for cmt in comments:
            cmt_id = cmt.get("id", "")
            if not cmt_id:
                continue

            # Seed subComments with whichever key has the initial batch
            initial = cmt.get("subComments") or cmt.get("sub_comments") or []
            seen     = {s.get("id") for s in initial if s.get("id")}
            cmt["subComments"] = list(initial)   # normalise to camelCase

            sub_has_more = cmt.get("subCommentHasMore") or cmt.get("sub_comment_has_more")
            sub_cursor   = cmt.get("subCommentCursor")  or cmt.get("sub_comment_cursor", "")
            if not (sub_has_more and sub_cursor):
                continue

            page_num = 0
            while sub_has_more and sub_cursor and page_num < 5:
                self._short_wait()
                result = self._page.evaluate(
                    _JS_SUB_COMMENT, [note_id, cmt_id, xsec, sub_cursor])
                if not result or not result.get("ok"):
                    break
                r = result.get("r", {})
                new_subs = r.get("comments", [])
                if not new_subs:
                    break
                for s in new_subs:
                    sid = s.get("id")
                    if sid not in seen:
                        cmt["subComments"].append(s)
                        seen.add(sid)
                sub_cursor   = r.get("cursor", "")
                sub_has_more = r.get("hasMore", False)
                page_num += 1

        return comments

    # ── Public API ────────────────────────────────────────────────────────────

    def search_notes(self, keyword: str, page: int = 1,
                     sort: str = "general", note_type: int = 0) -> dict:
        """
        Navigate to the search page, capture basic note list, then click each
        note card to enrich it with feed data (desc, time, ip, video, tags)
        and pre-fetch all its comments.
        """
        self._wait()
        kw_enc     = urllib.parse.quote(keyword)
        search_url = (f"{self.BASE_URL}/search_result/"
                      f"?keyword={kw_enc}&type=51&sort_type={sort}")

        if page == 1:
            self._search_url = search_url
            search_data = self._capture_api(
                "search/notes",
                lambda: self._page.goto(search_url, wait_until="load",
                                        timeout=30000),
                timeout_ms=15000,
            )
        else:
            # Scroll to trigger the next page of results
            search_data = self._capture_api(
                "search/notes",
                lambda: self._page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"),
                timeout_ms=10000,
            )

        if search_data is None:
            title = self._page.title()
            if "登录" in title or len(self._page.content()) < 5000:
                return {"code": 301, "msg": "Cookie expired — please get a fresh cookie."}
            return {"code": 0, "data": {"items": [], "has_more": False}}

        # Normalise outer wrapper (sometimes absent after XHS interceptors)
        if "code" in search_data:
            items = search_data.get("data", {}).get("items", [])
        else:
            items = search_data.get("items", [])

        if not items:
            return {"code": 0, "data": {"items": [], "has_more": False}}

        # ── Click each note card to enrich + pre-fetch comments ──────────────
        enriched_map: dict = {}   # note_id → feed note_card data
        feed_responses: dict = {}  # note_id → captured feed JSON (raw)

        def _register_feed(r):
            if "/api/sns/web/v1/feed" in r.url:
                try:
                    body = r.json()
                    feed_items = (body.get("data") or {}).get("items", [])
                    for fi in feed_items:
                        nid = (fi.get("note_card") or {}).get("note_id", "")
                        if nid:
                            feed_responses[nid] = fi
                except Exception:
                    pass

        self._page.on("response", _register_feed)

        cards = self._page.query_selector_all("section.note-item")
        for card in cards:
            a = card.query_selector('a[href*="/explore/"]')
            if not a:
                continue
            href    = a.get_attribute("href") or ""
            note_id = (href.split("/explore/")[-1].split("?")[0]) if "/explore/" in href else ""
            if not note_id:
                continue

            # Set up comment listener BEFORE clicking (response fires during click)
            comment_captured: dict = {}
            def _on_cmt(r, _c=comment_captured):
                if "comment/page" in r.url and "data" not in _c:
                    try:
                        _c["data"] = r.json()
                    except Exception:
                        pass

            self._page.on("response", _on_cmt)
            try:
                self._short_wait()
                card.click()
                # Wait for feed + comment API responses to arrive
                self._page.wait_for_timeout(4000)

                xsec = self._xsec_from_url()
                comment_data = comment_captured.get("data")

                # Paginate remaining comment pages via webpack injection
                if comment_data is not None:
                    cmt_inner = comment_data.get("data", comment_data)
                    first_cmts = cmt_inner.get("comments", [])
                    cursor     = cmt_inner.get("cursor", "") or ""
                    has_more   = (cmt_inner.get("has_more")
                                  or cmt_inner.get("hasMore", False))

                    all_cmts = self._fetch_all_comments(
                        note_id, xsec, first_cmts, cursor, has_more)
                    all_cmts = self._expand_sub_comments(note_id, xsec, all_cmts)
                    self._comment_cache[note_id] = {
                        "comments": all_cmts,
                        "has_more": False,
                        "cursor":   "",
                    }

                # Go back to search results
                self._page.go_back(wait_until="load", timeout=15000)
                self._page.wait_for_timeout(1500)

            except Exception:
                try:
                    self._page.goto(search_url, wait_until="load", timeout=15000)
                    self._page.wait_for_timeout(2000)
                except Exception:
                    pass
            finally:
                self._page.remove_listener("response", _on_cmt)

        self._page.remove_listener("response", _register_feed)

        # ── Merge feed data into search items ────────────────────────────────
        wrapped = []
        for item in items:
            note_id = item.get("id", "")
            feed    = feed_responses.get(note_id, {})
            nc_feed = feed.get("note_card", {})
            nc_src  = item.get("note_card", {})

            # Prefer feed fields (richer) but fall back to search card
            merged_nc = {
                **nc_src,
                "title":           nc_feed.get("title") or nc_src.get("title") or nc_src.get("display_title", ""),
                "display_title":   nc_feed.get("display_title") or nc_src.get("display_title", ""),
                "desc":            nc_feed.get("desc", ""),
                "type":            nc_feed.get("type") or nc_src.get("type", "normal"),
                "tag_list":        nc_feed.get("tag_list") or nc_src.get("tag_list") or [],
                "image_list":      nc_feed.get("image_list") or nc_src.get("image_list") or [],
                "video":           nc_feed.get("video", {}),
                "time":            nc_feed.get("time") or nc_src.get("time", 0),
                "last_update_time": nc_feed.get("last_update_time") or nc_src.get("last_update_time", 0),
                "ip_location":     nc_feed.get("ip_location") or nc_src.get("ip_location", ""),
                "interact_info":   nc_feed.get("interact_info") or nc_src.get("interact_info", {}),
                "user":            nc_feed.get("user") or nc_src.get("user", {}),
            }
            wrapped.append({
                "id":         note_id,
                "xsec_token": item.get("xsec_token", ""),
                "note_card":  merged_nc,
            })

        return {"code": 0, "data": {"items": wrapped, "has_more": True}}

    def get_comments(self, note_id: str, cursor: str = "",
                     xsec_token: str = "") -> dict:
        """
        Return cached comments collected during search_notes().
        If not cached (e.g. comment collection was skipped), returns empty.
        """
        if note_id in self._comment_cache:
            return {"code": 0, "data": self._comment_cache[note_id]}
        return {"code": 0, "data": {"comments": [], "has_more": False, "cursor": ""}}

    def get_user_info(self, user_id: str) -> dict:
        clean_id = user_id.split("?")[0]
        self._wait()

        # Primary: webpack injection from current page (fast, no navigation needed)
        try:
            result = self._page.evaluate(_JS_USER, [clean_id])
            if result and result.get("ok"):
                r = result.get("r") or {}
                if isinstance(r, dict) and r:
                    # Webpack response omits user_id — inject it from the argument
                    for key in ("basicInfo", "basic_info"):
                        if key in r:
                            r[key]["user_id"] = clean_id
                            break
                    return {"code": 0, "data": r}
        except Exception:
            pass

        # Fallback: navigate to user profile page and intercept the API response
        data = self._capture_api(
            "otherinfo",
            lambda: self._page.goto(
                f"{self.BASE_URL}/user/profile/{clean_id}",
                wait_until="networkidle", timeout=30000),
            timeout_ms=12000,
        )

        if data is None:
            return {"code": 0, "data": {}}
        if "code" in data:
            return data
        return {"code": 0, "data": data}

    def close(self) -> None:
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            pass

    def __del__(self):
        self.close()
