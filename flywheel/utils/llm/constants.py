import torch

# llama
DEFAULT_LLAMA_CONFIG = {
    "task": "text-generation",
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "device": torch.device("cuda:1"),
    "torch_dtype": torch.bfloat16,
    "temperature": 0.9,
    "max_new_tokens": 10000,
    "pad_token_id": 128001,
    "clean_up_tokenization_spaces": False
}

DEFAULT_LLAMA_BATCH_SIZE = 8