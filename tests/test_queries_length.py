import json

# TODO: Improve code design for readability and maintainability

def load_json(filepath):
    """
    Loads and parses JSON data from a file.

    :param filepath: Path to the JSON file.
    :return: Parsed JSON data (dict or list).
    :raises: FileNotFoundError, json.JSONDecodeError
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from '{filepath}'.")
        
def test_queries_fetched():
    filepath = "./analysis/url_scraper/search_results.json"
    results = load_json(filepath)
    
    total_queries = sum(len(result["results"]) for result in results)
    
    total_urls = 0
    
    for result in results:
        for query in result["results"]:
            for urls in query:
                total_urls += len(query[urls])
        
    print(f"Total queries fetched: {total_queries}")
    
    print(f"Total URLs fetched: {total_urls}")