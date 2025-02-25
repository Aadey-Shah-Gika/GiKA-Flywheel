import json
from .constants import DEFAULT_ANN_STORE_CONFIG as default_config

class BaseANNStore:
    def __init__(self, **kwargs):
        
        default_kwargs = {
            "model": default_config["model"],
            "index_file_path": default_config["index_file_path"]
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        
        self.configure(**config_kwargs)
        
        self.load_index()
        
    def configure(self, **kwargs):
        """Update the parameters of the ANNStore."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self

    def read_index(self):
        """Implement this method in child classes to read index from a file."""
        pass
    
    def write_index(self):
        """Implement this method in child classes to write index to a file."""
        pass
    
    def load_index(self):
        """Implement this method in child classes to load index from a file."""
        pass
    
    def save_index(self, index):
        """Implement this method in child classes to save index to memory."""
        pass
    
    def add(self, vectors):
        """Implement this method in child classes to add index to memory."""
        pass
    
    def convert_text_to_embeddings(self, data):
        """Convert text data into embeddings."""
        return self.model.encode(data)
    
    def search_similar_items(self, encoded_query, k):
        """implement subclass-specific search logic here."""
        pass