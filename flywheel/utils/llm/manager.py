from .llm_interface import LLMInterface
import requests


class LlmManager(LLMInterface):
    """
    LlmManager is responsible for handling interactions with an LLM (Large Language Model).
    It extends LLMInterface and provides methods to send queries and process responses.
    """

    def __init__(self, **kwargs):
        """
        Initializes the LlmManager instance with optional keyword arguments.

        This method is responsible for setting up any necessary configurations or parameters
        for the LLM manager. It currently does not perform any specific initialization tasks.

        :param kwargs: Optional keyword arguments that can be used to configure the LLM manager.
                       These arguments are passed directly to the base class constructor.
        """
        pass

    def format_llm_response(self, response):
        """
        Formats the response from the LLM to align with the expected schema.

        This method takes the raw response from the LLM and applies any necessary formatting
        or transformations to ensure that the response adheres to the expected schema.

        :param response: The raw response from the LLM, which will be in a JSON format.

        :return: The formatted response, which should now align with the expected schema.
        """
        # TODO: Implement response formatting logic to align with the expected schema

        return response

    def get_response(self, query):
        """
        Sends a query to the locally hosted LLM inference server and processes the response.

        This method constructs a request payload with the necessary parameters for text generation,
        sends the request to the LLM inference server, converts the response to JSON format,
        and then formats the response to match the expected schema.

        :param query: The user query to be processed by the LLM.

        :return: The formatted response from the LLM, which should now align with the expected schema.
        """

        # Define the request payload with the necessary parameters for text generation
        payload = {
            "type": "text-generation",  # Specifies the type of LLM task
            "model_name": "meta-llama/Llama-3.1-8B-Instruct",  # Defines the model being used
            "input_text": query,  # The user query to be processed
            "temperature": 0.9,  # Controls randomness of the output
            "max_new_tokens": 1024,  # Limits the number of generated tokens
        }

        # Send the request to the locally hosted LLM inference server
        response = requests.post("http://localhost:5000/infer", json=payload)

        # Convert the response to JSON format
        json_response = response.json()

        # Format the response to match the expected schema
        formatted_response = self.format_llm_response(json_response)

        return formatted_response
