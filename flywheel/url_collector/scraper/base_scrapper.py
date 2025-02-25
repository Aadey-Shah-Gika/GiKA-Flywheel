import random
import time

from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config

class BaseScraper:
    def __init__(self, **kwargs):
        default_kwargs = {
            "batch_size": default_config["batch_size"],
            "url_limit": default_config["url_limit"],
            "max_request_retries": default_config["max_request_retries"],
            "browser": default_config["browser"],
            "remaining_fetches_range": default_config["remaining_fetches_range"], # Waiting for some time after $remaining_fetches number of fetches
            "wait_time_between_fetches": default_config["wait_time_between_fetches"], # Waiting for some time after each fetch
            "wait_time_after_certain_fetches_range": default_config["wait_time_after_certain_fetches_range"], # Waiting for some time after a certain number of fetches
        }
        
        # For tracking unsuccessful queries
        self.unsuccessful_queries = []

        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}

        self.configure(**config_kwargs)
        self.init_remaining_fetches()

    def configure(self, **kwargs):
        """Update the parameters of the BaseScraper."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def reset_remaining_fetches(self):
        """Reset remaining_fetches counter."""
        self.set_remaining_fetches(random.randint(self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1))
        time.sleep(random.uniform(self.wait_time_after_certain_fetches_range[0], self.wait_time_after_certain_fetches_range[1]))

    def set_remaining_fetches(self, remaining_fetches):
        """Set remaining_fetches counter."""
        self.configure(remaining_fetches=remaining_fetches)
        if self.remaining_fetches < 0:
            self.reset_remaining_fetches()

    def decrement_remaining_fetches(self):
        """Decrement remaining_fetches counter."""
        self.set_remaining_fetches(self.remaining_fetches - 1)
        self.browser.decrease_remaining_fetches()
        time.sleep(random.uniform(self.wait_time_between_fetches[0], self.wait_time_between_fetches[1]))

    def init_remaining_fetches(self):
        """Initialize the remaining_fetches counter."""
        self.set_remaining_fetches(random.randint(self.remaining_fetches_range[0], self.remaining_fetches_range[1] + 1))

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

    def run_scraper(self, queries, num_results_per_query):
        """Perform searches for a list of queries and return results."""
        
        # default to url_limit if not provided
        num_results_per_query = num_results_per_query or self.url_limit
        
        results = {}
        
        for query in queries:
            try:
                results[query] = self.execute_query(query, num_results_per_query)
            except Exception as e:
                results[query] = {"error": str(e)}
                self.unsuccessful_queries.append(query)
                
                # TODO: Add logging mechanism here
                print(f"Error in {query}: {str(e)}")
                
                #TODO: Add Exception raising mechanism here
                raise Exception("Error in run_scraper")
            
            # decrement remaining_fetches after each fetch
            self.decrement_remaining_fetches()
        return results
