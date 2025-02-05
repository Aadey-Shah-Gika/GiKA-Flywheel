from .llm_interface import LLMInterface

from transformers import pipeline
import torch
from tqdm import tqdm

from .constants import DEFAULT_LLAMA_CONFIG, DEFAULT_LLAMA_BATCH_SIZE


class Llama(LLMInterface):

    def __init__(self, config=DEFAULT_LLAMA_CONFIG):
        self.llama_pipe = None
        self.config = config
        self.__initialize_llama_pipe(config)

    def __initialize_llama_pipe(self, config):
        """Initialize the llama pipeline based on the provided config."""

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

        with torch.no_grad():
            output = self.llama_pipe(batch)
        outputs = [item[0]['generated_text'][-1]['content'] for item in output]
        torch.cuda.empty_cache()
        return outputs

    def generate_single_text(self, messages, batch_size=DEFAULT_LLAMA_BATCH_SIZE):

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
        return self.generate_single_text(query)
