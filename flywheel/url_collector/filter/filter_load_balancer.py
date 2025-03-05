import json

from filelock import FileLock
from threading import Lock as ThreadLock

from flywheel.utils.load_balancer import AbstractLoadBalancer

class FilterLoadBalancer(AbstractLoadBalancer):
    def __init__(self, **kwargs):
        
        self._progress_pLock = FileLock("./flywheel/data/urls/scraped.json.lock")
        self._progress_tLock = ThreadLock()
        
        super().__init__(**kwargs)
        
    def get_max_processes(self):
        return 9
    
    def get_max_threads_per_process(self):
        return 1
    
    def save_tasks(self, tasks):
        """Save the tasks to a file"""
        with self._progress_pLock:
            with self._progress_tLock:
                try:
                    with open("./flywheel/data/urls/scraped.json", "r", encoding="utf-8") as json_file:
                        data = json.load(json_file)
                except FileNotFoundError:
                    data = []
                
                data.append(tasks)
                
                with open("./flywheel/data/urls/scraped.json", 'w', encoding="utf-8") as json_file:
                    json.dump(data, json_file, indent=4)
    
    def run(self, task):
        
        print("\n[DEBUG] -- FilterLoadBalancer :: run | task:", task, "\n")
        
        self.save_tasks(task)
        
        urls = task['result']
        
        # TODO: Fix this description and snippet key conflicts
        # ! Temporary Solution
        formatted_url = [{'url': url['url'], 'title': url['title'], 'snippet': url['description']} for url in urls]
            
        results = self.filter_urls(formatted_url)
        
        response = {
            "task": urls,
            "result": results,
        }
        
        print(f"\n[DEBUG] -- FilterLoadBalancer :: run | results: {response}\n")
        
        return response