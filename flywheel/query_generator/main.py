import torch
import logging

from .constants import DEFAULT_QUERY_GENERATOR_CONFIG as default_config
from .task_manager import QueryGeneratorTaskManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)

class QueryGenerator(QueryGeneratorTaskManager):
    """
    A class responsible for generating query statements using an LLM (Large Language Model).
    It processes input content, constructs prompts, retrieves responses from the LLM, and
    extracts meaningful queries from the generated output.
    """

    def __init__(self, **kwargs):
        """
        Initializes the QueryGenerator by instantiating the LLM and calling the parent class constructor.
        """
        
        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)

        # configuration parameters
        config_keys = ["llm", "system_instructions"]

        # configure config for assigning class variables
        config = {}
        for key in config_keys:
            # if config key is not specified take the default [defined in constants.py]
            config[key] = kwargs.get(key, default_config[key])

        # Configure the scraper with the provided or default settings
        self.configure(**config)

        # Initialize the parent class
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
            # self.key = value
            setattr(self, key, value)
        return self

    def _generate_user_context(self, content):
        """
        Creates a user instruction that provides guidelines for the LLM to generate detailed question-answer pairs.

        Parameters:
        - content (str): The input context from which the LLM will generate questions and queries.

        Returns:
        - str: A formatted user instruction string.
        """
        return (
            "Generate 25 detailed and verbose question-answer pairs from the following context. "
            "For each question, provide a small query statement that could be used to search for the answer:\n\n"
            f"{content}"
        )

    def build_prompt(self, context):
        """
        Builds a structured prompt for the LLM containing both system and user instructions.

        Parameters:
        - context (str): The input context used for question and query generation.

        Returns:
        - list: A list containing the system and user prompts.
        """

        self.logger.info("Building prompt for the LLM...")
        system_prompt = {"role": "system", "content": self.system_instructions}
        user_prompt = {"role": "user", "content": self._generate_user_context(context)}

        return [system_prompt, user_prompt]

    def build_llm_message(self, content):
        """
        Constructs LLM messages for batch processing.

        Parameters:
        - content (list of str): A list of input contexts.

        Returns:
        - list: A list of structured LLM messages.
        """
        self.logger.info("Building LLM messages...")
        return [self.build_prompt(context) for context in content]

    def _extract_content_from_response(self, responses):
        """
        Extracts the useful content from the LLM-generated responses.

        Parameters:
        - responses (list): A list of responses from the LLM.

        Returns:
        - list: A list of extracted content from each response.
        """
        self.logger.info("Extracting content from LLM responses...")
        extracted_response = []
        for response in responses:
            content = response[-1]["content"]
            extracted_response.append(
                content.split("Here are the 25 question-answer pairs:")[-1].strip()
            )

        return extracted_response

    def get_formatted_response_from_llm(self, content):
        """
        Fetches and formats the LLM-generated response.

        Parameters:
        - content (list of str): A list of input contexts.

        Returns:
        - list: A list of formatted responses extracted from the LLM output.
        """
        self.logger.info("Fetching responses from LLM...")
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        return self._extract_content_from_response(response)

    def _extract_queries(self, response_text):
        """
        Extracts query statements from the LLM-generated response.

        Parameters:
        - response_text (str): A single LLM-generated response containing question-answer pairs.

        Returns:
        - list: A list of extracted query statements.
        """
        self.logger.info("Extracting query statements from response...")
        return [
            line.split("Query:")[-1].strip()
            for line in response_text.split("\n")
            if line.startswith("Query:")
        ]

    def generate_queries(self, content):
        """
        Generates a list of queries extracted from the formatted LLM response.

        Parameters:
        - content (str): The input context from which queries are to be generated.

        Returns:
        - list of list: A list containing lists of extracted queries.
        """
        self.logger.info("Generating queries from LLM response...")
        responses = self.get_formatted_response_from_llm(content)
        torch.cuda.empty_cache()  # Free up GPU memory after processing
        queries = [self._extract_queries(response) for response in responses]
        return queries
