from .llm_interface import LLMInterface

from transformers import pipeline
import torch
from tqdm import tqdm

from .constants import DEFAULT_LLAMA_CONFIG as default_config, DEFAULT_LLAMA_BATCH_SIZE


class Llama(LLMInterface):

    def __init__(self, **kwargs):
        """
        Initialize the Llama class with the provided configuration parameters.

        Parameters:
        - **kwargs** (dict): Keyword arguments for configuring the Llama model.

        Attributes:
        - **llama_pipe** (transformers.pipeline): The Llama pipeline for generating text.
        - **config** (dict): The configuration parameters for the Llama model.

        The configuration parameters are merged with the default configuration parameters.
        The Llama pipeline is initialized using the provided configuration parameters.
        """
        self.llama_pipe = None
        self.config = {**default_config, **kwargs}
        self.__initialize_llama_pipe(self.config)

    def __initialize_llama_pipe(self, config):
        """
        Initialize the llama pipeline based on the provided config.

        Parameters:
        - config (dict): A dictionary containing configuration parameters for the Llama model.
            - "task" (str): The task for which the Llama model will be used.
            - "model" (str): The name or path of the Llama model.
            - "device" (str): The device on which the Llama model will be executed (e.g., 'cpu', 'cuda').
            - "torch_dtype" (torch.dtype): The data type for the Llama model's tensors.
            - "temperature" (float): The temperature for sampling from the Llama model's output distribution.
            - "max_new_tokens" (int): The maximum number of new tokens to generate.
            - "pad_token_id" (int): The ID of the padding token.
            - "clean_up_tokenization_spaces" (bool): Whether to clean up spaces in the tokenization process.

        Returns:
        None
        """
        if not self.llama_pipe:
            self.llama_pipe = pipeline(
                config["task"],
                model=config["model"],
                device=config["device"],
                torch_dtype=config["torch_dtype"],
                temperature=config["temperature"],
                max_new_tokens=config["max_new_tokens"],
                pad_token_id=config["pad_token_id"],
                clean_up_tokenization_spaces=config["clean_up_tokenization_spaces"],
            )

    def generate_single_output(self, batch):
        """
        Generate a single output from the Llama model for a given batch of inputs.

        Parameters:
        - batch (list): A list of input strings for which the Llama model will generate output.

        Returns:
        - list: A list of generated outputs corresponding to the input batch. Each output is a string.

        The function uses the Llama pipeline to generate output for the given batch of inputs.
        It disables gradient computation using torch.no_grad() to improve performance.
        The generated outputs are extracted from the model's output and returned as a list.
        Finally, it clears the CUDA cache using torch.cuda.empty_cache() to free up GPU memory.
        """
        with torch.no_grad():
            output = self.llama_pipe(batch)
        outputs = [item[0]['generated_text'][-1]['content'] for item in output]
        torch.cuda.empty_cache()
        return outputs

    def generate_single_text(self, messages, batch_size=DEFAULT_LLAMA_BATCH_SIZE):
        """
        Generate a single text response for a batch of input messages using the Llama model.

        Parameters:
        - messages (list): A list of input messages for which the Llama model will generate responses.
            Each message is a list of dictionaries, where each dictionary represents a message part.
            Each message part has the following structure: {"role": str, "content": str}.
        - batch_size (int, optional): The number of messages to process in a single batch.
            Defaults to DEFAULT_LLAMA_BATCH_SIZE (defined in constants.py).

        Returns:
        - list: A list of updated messages, where each message is a list of dictionaries.
            Each message part now includes the generated "content" for the assistant role.
        The function processes the input messages in batches, generates responses for each batch using
        the Llama model's generate_single_output method, and appends the generated responses to the messages.
        """
        results = []
        for i in tqdm(range(0, len(messages), batch_size)):
            results += self.generate_single_output(messages[i:i+batch_size])
        for ind, result in enumerate(results):
            messages[ind].append(
                {
                    "role": "assistant",
                    "content": result
                }
            )

        return messages

    def get_response(self, query):
        """
        Generate a response for a given query using the Llama model.

        Parameters:
        - query (list): A list of input messages for which the Llama model will generate responses.
            Each message is a list of dictionaries, where each dictionary represents a message part.
            Each message part has the following structure: {"role": str, "content": str}.

        Returns:
        - list: A list of updated messages, where each message is a list of dictionaries.
            Each message part now includes the generated "content" for the assistant role.

        This function acts as a wrapper around the `generate_single_text` method, passing the query
        to it and returning the generated response.
        """
        return self.generate_single_text(query)
