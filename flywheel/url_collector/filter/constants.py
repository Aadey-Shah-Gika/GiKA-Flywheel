from flywheel.utils.ann_store import ANNStore

DEFAULT_URL_FILTER_CONFIG = {
    "ann_store": {
            "title": ANNStore(index_file_path="./flywheel/data/defaults/ann_store/title_index_file.bin"),
            "snippet": ANNStore(index_file_path="./flywheel/data/defaults/ann_store/snippet_index_file.bin"),
        },
    "urls": [],  # List of URLs to filter and encode. Set in load_urls() method.  # noqa: E501
    "snippet_length_threshold": 40 # if snippet length is greater than this threshold, it will be included in the indexed data.
}