DEFAULT_CRAWLER_WRAPPER_CONFIG = {
    "urls": {
        "crawl": "http://localhost:1234/crawl",
        "crawl_status": "http://127.0.0.1:1234/crawl_status",
    },
    "task_storage_file": "./flywheel/data/urls/filtered_urls.json"
}

BLOCKED_DOMAINS = [
    "facebook",
    "twitter",
    "google",
    "youtube",
    "linkedin",
    "instagram",
    "justdial",
    "TikTok",
    "Telegram",
    "reddit",
    "x.com",
    "threads.com",
    "pinterest",
]
