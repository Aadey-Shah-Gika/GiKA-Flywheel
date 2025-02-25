from stem import Signal
from stem.control import Controller
from googlesearch import search

from ....base_scrapper import BaseScraper
from .constants import DEFAULT_CONFIG as default_config

class GoogleSearchWebScraper(BaseScraper):
    def __init__(self, **kwargs):
        default_kwargs = {
            "proxy": default_config["proxy"],
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        
        self.configure(**config_kwargs)
        super().__init__(**config_kwargs)
    
    def configure(self, **kwargs):
        """Configure proxy settings with provided values or defaults."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        super().configure(**kwargs)
        
    def parse_search_results(self, search_results):
        """Parse search results from Google's search engine API."""
        # TODO: Add error handling mechanism here
        return [vars(result) for result in search_results]

    def fetch_results(self, query, limit):
        """Fetch search results for a query using Google's search engine API."""
        search_results = list(search(query, num_results=limit, unique=True, proxy=self.proxy, advanced=True))
        parsed_results = self.parse_search_results(search_results)
        
        # TODO: Add logging mechanism here
        # TODO: Add exception handling mechanism here
        return parsed_results
