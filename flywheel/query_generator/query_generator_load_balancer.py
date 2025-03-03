import os
import time
from .constants import DEFAULT_LOAD_BALANCER_CONFIG as default_config

class QueryGeneratorLoadBalancer:
    def __init__(self, **kwargs):
        self.manager = kwargs['manager']
        self.task_queue = kwargs['task_queue']
        self.submit_task_queue = kwargs['submit_task_queue']
        
        if 'max_tasks_once' in kwargs:
            self.max_tasks_once = kwargs['max_tasks_once']
        else:
            self.max_tasks_once = default_config['max_tasks_once']
        
    def start(self):
        # ! Remove after testing
        time.sleep(5)
        while True:
            raw_tasks = self.task_queue.get()
            tasks = raw_tasks['result']
            
            
            while len(tasks) < self.max_tasks_once and not self.task_queue.empty():
                extra_tasks = self.task_queue.get()
                tasks.extend(extra_tasks['result'])
            
            response = self.run(tasks)
            self.submit_task(response)
    
    def run(self, task):
        
        print("\n[DEBUG] -- QueryGeneratorLoadBalancer :: run | task:", task, "\n")
        
        results = self.generate_queries(task)
        
        response = {
            "task": task,
            "result": results
        }
        
        print(f"\n[DEBUG] -- QueryGeneratorLoadBalancer :: run | response: {response}\n")
        
        return response
    
    def submit_task(self, task):
        """Submit a task to the next load balancer."""
        print(f"[INFO] -- [PID:{os.getpid()}] -- [LOAD_BALANCER::submit_task]")
        
        for i in range(len(task['result'])):
            queries = task['result'][i]
            
            for query in queries:
                print(f"\n[DEBUG] -- QueryGeneratorLoadBalancer :: submit_task | query: {query}\n")
                
                cur_task = {
                    "task": task['task'][i],
                    "result": query
                }
                
                self.submit_task_queue.put(cur_task)