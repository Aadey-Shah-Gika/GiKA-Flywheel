import pytest
from dotenv import load_dotenv

# Load the .env file before running any tests
load_dotenv()

@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()  # Ensures environment variables are loaded
