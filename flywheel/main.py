from .constants import DEFAULT_FLYWHEEL_CONFIG as default_config

from .url_collector import URLCollector
from .query_generator import QueryGenerator
from .Crawler_py.packages.seleniumCrawler.crawler import Crawler
class Flywheel:
    
    def __init__(self, **kwargs):
        """Initialize Flywheel with default parameters."""
        defaults = {
            "number_of_threads": default_config["number_of_threads"],
            "crawled_urls_limit": default_config["crawled_urls_limit"],
            "total_urls_crawled": default_config["total_urls_crawled"],
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
        
        urls = []
        for _ in range(self.number_of_threads):
            urls.append(self.url_collector.collect_urls(queries))
            
        return urls
    
    def crawl_url(self, url):
        crawler = Crawler({
        url
        }, storage='/home/aadey/workspace/data_enrichment/GiKA-Flywheel/flywheel/Crawler_py/storage',tor_browser_path='/root/old_server/PrabhathE2E/crawler-py-copy/Crawler-py/tor_browser')
        crawler.start()
    
    def start_flywheel(self, context):
        queries = self.generate_queries(context)
        urls = self.collect_urls(queries)
        
        for url_set in urls:
            for url in url_set:
                new_contexts = self.crawl_url(url)
                self.increase_total_urls_crawled()
                if(self.total_urls_crawled >= self.crawled_urls_limit):
                    return
                for new_context in new_contexts:
                    self.start_flywheel(new_context)