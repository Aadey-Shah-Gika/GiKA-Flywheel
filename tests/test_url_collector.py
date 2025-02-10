import json
from flywheel.url_collector.url_scraper import URLScraper
from submodules.browser import Browser
import threading
import time
import queue

def parse_queries_from_file(file_path):
    with open(file_path, 'r') as file:
        # Read lines from the file, strip newlines, and create a list
        words = [line.strip() for line in file.readlines()]
    return words


def thread_function(thread_id, queries, result_queue):
    proxies = {
        'http': f'socks5h://127.0.0.1:{9050 + thread_id}',
        'https': f'socks5h://127.0.0.1:{9050 + thread_id}',
    }
    browser = Browser(port=(9060 + thread_id), proxies=proxies)
    url_scraper = URLScraper(browser=browser)
    results = url_scraper.scrape(queries)
    result_queue.put((thread_id, results, url_scraper.unsuccessful_queries))  # Put results in the queue
    print(f"ID: {thread_id} | Failed: {url_scraper.unsuccessful_queries} | Length: {len(results)}")


def test_search_engine():
    start_time = time.time()
    queries = parse_queries_from_file("./tests/queries.txt")
    total_queries = len(queries)
    print(f"Total queries: {total_queries}")

    threads = []
    result_queue = queue.Queue()  # Initialize a queue for results

    # Start 10 threads
    for i in range(1, 11):
        thread = threading.Thread(target=thread_function, args=(i, queries[((i - 1) * 1):(i * 1)], result_queue))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Collect all results from the queue
    all_results = []
    while not result_queue.empty():
        thread_id, results, unsuccessful_queries = result_queue.get()
        all_results.append({
            'thread_id': thread_id,
            'results': results,
            'unsuccessful_queries': unsuccessful_queries
        })

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Total time: {elapsed_time} seconds")

    # You can now work with `all_results`, which contains results from all threads
    print("All results:", all_results)
    
    # file_path = "./analysis/url_scraper/search_results.json"
    # with open(file_path, "w") as file:
    #     json.dump(results, file, indent=4)