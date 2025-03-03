import os
import json
import time
import math
from rich import print
from multiprocessing import Process, Manager, Queue
from threading import Thread

from flywheel import URLFilter


def setup_url_filter(task_queue, submit_task_queue):

    with Manager() as manager:
        url_filter = URLFilter(
            manager=manager, task_queue=task_queue, submit_task_queue=submit_task_queue
        )
        url_filter.start()


def setup_collector(task_queue, max_results):
    file_path = "./tests/data/load_balancer/test_start/collector_result.json"
    results = []
    
    results_collected = 0
    
    while results_collected < max_results:
        task = task_queue.get()
        print("[COLLECTOR] -- TASK COLLECTED -- task:", task)
        result = task['result']
        results.extend(result)
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(results, file, indent=4)
        
        results_collected += 1


def assign_tasks(tasks, task_queue, thread_id):
    print(f"DEBUG -- [THREAD_ID:{thread_id}] -- [STARTING]...")

    for task in tasks:
        print(f"DEBUG -- [THREAD_ID:{thread_id}] -- [ASSIGNING TASK] :: CURRENT:", task)
        request = {
            'result': [task]
        }
        task_queue.put(request)


def test_start():
    
    start_time = time.time()
    
    query_urls = [
        {
            "search": "Mercedes-Benz G-Class",
            "title": "Mercedes-Benz G-Class Price - Images, Colours & Reviews",
            "snippet": "Mercedes-Benz G-Class Price. Mercedes-Benz G-Class price for the base model starts at Rs. 2.55 Crore and the top model price goes upto Rs. 4.00 Crore (Avg. ex- ...",
        },
        {
            "search": "lakme lipstick shades",
            "title": "Buy Lakmé Lipstick Online At Best Price In India - LakméIndia",
            "snippet": "While those with neutral undertones have access to a wide spectrum of colours starting from pink, mauve to wine shades. You can buy online lipstick ...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Winter Fun Recipes",
            "snippet": "Warm up your winter with our Snow Day recipe assortment! Create lasting memories with the kids by preparing these fun, kid-tested...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Healthy and Delicious Winter Snacks for Kids",
            "snippet": "Warm up your winter with our Snow Day recipe assortment! Create lasting memories with the kids by preparing these fun, kid-tested...",
        },
        {
            "search": "winter snacks for kids",
            "title": "Healthy and Delicious Winter Snacks for Kids",
            "snippet": " From creative apple slices to savory idlis and warming poha, there are numerous ways to make winter snacking enjoyable and beneficial.",
        },
    ]

    task_queue = Queue()
    submit_task_queue = Queue()

    url_filtering_process = Process(
        target=setup_url_filter,
        args=(
            task_queue,
            submit_task_queue,
        ),
    )
    url_filtering_process.start()

    result_process = Process(target=setup_collector, args=(submit_task_queue, len(query_urls), ))
    result_process.start()

    print("DEBUG -- [MAIN] -- Starting child threads...")


    threads = []

    m = math.ceil(len(query_urls) / 10)

    for i in range(10):
        start = m * i
        end = min(start + m, len(query_urls))
        tasks = query_urls[start:end]  # Divide the tasks among the threads
        thread = Thread(target=assign_tasks, args=(tasks, task_queue, i))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    result_process.join()
    
    end_time = time.time()

    print("All tasks processed.")
    
    print("Time Elapsed:", end_time - start_time)
