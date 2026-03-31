"""微博爬虫配置常量"""

# 桌面版搜索
SEARCH_BASE_URL = "https://s.weibo.com"
SEARCH_PATH = "/weibo"

# 用户资料页（桌面版）
PROFILE_BASE_URL = "https://weibo.com/ajax/profile/info"

# 请求控制
DEFAULT_DELAY_RANGE = (3, 7)
MAX_RETRIES = 3
RETRY_BACKOFF = 5
LONG_BLOCK_PAUSE = 60
REQUEST_TIMEOUT = 15

# 输出
DEFAULT_OUTPUT_DIR = "output"
INCREMENTAL_SAVE_INTERVAL = 10  # 每爬10页保存一次

# 请求头（桌面版）
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://s.weibo.com/",
}
