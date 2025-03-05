from multiprocessing import Process, Manager, Queue
import json
import math
import time

from flywheel import GoogleSearchWebScraper


def search_engine_worker(task_queue, submit_queue):
    with Manager() as manager:
        scraper = GoogleSearchWebScraper(
            manager=manager, task_queue=task_queue, submit_task_queue=submit_queue
        )
        scraper.start()


def collect_results_worker(task_queue, max_tasks):
    results = []
    while len(results) < max_tasks:
        task = task_queue.get()
        results.append(task["data"])
        print("[INFO] -- [COLLECTOR] :: COMPLETED:", len(results))
        with open(
            "./tests/data/test_search_engine/results.json", "w", encoding="utf-8"
        ) as file:
            json.dump(results, file, indent=4)


def enqueue_task(queries, task_queue, thread_id):
    for query in queries:
        print(
            f"[ENQUEUE] -- [THREAD_ID:{thread_id}] -- [SENDING TASK] :: CURRENT:", query
        )
        task_queue.put({"args": {"query": query}})


def get_queries():
    queries = []
    with open("./tests/queries.json", "r", encoding="utf-8") as query_file:
        data = json.load(query_file)
        for results in data:
            queries.append(results["Title"])
    return queries


def test_search_engine():

    print("\n")

    start_time = time.time()

    task_queue = Queue(maxsize=30)
    submit_queue = Queue(maxsize=30)

    search_engine_process = Process(
        target=search_engine_worker,
        args=(
            task_queue,
            submit_queue,
        ),
    )
    search_engine_process.start()

    queries = get_queries()

    num_enqueue_threads = 10

    queries_per_thread = math.ceil(len(queries) / num_enqueue_threads)

    print("[MAIN] -- [STATE] -- total queries:", len(queries))
    print("[MAIN] -- [STATE] -- num_enqueue_threads:", num_enqueue_threads)
    print("[MAIN] -- [STATE] -- queries per thread:", queries_per_thread)
    print("[MAIN] -- [STATE] -- num_enqueue_threads", num_enqueue_threads)

    enqueue_threads = []
    for num in range(num_enqueue_threads):
        start = num * queries_per_thread
        end = min(start + queries_per_thread, len(queries))
        cur_queries = queries[start:end]
        thread = Process(
            target=enqueue_task,
            args=(
                cur_queries,
                task_queue,
                num,
            ),
        )
        thread.start()
        enqueue_threads.append(thread)

    result_collector_process = Process(
        target=collect_results_worker, args=(submit_queue, len(queries))
    )
    result_collector_process.start()

    result_collector_process.join()

    end_time = time.time()

    print("[MAIN] -- [STATS] :: TIME ELAPSED:", end_time - start_time)
