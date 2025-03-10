import torch
import logging
from flywheel.utils.llm import Llm
from .constants import DEFAULT_SUMMARY_GENERATOR_CONFIG as default_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)


class SummaryGenerator:

    def __init__(self, **kwargs):

        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load configuration with default summarization instruction if not provided
        config = {
            "llm": Llm(temperature=0.1),
            "summarizing_instruction": kwargs.pop(
                "summarizing_instruction", default_config.get("summarizing")
            ),
        }
        self.configure(**config)
        self.logger.info("SummaryGenerator initialized with configuration: %s", config)

    def _generate_user_context(self, content):
        """
        Creates a user instruction that provides guidelines for the LLM to generate a concise summary.

        Parameters:
        - content (str): The input text that needs to be summarized.

        Returns:
        - str: A formatted user instruction string for summarization.
        """
        self.logger.debug("Generating user instruction for content summarization...")
        return f"Summarize the following text in a brief paragraph: {content}"

    def build_prompt(self, context):
        """
        Builds a structured prompt for the LLM, consisting of both system and user instructions.

        Parameters:
        - context (str): The input text to be summarized.

        Returns:
        - list: A list containing system and user prompts formatted for LLM processing.
        """
        self.logger.info("Building prompt for the LLM...")
        # Define system-level prompt for the LLM
        system_prompt = {"role": "system", "content": self.summarize_content}
        # Define user-level instruction using input context
        user_prompt = {"role": "user", "content": self._generate_user_context(context)}

        self.logger.debug("Prompt constructed: %s", [system_prompt, user_prompt])
        return [system_prompt, user_prompt]

    def build_llm_message(self, content):
        """
        Constructs multiple LLM messages for batch processing.

        Parameters:
        - content (list of str): A list of input texts for summarization.

        Returns:
        - list: A list of structured prompts ready for LLM processing.
        """
        self.logger.info("Building LLM messages for batch processing...")
        # Create prompts for each content item
        messages = [self.build_prompt(context) for context in content]
        self.logger.debug("LLM messages constructed: %s", messages)
        return messages

    def _extract_content_from_response(self, responses):
        """
        Extracts relevant content from the LLM-generated responses.

        Parameters:
        - responses (list): A list of LLM responses.

        Returns:
        - list: Extracted and cleaned summaries from each response.
        """
        self.logger.info("Extracting content from LLM responses...")
        extracted_response = []
        for response in responses:
            # Extract content from the last message in the response list
            content = response[-1]["content"]
            # Remove any prefixed instructions and keep only the summary
            extracted_response.append(
                content.split("Here are the 25 question-answer pairs:")[-1].strip()
            )

        self.logger.debug("Extracted responses: %s", extracted_response)
        return extracted_response

    def get_formatted_response_from_llm(self, content):
        """
        Fetches responses from the LLM and formats them for better readability.

        Parameters:
        - content (list of str): A list of input texts.

        Returns:
        - list: A list of formatted and extracted summaries.
        """
        self.logger.info("Fetching and formatting responses from LLM...")
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        formatted_response = self._extract_content_from_response(response)
        self.logger.info("Formatted LLM responses retrieved successfully.")
        return formatted_response

    def _extract_queries(self, response_text):
        """
        Extracts specific queries from the LLM-generated response.

        Parameters:
        - response_text (str): The full LLM-generated response containing multiple statements.

        Returns:
        - list: Extracted query statements.
        """
        self.logger.info("Extracting queries from response text...")
        # Identify lines that contain queries and extract them
        queries = [
            line.split("Query:")[-1].strip()
            for line in response_text.split("\n")
            if line.startswith("Query:")
        ]
        self.logger.debug("Extracted queries: %s", queries)
        return queries

    def summarize_content(self, content):
        """
        Summarizes given content using the LLM model.

        Parameters:
        - content (list of str): A list of input texts to be summarized.

        Returns:
        - list: A list of summarized versions of the input texts.
        """
        self.logger.info("Summarizing content using LLM...")
        # Create LLM messages based on the provided content
        messages = self.build_llm_message(content)
        # Send messages to LLM and retrieve responses
        response = self.llm.get_response(query=messages)
        # Clear GPU memory after processing
        torch.cuda.empty_cache()
        # Extract summarized content from responses
        summarized_content = self._extract_content_from_response(response)
        self.logger.info("Content summarization completed successfully.")
        return summarized_content
