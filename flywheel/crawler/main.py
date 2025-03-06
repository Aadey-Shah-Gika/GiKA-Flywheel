import requests
import json
import time
import logging
from multiprocessing import Process, Queue
from urllib.parse import urlparse

from flywheel.utils.summary_generator import SummaryGenerator

from .constants import (
    DEFAULT_CRAWLER_WRAPPER_CONFIG as default_config,
    BLOCKED_DOMAINS,
    TASK_STORAGE_DIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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


class Crawler:
    """
    Crawler class that interacts with a crawler service to fetch web page content,
    process tasks, summarize content using LLM, and manage task submission.
    """

    def __init__(self, **kwargs):
        config = {
            "task_queue": kwargs["task_queue"],
            "submit_task_queue": kwargs["submit_task_queue"],
            "urls": kwargs.pop("urls", default_config.get("urls")),
            "summarizing_instruction": kwargs.pop(
                "summarizing_instruction", default_config.get("summarizing")
            ),
            "urls_queue": Queue(),
            "summary_generator": SummaryGenerator(),
        }
        self.configure(**config)

    def configure(self, **kwargs):
        """
        Update the parameters of the Crawler class dynamically.

        This method allows for dynamic configuration of the Crawler class by
        updating its attributes based on the provided keyword arguments.

        Parameters:
        - kwargs (dict): A dictionary containing the attribute names as keys and their new values as values.

        Returns:
        - None: This method does not return any value. It updates the attributes of the Crawler class.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)

    def submit_task(self, results):
        """
        Submit a processed task to the submit_task_queue for further processing.

        Parameters:
        - results (dict): A dictionary containing the result of a processed task. The dictionary should have the following keys:
            - 'task': The task identifier.
            - 'result': The result of the task.
            - 'status': The status of the task (e.g., 'SUCCESS', 'FAILED', 'BLOCKED').

        Returns:
        - None: This method does not return any value. It logs the task result and adds it to the `submit_task_queue`.
        """
        logging.info(f"Submitting task result: {results}")
        self.submit_task_queue.put(results)

    def save_tasks(self, tasks):
        """
        Save tasks to a JSON file for persistence.

        This function reads existing tasks from a JSON file, appends the provided tasks,
        and writes the updated data back to the file. If the file does not exist, it creates a new file.

        Parameters:
        - tasks (dict): A dictionary containing the task details to be saved.

        Returns:
        - None: This function does not return any value. It logs a success message upon successful saving.

        Raises:
        - FileNotFoundError: If the specified TASK_STORAGE_DIR file does not exist.
        - IOError: If there is an error writing to the file.
        """
        try:
            data = read_json_file(TASK_STORAGE_DIR)
        except FileNotFoundError:
            data = []

        data.append(tasks)

        write_json_file(TASK_STORAGE_DIR, data)

        logging.info("Tasks saved successfully.")

    def get_crawl_status(self, url):
        """
        Check the status of a crawled URL from the crawler service.

        This function sends a POST request to the crawler service's "crawl_status" endpoint
        with the provided URL as a JSON payload. It then waits for the response, checks for
        any exceptions, and returns the JSON response if successful. If an exception occurs,
        it logs the error and returns None.

        Parameters:
        url (str): The URL for which the crawl status needs to be checked.

        Returns:
        dict or None: The JSON response from the crawler service if the request is successful.
                       If an exception occurs, it returns None.
        """
        try:
            response = requests.post(self.urls["crawl_status"], json={"url": url})
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logging.error(f"Failed to fetch crawl status for {url}: {e}")
            return None

    def start_content_collector(self):
        """
        Worker process that checks for completed crawl tasks and summarizes content.

        This function is responsible for monitoring the completion of crawl tasks,
        fetching the crawled content, and summarizing it using the LLM model. It runs
        in a separate process and communicates with the main process through queues.

        Parameters:
        None

        Returns:
        None
        """
        urls = set()

        while True:
            time.sleep(5)
            while not self.urls_queue.empty():
                urls.add(self.urls_queue.get())

            for url in list(urls):
                crawl_status_response = self.get_crawl_status(url)
                if not crawl_status_response:
                    continue

                if crawl_status_response["status"] == "COMPLETED":
                    summarized_content = self.summarize_content(
                        [crawl_status_response["content"]]
                    )
                    self.submit_task(
                        {"task": url, "result": summarized_content, "status": "SUCCESS"}
                    )
                    urls.remove(url)
                elif crawl_status_response["status"] == "FAILED":
                    self.submit_task(
                        {
                            "task": url,
                            "result": f"Failed to crawl {url}",
                            "status": "FAILED",
                        }
                    )
                    urls.remove(url)

    def summarize_content(self, content):
        """
        Summarizes given content using the LLM model.

        Parameters:
        content (list): A list of strings representing the content to be summarized.
                        Each string in the list should contain a single paragraph of text.

        Returns:
        str: A string representing the summarized content.
             The summarized content is generated using the LLM model.
        """
        return self.summary_generator.summarize_content(content)

    def start_crawl_url(self, url):
        """
        Requests the crawler service to start crawling a given URL.

        This function sends a POST request to the crawler service's "crawl" endpoint
        with the provided URL as a JSON payload to add URL for crawling. It waits for the response, checks for
        any exceptions, and returns True if the add crawl request is successful. If an exception occurs,
        it logs the error and returns False.

        Parameters:
        url (str): The URL to be crawled. The URL should be a valid and accessible web address.

        Returns:
        bool: True if the crawler service successfully starts crawling the given URL.
              False if an exception occurs during the request.
        """
        try:
            response = requests.post(self.urls["crawl"], json={"url": url})
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to start crawling for {url}: {e}")
            return False

    @staticmethod
    def get_url_domain(url):
        """Extracts the domain from a URL."""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"

    def run(self, task):
        """
        Processes tasks from the queue, filtering and enqueuing URLs for crawling.

        Parameters:
        task (dict): A dictionary representing a task. The dictionary should have a 'result' key,
                     which contains a list of URLs to be processed. Each URL is represented as a dictionary
                     with a 'url' key.

        Returns:
        None: This function does not return any value. It processes the task, filters URLs,
              and enqueues URLs for crawling.
        """
        urls = task["result"]
        for url in urls:
            link = url["url"]
            domain = self.get_url_domain(link)
            if any(blocked in domain for blocked in BLOCKED_DOMAINS):
                self.submit_task(
                    {
                        "task": link,
                        "result": f"URL {link} is blocked.",
                        "status": "BLOCKED",
                    }
                )
                continue

            if self.start_crawl_url(link):
                self.urls_queue.put(link)

    def setup_content_collector(self):
        """
        Sets up the content collector process.

        This function creates a new process to run the `start_content_collector` method.
        The process is started immediately after creation. The function logs a message indicating
        that the content collector process has been started.

        Parameters:
        None

        Returns:
        None
        """
        content_collector_process = Process(target=self.start_content_collector)
        content_collector_process.start()
        logging.info("Content collector process started.")

    def start(self):
        """
        Main loop for the crawler worker to process tasks.

        This function acts as the main entry point for the crawler worker. It initializes the content collector process,
        then enters a loop to continuously fetch tasks from the task queue, save the tasks to a JSON file, and process the tasks.

        Parameters:
        None

        Returns:
        None
        """
        self.setup_content_collector()
        while True:
            task = self.task_queue.get()
            self.save_tasks(task)
            self.run(task)
