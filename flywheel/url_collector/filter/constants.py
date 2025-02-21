from flywheel.utils.ann_store import ANNStore

DEFAULT_URL_FILTER_CONFIG = {
    "ann_store": ANNStore(),
    "urls": [],  # List of URLs to filter and encode. Set in load_urls() method.  # noqa: E501
}