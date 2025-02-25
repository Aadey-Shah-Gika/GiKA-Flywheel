from .constants import DEFAULT_URL_FILTER_CONFIG as default_config
import pandas as pd
import numpy as np


class URLFilter:
    def __init__(self, **kwargs):
        """Initialize the URLFilter with default parameters."""

        defaults = {
            "ann_store": default_config["ann_store"],
            "urls": default_config["urls"],
            "snippet_length_threshold": default_config["snippet_length_threshold"],
        }

        # Merge default values with user-provided values
        config_kwargs = {**defaults, **kwargs}
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

    def encode_text(self, text):
        """encode a URL using ANN Utils."""
        encoded_entry = self.ann_store["title"].convert_text_to_embeddings(text)
        return encoded_entry
    
    def encode_url(self, url, key):
        """encode a URL using ANN Utils."""
        
        text = url[key] if key in url else ""
        
        encoded_entry = self.encode_text(text)
        return encoded_entry
    
    def encode_url_query(self, query):
        """encode a URL using ANN Utils."""
        
        transformed_text = f"""
        Title: {query["title"]}
        \n==================================\n
        Description: {query["snippet"]}
        """
        
        encoded_query = self.encode_text(transformed_text)
        
        return encoded_query

    @staticmethod
    def convert_list_to_vectors(data):
        """Convert JSON data to CSV format"""
        vectors = np.array(data, dtype=np.float32)
        return vectors

    def index_urls(self, encoded_data, ann_store):
        """encode URLs data into embeddings using ANN Utils."""
        encoded_vectors = self.convert_list_to_vectors(encoded_data)
        ann_store.add(encoded_vectors)
        return self

    def encode_and_index_url_info(self, urls, key):
        encoded_data = [self.encode_url(url, key) for url in urls]
        self.index_urls(encoded_data, self.ann_store[key])
        return self
    
    def preprocess_urls(self, urls):
        """Preprocess URLs before indexing."""
        preprocessed_urls = []
        
        for url in urls:
            if len(url["snippet"]) <= self.snippet_length_threshold:
                url["snippet"] = ""
            preprocessed_urls.append(url)
        return preprocessed_urls

    def add_urls(self, urls):
        """Add new URLs to the existing data and update the index."""
        preprocessed_urls = self.preprocess_urls(urls)
        self.urls.extend(preprocessed_urls)
        print("DEBUG -- Preprocessing URLs Length:", len(preprocessed_urls))
        self.encode_and_index_url_info(preprocessed_urls, "title")
        self.encode_and_index_url_info(preprocessed_urls, "snippet")
        return self

    def find_similar_urls(self, query, key):
        encoded_query_vector = self.encode_url_query(query)
        encoded_query_vector = [encoded_query_vector]
        encoded_query_np = np.array(encoded_query_vector, dtype=np.float32)
        nearest_neighbors = self.ann_store[key].search_similar_items(
            encoded_query_np, 2
        )
        return nearest_neighbors
    
    def get_similarity_score(self, nearest_neighbors):
        """Calculate similarity score between query and nearest neighbors."""
        similarity_score_title = nearest_neighbors["title"]
        similarity_score_snippet = nearest_neighbors["snippet"]
        similarity_score = (similarity_score_title + similarity_score_snippet) / 2
        return similarity_score
        
    def filter_urls(self, urls):
        """Filter search results based on the ANN search results."""
        filtered_results = []
        for url in urls:
            nearest_neighbors = {
                "title": self.find_similar_urls(url, "title"),
                "snippet": self.find_similar_urls(url, "snippet")
            }
            
            similarity_score = self.get_similarity_score(nearest_neighbors)
            
            if similarity_score >= 0.5:
                filtered_results.append(url)
        
        return filtered_results
