import logging
import numpy as np
from filelock import FileLock
from threading import Lock as ThreadLock
from .constants import DEFAULT_ANN_STORE_CONFIG as default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)

class BaseANNStore:
    """
    Base class for an Approximate Nearest Neighbors (ANN) Store.

    This class provides a structure for managing an ANN index with support for:
    - Configurable parameters (model, index file path, etc.)
    - Thread safety using file locks and threading locks
    - Placeholder methods for reading, writing, and searching indexes

    Subclasses should implement the abstract methods to define custom behavior.
    """

    def __init__(self, **kwargs):
        """
        Initialize the ANN store with configurable parameters.
        Merges user-provided configurations with default settings.

        :param kwargs: Custom configuration values.
        """

        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)

        # Default configurations
        default_kwargs = {
            "model": default_config["model"],
            "index_file_path": default_config["index_file_path"],
        }

        # Merge default values with user-provided values
        config_kwargs = {**default_kwargs, **kwargs}
        self.configure(**config_kwargs)

        # Initialize file locks for atomic operations
        self.init_locks()

        self.logger.info("Initializing ANN Store and restoring index...")
        # Load index if available
        self.load_index()

    def init_locks(self):
        """
        Initialize file locks for thread safety.

        This function ensures the existence of the directory and file specified by `url_file_path`.
        It then creates file locks for both process-level and thread-level synchronization.
        If the directory does not exist, it is created.
        If the file does not exist, an empty file is created.

        Parameters:
        - None

        Returns:
        - None

        The function does not return any value. It initialize the instance attributes `_file_pLock` and `_file_tLock`.
        """
        try:
            # Lock to synchronize file access across multiple processes
            self._file_pLock = FileLock(f"{self.index_file_path}.lock")

            # Lock to synchronize file access across multiple threads
            self._file_tLock = ThreadLock()

        except FileNotFoundError as e:
            self.logger.error(f"FILE NOT FOUND: {self.url_file_path}")
            raise

    def configure(self, **kwargs):
        """
        Update the parameters of the ANN store.
        This allows dynamic configuration changes.

        :param kwargs: Dictionary of key-value configuration parameters.
        :return: Self instance to allow method chaining.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.logger.info("Configuration updated: %s", kwargs)
        return self

    def read_index(self):
        """
        Read the ANN index from a file.
        This method should be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses must implement read_index method.")

    def write_index(self):
        """
        Write the ANN index to a file.
        This method should be implemented in subclasses.
        """
        raise NotImplementedError("Subclasses must implement write_index method.")

    def load_index(self):
        """
        Load the ANN index from storage.
        This method should be implemented in subclasses.
        """
        self.logger.info("Loading ANN index from storage...")
        raise NotImplementedError("Subclasses must implement load_index method.")

    def save_index(self, index):
        """
        Save the ANN index to memory.
        This method should be implemented in subclasses.

        :param index: The index data to be saved.
        """
        self.logger.info("Saving ANN index to memory...")
        raise NotImplementedError("Subclasses must implement save_index method.")

    def add(self, vectors):
        """
        Add vectors to the ANN index.
        This method should be implemented in subclasses.

        :param vectors: List or NumPy array of vectors to be added to the index.
        """
        self.logger.info("Adding vectors to the ANN index...")
        raise NotImplementedError("Subclasses must implement add method.")

    def convert_text_to_embeddings(self, data):
        """
        Convert text data into embeddings using the configured model.

        :param data: A list or single instance of text data to convert.
        :return: NumPy array of generated embeddings.
        """
        self.logger.info("Converting text data to embeddings...")
        return self.model.encode(data)

    @staticmethod
    def convert_to_vector(data):
        """
        Convert a list of numerical data into a NumPy float32 array.

        :param data: List of numerical values.
        :return: NumPy array with dtype float32.
        """
        return np.array(data, dtype=np.float32)

    def search_similar_items(self, encoded_query, k):
        """
        Search for the top-k similar items in the ANN index.
        This method should be implemented in subclasses.

        :param encoded_query: The query vector (embedding) to search for.
        :param k: Number of top similar results to return.
        """
        self.logger.info("Searching for top-%d similar items...", k)
        raise NotImplementedError(
            "Subclasses must implement search_similar_items method."
        )
