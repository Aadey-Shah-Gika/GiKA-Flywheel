import random
import time
import logging

from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config
from .load_balancer import ScrapperLoadBalancer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)


class BaseScraper(ScrapperLoadBalancer):
    """
    Base class for web scrapers that manages search queries and fetch limits.
    It inherits from ScrapperLoadBalancer and implements query execution with retry mechanisms.
    """

    def __init__(self, **kwargs):
        """
        Initializes the scraper with default or provided configuration values.
        """

        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)

        # configuration parameters
        config_keys = [
            "batch_size",
            "url_limit",
            "max_request_retries",
            "browser",
            "remaining_fetches_range",
            "wait_time_between_fetches_range",
            "wait_time_after_certain_fetches_range",
        ]

        # configure config for assigning class variables
        config = {}
        for key in config_keys:
            # if config key is not specified take the default [defined in constants.py]
            config[key] = kwargs.get(key, default_config[key])

        # List to keep track of unsuccessful queries
        self.unsuccessful_queries = []

        # Configure the scraper with the provided or default settings
        self.configure(**config)
        self.init_remaining_fetches()

        # Initialize the Load Balancer
        super().__init__(**kwargs)

    def configure(self, **kwargs):
        """
        Updates the scraper's configuration parameters.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_remaining_fetches(self):
        """
        Resets the remaining fetches counter to a random value within the configured range.
        Introduces a random delay after resetting.
        """
        self.logger.info("Resetting remaining fetches counter.")

        self.set_remaining_fetches(
            random.randint(
                self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1
            )
        )

        # Fluctuate the sleep timings after certain fetches to escape pattern tracking
        time.sleep(
            random.uniform(
                self.wait_time_after_certain_fetches_range[0],
                self.wait_time_after_certain_fetches_range[1],
            )
        )

    def set_remaining_fetches(self, remaining_fetches):
        """
        Sets the remaining fetches counter and resets if it falls below zero.
        """
        self.logger.info(f"Setting remaining fetches: {remaining_fetches}")

        self.configure(remaining_fetches=remaining_fetches)

        if self.remaining_fetches < 0:
            # Reset the remaining fetches counter and sleep for some time
            self.reset_remaining_fetches()

    def decrement_remaining_fetches(self):
        """
        Decrements the remaining fetches counter and applies a wait time between fetches.
        """
        self.logger.info("Decrementing remaining fetches.")

        self.set_remaining_fetches(self.remaining_fetches - 1)

        # Decrement the remaining fetches counter in the browser to manage IP rotation
        self.browser.decrease_remaining_fetches()

        # sleep after every fetch to avoid getting blocked by exceeding hit rate
        time.sleep(
            random.uniform(
                self.wait_time_between_fetches_range[0],
                self.wait_time_between_fetches_range[1],
            )
        )

    def init_remaining_fetches(self):
        """
        Initializes the remaining fetches counter to a random value within the configured range.
        """

        self.logger.info("Initializing remaining fetches.")

        self.set_remaining_fetches(
            random.randint(
                self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1
            )
        )

    def fetch_results(self, query, limit):
        """
        Abstract method to be implemented in child classes for fetching search results.
        """
        pass

    def execute_query(self, query, limit):
        """
        Executes a search query with retry logic in case of failures.
        """
        self.logger.info(f"Executing query: {query}")

        # Try fetching query results several times to overcome unexpected failures
        for attempt in range(self.max_request_retries):
            try:
                result = self.fetch_results(query, limit)
                # Decrement remaining fetches after each fetch
                self.decrement_remaining_fetches()
                return result
            except Exception as e:
                self.logger.warning(
                    f"Error executing query '{query}', Attempt {attempt + 1} of {self.max_request_retries}: {str(e)}"
                )
                continue

        self.logger.error(f"Exceeded maximum retry attempts for query: {query}")

        raise Exception("Exceeded maximum retry attempts for execute_query")

    def run_scraper(self, query, num_results_per_query=None):
        """
        Executes a scraper search for a given query and handles failures.
        """

        self.logger.info(f"Running scraper for query: {query}")

        num_results_per_query = num_results_per_query or self.url_limit
        try:
            result = self.execute_query(query, num_results_per_query)
            return result
        except Exception as e:
            self.logger.error(f"Query failed: {query}, Error: {str(e)}")
            result = {"error": str(e), "status": 400}
            self.unsuccessful_queries.append(query)
            return result
