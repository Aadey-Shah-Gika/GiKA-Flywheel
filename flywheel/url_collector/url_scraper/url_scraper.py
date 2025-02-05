from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config

class URLScraper:
    def __init__(self,
        url=None,
        api_key=None,
        search_engine_id=None,
        batch_size=None,
        url_limit=None,
        browser=None
    ):
        self.config(self, url, api_key, search_engine_id, batch_size, url_limit, browser)
    def config(
        self,
        url, 
        api_key, 
        search_engine_id,
        batch_size,
        url_limit,
        browser
    ):
        """Configure search engine settings with provided values or defaults."""
        self.url = url or self.url or default_config["url"]
        self.api_key = api_key or self.api_key or default_config["api_key"]
        self.search_engine_id = search_engine_id or self.search_engine_id or default_config["search_engine_id"]
        self.batch_size = batch_size or self.batch_size or default_config["batch_size"]
        self.url_limit = url_limit or self.url_limit or default_config["url_limit"]
        self.browser = browser or self.browser or default_config["browser"]()
    
    def fetch_urls(self, query, limit):
        """Fetch search results for a query using the search engine API."""
        try:
            self.update_remaining_fetches()
            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.search_engine_id,
                "lr": "lang_en",
                "gl": "IN",
            }
            results = []
            for start in range(1, limit + 1, self.batch_size):
                params.update({"start": start, "num": min(
                    self.batch_size, limit - start + 1)})
                data = self.browser.request(url = self.url, params=params)
                results.extend(data.get("items", []))
            return results
        except Exception as e:
            raise Exception(f"Error in fetch_urls: {str(e)}")

    def search_query(self, query, limit):
        """Perform search for a single query with retries."""
        for _ in range(self.max_request_retries):
            try:
                return self.fetch_urls(query)
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