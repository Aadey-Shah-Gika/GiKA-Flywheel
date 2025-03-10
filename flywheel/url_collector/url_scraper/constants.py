import os
from submodules.browser import Browser

DEFAULT_URL_SCRAPPER_CONFIG = {
    "url": os.environ.get("SEARCH_ENGINE_URL", ),
    "api_key": os.environ.get('GOOGLE_CLOUD_API_KEY', ""),
    "search_engine_id": os.environ.get('SEARCH_ENGINE_ID', ""),
    "batch_size": 10,
    "url_limit": 10,
    "max_request_retries": 5,
    "browser": Browser,
}