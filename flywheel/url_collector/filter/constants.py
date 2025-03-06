DEFAULT_URL_FILTER_CONFIG = {
    "ann_store_urls": {
        "title": "http://127.0.0.1:5678/title",
        "snippet": "http://127.0.0.1:5678/snippet"  # replace with your ANN store URL.  # noqa: E501
    },
    "snippet_length_threshold": 40, # if snippet length is greater than this threshold, it will be included in the indexed data.
    "url_file_path": "./flywheel/data/urls/data.json"
}

TASK_STORAGE_DIR = "./flywheel/data/urls/scraped.json"