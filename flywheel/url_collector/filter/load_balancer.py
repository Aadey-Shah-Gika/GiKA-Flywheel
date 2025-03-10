import json
import logging
from filelock import FileLock
from threading import Lock as ThreadLock

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
    Read a JSON file and return its contents.

    Parameters:
    filename (str): The path to the JSON file to be read.

    Returns:
    dict: The contents of the JSON file as a Python dictionary.

    Raises:
    FileNotFoundError: If the specified file does not exist.
    json.JSONDecodeError: If the file contains invalid JSON data.
    """
    try:
        with open(filename, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        logging.warning(f"File not found: {filename}. Returning empty data.")
        return {}
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {filename}: {e}")
        return {}


def write_json_file(filename, data):
    """
    Write the provided data to a JSON file.

    Parameters:
    filename (str): The path to the JSON file to be written. If the file does not exist, it will be created.
    data (dict): The Python dictionary to be written to the JSON file.

    Returns:
    None

    Raises:
    IOError: If there is an error writing to the file.
    """
    try:
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        logging.info(f"Successfully wrote data to {filename}.")
    except IOError as e:
        logging.error(f"Error writing to {filename}: {e}")

class FilterLoadBalancer(AbstractLoadBalancer):
    def __init__(self, **kwargs):
        
        # Create a logger for this class
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # file to store the task
        self.task_storage_file = kwargs.get('task_storage_file', TASK_STORAGE_DIR)
        
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
        Get the maximum number of processes that can be used concurrently.

        Returns:
        int: The maximum number of processes. In this case, it is set to 9.
        """
        return 9

    def get_max_threads_per_process(self):
        """
        Get the maximum number of threads that can be executed concurrently within a single process.

        Returns:
        int: The maximum number of threads. In this case, it is set to 9.
        """
        return 9

    def save_tasks(self, tasks):
        """
        Save the tasks to a file.

        This function is responsible for writing the provided tasks to a JSON file. It uses locks to ensure that concurrent processes and threads do not interfere with each other while accessing the file.

        Parameters:
        tasks (dict): A dictionary containing the task details to be saved.

        Returns:
        None

        The function performs the following steps:
        1. Acquires a file lock to ensure exclusive access to the task storage file.
        2. Acquires a thread lock to prevent race conditions within a single process.
        3. Attempts to read the existing tasks from the file. If the file does not exist, an empty list is used.
        4. Appends the provided tasks to the existing data.
        5. Writes the updated data back to the file using the `write_json_file` function.
        """
        self.logger.info("Saving tasks...")
        with self._progress_pLock:
            with self._progress_tLock:
                try:
                    data = read_json_file(TASK_STORAGE_DIR)
                except Exception as e:
                    self.logger.error(f"Error reading task storage file: {e}")
                    data = []

                data.append(tasks)

                try:
                    write_json_file(TASK_STORAGE_DIR, data)
                except Exception as e:
                    self.logger.error(f"Error writing task storage file: {e}")

    def run(self, task):
        """
        Execute the main logic of the filter load balancer.

        Parameters:
        task (dict): A dictionary containing the task details. The dictionary should have a 'result' key, which contains the URLs to be processed.

        Returns:
        dict: A dictionary containing the original task details and the filtered results. The dictionary has the following structure:
            {
                "task": urls,
                "result": results,
            }
            - urls: The original URLs provided in the task.
            - results: The filtered results obtained after processing the URLs.

        The function performs the following steps:
        1. Save the task details to a file using the `save_tasks` method.
        2. Extract the URLs from the task details.
        3. Format the URLs into a specific structure.
        4. Filter the URLs using the `filter_urls` method.
        5. Create a response dictionary containing the original task details and the filtered results.
        6. Return the response dictionary.
        """
        self.logger.info("Running task filtering process...")

        try:
            self.save_tasks(task)
            urls = task.get("result", [])

            if not urls:
                self.logger.warning("No URLs found in task result.")
                return {"task": urls, "result": []}

            formatted_urls = [
                {
                    "url": url["url"],
                    "title": url["title"],
                    "snippet": url.get("description", ""),
                }
                for url in urls
                if "url" in url and "title" in url
            ]

            results = self.filter_urls(formatted_urls)

            response = {
                "task": urls,
                "result": results,
            }

            self.logger.info("Task processing completed successfully.")
            return response
        except Exception as e:
            self.logger.error(f"Unexpected error in run method: {e}")
            return {"task": task, "result": []}
