import json
import threading
import time
import queue
from flywheel import GoogleSearchWebScraper
from submodules.browser import Browser
import random


# Read queries from a file and return them as a list
def parse_queries_from_file(file_path):
    with open(file_path, "r") as file:
        return [line.strip() for line in file.readlines()]


# Function for each thread to scrape queries using a unique Tor instance
def thread_function(thread_id, queries, result_queue):
    if not queries:  # Skip threads with no assigned queries
        return

    proxy_port = 9050 + thread_id  # Assign a unique SOCKS proxy port
    control_port = 9150 + thread_id  # Assign a unique ControlPort

    proxies = {
        "http": f"socks5h://127.0.0.1:{proxy_port}",
        "https": f"socks5h://127.0.0.1:{proxy_port}",
    }

    browser = Browser(port=control_port, proxies=proxies)
    url_scraper = GoogleSearchWebScraper(proxy=browser.getProxy("http"))

    for query in queries:
        time.sleep(random.uniform(0, 1))  # Add random delay to avoid throttling
        browser.renew_tor_identity()  # Increase remaining fetches for the current thread to avoid getting blocked by Google
        results = url_scraper.run_scraper(query)
        time.sleep(5)

    time.sleep(5)

    result_queue.put(
        {
            "thread_id": thread_id,
            "results": results,
            "unsuccessful_queries": url_scraper.unsuccessful_queries,
        }
    )

    print(
        f"Thread {thread_id} | Failed: {len(url_scraper.unsuccessful_queries)} | Success: {len(results)}"
    )


# Main function to distribute queries and run scraping
def test_search_engine():
    start_time = time.time()

    queries = parse_queries_from_file("./tests/queries.txt")
    total_queries = len(queries)

    print(f"Total queries: {total_queries}")

    num_threads = 10
    chunk_size = (total_queries // num_threads) + (
        total_queries % num_threads > 0
    )  # Evenly distribute queries

    threads = []
    result_queue = queue.Queue()

    # Start threads with evenly split queries
    for i in range(1, num_threads + 1):
        start_index = (i - 1) * chunk_size
        end_index = min(start_index + chunk_size, total_queries)
        thread_queries = queries[start_index:end_index]

        thread = threading.Thread(
            target=thread_function, args=(i, thread_queries, result_queue)
        )
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Collect results
    all_results = []
    while not result_queue.empty():
        all_results.append(result_queue.get())

    elapsed_time = time.time() - start_time
    print(f"Total time: {elapsed_time:.2f} seconds")

    # Save results to a JSON file
    file_path = "./analysis/url_scraper/search_results.json"
    with open(file_path, "w") as file:
        json.dump(all_results, file, indent=4)

    print(f"Results saved to {file_path}")
