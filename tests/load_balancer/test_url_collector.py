import json
import time
import math
from multiprocessing import Process, Manager, Queue
from threading import Thread

from flywheel import GoogleSearchWebScraper, URLFilter

def start_search_engine(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            'manager': manager,
            'task_queue': task_queue,
            'submit_task_queue': submit_task_queue
        }
        scraper = GoogleSearchWebScraper(**config)
        scraper.start()

def start_url_filter(task_queue, submit_task_queue):
    with Manager() as manager:
        config = {
            'manager': manager,
            'task_queue': task_queue,
            'submit_task_queue': submit_task_queue
        }
        url_filter = URLFilter(**config)
        url_filter.start()

def start_collector(task_queue, max_results):
    results = []
    while len(results) < max_results:
        task = task_queue.get()
        results.append(task)
        print(f"[COLLECTOR] -- [TASK COMPLETED: {len(results)}] -- COLLECTED:", task)
        with open('./tests/data/load_balancer/test_url_collector/results.json', 'w', encoding='utf8') as file:
            json.dump(results, file, indent=4)

def assign_task(tasks, task_queue, thread_id):
    for task in tasks:
        print(f'[ASSIGN] -- [THREAD_ID:{thread_id}] -- [SENDING TASK] :: CURRENT:', task)
        req = {'result': task}
        task_queue.put(req)

def test_url_collector():
    
    start_time = time.time()
    
    search_engine_tq = Queue()
    url_filter_tq = Queue()
    crawler_tq = Queue()
    
    tasks = ['Swastiks Tomato Pickle Tomato Pickle', 'ingredients for lasagna', 'bombay shaving company face wash coffee']
    
    search_engine_process = Process(target=start_search_engine, args=(search_engine_tq, url_filter_tq,))
    search_engine_process.start()
    
    url_filter_process = Process(target=start_url_filter, args=(url_filter_tq, crawler_tq,))
    url_filter_process.start()
    
    collector_process = Process(target=start_collector, args=(crawler_tq, len(tasks),))
    collector_process.start()
    
    thread_count = 10
    
    threads = []
    
    num_tasks_per_thread = math.ceil(len(tasks) / thread_count)
    
    for i in range(thread_count):
        
        start = num_tasks_per_thread * i
        end = min(start + num_tasks_per_thread, len(tasks))
        
        if start > end:
            continue
        
        thread = Thread(target=assign_task, args=(tasks[start:end], search_engine_tq, i))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    collector_process.join()
    
    end_time = time.time()
    
    print("TIME ELAPSED: ", end_time - start_time)