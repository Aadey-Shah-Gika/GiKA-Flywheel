import os

# Get the absolute path of the current script's directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the path to the prompt file relative to the current directory
PROMPT_FILE = os.path.join(CURRENT_DIR, "prompt.txt")

with open(PROMPT_FILE, "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTIONS = file.read()
    
DEFAULT_SUMMARY_GENERATOR_CONFIG = {
    "summarizing_instruction": SYSTEM_INSTRUCTIONS
}