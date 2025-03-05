import requests
import json
import time
import torch
import logging
from multiprocessing import Process, Queue
from urllib.parse import urlparse

from flywheel.utils.llm import Llm
from .constants import (
    DEFAULT_CRAWLER_WRAPPER_CONFIG as default_config,
    BLOCKED_DOMAINS,
    TASK_STORAGE_DIR,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
            "summarizing_instruction": kwargs.pop("summarizing_instruction", default_config.get("summarizing")),
            "urls_queue": Queue(),
        }
        self.configure(**config)

    def configure(self, **kwargs):
        """Update the parameters of the Crawler class dynamically."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def submit_task(self, results):
        """Submit a processed task to the submit_task_queue."""
        logging.info(f"Submitting task result: {results}")
        self.submit_task_queue.put(results)

    def save_tasks(self, tasks):
        """Save tasks to a JSON file for persistence."""
        try:
            with open(TASK_STORAGE_DIR, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []

        data.append(tasks)

        with open(TASK_STORAGE_DIR, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=4)
        logging.info("Tasks saved successfully.")

    def get_crawl_status(self, url):
        """Check the status of a crawled URL from the crawler service."""
        try:
            response = requests.post(self.urls["crawl_status"], json={"url": url})
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logging.error(f"Failed to fetch crawl status for {url}: {e}")
            return None

    def start_content_collector(self):
        """Worker process that checks for completed crawl tasks and summarizes content."""
        self.configure(llm=Llm(temperature=0.1))
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
                    summarized_content = self.summarize_content([crawl_status_response["content"]])
                    self.submit_task({"task": url, "result": summarized_content, "status": "SUCCESS"})
                    urls.remove(url)
                elif crawl_status_response["status"] == "FAILED":
                    self.submit_task({"task": url, "result": f"Failed to crawl {url}", "status": "FAILED"})
                    urls.remove(url)

    def summarize_content(self, content):
        """Summarizes given content using the LLM model."""
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        torch.cuda.empty_cache()
        return self._extract_content_from_response(response)

    def start_crawl_url(self, url):
        """Requests the crawler service to start crawling a given URL."""
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
        """Processes tasks from the queue, filtering and enqueuing URLs for crawling."""
        urls = task["result"]
        for url in urls:
            link = url["url"]
            domain = self.get_url_domain(link)
            if any(blocked in domain for blocked in BLOCKED_DOMAINS):
                self.submit_task({"task": link, "result": f"URL {link} is blocked.", "status": "BLOCKED"})
                continue

            if self.start_crawl_url(link):
                self.urls_queue.put(link)

    def setup_content_collector(self):
        """Sets up the content collector process."""
        content_collector_process = Process(target=self.start_content_collector)
        content_collector_process.start()
        logging.info("Content collector process started.")

    def start(self):
        """Main loop for the crawler worker to process tasks."""
        self.setup_content_collector()
        while True:
            task = self.task_queue.get()
            self.save_tasks(task)
            self.run(task)
