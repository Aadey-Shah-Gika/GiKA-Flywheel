import json
import threading
import time
import queue
from flywheel import GoogleSearchWebScraper
from submodules.browser import Browser
import random
import requests

# TODO: Improve code design for readability and maintainability

def parse_queries_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    return [item["Title"] for item in data if "Title" in item]


def check_my_ip(proxies):
    test_url = "https://check.torproject.org/api/ip"
    response = requests.get(test_url, proxies=proxies, timeout=10)
    print("IMPORTANT DEBUG -", response.json())
    return response.json()["IP"]


def check_ip_rotation(proxies, browser):
    start_time = time.time()
    old_ip = check_my_ip(proxies)
    browser.renew_tor_identity()
    new_ip = check_my_ip(proxies)
    elapsed_time = time.time() - start_time
    print(f"IP CHECK - took: {elapsed_time:.2f} seconds")
    assert old_ip != new_ip, f"IP rotation failed for PROXIES -\n{proxies}"


def thread_function(thread_id, queries, result_queue):
    proxy_port = 9050 + thread_id
    control_port = 9150 + thread_id

    proxies = {
        "http": f"socks5h://127.0.0.1:{proxy_port}",
        "https": f"socks5h://127.0.0.1:{proxy_port}",
    }

    browser = Browser(port=control_port, proxies=proxies)
    url_scraper = GoogleSearchWebScraper(
        proxy=browser.getProxy("http"), max_request_retries=1, browser=browser,
    )

    # check_ip_rotation(proxies, browser)

    print("Proxy Port:", proxy_port)
    print("Control Port:", proxy_port)
    print("Thread ID:", thread_id)
    print("Number of Queries:", len(queries))
    print("Proxies:", proxies)

    results = []
    
    remaining_fetches = random.randint(10, 20)  # Random number of fetches per query
    
    for query in queries:
        found = False
        for _ in range(2):  # Retry 3 times
            if remaining_fetches <= 0:
                time.sleep(random.uniform(20, 100))
                remaining_fetches = random.randint(10, 20)  # Reset remaining fetches after a failure
            time.sleep(random.uniform(5, 20))  # Wait for a random amount of time before retrying
            try:
                results.append(url_scraper.run_scraper([query]))
                browser.decrease_remaining_fetches()
                remaining_fetches -= 1
                found = True
                break
            except Exception as e:
                browser.renew_tor_identity()
        if not found:
            break

    result_queue.put(
        {
            "thread_id": thread_id,
            "results": results,
            "unsuccessful_queries": url_scraper.unsuccessful_queries,
        }
    )

    print(
        f"Thread {thread_id} | Failed: {len(url_scraper.unsuccessful_queries)} | Success: {len(queries) - len(url_scraper.unsuccessful_queries)}"
    )


def test_search_engine():
    start_time = time.time()

    queries = parse_queries_from_file("./tests/queries.json")

    total_queries = len(queries)
    
    num_threads = 9

    print("Total Queries:", total_queries)
    print("Number of Threads:", num_threads)

    chunk_size = total_queries // num_threads

    threads = []
    result_queue = queue.Queue()

    for i in range(1, num_threads + 1):
        start_index = (i - 1) * chunk_size
        end_index = min(start_index + chunk_size, total_queries)
        thread_queries = queries[start_index:end_index]

        thread = threading.Thread(
            target=thread_function, args=(i, thread_queries, result_queue)
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    all_results = []
    while not result_queue.empty():
        result = result_queue.get()
        all_results.append(result)

    elapsed_time = time.time() - start_time
    print(f"Total time: {elapsed_time:.2f} seconds")

    file_path = "./analysis/url_scraper/search_results.json"
    with open(file_path, "w") as file:
        json.dump(all_results, file, indent=4)
    print(f"Results saved to {file_path}")
