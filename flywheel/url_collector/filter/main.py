from .constants import DEFAULT_URL_FILTER_CONFIG as default_config
import pandas as pd

class URLFilter:
    def __init__(self, **kwargs):
        """Initialize the URLFilter with default parameters."""
        
        default_config = {
            "ann_store": default_config["ann_store"],
            "urls": default_config["urls"],  # List of URLs to filter and encode. Set in load_urls() method.  # noqa: E501
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_config, **kwargs}
        self.configure(**config_kwargs)
        
    def configure(self, **kwargs):
        """Update the parameters of the URLFilter."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def load_urls(self, urls):
        """Load URLs (json format)."""
        self.configure(urls=urls)
        return self

    def encode_url(self, url):
        """encode a URL using ANN Utils."""
        encoded_entry = {
                "url": url["url"],
                "title_embedding": self.ann_store.convert_text_to_embeddings(url["title"]),
                "description_embedding": self.ann_store.convert_text_to_embeddings(url["description"])
            }
        return encoded_entry
    
    @staticmethod
    def convert_json_to_csv(data):
        """Convert JSON data to CSV format"""
        df = pd.DataFrame(data)
        return df
    
    def index_urls(self):
        """encode URLs data into embeddings using ANN Utils."""
        encoded_data = [self.encode_url(url) for url in self.urls]
        encoded_df = self.convert_json_to_csv(encoded_data)
        self.ann_store.add(encoded_df)
        return self
    
    def add_urls(self, urls):
        """Add new URLs to the existing data and update the index."""
        self.urls.extend(urls)
        self.index_urls()
        return self
    
    def find_similar_urls(self, query_vector):
        
