import threading

from .constants import DEFAULT_FLYWHEEL_CONFIG as default_config

from .url_collector import URLCollector
from .query_generator import QueryGenerator
class Flywheel:
    
    def __init__(self, **kwargs):
        """Initialize Flywheel with default parameters."""
        defaults = {
            "number_of_threads": default_config["number_of_threads"],
            "crawled_urls_limit": default_config["crawled_urls_limit"],
            "total_urls_crawled": default_config["total_urls_crawled"],
            "urls": set() # TESTING PURPOSE
        }
        
        config_kwargs = {**defaults, **kwargs}
        
        self.configure(**config_kwargs)
        self.init_query_generator()
        self.init_url_collector()
        
    def configure(self, **kwargs):
        """Update the parameters of Flywheel."""
        for key, value in kwargs.items():
            setattr(self, key, value)
            
    def init_query_generator(self):
        """Initialize the QueryGenerator with the provided context."""
        self.configure(query_generator = QueryGenerator())
    
    def init_url_collector(self):
        """Initialize the URLCollector with the provided thread id."""
        self.configure(url_collector = URLCollector(url_file_path="./analysis/url_scraper/search_results.json"))
    
    def increase_total_urls_crawled(self):
        self.configure(total_urls_crawled = self.total_urls_crawled + 1)
        return self
        
    def generate_queries(self, context):
        return self.query_generator.generate_queries(context)
    
    
    def collect_urls(self, queries):
        """Collect URLs from the provided queries using the configured number of threads."""
        for url in self.url_collector.collect_urls(queries):
            yield url  # Yield each URL as soon as it is collected
    
    def isExistingURL(self, url):
        """Check if the provided URL is already existing in the list of URLs."""
        return url in self.urls
    
    def crawl_url(self, url):
        crawler = Crawler({
        url
        }, storage='/home/aadey/workspace/data_enrichment/GiKA-Flywheel/flywheel/Crawler_py/storage',tor_browser_path='/root/old_server/PrabhathE2E/crawler-py-copy/Crawler-py/tor_browser')
        crawler.start()
        return crawler.results
    
    def run_crawler(self, url):
        """Run a crawler in a new thread for the given URL and process new contexts."""
        if self.total_urls_crawled >= self.crawled_urls_limit:
            return

        self.increase_total_urls_crawled()

        def crawl_worker():
            new_contexts = self.crawl_url(url)  # Get new contexts
            if new_contexts:
                for context in new_contexts:
                    self.start_flywheel(context)  # Start a new Flywheel for each context

        # Start a new thread for crawling the URL
        crawler_thread = threading.Thread(target=crawl_worker)
        crawler_thread.start()
    
    def start_flywheel(self, context):
        """Start a new Flywheel instance in a separate thread."""
        def flywheel_worker():
            queries = self.generate_queries(context)
            for url in self.collect_urls(queries):
                if not self.isExistingURL(url):
                    self.urls.add(url)
                    self.run_crawler(url)

        # Start a new thread for the Flywheel process
        flywheel_thread = threading.Thread(target=flywheel_worker)
        flywheel_thread.start()
