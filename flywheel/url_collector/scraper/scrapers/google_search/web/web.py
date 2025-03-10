import logging
from googlesearch import search

from ....base_scrapper import BaseScraper
from .constants import DEFAULT_CONFIG as default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)


class GoogleSearchWebScraper(BaseScraper):
    """
    A web scraper that fetches search results from Google's search engine API.
    It supports proxy configuration and result parsing.
    """

    def __init__(self, **kwargs):
        """
        Initializes the scraper with optional proxy settings.

        :param kwargs: Additional configuration parameters.
        """
        
        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)
        
        config_keys = ["proxy"]
        config = {}
        
        # configure config for assigning class variables
        for key in config_keys:
            # if config key is not specified take the default [defined in constants.py]
            config[key] = kwargs.get(key, default_config.get(key))

        # Configure the scraper with the provided or default settings
        self.configure(**config)
        
        # Initialize the parent class
        super().__init__(**kwargs)

    def configure(self, **kwargs):
        """
        Configure proxy settings with provided values or defaults.

        :param kwargs: Configuration parameters like proxy settings.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Configure BaseScraper
        super().configure(**kwargs)
        self.logger.info("Scraper configured with: %s", kwargs)

    def parse_search_results(self, search_results):
        """
        Parse search results from Google's search engine.

        :param search_results: Raw search results.
        :return: A list of parsed search results.
        """
        try:
            parsed_results = [vars(result) for result in search_results]
            
            self.logger.info("Parsed %d search results.", len(parsed_results))
            
            return parsed_results
        except Exception as e:
            self.logger.error("Error parsing search results: %s", str(e))
            return []

    def fetch_results(self, query, limit):
        """
        Fetch search results for a given query using Google's search engine API.

        :param query: The search query string.
        :param limit: The number of search results to fetch.
        :return: Parsed search results.
        """
        try:
            self.logger.info("Fetching results for query: '%s' with limit: %d", query, limit)
            
            search_results = list(
                search(
                    query,
                    num_results=limit,
                    unique=True,
                    proxy=self.proxy,
                    advanced=True,
                )
            )

            # Parse the search results [SearchResults -> list]
            parsed_results = self.parse_search_results(search_results)
            
            self.logger.info(
                "Successfully fetched and parsed %d results.", len(parsed_results)
            )
            
            return parsed_results
        except Exception as e:
            self.logger.error("Error fetching search results: %s", str(e))
            return []
