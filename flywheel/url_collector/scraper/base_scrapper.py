from .constants import DEFAULT_URL_SCRAPPER_CONFIG as default_config

class BaseScraper:
    def __init__(self, **kwargs):
        default_kwargs = {
            "batch_size": default_config["batch_size"],
            "url_limit": default_config["url_limit"],
            "max_request_retries": default_config["max_request_retries"],
        }
        
        # For tracking unsuccessful queries
        self.unsuccessful_queries = []

        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}

        self.configure(**config_kwargs)

    def configure(self, **kwargs):
        """Update the parameters of the BaseScraper."""
        for key, value in kwargs.items():
            setattr(self, key, value)

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

    def run_scraper(self, queries, num_results_per_query=None):
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
        return results
