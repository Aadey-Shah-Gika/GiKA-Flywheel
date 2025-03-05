from .llama import Llama
from .manager import LlmManager

# Default Model
# ! Use only when our GPUS are free
Llm = Llama

# Llm = LlmManager

__all__ = ["Llm", "Llama", "LlmManager"]
