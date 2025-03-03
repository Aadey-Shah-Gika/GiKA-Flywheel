from submodules.browser import Browser

DEFAULT_URL_SCRAPPER_CONFIG = {
    "batch_size": 10,
    "url_limit": 10,
    "max_request_retries": 2,
    "browser": Browser(),
    "remaining_fetches_range": [10, 20],
    "wait_time_between_fetches_range": [15, 20],
    "wait_time_after_certain_fetches_range": [40, 100],
}
