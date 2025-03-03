import random
import time

from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config
from .scrape_load_balancer import ScrapperLoadBalancer

class BaseScraper(ScrapperLoadBalancer):
    def __init__(self, **kwargs):
        
        config_keys = [
            "batch_size",
            "url_limit",
            "max_request_retries",
            "browser",
            "remaining_fetches_range",
            "wait_time_between_fetches_range",
            "wait_time_after_certain_fetches_range",
        ]
        
        config = {}
        for key in config_keys:
            config[key] = kwargs.get(key, default_config[key])

        # For tracking unsuccessful queries
        self.unsuccessful_queries = []

        self.configure(**config)
        self.init_remaining_fetches()

        super().__init__(**kwargs)

    def configure(self, **kwargs):
        """Update the parameters of the BaseScraper."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_remaining_fetches(self):
        """Reset remaining_fetches counter."""
        self.set_remaining_fetches(
            random.randint(
                self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1
            )
        )
        time.sleep(
            random.uniform(
                self.wait_time_after_certain_fetches_range[0],
                self.wait_time_after_certain_fetches_range[1],
            )
        )

    def set_remaining_fetches(self, remaining_fetches):
        """Set remaining_fetches counter."""
        self.configure(remaining_fetches=remaining_fetches)
        if self.remaining_fetches < 0:
            self.reset_remaining_fetches()

    def decrement_remaining_fetches(self):
        """Decrement remaining_fetches counter."""
        self.set_remaining_fetches(self.remaining_fetches - 1)
        self.browser.decrease_remaining_fetches()
        time.sleep(
            random.uniform(
                self.wait_time_between_fetches_range[0],
                self.wait_time_between_fetches_range[1],
            )
        )

    def init_remaining_fetches(self):
        """Initialize the remaining_fetches counter."""
        self.set_remaining_fetches(
            random.randint(
                self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1
            )
        )

    def fetch_results(self, query, limit):
        """Implement this method in child classes to fetch search results."""
        pass

    def execute_query(self, query, limit):
        """Perform search for a single query with retries."""
        for _ in range(self.max_request_retries):
            try:
                return self.fetch_results(query, limit)
            except Exception as e:
                # TODO: Add logging mechanism here
                print(f"Error in query: '{query}'")
                print(f"\nError: {str(e)}\n\n")
                print(f"Attempt Number: {_ + 1} / {self.max_request_retries}")
                continue
        raise Exception("Exceeded maximum retry attempts for execute_query")

    def run_scraper(self, query, num_results_per_query=None):
        """Perform searches for a list of queries and return results."""

        # default to url_limit if not provided
        num_results_per_query = num_results_per_query or self.url_limit
        result = None
        try:
            result = self.execute_query(query, num_results_per_query)
        except Exception as e:
            result = {"error": str(e), "status": 400}
            self.unsuccessful_queries.append(query)
            return result

        # decrement remaining_fetches after each fetch
        self.decrement_remaining_fetches()
        return result
