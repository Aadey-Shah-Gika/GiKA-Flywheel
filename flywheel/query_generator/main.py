import torch
import logging

from .constants import SYSTEM_INSTRUCTIONS
from flywheel.utils.llm import Llm
from .task_manager import QueryGeneratorTaskManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
        logging.info("Initializing QueryGenerator...")
        self.llm = Llm()
        super().__init__(**kwargs)

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
        
        logging.info("Building prompt for the LLM...")
        system_prompt = {"role": "system", "content": SYSTEM_INSTRUCTIONS}
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
        logging.info("Building LLM messages...")
        return [self.build_prompt(context) for context in content]

    def _extract_content_from_response(self, responses):
        """
        Extracts the useful content from the LLM-generated responses.
        
        Parameters:
        - responses (list): A list of responses from the LLM.
        
        Returns:
        - list: A list of extracted content from each response.
        """
        logging.info("Extracting content from LLM responses...")
        extracted_response = []
        for response in responses:
            content = response[-1]["content"]
            extracted_response.append(content.split("Here are the 25 question-answer pairs:")[-1].strip())
        
        return extracted_response

    def get_formatted_response_from_llm(self, content):
        """
        Fetches and formats the LLM-generated response.
        
        Parameters:
        - content (list of str): A list of input contexts.
        
        Returns:
        - list: A list of formatted responses extracted from the LLM output.
        """
        logging.info("Fetching responses from LLM...")
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
        logging.info("Extracting query statements from response...")
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
        logging.info("Generating queries from LLM response...")
        responses = self.get_formatted_response_from_llm(content)
        torch.cuda.empty_cache()  # Free up GPU memory after processing
        queries = [self._extract_queries(response) for response in responses]
        return queries