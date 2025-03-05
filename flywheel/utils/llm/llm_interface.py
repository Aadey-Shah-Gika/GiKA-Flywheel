from abc import ABC

class LLMInterface(ABC):
    """
    Abstract base class for Language Models (LLMs) interface.

    This class provides an interface for different LLMs to be used in the data enrichment pipeline.
    Each LLM implementation should inherit from this class and implement the `get_response` method.

    Attributes:
    None

    Methods:
    get_response(queries):
        Abstract method to get responses from the LLM for a given list of queries.

    Parameters:
    queries (List[str]): A list of queries for which responses are required.

    Returns:
    List[str]: A list of responses corresponding to the input queries.
    """
    @abstractmethod
    def get_response(self, queries):
        pass
