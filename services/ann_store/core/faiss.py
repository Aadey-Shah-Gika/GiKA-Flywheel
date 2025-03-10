import faiss
import logging
from .base_ann_store.main import BaseANNStore
from .constants import DEFAULT_FAISS_ANN_STORE_CONFIG as default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)

class FaissANNStore(BaseANNStore):
    """
    A class for managing Approximate Nearest Neighbors (ANN) using the FAISS library.

    This class supports indexing, searching, and persisting high-dimensional vectors,
    enabling efficient similarity searches.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the Faiss ANN store with default or user-provided configuration.
        
        :param kwargs: Configuration parameters such as vector dimension, nearest neighbors, index type, etc.
        """
        
        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # configuration parameters
        config_keys = [
            "vector_dimension",
            "nearest_neighbors",
            "index",
            "similarity_threshold"
        ]
        
        # class variables' config dictionary
        config = {}
        
        for key in config_keys:
            # set the config dictionary to the provided value or set it to default
            config[key] = kwargs.get(key, default_config[key])
        
        # configure class variables with config
        self.configure(**config)
        
        # Initialize parent class
        super().__init__(**kwargs)
    
    def configure(self, **kwargs):
        """
        Configure the Faiss ANN store with provided values or defaults.
        
        :param kwargs: Configuration key-value pairs.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        super().configure(**kwargs)
    
    def read_index(self):
        """
        Load the FAISS index from a file.
        
        :return: Loaded FAISS index.
        """
        with self._file_pLock:
            with self._file_tLock:
                self.logger.info("Reading FAISS index from file.")
                return faiss.read_index(self.index_file_path)
    
    def write_index(self):
        """
        Save the FAISS index to a file for persistence.
        
        :return: Self instance.
        """
        with self._file_pLock:
            with self._file_tLock:
                self.logger.info("Saving FAISS index to file.")
                faiss.write_index(self.index, self.index_file_path)
        return self
    
    def save_index(self, index=None):
        """
        Save the FAISS index, optionally updating it first.
        
        :param index: Optional FAISS index to save.
        :return: Self instance.
        """
        if index is not None:
            self.configure(index=index)
        self.write_index()
        return self
    
    def encode_data(self, data):
        """
        Convert textual data into vector embeddings for indexing.
        
        :param data: List of text data.
        :return: Encoded numpy array of vectors.
        """
        encoded_data = [self.convert_text_to_embeddings(chunks) for chunks in data]
        vector = self.convert_to_vector(encoded_data)
        return vector
    
    def add(self, data):
        """
        Add data to the FAISS index.
        
        :param data: Textual data to be indexed.
        :return: Self instance.
        """
        vectors = self.encode_data(data)  # Convert text to vector embeddings
        self.add_vectors(vectors)  # Add vectors to index
        self.logger.info(f"Data added successfully: {data}")
        return self
    
    def add_vectors(self, vector):
        """
        Add vectors to the FAISS index while ensuring thread safety.
        
        :param vector: Numpy array of vectorized data.
        """
        with self._file_pLock:
            with self._file_tLock:
                self.index.add(vector)
        self.logger.info("Vectors added to FAISS index.")
        self.save_index()
    
    def init_index(self, data=None):
        """
        Initialize a new FAISS index.
        
        :param data: Optional initial data to populate the index.
        :return: Self instance.
        """
        self.index = faiss.IndexFlatIP(self.vector_dimension)
        self.logger.info("Initialized new FAISS index.")
        
        if data is not None:
            self.add_vectors(data)
        
        return self
    
    def load_index(self):
        """
        Load the FAISS index from a file, or create a new one if the file is missing.
        
        :return: Self instance.
        """
        try:
            self.index = self.read_index()
            self.logger.info("FAISS index loaded from file.")
        except Exception as e:
            self.logger.error(f"Error loading index: {e}")
            self.init_index()
            self.save_index()
            self.logger.warning(f"New FAISS index initialized due to missing file at {self.index_file_path}")
        return self
    
    def search_similar_items(self, query, k=None):
        """
        Perform a similarity search on the indexed vectors.
        
        :param query: Query text or vector for searching.
        :param k: Number of nearest neighbors to return (default: stored value).
        :return: List of dictionaries containing matched indices and their similarity scores.
        """
        k = k or self.nearest_neighbors  # Use default k if not provided
        encoded_query = self.encode_data(query)  # Convert text to vector embeddings
        
        with self._file_pLock:
            with self._file_tLock:
                distances, indices = self.index.search(encoded_query, k)
        
        neighbors = [
            {"distance": float(distance), "id": int(index)}
            for index, distance in zip(indices[0], distances[0])
            if index != -1 and distance >= self.similarity_threshold
        ]
        
        self.logger.info(f"Search completed. Found {len(neighbors)} similar items.")
        return neighbors
