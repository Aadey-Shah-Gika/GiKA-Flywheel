import requests
import json
import time
import torch
from multiprocessing import Process, Queue
from urllib.parse import urlparse

from flywheel.utils.llm import Llm
from .constants import DEFAULT_CRAWLER_WRAPPER_CONFIG as default_config, BLOCKED_DOMAINS


# Crawling and Parsing URLs' content from crawler service
class Crawler:
    def __init__(self, **kwargs):
        """Initialize a new CrawlerWrapper with the given arguments"""

        config = {
            "task_queue": kwargs["task_queue"],
            "submit_task_queue": kwargs["submit_task_queue"],
            "urls": kwargs.pop(
                "urls", default_config.get("urls")
            ),  # urls of crawler service
            "summarizing_instruction": kwargs.pop(
                "summarizing_instruction", default_config.get("summarizing")
            ),  # Llm instructions to summarize the content of crawled web page
            "urls_queue": Queue(),
        }

        # Set the class variables to config
        self.configure(**config)

    def configure(self, **kwargs):
        """Update the parameters of CrawlerWrapper."""
        for key, value in kwargs.items():
            setattr(self, key, value)

    def submit_task(self, results, submit_task_queue):
        """Submit a task to the submit_task_queue"""
        # results schema : {'task': url_info, 'result': summarized_crawl_content}
        submit_task_queue.put(results)

    def save_tasks(self, tasks):
        """Save the tasks to a file"""
        try:
            with open(
                "./flywheel/data/urls/filtered_urls.json", "r", encoding="utf-8"
            ) as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = []

        data.append(tasks)

        with open(
            "./flywheel/data/urls/filtered_urls.json", "w", encoding="utf-8"
        ) as json_file:
            json.dump(data, json_file, indent=4)
            

    def get_crawl_status(self, url):
        """Check if the crawler has completed crawling the given url."""
        try:
            payload = {"url": url}
            response = requests.post(self.urls["crawl_status"], json=payload)
        except requests.exceptions.RequestException as e:
            print(
                "[ERROR] -- [CrawlerWrapper.crawl_url] -- Failed to connect to server : ",
                str(e),
            )
            return None

        # check the status code of the response
        if response.status_code >= 400:
            # log the response for debugging
            print(response.text)

            print("[ERROR] -- [CrawlerWrapper.crawl_url] -- Failed to get crawl status")
            return None

        # jsonify the response
        try:
            response = response.json()
        except json.JSONDecodeError:
            print(
                "[ERROR] -- [CrawlerWrapper.crawl_url] -- Failed to parse JSON response : response :",
                response.text,
            )
            return None

        # check the crawl status
        try:
            crawl_status = response["status"]

            print(
                f"[INFO] -- [CRAWLER] -- [CrawlerWrapper.crawl_url] -- url : {url} ::: STATUS: {crawl_status}"
            )

            return response

        except KeyError or ValueError as e:
            print("[ERROR] -- [CrawlerWrapper.crawl_url] -- ", str(e))
            print(
                "[ERROR] -- [CrawlerWrapper.crawl_url] -- Invalid crawl_status Response : response :",
                response,
            )
            return None

    def start_content_collector(self, urls_queue, submit_task_queue):
        """Setup content collecting worker. checks if crawler has completed crawling any url?"""

        print(
            "[INFO] -- [CRAWLER] -- [CrawlerWrapper.start_content_collect] -- Initializing LLM FOR SUMMARIZING CONTENT"
        )

        self.configure(llm=Llm(temperature=0.1))

        print(
            "[INFO] -- [CRAWLER] -- [CrawlerWrapper.start_content_collect] -- LLM Initialized Successfully"
        )

        urls = set()
        while True:
            time.sleep(5)
            while not urls_queue.empty():
                urls.add(urls_queue.get())

            check_urls = list(urls)

            print(
                "[INFO] -- [CRAWLER] -- [CrawlerWrapper.start_content_collect] -- Remaining URLS:",
                urls,
            )

            for url in check_urls:
                crawl_status_response = self.get_crawl_status(url)

                if (
                    crawl_status_response
                    and crawl_status_response["status"] == "COMPLETED"
                ):
                    raw_content = crawl_status_response["content"]
                    print("[INFO] -- [CRAWLER] -- [CrawlerWrapper.start_content_collect] -- raw content:", raw_content)
                    summarized_content = self.summarize_content([raw_content])
                    response = {
                        "task": url,
                        "result": summarized_content,
                        "status": "SUCCESS",
                    }
                    self.submit_task(response, submit_task_queue)
                    urls.remove(url)
                elif crawl_status_response["status"] == "FAILED":
                    response = {
                        "task": url,
                        "result": f"Failed to crawl and summarize content for url: {url}",
                        "status": "FAILED",
                    }
                    self.submit_task(response, submit_task_queue)
                    urls.remove(url)

    def _generate_user_context(self, content):
        """Creates a user instruction based on the provided content with comprehensive guidelines."""
        return f"Summarize the following text in a brief paragraph:{content}"

    def build_prompt(self, context):
        system_prompt = {"role": "system", "content": self.summarizing_instruction}
        user_prompt = {"role": "user", "content": self._generate_user_context(context)}

        return [system_prompt, user_prompt]

    def build_llm_message(self, content):
        """Constructs the message structure for the LLM."""
        llm_message = [self.build_prompt(context) for context in content]
        return llm_message

    def _extract_content_from_response(self, responses):
        """Extracts meaningful content from the LLM response."""

        # print("DEBUG -- [QueryGenerator._extract_content_from_response] -- response:", response)

        extracted_response = []
        for response in responses:
            content = response[-1]["content"]
            extracted_response.append(
                content.split("Here is the summary of the passage:")[-1].strip()
            )

        return extracted_response

    def get_formatted_response_from_llm(self, content):
        """Fetches and formats the LLM response."""
        messages = self.build_llm_message(content)
        response = self.llm.get_response(query=messages)
        return self._extract_content_from_response(response)

    def summarize_content(self, content):
        """Summarize the given content[type: list(string)]"""

        responses = self.get_formatted_response_from_llm(content)
        torch.cuda.empty_cache()

        return responses

    def start_crawl_url(self, url):
        """Get contents of the given URL from the crawler service"""

        # Prepare the payload for the crawl request
        payload = {"url": url}

        # send the crawl request to the server
        response = requests.post(self.urls["crawl"], json=payload)

        # check if the request was successful
        if response.status_code == 200:
            return True
        else:
            print(
                f"[ERROR] -- [CRAWLER] -- [Crawler.crawl_url] -- Failed to add {url} for crawling"
            )
            print(f"[ERROR] -- [Crawler.crawl_url] -- response:", response.text)
            return False

    @staticmethod
    def get_url_domain(url):
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}/"
        
    def run(self, task):
        """Process tasks and submit them to the next module"""
        # task json schema: {'task': list_of_searched_urls, 'result': list_of_filtered_urls}  --> task is the input and result is the output

        # get filtered urls
        urls = task["result"]

        for url in urls:
            # url json schema: {'url': src_link, 'title': google_search_title, 'snippet': 'google_search_snippet'}

            link = url["url"]
            domain = self.get_url_domain(link)
            
            blocked = False
            
            for blocked_domain in BLOCKED_DOMAINS:
                if blocked_domain in domain:
                    response = {
                        "task": link,
                        "result": f"URL {link} is blocked by {blocked_domain}",
                        "status": "BLOCKED",
                    }
                    self.submit_task(response, self.submit_task_queue)
                    blocked = True
                    
            if blocked:
                continue
            
            # enqueue crawling the source link at crawler_service
            if self.start_crawl_url(url["url"]):
                # enqueue the crawled content for summarization at summarizer_service
                self.urls_queue.put(url["url"])
            else:
                print(
                    f"[ERROR] -- [CRAWLER] -- [Crawler.run] -- Failed to enqueue {url['url']} for crawling"
                )

    def setup_content_collector(self):
        urls_queue = self.urls_queue
        submit_task_queue = self.submit_task_queue
        print(
            "[INFO] -- [CRAWLER] -- [Crawler.setup_content_collector] -- urls_queue:",
            urls_queue,
        )
        content_collector_process = Process(
            target=self.start_content_collector,
            args=(
                urls_queue,
                submit_task_queue,
            ),
        )
        content_collector_process.start()

    def start(self):
        """Start the crawler worker to run the assigned tasks"""
        self.setup_content_collector()
        print("[INFO] -- [CRAWLER] -- [Crawler.start] -- CONTENT_COLLECTOR_SETUP DONE")
        while True:
            # get task(urls) from the task_queue
            print(
                "[INFO] -- [CRAWLER] -- [Crawler.start] -- CONTENT_COLLECTOR_SETUP DONE"
            )

            task = self.task_queue.get()

            print(
                "[INFO] -- [CRAWLER] -- [Crawler.setup_content_collector] | task:", task
            )

            print(
                "[INFO] -- [CRAWLER] -- [Crawler.setup_content_collector] | SAVING TASKS"
            )
            self.save_tasks(task)
            print(
                "[INFO] -- [CRAWLER] -- [Crawler.setup_content_collector] | TASKS SAVED"
            )

            # run tasks(urls) and submit them to next module as a task gets completed
            self.run(task)
