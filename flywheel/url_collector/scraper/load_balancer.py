import json
from filelock import FileLock
from threading import Lock as ThreadLock
import logging

from submodules.browser import Browser
from flywheel.utils.load_balancer import AbstractLoadBalancer
from .constants import TASK_STORAGE_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
)

# TODO: Create a separate file operation utils

def read_json_file(filename):
    """
    Read the content of a JSON file and return it as a dictionary.

    Parameters:
    filename (str): The path to the JSON file to be read.

    Returns:
    dict: The content of the JSON file as a dictionary.
    """
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)

def write_json_file(filename, data):
    """
    Write the given data to a JSON file.

    Parameters:
    filename (str): The path to the JSON file to be written.
    data (dict): The data to be written to the JSON file.
    """
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

class ScrapperLoadBalancer(AbstractLoadBalancer):
    """
    A load balancer for managing multiple scrapers using Tor proxies.
    Each process is assigned a unique Tor circuit to prevent blocking.
    """

    def __init__(self, **kwargs):
        """
        Initializes the ScrapperLoadBalancer with process and thread locks
        to ensure thread-safe file operations.
        """
        
        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)

        # file to store the task
        self.task_storage_file = kwargs.get("task_storage_file", TASK_STORAGE_DIR)

        # Initialize file locks for atomic operations
        self.init_locks()

        # Initialize parent class
        super().__init__(**kwargs)

    def init_locks(self):
        """
        Initialize file locks for thread safety.

        This function ensures the existence of the directory and file specified by `url_file_path`.
        It then creates file locks for both process-level and thread-level synchronization.
        If the directory does not exist, it is created.
        If the file does not exist, an empty file is created.

        Parameters:
        - None

        Returns:
        - None

        The function does not return any value. It initialize the instance attributes `_file_pLock` and `_file_tLock`.
        """
        try:
            # Lock to synchronize file access across multiple processes
            self._file_pLock = FileLock(f"{self.task_storage_file}.lock")
            
            # Lock to synchronize file access across multiple threads
            self._file_tLock = ThreadLock()
        except FileNotFoundError as e:
            self.logger.error(f"FILE NOT FOUND: {self.task_storage_file}: {e}")
            raise

    def get_max_processes(self):
        """
        Returns the maximum number of processes allowed.
        """
        return 9

    def get_max_threads_per_process(self):
        """
        Returns the maximum number of threads allowed per process.
        """
        return 1

    def save_tasks(self, tasks):
        """
        Saves the given tasks to a file in a thread-safe and process-safe manner.
        """
        self.logger.info("Saving tasks to the storage file.")
        with self._progress_pLock:  # Ensures only one process accesses the file at a time
            with self._progress_tLock:  # Ensures only one thread writes at a time
                try:
                    data = read_json_file(TASK_STORAGE_DIR)
                except FileNotFoundError:
                    self.logger.warning("Task storage file not found. Creating a new one.")
                    data = []

                data.append(tasks)
                write_json_file(TASK_STORAGE_DIR, data)
                self.logger.info("Tasks saved successfully.")

    def run(self, task):
        """
        Runs the scraper task and returns the results.
        """
        self.logger.info(f"Received task: {task}")

        # Save the task before execution
        self.save_tasks(task)

        query = task["result"]
        self.logger.info(f"Running scraper for query: {query}")

        # Execute the scraping operation
        results = self.run_scraper(query)

        response = {"task": query, "result": results}
        self.logger.info("Scraper execution completed.")
        return response
    
    def init_browser(self, id):
        """
        Initializes and configures a browser instance to route traffic through a Tor proxy.

        This function dynamically assigns a unique control and SOCKS port for each browser 
        instance based on the provided `id`. It then sets up the necessary proxy configuration 
        to ensure all HTTP and HTTPS requests go through the Tor network.

        Args:
            id (int): A unique identifier used to determine the control and SOCKS port numbers 
                    for the Tor proxy configuration.

        Returns:
            Browser: An initialized browser instance configured to use the Tor network with 
                    the specified proxy settings.

        Details:
            - The control port is set to `9150 + id`, allowing interaction with the Tor network.
            - The SOCKS proxy port is set to `9050 + id`, enabling the browser to route traffic 
            through Tor.
            - Proxy settings are applied to ensure all requests go through the appropriate SOCKS proxy.
            - The browser instance is created with a limit of 3 requests per identity to enhance privacy.

        Example:
            ```python
            browser = self.init_browser(id=1)
            ```
        """
        # Define ports for Tor proxy and control communication
        control_port = 9150 + id
        socks_port = 9050 + id

        # Proxy configuration for HTTP and HTTPS requests
        proxies = {
            "http": f"socks5h://127.0.0.1:{socks_port}",
            "https": f"socks5h://127.0.0.1:{socks_port}",
        }

        self.logger.info(
            f"Tor proxy setup: Control Port = {control_port}, SOCKS Port = {socks_port}"
        )

        # Initialize a browser instance with the configured Tor proxy
        browser = Browser(port=control_port, proxies=proxies, requests_per_identity=3)
        
        return browser

    def setup_process(self, id):
        """
        Sets up a process with a Tor proxy using a specific Tor circuit.
        Each process gets assigned unique control and SOCKS ports to avoid conflicts.
        """
        self.logger.info(f"Setting up process {id} with a unique Tor circuit.")

        # Initialize a browser for managing tor
        browser = self.init_browser(id)

        # Retrieve HTTP proxy for Google search requests
        proxy = browser.getProxy("http")
        self.logger.info("Browser and proxy setup complete.")

        # Configure the scraper with the initialized browser and proxy
        self.configure(browser=browser, proxy=proxy)
        self.logger.info(f"Process {id} setup complete.")
