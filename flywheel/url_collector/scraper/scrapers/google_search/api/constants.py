import os
from submodules.browser import Browser

DEFAULT_URL_SCRAPPER_CONFIG = {
    "url": os.environ.get("SEARCH_ENGINE_URL", ),
    "api_key": os.environ.get('GOOGLE_CLOUD_API_KEY', ""),
    "search_engine_id": os.environ.get('SEARCH_ENGINE_ID', ""),
    "browser": Browser,
}