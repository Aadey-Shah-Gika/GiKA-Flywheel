from .constants import DEFAULT_URL_FILTER_CONFIG as default_config
import pandas as pd
import numpy as np
import requests
import json

from filelock import FileLock
from threading import Lock

from .filter_load_balancer import FilterLoadBalancer

class URLFilter(FilterLoadBalancer):
    def __init__(self, **kwargs):
        """Initialize the URLFilter with default parameters."""

        defaults = {
            "ann_store_urls": default_config["ann_store_urls"],
            "snippet_length_threshold": default_config["snippet_length_threshold"],
            "url_file_path": default_config["url_file_path"],
        }

        # Merge default values with user-provided values
        config_kwargs = {**defaults, **kwargs}
        self.configure(**config_kwargs)
        
        # initializing locks
        self._file_pLock = FileLock(f"{self.url_file_path}.lock")
        self._file_tLock = Lock()
        
        super().__init__(**kwargs)

    def configure(self, **kwargs):
        """Update the parameters of the URLFilter."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
    
    def save_url(self, urls):
        """Save the url to file."""
        with self._file_pLock:
            with self._file_tLock:
                
                with open(self.url_file_path, 'r', encoding='utf-8') as file:
                    json_file = json.load(file)
                    json_file.extend(urls)
                
                with open(self.url_file_path, 'w', encoding='utf-8') as file:
                    json.dump(json_file, file, indent=4)
                    
    
    def transform_url_query(self, query):
        """Transform JSON to a query string"""
        
        transformed_query = f"""
        Title: {query["title"]}
        \n==================================\n
        Description: {query["snippet"]}
        """
        
        return transformed_query

    def index_urls(self, data, ann_store_name):
        """Store the url to respective stores"""
        
        url = f"{self.ann_store_urls[ann_store_name]}/add"
        
        headers = {
            "Content-Type": "application/json"  # Ensure the correct Content-Type
        }
        
        print("DEBUG -- [URLFilter.index_urls] -- url:", url)
        
        response = {'data': data}
        
        response = requests.post(url, json=response, headers=headers)
        
        if response.status_code == 200:
            print("DEBUG -- [URLFilter.index_url] -- INDEXED SUCCESSFULLY")
            print("Indexed successfully.")
            return self
        
        print("Failed to index.")
        return self
    
    def preprocess_urls(self, urls):
        """Preprocess URLs before indexing."""
        preprocessed_urls = []
        
        for url in urls:
            if len(url["snippet"]) <= self.snippet_length_threshold:
                url["snippet"] = url['title']
            preprocessed_urls.append(url)
        return preprocessed_urls

    def add_urls(self, urls):
        """Add new URLs to the existing data and update the index."""
        if(len(urls) == 0):
            print("No URLs to add.")
            return self
        
        print("DEBUG -- [URLFilter.add_url] -- urls:", urls)
        
        preprocessed_urls = self.preprocess_urls(urls)
        
        self.save_url(preprocessed_urls)
        
        self.index_urls(preprocessed_urls, "title")
        self.index_urls(preprocessed_urls, "snippet")
        
        return self

    def find_similar_urls(self, query, key):
        
        transformed_query = self.transform_url_query(query)
        
        url = f"{self.ann_store_urls[key]}/nearest_neighbor"
        
        headers = {
            "Content-Type": "application/json"  # Ensure the correct Content-Type
        }

        data = {
            'query': transformed_query,
            'k': 1
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            nearest_neighbors = response.json()['data']
            return nearest_neighbors

        print("Failed to find similar URLs.")
        print("Response:", response.text)
        return [{'distance': 0, 'id': -1}]
    
    def avg_similarity_score(self, nearest_neighbors):
        """Calculate average similarity score between query and all URLs."""
        
        if not nearest_neighbors:  # More Pythonic check for empty list
            return 0
        
        # Extracting distances and computing the average
        total_distance = sum(neighbor["distance"] for neighbor in nearest_neighbors)
        return total_distance / len(nearest_neighbors)
    
    def get_similarity_score(self, nearest_neighbors):
        """Calculate similarity score between query and nearest neighbors."""
        
        similarity_score_title = self.avg_similarity_score(nearest_neighbors["title"])
        similarity_score_snippet = self.avg_similarity_score(nearest_neighbors["snippet"])
        
        print("DEBUG -- [URLFilter.get_similarity_score] -- similarity_score_title:", similarity_score_title)
        print("DEBUG -- [URLFilter.get_similarity_score] -- similarity_score_snippet:", similarity_score_snippet)
        
        similarity_score = (similarity_score_title + similarity_score_snippet) / 2
        
        print("DEBUG -- [URLFilter.get_similarity_score] -- similarity_score:", similarity_score)
        
        return similarity_score
        
    def filter_urls(self, urls):
        """Filter search results based on the ANN search results."""
        
        print("DEBUG -- [URLFilter.filter_urls] -- urls:", urls)
        
        filtered_results = []
        
        for url in urls:
            nearest_neighbors = {
                "title": self.find_similar_urls(url, "title"),
                "snippet": self.find_similar_urls(url, "snippet")
            }
            
            print("DEBUG -- [URLFilter.filter_urls] -- Filtering URL:", url)
            
            similarity_score = self.get_similarity_score(nearest_neighbors)
            
            if similarity_score >= 0.5:
                filtered_results.append(url)
        
        if filtered_results and len(filtered_results) > 0:
            self.add_urls(filtered_results)  # Add filtered URLs back to the existing data.
        
        return filtered_results
    
