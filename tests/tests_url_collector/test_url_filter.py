import os
import json
import time
from rich import print

from flywheel import URLFilter
from flywheel.utils.ann_store import ANNStore


default_url_path = "./analysis/url_scraper/search_results.json"


def delete_files_in_directory(directory_path):
    try:
        files = os.listdir(directory_path)
        for file in files:
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        print("All files deleted successfully.")
    except OSError:
        print("Error occurred while deleting files.")


def get_urls(file_path=default_url_path):
    """Load URLs from a file."""
    with open(file_path, "r", encoding="utf-8") as file:
        json_file = json.load(file)

    urls = []

    cnt = 1

    for thread in json_file:
        for result in thread["results"]:
            for query in result:
                for url in result[query]:
                    formatted_url = {
                        "title": url["title"].strip(),
                        "snippet": url["description"].strip(),
                    }
                    urls.append(formatted_url)

    return urls


def test_url_filter():
    """Test URLFilter class."""

    # delete_files_in_directory("./flywheel/data/defaults/ann_store")

    start_time = time.time()

    urls = get_urls()

    # test_url_set = urls[:10]
    test_url_set = urls

    print("\n")
    print("Total urls:", len(urls))
    print("Test urls:", len(test_url_set))

    filter_obj = URLFilter()
    # filter_obj.add_urls(test_url_set)
    
    print("DEBUG -- Urls Added(title):", filter_obj.ann_store["title"].index.ntotal)
    print("DEBUG -- Urls Added(snippet):", filter_obj.ann_store["snippet"].index.ntotal)

    query_urls = [
        {
            "search": "Mercedes-Benz G-Class",
            "title": "Mercedes-Benz G-Class Price - Images, Colours & Reviews",
            "snippet": "Mercedes-Benz G-Class Price. Mercedes-Benz G-Class price for the base model starts at Rs. 2.55 Crore and the top model price goes upto Rs. 4.00 Crore (Avg. ex- ...",
        },
        {
            "search": "lakme lipstick shades",
            "title": "Buy Lakmé Lipstick Online At Best Price In India - LakméIndia",
            "snippet": "While those with neutral undertones have access to a wide spectrum of colours starting from pink, mauve to wine shades. You can buy online lipstick ...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Winter Fun Recipes",
            "snippet": "Warm up your winter with our Snow Day recipe assortment! Create lasting memories with the kids by preparing these fun, kid-tested...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Healthy and Delicious Winter Snacks for Kids",
            "snippet": "Warm up your winter with our Snow Day recipe assortment! Create lasting memories with the kids by preparing these fun, kid-tested...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Healthy and Delicious Winter Snacks for Kids",
            "snippet": " From creative apple slices to savory idlis and warming poha, there are numerous ways to make winter snacking enjoyable and beneficial.",
        }
    ]
    
    for query_url in query_urls:

        similar_urls_titles = filter_obj.find_similar_urls(query_url, "title")
        similar_urls_snippets = filter_obj.find_similar_urls(query_url, "snippet")

        current_time = time.time()

        results_titles = [
            {"distance": url_info["distance"], "url_info": urls[url_info["id"]]}
            for url_info in similar_urls_titles
        ]

        results_snippets = [
            {"distance": url_info["distance"], "url_info": urls[url_info["id"]]}
            for url_info in similar_urls_snippets if url_info["id"] >= 0
        ]

        results = {
            "query": query_url,
            "title_results": results_titles,
            "snippet_results": results_snippets,
        }

        print("Results:", results)

    print("Time taken:", current_time - start_time, "seconds")