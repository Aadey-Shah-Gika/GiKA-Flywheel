import os
import pytest
from dotenv import load_dotenv

# Load the .env file before any tests run

def pytest_sessionstart(session):
    """Clear environment variables before test session starts."""
    os.environ.clear()
    load_dotenv()

@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()  # Ensures environment variables are available globally