import json
from multiprocessing import Process, Manager, Queue

from flywheel import QueryGenerator, GoogleSearchWebScraper, URLFilter, Crawler

INITIAL_DOCUMENT = [
    "Both Hathi Masala and Zoff Foods have their strengths, and the better choice depends on what you’re looking for in spices. Hathi Masala is a well-established brand with a strong reputation for its traditional spice blends. If you prefer time-tested flavors and a brand that has been around for years, this might be the better option for you. Zoff Foods, on the other hand, focuses on freshness and quality using cold grinding technology, which helps retain the natural oils and flavors of the spices. If you want something fresher and processed with modern techniques, Zoff might be a good pick. At the end of the day, both spice brands offer good quality, and it comes down to personal preference. If you want a deeper comparison, this blog breaks it down in detail: Hathi Masala vs Zoff Foods"
]


def start_query_generator(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        query_generator = QueryGenerator(**config)
        query_generator.start()


def start_search_engine(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        scraper = GoogleSearchWebScraper(**config)
        scraper.start()


def start_url_filter(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        url_filter = URLFilter(**config)
        url_filter.start()


def start_crawler(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            # "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        crawler = Crawler(**config)
        crawler.start()


def start_collector(
    task_queue,
):
    results = []
    while True:
        task = task_queue.get()
        results.append(task)
        print(f"[COLLECTOR] -- [TASK COMPLETED: {len(results)}] -- COLLECTED:", task)

        with open(
            "./tests/data/test_flywheel/results.json", "w", encoding="utf8"
        ) as json_file:
            json.dump(results, json_file, indent=4)


def initialize_flywheel(initial_document, task_queue):
    task = {"result": initial_document}
    print("\n\ninitializing flywheel with task:", task)
    task_queue.put(task)


def test_url_collector():

    query_generator_tq = Queue()
    search_engine_tq = Queue()
    url_filter_tq = Queue()
    crawler_tq = Queue()

    collector_tq = Queue()

    query_generator_process = Process(
        target=start_query_generator,
        args=(
            query_generator_tq,
            search_engine_tq,
        ),
    )
    query_generator_process.start()

    search_engine_process = Process(
        target=start_search_engine,
        args=(
            search_engine_tq,
            url_filter_tq,
        ),
    )
    search_engine_process.start()

    url_filter_process = Process(
        target=start_url_filter,
        args=(
            url_filter_tq,
            crawler_tq,
        ),
    )
    url_filter_process.start()

    crawler_process = Process(
        target=start_crawler,
        args=(
            crawler_tq,
            collector_tq,
        ),
    )
    crawler_process.start()

    collector_process = Process(
        target=start_collector,
        args=(collector_tq,),
    )
    collector_process.start()

    initialize_flywheel(INITIAL_DOCUMENT, query_generator_tq)
