from flywheel import URLCollector
import json
from rich import print

def test_collector():
    queries = [f"test {i}" for i in range(11)]
    
    url_collector = URLCollector(url_file_path="./tests/url_scraper/test_url.json")
    
    with open("./tests/url_scraper/test_url.json", "r") as file:
        urls = json.load(file)
    
    search_results = urls[-100:]
    
    print("Search Results: ", search_results)
    
    filtered_results = url_collector.filter_urls(search_results)
    
    print("Results: ", filtered_results)
    