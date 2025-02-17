import time
import json
import random
import requests
from stem import Signal
from stem.control import Controller
from googlesearch import search

from ....base_scrapper import BaseScraper
from .constants import DEFAULT_CONFIG as default_config

class GoogleSearchWebScraper(BaseScraper):
    def __init__(self, **kwargs):
        default_kwargs = {
            "proxy": default_config["proxy"]
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        
        self.configure(**config_kwargs)
        super().__init__(**config_kwargs)
    
    def configure(self, **kwargs):
        """Configure proxy settings with provided values or defaults."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        super().configure(**kwargs)

    def fetch_results(self, query, limit):
        limit = 10
        print(f"IMPORTANT IMPORTANT IMPORTANT : Fetching results for query: '{query}' '({limit}) results'...")
        return list(
            search(query, num_results=limit, unique=True, proxy=self.proxy, advanced=True)
        )
