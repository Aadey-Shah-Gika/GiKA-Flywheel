import json

def test_urls():
    """Load URLs from a file."""
    with open("./analysis/url_scraper/search_results.json", "r", encoding="utf-8") as file:
        json_file = json.load(file)

    urls = []

    for thread in json_file:
        for result in thread["results"]:
            for query in result:
                for url in result[query]:
                    formatted_url = {
                        "url": url["url"].strip(),
                        "title": url["title"].strip(),
                        "snippet": url["description"].strip(),
                    }
                    urls.append(formatted_url)

    with open("./analysis/url_scraper/urls/formatted_urls.json", "w", encoding="utf-8") as file:
        json.dump(urls, file, indent=4)