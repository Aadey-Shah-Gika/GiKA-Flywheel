import json
import time
import math
from multiprocessing import Process, Manager, Queue
from threading import Thread

from flywheel import Crawler


def get_tasks():
    tasks = [
        [
            {
                "url": "https://www.youtube.com/watch?v=B26rvZlkR3Q",
                "title": "Lotus Biscoff Cookie Butter",
                "snippet": "Lotus Biscoff Cookie Butter",
            },
            
        ]
    ]
    return tasks


def start_crawler(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            # "manager": manager,
            "task_queue": task_queue,
            "submit_task_queue": submit_task_queue,
        }
        crawler = Crawler(**config)
        crawler.start()


def start_collector(task_queue):
    results = []
    while True:
        task = task_queue.get()
        results.append(task)
        print(f"[COLLECTOR] -- [TASK COMPLETED: {len(results)}] -- COLLECTED:", task)
        with open(
            "./tests/data/test_crawler/results.json",
            "w",
            encoding="utf8",
        ) as file:
            json.dump(results, file, indent=4)


def assign_task(tasks, task_queue, thread_id):
    for task in tasks:
        print(
            f"[ASSIGN] -- [THREAD_ID:{thread_id}] -- [SENDING TASK] :: CURRENT:", task
        )
        req = {"result": task}
        task_queue.put(req)


def test_url_collector():

    start_time = time.time()

    tasks = get_tasks()

    print("[INFO] -- [MAIN] -- tasks:", tasks)

    crawler_tq = Queue()
    generator_tq = Queue()

    crawler_process = Process(
        target=start_crawler,
        args=(
            crawler_tq,
            generator_tq,
        ),
    )
    crawler_process.start()

    collector_process = Process(
        target=start_collector,
        args=(generator_tq,),
    )
    collector_process.start()

    thread_count = 10

    threads = []

    num_tasks_per_thread = math.ceil(len(tasks) / thread_count)

    for i in range(thread_count):

        start = num_tasks_per_thread * i
        end = min(start + num_tasks_per_thread, len(tasks))

        if start > end:
            continue

        thread = Thread(target=assign_task, args=(tasks[start:end], crawler_tq, i))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    collector_process.join()

    end_time = time.time()

    print("TIME ELAPSED: ", end_time - start_time)
