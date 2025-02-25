import json


def test_urls():
    """Load URLs from a file."""
    with open("./flywheel/data/urls/data.json", "r", encoding="utf-8") as file:
        urls = json.load(file)

    result = []

    for url in urls:
        result.append({
            "url": url["url"],
            "title": url["title"],
            "snippet": url["snippet"]
        })

    with open("./flywheel/data/urls/data.json", "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)
