from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config
from ....base_scrapper import BaseScraper

class GoogleSearchApiScraper(BaseScraper):
    def __init__(self, **kwargs):
        default_kwargs = {
            "url": default_config["url"],
            "api_key": default_config["api_key"],
            "search_engine_id": default_config["search_engine_id"],
            "browser": default_config["browser"](),
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        
        self.configure(**config_kwargs)
        super().__init__(**config_kwargs)

    def configure(self, **kwargs):
        """Configure search engine settings with provided values or defaults."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        super().configure(**kwargs)

    def fetch_results(self, query, limit):
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
                    "num": min(self.batch_size, limit - start + 1),
                }
                data = self.browser.request(url=self.url, params=params)
                results.extend(data.get("items", []))
            return results
        except Exception as e:
            raise Exception(f"Error in fetch_results: {str(e)}")
