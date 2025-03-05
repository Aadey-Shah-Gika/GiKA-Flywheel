import os

# Get the absolute path of the current script's directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(CURRENT_DIR, "prompt.txt")

# Open the file with the absolute path
with open(FILE_PATH, "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTIONS = file.read()

DEFAULT_CRAWLER_WRAPPER_CONFIG = {
    "urls": {
        "crawl": "http://localhost:1234/crawl",
        "crawl_status": "http://127.0.0.1:1234/crawl_status",
    },
    "summarizing_instruction": SYSTEM_INSTRUCTIONS,
}

TASK_STORAGE_DIR = "./flywheel/data/urls/filtered_urls.json"

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
