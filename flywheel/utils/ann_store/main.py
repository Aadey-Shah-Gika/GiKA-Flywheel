import pandas as pd

from .constants import DEFAULT_ANN_STORE_CONFIG as default_config

class BaseANNStore:
    def __init__(self, **kwargs):
        
        default_kwargs = {
            "model": default_config["model"],
            "csv_data_file_path": default_config["csv_data_file_path"],
            "index_file_path": default_config["index_file_path"],
            "encoded_csv_data": default_config["encoded_csv_data"],  # DataFrame containing encoded data. Set in load_encoded_csv_data() method.  # noqa: E501
        }
        
        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        
        self.configure(**config_kwargs)
        
        self.load_data()
        self.load_index()
        
    def configure(self, **kwargs):
        """Update the parameters of the ANNStore."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
        
    def read_csv_data(self):
        """Read data from a CSV file."""
        try:
            csv_data = pd.read_csv(self.csv_data_file_path)
            return csv_data
        except FileNotFoundError:
            print(f"Error: File '{self.csv_data_file_path}' not found.")
            return self.encoded_csv_data
    
    def write_csv_data(self):
        """Write data to a CSV file."""
        self.encoded_csv_data.to_csv(self.csv_data_file_path, index=False)
        return self
    
    def load_data(self):
        """Load encoded data from CSV file into attributes."""
        encoded_df = self.read_csv_data()
        self.configure(encoded_csv_data=encoded_df)
        return self
    
    def save_data(self, data):
        """Save data to memory."""
        self.configure(encoded_csv_data=data)
        self.write_csv_data()
        return self
    
    def add_data(self, encoded_data):
        """Add new data to the existing and update encoded CSV data."""
        
        # Append new data
        updated_df = pd.concat([self.encoded_csv_data, encoded_data], ignore_index=True)
        
        # Save updated data
        self.save_data(updated_df)
        
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
    
    def add_vector(self, data):
        """Implement this method in child classes to add index to memory."""
        pass
    
    def convert_text_to_embeddings(self, data):
        """Convert text data into embeddings."""
        return self.model.encode(data)
    
    def add(self, data):
        """Add data to the store and synchronize with database."""
        self.add_data(data)
        self.add_vector(data)
    
    def search_similar_items(self, query_embedding, k):
        """implement subclass-specific search logic here."""
        pass
    
    #TESTING PURPOSE ONLY
    def debug_self(self):
        """Print all attributes of the ANNStore instance."""
        print("IMPORTANT -- Attributes of ANNStore instance:")
        for attr, value in self.__dict__.items():
            print(f"{attr}: {value}")