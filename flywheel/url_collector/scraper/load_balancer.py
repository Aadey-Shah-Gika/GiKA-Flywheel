import json
from filelock import FileLock
from threading import Lock as ThreadLock
import logging

from submodules.browser import Browser
from flywheel.utils.load_balancer import AbstractLoadBalancer
from .constants import TASK_STORAGE_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Lock to synchronize file access across multiple processes
        self._progress_pLock = FileLock(f"{TASK_STORAGE_DIR}.lock")
        
        # Lock to synchronize access across multiple threads
        self._progress_tLock = ThreadLock()

        super().__init__(**kwargs)

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
        logging.info("Saving tasks to the storage file.")
        with self._progress_pLock:  # Ensures only one process accesses the file at a time
            with self._progress_tLock:  # Ensures only one thread writes at a time
                try:
                    data = read_json_file(TASK_STORAGE_DIR)
                except FileNotFoundError:
                    logging.warning("Task storage file not found. Creating a new one.")
                    data = []

                data.append(tasks)
                write_json_file(TASK_STORAGE_DIR, data)
                logging.info("Tasks saved successfully.")

    def run(self, task):
        """
        Runs the scraper task and returns the results.
        """
        logging.info(f"Received task: {task}")
        
        # Save the task before execution
        self.save_tasks(task)

        query = task["result"]
        logging.info(f"Running scraper for query: {query}")
        
        # Execute the scraping operation
        results = self.run_scraper(query)
        
        response = {"task": query, "result": results}
        logging.info("Scraper execution completed.")
        return response

    def setup_process(self, id):
        """
        Sets up a process with a Tor proxy using a specific Tor circuit.
        Each process gets assigned unique control and SOCKS ports to avoid conflicts.
        """
        logging.info(f"Setting up process {id} with a unique Tor circuit.")
        
        # Define ports for Tor proxy and control communication
        control_port = 9150 + id
        socks_port = 9050 + id

        # Proxy configuration for HTTP and HTTPS requests
        proxies = {
            "http": f"socks5h://127.0.0.1:{socks_port}",
            "https": f"socks5h://127.0.0.1:{socks_port}",
        }

        logging.info(f"Tor proxy setup: Control Port = {control_port}, SOCKS Port = {socks_port}")
        
        # Initialize a browser instance with the configured Tor proxy
        browser = Browser(port=control_port, proxies=proxies, requests_per_identity=3)
        
        # Retrieve an HTTP proxy for Google search requests
        proxy = browser.getProxy("http")
        logging.info("Browser and proxy setup complete.")
        
        # Configure the scraper with the initialized browser and proxy
        self.configure(browser=browser, proxy=proxy)
        logging.info(f"Process {id} setup complete.")
