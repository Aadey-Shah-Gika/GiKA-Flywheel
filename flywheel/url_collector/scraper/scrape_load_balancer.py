import json
from filelock import FileLock
from threading import Lock as ThreadLock

from submodules.browser import Browser
from flywheel.utils.load_balancer import AbstractLoadBalancer


class ScrapperLoadBalancer(AbstractLoadBalancer):
    def __init__(self, **kwargs):

        self._progress_pLock = FileLock("./flywheel/data/queries/generated.json.lock")
        self._progress_tLock = ThreadLock()

        super().__init__(**kwargs)

    def get_max_processes(self):
        return 9

    def save_tasks(self, tasks):
        """Save the tasks to a file"""
        with self._progress_pLock:
            with self._progress_tLock:
                try:
                    with open(
                        "./flywheel/data/queries/generated.json", "r", encoding="utf-8"
                    ) as json_file:
                        data = json.load(json_file)
                except FileNotFoundError:
                    data = []

                data.append(tasks)

                with open(
                    "./flywheel/data/queries/generated.json", "w", encoding="utf-8"
                ) as json_file:
                    json.dump(data, json_file, indent=4)

    def get_max_threads_per_process(self):
        return 1

    def run(self, task):
        print("\n[DEBUG] -- QueryGeneratorLoadBalancer :: run | task:", task, "\n")

        self.save_tasks(task)

        query = task["result"]

        results = self.run_scraper(query)

        response = {"task": query, "result": results}

        print(f"\n[DEBUG] -- ScrapperLoadBalancer :: run | response: {response}\n")

        return response

    def setup_process(self, id):
        control_port = 9150 + id
        socks_port = 9050 + id
        proxies = {
            "http": f"socks5h://127.0.0.1:{socks_port}",
            "https": f"socks5h://127.0.0.1:{socks_port}",
        }

        browser = Browser(port=control_port, proxies=proxies, requests_per_identity=3)
        proxy = browser.getProxy("http")

        self.configure(browser=browser, proxy=proxy)
