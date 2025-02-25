import json

from .constants import DEFAULT_URL_COLLECTOR_CONFIG as default_config
from submodules.browser import Browser
from flywheel import GoogleSearchWebScraper, URLFilter

class URLCollector:
    def __init__(self, **kwargs):
        """Initialize the URLCollector with default parameters."""
        defaults = {
            "url_file_path": default_config["url_file_path"],
            "thread_id": default_config["thread_id"],
        }
        
        config_kwargs = {**defaults, **kwargs}
        
        self.configure(**config_kwargs)
        self.init_browser()
        self.init_scraper()
        self.load_urls()
        self.init_filter()
    
    def configure(self, **kwargs):
        """Update the parameters of the URLCollector."""
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def init_browser(self):
        """Initialize the Browser with the provided proxy settings."""
        thread_id = self.thread_id
        
        proxy_port = 9050 + thread_id
        control_port = 9150 + thread_id

        proxies = {
            "http": f"socks5h://127.0.0.1:{proxy_port}",
            "https": f"socks5h://127.0.0.1:{proxy_port}",
        }
        
        self.configure(browser = Browser(port=control_port, proxies=proxies))
        return self

    def init_scraper(self):
        """Initialize the GoogleSearchWebScraper with the browser."""
        url_scraper = GoogleSearchWebScraper(proxy=self.browser.getProxy("http"), max_request_retries=2, browser=self.browser)
        self.configure(url_scraper=url_scraper)
        return self
    
    def load_urls(self):
        with open(self.url_file_path, "r") as file:
            urls = json.load(file)
        self.configure(urls=urls)

    def init_filter(self):
        """Initialize the URLFilter with the scraper."""
        url_filter = URLFilter()
        url_filter.add_urls(self.urls)
        self.configure(url_filter=url_filter)
        return self
    
    def scrape_urls(self, queries):
        search_results = self.url_scraper.run_scraper(queries)
        return search_results
    
    def collect_urls(self, queries):
        """Implement this method to collect URLs from a source."""
        search_results = self.url_scraper.run_scraper(queries)
        filtered_results = self.url_filter.filter_urls(search_results)
        return filtered_results