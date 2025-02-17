from flywheel.utils.llm import Llm
from .constants import SYSTEM_INSTRUCTIONS
import torch


class QueryGenerator:
    def __init__(self):
        self.llm = Llm()

    def _generate_user_context(self, content):
        """Creates a user instruction based on the provided content with comprehensive guidelines."""
        return (
            "Generate 25 detailed and verbose question-answer pairs from the following context. "
            "For each question, provide a small query statement that could be used to search for the answer:\n\n"
            f"{content}"
        )

    def build_llm_message(self, content):
        """Constructs the message structure for the LLM."""
        system_prompt = {"role": "system", "content": SYSTEM_INSTRUCTIONS}
        user_prompt = {"role": "user", "content": self._generate_user_context(content)}
        return [[system_prompt, user_prompt]]

    def _extract_content_from_response(self, response):
        """Extracts meaningful content from the LLM response."""
        content = response[0][-1]["content"]
        return content.split("Here are the 25 question-answer pairs:")[-1].strip()

    def get_formatted_response_from_llm(self, content):
        """Fetches and formats the LLM response."""
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        return self._extract_content_from_response(response)

    def _extract_queries(self, response_text):
        """Extracts query statements from the LLM-generated response."""
        return [
            line.split("Query:")[-1].strip()
            for line in response_text.split("\n")
            if line.startswith("Query:")
        ]

    def generate_queries(self, content):
        """Generates a list of queries extracted from the formatted LLM response."""
        response_text = self.get_formatted_response_from_llm(content)
        torch.cuda.empty_cache()
        return self._extract_queries(response_text)
