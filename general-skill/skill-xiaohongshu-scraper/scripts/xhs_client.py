"""
Xiaohongshu (小红书) scraper using Selenium + Edge.
Navigates real XHS pages and extracts data from the rendered DOM —
no API signing required.

Key behaviours:
- search_notes: scrolls the search page; clicks each note card briefly
  to capture its xsec_token from the URL, then goes back.
- get_comments: navigates directly to /explore/ID?xsec_token=TOKEN
  (direct navigation without token is blocked by XHS).
- get_user_info: navigates to /user/profile/ID and reads the data block.
"""

import time
import random
import json
import urllib.parse


class XHSClient:

    BASE_URL = "https://www.xiaohongshu.com"

    def __init__(self, cookie: str, delay_min: float = 3.0, delay_max: float = 7.0,
                 **kwargs):
        try:
            from selenium import webdriver
            from selenium.webdriver.edge.options import Options
        except ImportError:
            raise ImportError("Please install selenium: pip install selenium")

        self.cookie_str = cookie
        self.delay_min  = delay_min
        self.delay_max  = delay_max

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
        )

        from selenium import webdriver
        self.driver = webdriver.Edge(options=options)

        self.driver.get(self.BASE_URL)
        time.sleep(1)
        self.driver.delete_all_cookies()
        for part in self.cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                try:
                    self.driver.add_cookie({
                        "name":   k.strip(),
                        "value":  v.strip(),
                        "domain": ".xiaohongshu.com",
                        "path":   "/",
                    })
                except Exception:
                    pass

    def validate_cookie(self) -> bool:
        return "a1" in self.cookie_str

    def _wait(self) -> None:
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def _short_wait(self) -> None:
        time.sleep(random.uniform(1.0, 2.0))

    def _extract_xsec_token_from_url(self) -> str:
        """Parse xsec_token out of the current browser URL."""
        try:
            url = self.driver.current_url
            qs = urllib.parse.urlparse(url).query
            return urllib.parse.parse_qs(qs).get("xsec_token", [""])[0]
        except Exception:
            return ""

    def search_notes(self, keyword: str, page: int = 1,
                     sort: str = "general", note_type: int = 0) -> dict:
        """
        Navigate to the search results page, scroll to the requested page,
        extract note metadata from the DOM, then click each note briefly to
        capture its xsec_token from the URL before going back.
        """
        self._wait()

        sort_map = {
            "general":               "general",
            "time_descending":       "time_descending",
            "popularity_descending": "popularity_descending",
        }
        sort_val = sort_map.get(sort, "general")
        kw_enc = urllib.parse.quote(keyword)
        search_url = f"{self.BASE_URL}/search_result/?keyword={kw_enc}&type=51&sort_type={sort_val}"

        self.driver.get(search_url)
        time.sleep(4)

        # Scroll to load the requested page number
        for _ in range(page - 1):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        # Extract basic metadata from DOM
        raw = self.driver.execute_script("""
        var items = document.querySelectorAll('section.note-item');
        var results = [];
        for (var i = 0; i < items.length; i++) {
            var el = items[i];
            var a = el.querySelector('a[href*="/explore/"]');
            var href = a ? a.getAttribute('href') : '';
            var noteId = '';
            if (href) {
                var rest = href.split('/explore/')[1] || '';
                noteId = rest.split('?')[0];
            }

            var titleEl = el.querySelector('.title span, [class*="title"] span');
            var title = titleEl ? titleEl.innerText.trim() : '';

            var authorEl = el.querySelector('.author span, [class*="author"] span, .name');
            var author = authorEl ? authorEl.innerText.trim() : '';

            var likeEl = el.querySelector('[class*="like"] span:last-child, .like-wrapper span');
            var likes = likeEl ? likeEl.innerText.trim() : '0';

            var imgEl = el.querySelector('img');
            var img = imgEl ? (imgEl.getAttribute('src') || imgEl.getAttribute('data-src') || '') : '';

            var authorHref = el.querySelector('a[href*="/user/profile/"]');
            var authorId = '';
            if (authorHref) {
                authorId = (authorHref.getAttribute('href').split('/user/profile/')[1] || '').split('?')[0];
            }

            results.push({
                note_id:     noteId,
                title:       title,
                author:      author,
                author_id:   authorId,
                liked_count: likes,
                cover_url:   img,
                xsec_token:  '',
            });
        }
        return JSON.stringify(results);
        """)

        try:
            items = json.loads(raw) if raw else []
        except Exception:
            items = []

        if not items:
            page_title = self.driver.title
            if "登录" in page_title or len(self.driver.page_source) < 10000:
                return {"code": 301, "msg": "Cookie expired — please get a fresh cookie."}
            return {"code": 0, "data": {"items": [], "has_more": False}}

        # Click each note card to capture: xsec_token, interact counts, publish date.
        from selenium.webdriver.common.by import By
        note_cards = self.driver.find_elements(By.CSS_SELECTOR, "section.note-item")
        detail_data = {}   # note_id → {xsec_token, liked, collected, comments, date, ip}
        for idx, card in enumerate(note_cards):
            note_id = items[idx]["note_id"] if idx < len(items) else ""
            if not note_id:
                continue
            try:
                card.click()
                self._short_wait()
                token = self._extract_xsec_token_from_url()
                # Read counts and publish date from the loaded panel
                panel_data = self.driver.execute_script(
                    """
                    var out = {liked:0, collected:0, comments:0, date:'', ip:''};
                    var counts = document.querySelectorAll('.engage-bar-style .count');
                    if (counts.length >= 1) out.liked     = counts[0].innerText.trim();
                    if (counts.length >= 2) out.collected = counts[1].innerText.trim();
                    if (counts.length >= 3) out.comments  = counts[2].innerText.trim();
                    var dateEl = document.querySelector('.bottom-container span.date, [class*="info"] .date');
                    out.date = dateEl ? dateEl.innerText.trim() : '';
                    var ipEl = document.querySelector('.bottom-container [class*="ip"], [class*="ip-location"]');
                    out.ip = ipEl ? ipEl.innerText.trim() : '';
                    return JSON.stringify(out);
                    """
                )
                try:
                    pd = json.loads(panel_data) if panel_data else {}
                except Exception:
                    pd = {}
                detail_data[note_id] = {**pd, "xsec_token": token}
                self.driver.back()
                time.sleep(2)
            except Exception:
                self.driver.get(search_url)
                time.sleep(3)

        def _parse_count(v):
            try:
                s = str(v).replace(",", "").strip()
                if not s or not any(c.isdigit() for c in s):
                    return 0
                if "万" in s:
                    return int(float(s.replace("万", "")) * 10000)
                return int("".join(c for c in s if c.isdigit()))
            except Exception:
                return 0

        # Wrap to snake_case shape expected by parse_note()
        wrapped = []
        for n in items:
            if not n.get("note_id"):
                continue
            dd = detail_data.get(n["note_id"], {})
            wrapped.append({
                "id":         n["note_id"],
                "xsec_token": dd.get("xsec_token", ""),
                "note_card": {
                    "title":    n.get("title", ""),
                    "desc":     "",
                    "type":     "normal",
                    "user": {
                        "user_id":  n.get("author_id", ""),
                        "nickname": n.get("author", ""),
                    },
                    "interact_info": {
                        "liked_count":     _parse_count(dd.get("liked", 0)),
                        "collected_count": _parse_count(dd.get("collected", 0)),
                        "comment_count":   _parse_count(dd.get("comments", 0)),
                        "share_count":     0,
                    },
                    "image_list":       [{"url": n["cover_url"]}] if n.get("cover_url") else [],
                    "tag_list":         [],
                    "time":             dd.get("date", ""),
                    "last_update_time": dd.get("date", ""),
                    "ip_location":      dd.get("ip", ""),
                },
            })

        return {"code": 0, "data": {"items": wrapped, "has_more": True}}

    def get_comments(self, note_id: str, cursor: str = "",
                     xsec_token: str = "") -> dict:
        """
        Navigate to the note page (requires a valid xsec_token) and extract
        comments from the rendered DOM.
        """
        self._wait()

        url = f"{self.BASE_URL}/explore/{note_id}"
        if xsec_token:
            url += f"?xsec_token={xsec_token}&xsec_source=pc_search"
        self.driver.get(url)
        time.sleep(5)

        # Confirm the note actually loaded (not redirected to /explore)
        if "/explore/" not in self.driver.current_url or self.driver.current_url.rstrip("/") == f"{self.BASE_URL}/explore":
            return {"code": 0, "data": {"comments": [], "has_more": False, "cursor": ""}}

        raw = self.driver.execute_script(
        """
        function extractComment(el, noteId) {
            var commentId = (el.id || '').replace('comment-', '');

            var nameEl    = el.querySelector('.name');
            var contentEl = el.querySelector('.note-text, .content');
            var dateEl    = el.querySelector('.date');
            var locEl     = el.querySelector('.location');
            var interEl   = el.querySelector('.interactions');

            var userA = el.querySelector('a[href*="/user/profile/"]');
            var userId = '';
            if (userA) {
                userId = (userA.getAttribute('href').split('/user/profile/')[1] || '').split('?')[0];
            }

            var likesText = '0';
            if (interEl) {
                var nums = interEl.innerText.match(/[0-9]+/g);
                if (nums) likesText = nums[0];
            }

            var dateText = dateEl ? dateEl.innerText.trim() : '';
            var locText  = locEl  ? locEl.innerText.trim()  : '';
            if (locText && dateText.endsWith(locText)) {
                dateText = dateText.slice(0, dateText.length - locText.length).trim();
            }

            return {
                comment_id: commentId,
                user:       nameEl ? nameEl.innerText.trim() : '',
                user_id:    userId,
                content:    contentEl ? contentEl.innerText.trim() : '',
                likes:      likesText,
                date:       dateText,
                location:   locText,
                is_sub:     false,
            };
        }

        // Each top-level comment is a .parent-comment block containing:
        //   .comment-item  (the main comment)
        //   .reply-container > .comment-item[]  (sub-comments/replies)
        var parentBlocks = document.querySelectorAll('.parent-comment');
        var results = [];
        for (var i = 0; i < parentBlocks.length; i++) {
            var block = parentBlocks[i];
            var topEl = block.querySelector('.comment-item');
            if (!topEl) continue;

            var top = extractComment(topEl, '');

            // Sub-comments live inside .reply-container sibling
            var replyContainer = block.querySelector('.reply-container');
            var subs = [];
            if (replyContainer) {
                var subEls = replyContainer.querySelectorAll('.comment-item');
                for (var j = 0; j < subEls.length; j++) {
                    var sub = extractComment(subEls[j], '');
                    sub.is_sub = true;
                    sub.parent_id = top.comment_id;
                    subs.push(sub);
                }
            }
            top.sub_comments = subs;
            results.push(top);
        }
        return JSON.stringify(results);
        """
        )

        try:
            dom_comments = json.loads(raw) if raw else []
        except Exception:
            dom_comments = []

        def _wrap_comment(c, parent_id=""):
            try:
                likes_int = int(str(c.get("likes", "0")).replace(",", ""))
            except Exception:
                likes_int = 0
            subs_wrapped = [_wrap_comment(s, c.get("comment_id", "")) for s in c.get("sub_comments", [])]
            return {
                "id":       c.get("comment_id", ""),
                "user_info": {
                    "user_id":  c.get("user_id", ""),
                    "nickname": c.get("user", ""),
                },
                "content":           c.get("content", ""),
                "like_count":        likes_int,
                "create_time":       c.get("date", ""),
                "ip_location":       c.get("location", ""),
                "sub_comment_count": len(subs_wrapped),
                "target_comment":    {"id": parent_id} if parent_id else {},
                "sub_comments":      subs_wrapped,
            }

        api_comments = [_wrap_comment(c) for c in dom_comments]
        return {"code": 0, "data": {"comments": api_comments, "has_more": False, "cursor": ""}}

    def get_user_info(self, user_id: str) -> dict:
        """
        Navigate to the user profile page and extract follower/following/likes
        from the data block, plus nickname and bio.
        """
        # Strip any query params accidentally included in user_id
        clean_id = user_id.split("?")[0]
        self._wait()

        self.driver.get(f"{self.BASE_URL}/user/profile/{clean_id}")
        time.sleep(4)

        raw = self.driver.execute_script(
        """
        var result = {};
        var nickEl = document.querySelector('[class*="nickname"]');
        result.nickname = nickEl ? nickEl.innerText.trim() : '';
        var descEl = document.querySelector('[class*="desc"]');
        result.desc = descEl ? descEl.innerText.trim() : '';
        var dataEl = document.querySelector('[class*="data"]');
        var counts = dataEl ? dataEl.querySelectorAll('[class*="count"]') : [];
        result.counts = [];
        for (var i = 0; i < counts.length; i++) {
            result.counts.push(counts[i].innerText.trim());
        }
        return JSON.stringify(result);
        """
        )

        try:
            dom = json.loads(raw) if raw else {}
        except Exception:
            dom = {}

        def _int(v):
            try:
                s = str(v).replace(",", "")
                if "万" in s:
                    return int(float(s.replace("万", "")) * 10000)
                return int(s)
            except Exception:
                return 0

        # counts[0]=following, counts[1]=fans/followers, counts[2]=liked+collected
        counts = dom.get("counts", [])
        following  = _int(counts[0]) if len(counts) > 0 else 0
        followers  = _int(counts[1]) if len(counts) > 1 else 0
        liked      = _int(counts[2]) if len(counts) > 2 else 0

        return {"code": 0, "data": {
            "basic_info": {
                "user_id":    clean_id,
                "nickname":   dom.get("nickname", ""),
                "gender":     "",
                "ip_location": "",
                "desc":        dom.get("desc", ""),
            },
            "interactions": [
                {"type": "fans",      "count": followers},
                {"type": "follows",   "count": following},
                {"type": "notes",     "count": 0},
                {"type": "liked",     "count": liked},
                {"type": "collected", "count": 0},
            ],
            "extra_info": {},
        }}

    def close(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass

    def __del__(self):
        self.close()
