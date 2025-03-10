import json
import logging
from multiprocessing import Process, Manager, Queue
from flywheel import QueryGenerator, GoogleSearchWebScraper, URLFilter, Crawler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def start_query_generator(task_queue: Queue, submit_task_queue: Queue):
    """
    Initializes and starts the QueryGenerator process.

    Parameters:
    task_queue (Queue): A multiprocessing Queue object used to pass tasks to the QueryGenerator process.
    submit_task_queue (Queue): A multiprocessing Queue object used to pass tasks from the QueryGenerator process to the next process in the pipeline.

    Returns:
    None
    """
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        logging.info("Starting Query Generator...")
        query_generator = QueryGenerator(**config)
        query_generator.start()

def start_search_engine(task_queue: Queue, submit_task_queue: Queue):
    """
    Initializes and starts the GoogleSearchWebScraper process.

    This function is responsible for creating and starting a new process that performs web scraping
    using the GoogleSearchWebScraper class. It initializes the necessary configuration for the
    GoogleSearchWebScraper instance and then starts the scraping process.

    Parameters:
    task_queue (Queue): A multiprocessing Queue object used to pass tasks to the GoogleSearchWebScraper process.
    submit_task_queue (Queue): A multiprocessing Queue object used to pass tasks from the GoogleSearchWebScraper process to the next process in the pipeline.

    Returns:
    None
    """
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        logging.info("Starting Search Engine...")
        scraper = GoogleSearchWebScraper(**config)
        scraper.start()

def start_url_filter(task_queue: Queue, submit_task_queue: Queue):
    """
    Initializes and starts the URLFilter process.

    The URLFilter process is responsible for filtering and processing URLs obtained from the previous process in the pipeline.
    It ensures that only relevant and valid URLs are passed to the next process for further crawling and data extraction.

    Parameters:
    task_queue (Queue): A multiprocessing Queue object used to receive tasks from the previous process in the pipeline.
    submit_task_queue (Queue): A multiprocessing Queue object used to pass processed tasks to the next process in the pipeline.

    Returns:
    None
    """
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        logging.info("Starting URL Filter...")
        url_filter = URLFilter(**config)
        url_filter.start()

def start_crawler(task_queue: Queue, submit_task_queue: Queue):
    """
    Initializes and starts the Crawler process.

    The Crawler process is responsible for crawling the web pages obtained from the URLFilter process.
    It extracts relevant data from the crawled pages and passes the extracted information to the next process in the pipeline.

    Parameters:
    task_queue (Queue): A multiprocessing Queue object used to receive tasks from the URLFilter process.

    submit_task_queue (Queue): A multiprocessing Queue object used to pass processed tasks to the next process in the pipeline.

    Returns:
    None
    """
    config = {
        "task_queue": task_queue,
        "submit_task_queue": submit_task_queue,
    }
    logging.info("Starting Crawler...")
    crawler = Crawler(**config)
    crawler.start()

def start_collector(task_queue: Queue):
    """
    Collects results from the pipeline and stores them in a JSON file.
    """
    results = []
    while True:
        task = task_queue.get()
        results.append(task)
        logging.info(f"[COLLECTOR] Task Completed: {len(results)} - Collected: {task}")
        
        with open("./tests/data/test_flywheel/results.json", "w", encoding="utf8") as json_file:
            json.dump(results, json_file, indent=4)

def initialize_flywheel(initial_document: str, task_queue: Queue):
    """
    Initializes the Flywheel pipeline with the first document and adds it to the task queue.

    This function takes an initial document and a task queue as input. It creates a task dictionary
    with the initial document as the result, logs the initialization message, and adds the task to the
    task queue. This function is intended to be called at the beginning of the Flywheel pipeline to
    kickstart the data processing.

    Parameters:
    initial_document (str): The initial document that will be processed by the Flywheel pipeline.
    task_queue (Queue): A multiprocessing Queue object used to pass tasks between different processes in the pipeline.

    Returns:
    None
    """
    task = {"result": initial_document}
    logging.info(f"Initializing Flywheel with task: {task}")
    task_queue.put(task)
    
def run_flywheel(initial_document: str):
    """
    Runs the Flywheel pipeline with multiple processes for each component.

    The Flywheel pipeline is a multi-process data processing system designed to extract and analyze data from the web.
    It consists of several components, each running in its own process, to perform tasks such as generating queries,
    scraping web pages, filtering URLs, crawling web pages, and collecting results.

    Parameters:
    initial_document (str): The initial document that will be processed by the Flywheel pipeline.
        This document can be any piece of information that will be used to generate initial queries.

    Returns:
    None
    """
    logging.info("Setting up task queues for Flywheel...")
    query_generator_tq = Queue()
    search_engine_tq = Queue()
    url_filter_tq = Queue()
    crawler_tq = Queue()
    collector_tq = Queue()

    processes = [
        Process(target=start_query_generator, args=(query_generator_tq, search_engine_tq)),
        Process(target=start_search_engine, args=(search_engine_tq, url_filter_tq)),
        Process(target=start_url_filter, args=(url_filter_tq, crawler_tq)),
        Process(target=start_crawler, args=(crawler_tq, collector_tq)),
        Process(target=start_collector, args=(collector_tq,)),
    ]

    # Start all processes
    for process in processes:
        process.start()
    
    # Initialize the Flywheel with the first document
    initialize_flywheel(initial_document, query_generator_tq)
