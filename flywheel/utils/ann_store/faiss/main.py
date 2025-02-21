import faiss
import numpy as np

from .. import BaseANNStore
from .constants import DEFAULT_FAISS_ANN_STORE_CONFIG as default_config

class FaissANNStore(BaseANNStore):
    def __init__(self, **kwargs):
        """Initialize Faiss ANN store with default or provided configuration."""
        default_kwargs = {
            "vector_dimension": default_config["vector_dimension"],
            "nearest_neighbors": default_config["nearest_neighbors"],
            "ncluster": default_config["ncluster"],
            "nprobe": default_config["nprobe"],
            "index": default_config["index"],  # Faiss index object. Set in load_index() method.  # noqa: E501
        }

        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}

        self.configure(**config_kwargs)
        super().__init__(**config_kwargs)

    def configure(self, **kwargs):
        """Configure Faiss ANN store settings with provided values or defaults."""
        for key, value in kwargs.items():
            setattr(self, key, value)

        super().configure(**kwargs)
        
    def convert_csv_to_vectors(self, encoded_data):
        """Convert encoded data (DataFrame) to vectors."""
        data_vector = encoded_data.to_numpy(dtype=np.float32)
        return data_vector
        
    def read_index(self):
        """Read Faiss index from a file."""
        return faiss.read_index(self.index_file_path)
    
    def write_index(self):
        """Write Faiss index to a file."""
        faiss.write_index(self.index, self.index_file_path)
        return self
    
    def save_index(self, index=None):
        """Save Faiss index"""
        
        if index is not None:
            self.configure(index=index)
            
        self.write_index()
        return self
    
    
    def add_vectors(self, data):
        """Index encoded data using Faiss."""
        vectors = self.convert_csv_to_vectors(data)
        self.index.add(vectors)
        self.write_index(vectors)
        return self
    
    def init_index(self, data=None):
        """Initialize Faiss index."""
        self.index = faiss.IndexFlatL2(self.vector_dimension)

        if data is not None:
            self.add_vectors(data)
        
        return self
    
    def load_index(self):
        """Load Faiss index from a file."""
        try:
            self.index = self.read_index_file(self.index_file_path)
        except FileNotFoundError:
            # default to saving a new index if file not found
            self.init_index()
            self.save_index()
            print(f"Index file not found at {self.index_file_path}")
        return self
    
    
    def find_nearest_neighbors(self, query_vector, k):
        """Search for similar items in the index."""
        k = k or self.nearest_neighbors
        return self.index.search(query_vector, k)