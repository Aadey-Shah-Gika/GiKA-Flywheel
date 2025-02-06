from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config

class URLScraper:
    def __init__(self,
        url=default_config["url"],
        api_key=default_config["api_key"],
        search_engine_id=default_config["search_engine_id"],
        batch_size=default_config["batch_size"],
        url_limit=default_config["url_limit"],
        browser=default_config["browser"](),
        max_request_retries=default_config["max_request_retries"],
    ):
        self.config(url, api_key, search_engine_id, batch_size, url_limit, browser, max_request_retries)
    def config(
        self,
        url, 
        api_key, 
        search_engine_id,
        batch_size,
        url_limit,
        browser,
        max_request_retries
    ):
        """Configure search engine settings with provided values or defaults."""
        self.url = url or self.url
        self.api_key = api_key or self.api_key
        self.search_engine_id = search_engine_id or self.search_engine_id
        self.batch_size = batch_size or self.batch_size
        self.url_limit = url_limit or self.url_limit
        self.browser = browser or self.browser
        self.max_request_retries = max_request_retries or self.max_request_retries
    
    def fetch_urls(self, query, limit):
        """Fetch search results for a query using the search engine API."""
        try:
            results = []
            for start in range(1, limit + 1, self.batch_size):
                params = {
                    "q": query,
                    "key": self.api_key,
                    "cx": self.search_engine_id,
                    "lr": "lang_en",
                    "gl": "IN",
                    "start": start,
                    "num": min(self.batch_size, limit - start + 1)
                }
                data = self.browser.request(url = self.url, params=params)
                results.extend(data.get("items", []))
            return results
        except Exception as e:
            raise Exception(f"Error in fetch_urls: {str(e)}")

    def search_query(self, query, limit):
        """Perform search for a single query with retries."""
        for _ in range(self.max_request_retries):
            try:
                return self.fetch_urls(query, limit)
            except Exception:
                continue
        raise Exception("Exceeded maximum retry attempts for search_query")

    def scrape(self, queries):
        """Perform searches for a list of queries and return results."""
        results = {}
        for query in queries:
            try:
                results[query] = self.search_query(query, self.url_limit)
            except Exception as e:
                results[query] = {"error": str(e)}
        return results