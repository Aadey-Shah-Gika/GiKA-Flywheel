import os

# Get the absolute path of the current script's directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(CURRENT_DIR, "prompt.txt")

# Open the file with the absolute path
with open(FILE_PATH, "r", encoding="utf-8") as file:
    SYSTEM_INSTRUCTIONS = file.read()

DEFAULT_LOAD_BALANCER_CONFIG = {
    'max_tasks_once': 30
}