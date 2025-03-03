from flywheel.utils.llm import Llm
from .constants import SYSTEM_INSTRUCTIONS
import torch
from .query_generator_load_balancer import QueryGeneratorLoadBalancer

class QueryGenerator(QueryGeneratorLoadBalancer):
    def __init__(self, **kwargs):
        self.llm = Llm()
        super().__init__(**kwargs)

    def _generate_user_context(self, content):
        """Creates a user instruction based on the provided content with comprehensive guidelines."""
        return (
            "Generate 25 detailed and verbose question-answer pairs from the following context. "
            "For each question, provide a small query statement that could be used to search for the answer:\n\n"
            f"{content}"
        )

    def build_prompt(self, context):
        system_prompt = {"role": "system", "content": SYSTEM_INSTRUCTIONS}
        user_prompt = {"role": "user", "content": self._generate_user_context(context)}
        
        return [system_prompt, user_prompt]

    def build_llm_message(self, content):
        """Constructs the message structure for the LLM."""
        llm_message = [self.build_prompt(context) for context in content]
        return llm_message

    def _extract_content_from_response(self, responses):
        """Extracts meaningful content from the LLM response."""
        
        # print("DEBUG -- [QueryGenerator._extract_content_from_response] -- response:", response)
        
        extracted_response = []
        for response in responses:
            content = response[-1]["content"]
            extracted_response.append(content.split("Here are the 25 question-answer pairs:")[-1].strip())
            
        return extracted_response

    def get_formatted_response_from_llm(self, content):
        """Fetches and formats the LLM response."""
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        return self._extract_content_from_response(response)

    def _extract_queries(self, response_text):
        """Extracts query statements from the LLM-generated response."""
        print('DEBUG -- [QueryGenerator._extract_queries] -- response text:', response_text)
        return [
            line.split("Query:")[-1].strip()
            for line in response_text.split("\n")
            if line.startswith("Query:")
        ]

    def generate_queries(self, content): # content is a string
        """Generates a list of queries extracted from the formatted LLM response."""
        responses = self.get_formatted_response_from_llm(content)
        torch.cuda.empty_cache()
        queries = [self._extract_queries(response) for response in responses]
        return queries
