import faiss as faiss
import numpy as np

from .. import BaseANNStore
from .constants import DEFAULT_FAISS_ANN_STORE_CONFIG as default_config


class FaissANNStore(BaseANNStore):
    def __init__(self, **kwargs):
        """Initialize Faiss ANN store with default or provided configuration."""
        default_kwargs = {
            "vector_dimension": default_config["vector_dimension"],
            "nearest_neighbors": default_config["nearest_neighbors"],
            "index": default_config["index"],
            "similarity_threshold": default_config["similarity_threshold"],
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

    def add(self, vectors):
        """Index encoded data using Faiss."""
        self.index.add(vectors)
        self.save_index()
        return self

    def init_index(self, data=None):
        """Initialize Faiss index."""
        self.index = faiss.IndexFlatIP(self.vector_dimension)

        if data is not None:
            self.add_vectors(data)

        return self

    def load_index(self):
        """Load Faiss index from a file."""
        try:
            self.index = self.read_index()
        except Exception as e:
            # default to saving a new index if file not found
            print("ERROR:", e)
            self.init_index()
            self.save_index()
            print(f"Index file not found at {self.index_file_path}")
        return self

    def search_similar_items(self, encoded_query, k=None):
        """Search for similar items in the index."""
        k = k or self.nearest_neighbors

        distances, indices = self.index.search(encoded_query, k)

        neighbors = [
            {"distance": distance, "id": index}
            for index, distance in zip(indices[0], distances[0])
            if index != -1 and distance >= self.similarity_threshold
        ]

        return neighbors
