from flywheel import URLCollector

def test_collector():
    queries = [f"test {i}" for i in range(11)]
    
    url_collector = URLCollector()
    
    search_results = url_collector.scrape_urls(queries)
    
    print("Results: ", search_results)
    