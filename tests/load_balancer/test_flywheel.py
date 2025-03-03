import json
import time
import math
from multiprocessing import Process, Manager, Queue
from threading import Thread

from flywheel import QueryGenerator, GoogleSearchWebScraper, URLFilter

RESULT_FILE_PATH = './tests/data/load_balancer/test_flywheel/results.json'
INITIAL_DOCUMENT = [
        [
            "This delicious Biscoff Cheesecake recipe features a buttery Biscoff cookie crust, and a creamy Biscoff cheesecake filling. It’s topped with melted Biscoff cookie butter, and Biscoff cookie crumbs, which makes for a stunning and tasty dessert"
        ],
        [
            "This delicious Biscoff Cheesecake recipe features a buttery Biscoff cookie crust, and a creamy Biscoff cheesecake filling. It’s topped with melted Biscoff cookie butter, and Biscoff cookie crumbs, which makes for a stunning and tasty dessert",
            "Mount Everest is the highest mountain in the world. It is located in the Himalayas on the border between Nepal and the Tibet Autonomous Region of China. The mountain's peak reaches an elevation of 8,848 meters (29,029 feet) above sea level.",
            "At its core, a co ord set for women (short for 'coordinated') is a two-piece outfit designed to be worn together, creating a harmonious and, well, coordinated look. These sets can range from casual ensembles perfect for a day out to more formal attire suitable for the office or a night on the town.",
            "Lightweight Gaming Mouse -The Ant Esports GM700 Wireless gaming mouse features a honeycomb shell that weighs only 90 grams, which is light but still durable. The honeycomb shell helps reduce weight to protect your wrist when you are gaming or working.",
            "The Wakeup Mushy Sofa provides a comfortable and supportive seating experience with its plush cushions and sturdy frame | Plush and comfortable: The Wakeup Mushy Sofa provides a luxurious seating experience with its soft and plush cushions, perfect for relaxation and lounging, Soft and supple upholstery for added luxury.",
            "The Mercedes-Benz G-Wagon is a luxury off-road SUV that combines rugged capability with high-end sophistication. Known for its iconic boxy design, powerful engine options, and premium interior, the G-Wagon delivers an unparalleled blend of performance, durability, and prestige. Whether tackling tough terrain or cruising in the city, it offers an elite driving experience with advanced technology and superior craftsmanship.",
        ],
    ]

def start_query_generator():
    with Manager() as manager:
        config = {
            "manager": manager,
            "query_queue": Queue(),
            "submit_task_queue": Queue(),
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


def start_collector(task_queue, max_results):
    results = []
    while len(results) < max_results:
        task = task_queue.get()
        results.append(task)
        print(f"[COLLECTOR] -- [TASK COMPLETED: {len(results)}] -- COLLECTED:", task)
        with open(
            RESULT_FILE_PATH,
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

    query_generator_tq = Queue()
    search_engine_tq = Queue()
    url_filter_tq = Queue()
    crawler_tq = Queue()

    tasks = INITIAL_DOCUMENT

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

    collector_process = Process(
        target=start_collector,
        args=(
            crawler_tq,
            len(tasks),
        ),
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

        thread = Thread(
            target=assign_task, args=(tasks[start:end], query_generator_tq, i)
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    collector_process.join()

    end_time = time.time()

    print("TIME ELAPSED: ", end_time - start_time)
