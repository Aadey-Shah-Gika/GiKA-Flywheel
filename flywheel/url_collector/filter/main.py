import json
import logging
import requests
import pandas as pd
import numpy as np
from filelock import FileLock
from threading import Lock
from .constants import DEFAULT_URL_FILTER_CONFIG as default_config
from .filter_load_balancer import FilterLoadBalancer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class URLFilter(FilterLoadBalancer):
    """
    A class to filter, store, and index URLs based on similarity using an ANN (Approximate Nearest Neighbor) search.
    """

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

        # Initialize file locks for thread safety
        self._file_pLock = FileLock(f"{self.url_file_path}.lock")
        self._file_tLock = Lock()

        super().__init__(**kwargs)

    def configure(self, **kwargs):
        """
        Update the parameters of the URLFilter.

        Parameters:
        - kwargs (dict): A dictionary of key-value pairs representing the parameters to be updated.

        Returns:
        - self: The updated instance of the URLFilter class.

        This method iterates through the key-value pairs in the kwargs dictionary and updates the corresponding attributes of the URLFilter instance.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def save_url(self, urls):
        """
        Save URLs to a file while ensuring thread safety.

        Parameters:
        - urls (list): A list of dictionaries, where each dictionary represents a URL with keys 'title' and 'snippet'.

        Returns:
        - None

        This function opens the specified URL file in read mode, loads the existing JSON data, appends the new URLs,
        and then writes the updated JSON data back to the file. It uses file locks to ensure thread safety.
        If any errors occur during file operations or JSON parsing, it logs the error message.
        """
        try:
            with self._file_pLock, self._file_tLock:
                with open(self.url_file_path, "r", encoding="utf-8") as file:
                    json_file = json.load(file)
                    json_file.extend(urls)

                with open(self.url_file_path, "w", encoding="utf-8") as file:
                    json.dump(json_file, file, indent=4)

            logging.info("URLs successfully saved to file.")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error saving URLs to file: {e}")

    def transform_url_query(self, query):
        """
        Transform a JSON query into a formatted query string for ANN search.

        Parameters:
        - query (dict): A dictionary representing a URL with keys 'title' and 'snippet'.
            The 'title' key contains the title of the URL, and the 'snippet' key contains the description or snippet of the URL.

        Returns:
        - str: A formatted query string containing the title and snippet of the URL.
            The query string is separated by a horizontal rule for better readability.

        This function takes a JSON query representing a URL and transforms it into a formatted query string for ANN search.
        The query string includes the title and snippet of the URL, separated by a horizontal rule.
        """
        return f"""
        Title: {query.get("title", "")}
        \n==================================\n
        Description: {query.get("snippet", "")}
        """

    def index_urls(self, data, ann_store_name):
        """
        Send URLs to the ANN store for indexing.

        Parameters:
        - data (list): A list of dictionaries, where each dictionary represents a URL
        - ann_store_name (str): The name of the ANN store to which the URLs will be indexed.

        Returns:
        - None

        This function sends a POST request to the specified ANN store URL with the provided data.
        It constructs the URL using the base URL from the `ann_store_urls` dictionary and the provided `ann_store_name`.
        The data is sent as a JSON payload in the request body.
        If the request is successful (status code 200), it logs a success message.
        If the request fails (status code other than 200), it logs a warning message.
        If any request exceptions occur, it logs an error message.
        """
        try:
            url = f"{self.ann_store_urls[ann_store_name]}/add"
            headers = {"Content-Type": "application/json"}
            response = requests.post(url, json={"data": data}, headers=headers)

            if response.status_code == 200:
                logging.info(f"Successfully indexed URLs under {ann_store_name}.")
            else:
                logging.warning(
                    f"Failed to index URLs. Status Code: {response.status_code}"
                )
        except requests.RequestException as e:
            logging.error(f"Request failed while indexing URLs: {e}")

    def preprocess_urls(self, urls):
        """
        Preprocess URLs before indexing by ensuring snippet length meets the threshold.

        Parameters:
        - urls (list): A list of dictionaries, where each dictionary represents a URL.
            Each URL dictionary should contain 'title' and 'snippet' keys.

        Returns:
        - list: A list of preprocessed URL dictionaries.
            Each preprocessed URL dictionary has the same structure as the input URLs.
            If the snippet length is less than or equal to the threshold, the snippet is replaced with the title.

        This function iterates through the input list of URLs, checks the length of the snippet,
        and replaces the snippet with the title if the snippet length is less than or equal to the threshold.
        The preprocessed URLs are then returned as a list.
        """
        preprocessed_urls = []
        for url in urls:
            if len(url.get("snippet", "")) <= self.snippet_length_threshold:
                url["snippet"] = url.get("title", "")
            preprocessed_urls.append(url)
        return preprocessed_urls

    def add_urls(self, urls):
        """
        Add new URLs to the data store and update the index.

        Parameters:
        - urls (list): A list of dictionaries, where each dictionary represents a URL.
            Each URL dictionary should contain 'title' and 'snippet' keys.

        Returns:
        - self: The instance of the URLFilter class after adding the URLs.
            If no URLs are provided, it returns the instance itself without any changes.

        This function preprocesses the URLs, saves them to a file, and indexes them using the ANN store.
        If no URLs are provided, it logs an information message and returns the instance itself without any changes.
        """
        if not urls:
            logging.info("No URLs to add.")
            return self

        preprocessed_urls = self.preprocess_urls(urls)
        self.save_url(preprocessed_urls)

        self.index_urls(preprocessed_urls, "title")
        self.index_urls(preprocessed_urls, "snippet")

        return self

    def find_similar_urls(self, query, key):
        """
        Find similar URLs using ANN search based on a given query.

        Parameters:
        - query (dict): A dictionary representing a URL with keys 'title' and 'snippet'.
            The 'title' key contains the title of the URL, and the 'snippet' key contains the description or snippet of the URL.
        - key (str): The key to access the ANN store URL from the `ann_store_urls` dictionary.

        Returns:
        - list: A list of dictionaries representing the nearest neighbors found by the ANN search.
            Each dictionary contains 'distance' and 'id' keys.
            If the ANN search is successful, the 'data' key from the response JSON is returned.
            If the ANN search fails or encounters an exception, a default list containing a single dictionary with 'distance' and 'id' set to 0 and -1, respectively, is returned.
        """
        transformed_query = self.transform_url_query(query)

        try:
            url = f"{self.ann_store_urls[key]}/nearest_neighbor"
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url, json={"query": transformed_query, "k": 1}, headers=headers
            )

            if response.status_code == 200:
                return response.json().get("data", [])

            logging.warning(
                f"ANN search failed with status code {response.status_code}."
            )
        except requests.RequestException as e:
            logging.error(f"Error performing ANN search: {e}")

        return [{"distance": 0, "id": -1}]

    def avg_similarity_score(self, nearest_neighbors):
        """
        Calculate the average similarity score from ANN results.

        Parameters:
        - nearest_neighbors (list): A list of dictionaries representing the nearest neighbors found by the ANN search.
            Each dictionary contains 'distance' and 'id' keys.

        Returns:
        - float: The average similarity score calculated from the nearest neighbors.
            If the nearest_neighbors list is empty, the function returns 0.
        """
        if not nearest_neighbors:
            return 0
        return sum(neighbor.get("distance", 0) for neighbor in nearest_neighbors) / len(
            nearest_neighbors
        )

    def get_similarity_score(self, nearest_neighbors):
        """
        Compute the overall similarity score by averaging title and snippet scores.

        Parameters:
        - nearest_neighbors (dict): A dictionary containing the nearest neighbors found by the ANN search.
            The dictionary has two keys: "title" and "snippet". Each key maps to a list of dictionaries,
            where each dictionary represents a nearest neighbor and contains 'distance' and 'id' keys.

        Returns:
        - float: The overall similarity score calculated by averaging the title and snippet scores.
            The similarity score is a float value between 0 and 1, representing the average similarity
            between the input URL and its nearest neighbors in the title and snippet spaces.
        """
        similarity_score_title = self.avg_similarity_score(
            nearest_neighbors.get("title", [])
        )
        similarity_score_snippet = self.avg_similarity_score(
            nearest_neighbors.get("snippet", [])
        )
        return (similarity_score_title + similarity_score_snippet) / 2

    def filter_urls(self, urls):
        """
        Filter URLs based on similarity scores computed using ANN search results.

        Parameters:
        - urls (list): A list of dictionaries, where each dictionary represents a URL.
            Each URL dictionary should contain 'title' and 'snippet' keys.

        Returns:
        - list: A list of dictionaries representing the filtered URLs.
            Each filtered URL dictionary has the same structure as the input URLs,
            plus additional keys 'similarity_score', 'title_similarity_score', and 'snippet_similarity_score'.
            These keys represent the overall similarity score, title similarity score, and snippet similarity score, respectively.
            If no URLs meet the filtering criteria, an empty list is returned.

        The function iterates through the input list of URLs, finds the nearest neighbors for each URL using the ANN search,
        computes the similarity scores, and filters out URLs with similarity scores less than 0.5.
        The filtered URLs are then stored in the data store and indexed using the ANN store.
        """
        filtered_results = []

        for url in urls:
            nearest_neighbors = {
                "title": self.find_similar_urls(url, "title"),
                "snippet": self.find_similar_urls(url, "snippet"),
            }

            similarity_score = self.get_similarity_score(nearest_neighbors)

            if similarity_score >= 0.5:
                url.update(
                    {
                        "similarity_score": similarity_score,
                        "title_similarity_score": self.avg_similarity_score(
                            nearest_neighbors["title"]
                        ),
                        "snippet_similarity_score": self.avg_similarity_score(
                            nearest_neighbors["snippet"]
                        ),
                    }
                )
                filtered_results.append(url)

        if filtered_results:
            self.add_urls(filtered_results)  # Store filtered URLs
            logging.info(
                f"Filtered {len(filtered_results)} URLs and added them to the index."
            )

        return filtered_results
