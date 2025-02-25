import json
import os

from .constants import DEFAULT_URL_COLLECTOR_CONFIG as default_config
from submodules.browser import Browser
from .scraper import GoogleSearchWebScraper
from .filter import URLFilter

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
        """Load URLs from file, creating an empty file if not found."""
        if not os.path.exists(self.url_file_path):
            # Create an empty JSON file
            with open(self.url_file_path, "w") as file:
                json.dump([], file)  # Store an empty list in the file
            print(f"DEBUG -- [URLCollector.load_urls()] -- File created: {self.url_file_path}")

        try:
            with open(self.url_file_path, "r") as file:
                urls = json.load(file)
            self.configure(urls=urls)
        except json.JSONDecodeError:
            # Handle case where file exists but is corrupted
            self.configure(urls=[])
            print(f"WARNING -- [URLCollector.load_urls()] -- Corrupt JSON. Resetting file: {self.url_file_path}")
            with open(self.url_file_path, "w") as file:
                json.dump([], file)  # Reset file with an empty list

    def init_filter(self):
        """Initialize the URLFilter with the scraper."""
        url_filter = URLFilter()
        self.configure(url_filter=url_filter)
        return self
    
    def extract_urls(self, search_results):
        """Add the URLs extracted from the search results to the list."""
        extracted_urls = []
        for query in search_results.keys():
            for url in search_results[query]:
                extracted_urls.append({
                    "url": url["url"],
                    "title": url["title"],
                    "snippet": url["description"],
                    "isIndexed": False
                })
        return extracted_urls
    
    def scrape_urls(self, queries):
        print("DEBUG -- Entered URLCollector.scrape_urls()")
        search_results = self.url_scraper.run_scraper(queries)
        extracted_urls = self.extract_urls(search_results)
        print("DEBUG -- [URLCollector.scrape_urls()] -- Extracted URLs: ", extracted_urls)
        
        self.urls.extend(extracted_urls)
        
        with open(self.url_file_path, "w") as file:
            json.dump(self.urls, file, indent=4)
        print("DEBUG -- Exiting URLCollector.scrape_urls()")
        return search_results
    
    def filter_urls(self, search_results):
        print("DEBUG -- Entered URLCollector.filter_urls()")
        filtered_results = self.url_filter.filter_urls(search_results)
        print("DEBUG -- Exiting URLCollector.filter_urls()")
        return filtered_results
    
    def get_urls_by_ids(self, ids):
        """Return the URLs by their IDs."""
        urls = [self.urls[id] for id in ids if id > 0 and id < len(self.urls)]
        return urls
    
    def collect_urls(self, queries):
        """Implement this method to collect URLs from a source."""
        for search_result in self.scrape_urls(queries).values():
            yield from self.filter_urls([search_result])
        filtered_urls = self.url_filter.filter_urls(search_results)
        return filtered_urls