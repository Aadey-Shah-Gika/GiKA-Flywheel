from abc import ABC, abstractmethod
from multiprocessing import Process
from threading import Thread
import os


class AbstractLoadBalancer(ABC):
    def __init__(self, **kwargs):
        
        manager = kwargs["manager"]
        task_queue = kwargs["task_queue"]
        submit_task_queue = kwargs["submit_task_queue"]
        
        print("DEBUG -------------------------------- ENTERED ABS_LB -- INIT")
        
        self.max_processes = self.get_max_processes()
        self.max_threads_per_process = self.get_max_threads_per_process()
        self.manager = manager
        self.num_processes = 0
        self.task_queue = task_queue
        self.potential_processes = self.manager.Queue()  # Store thread-related data
        self.task_queues = self.manager.dict()
        self.submit_task_queue = submit_task_queue

    @abstractmethod
    def get_max_processes(self) -> int:
        pass

    @abstractmethod
    def get_max_threads_per_process(self) -> int:
        pass

    @abstractmethod
    def run(self, task):
        pass

    def start(self):
        """Distribute tasks using priority scheduling. (Note: For equal priority, round-robin is used)"""

        while True:
            task = self.task_queue.get()
            pid = None
            
            if self.num_processes < self.max_processes:
                self.create_process()
            
            pid = self.potential_processes.get()
            self.assign_task_to_process(pid, task)

    def create_process(self):
        """Spawn a new process with a worker thread manager."""

        self.num_processes += 1
        
        proc = Process(target=self.process_worker, args=(self.num_processes,))
        proc.start()
        
        self.task_queues[proc.pid] = self.manager.Queue()
        for _ in range(self.max_threads_per_process):
            self.potential_processes.put(proc.pid)
            
    def assign_task_to_process(self, pid, task):
        """Assign task to an available thread or create a new one if limits allow."""
        self.task_queues[pid].put(task)  # Assign task to thread using Queue

    def assign_task_to_thread(self, task):
        """Assign task to an available thread or create a new one if limits allow."""
        thread = Thread(target=self._thread_worker, args=(task,))
        thread.start()

    def process_worker(self, id): # id here is one-based index
        """Worker process that waits for tasks."""
        
        pid = os.getpid()
        
        self.setup_process(id)
        
        while pid not in self.task_queues:
            pass
        
        child_process_task_queue = self.task_queues[pid]

        while True:
            print(f"[INFO] -- [PID:{pid}] -- [LOAD_BALANCER::process_worker] ===> STATUS : WAITING FOR TASK")
            task = child_process_task_queue.get()
            self.assign_task_to_thread(task)

    def setup_process(self, id):
        """This must be implemented in subclass for setting up process environment"""
        pass

    def _thread_worker(self, task):
        """Thread execution wrapper."""
        pid = os.getpid()
        print(f"[INFO] -- [PID:{pid}] -- [LOAD_BALANCER::_thread_worker] ===> task:", task)
        result = self.run(task)
        self.submit_task(result)  # Submit result back to manager
        self.potential_processes.put(os.getpid())
    
    def submit_task(self, task):
        """Submit a task to the next load balancer."""
        print(f"[INFO] -- [PID:{os.getpid()}] -- [LOAD_BALANCER::submit_task]")
        self.submit_task_queue.put(task)
