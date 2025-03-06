from abc import ABC, abstractmethod
from multiprocessing import Process, Manager
from threading import Thread
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AbstractLoadBalancer(ABC):
    def __init__(self, **kwargs):
        """
        Initialize the load balancer with the provided parameters.

        Parameters:
        - manager (multiprocessing.Manager): A manager object for inter-process communication.
        - task_queue (multiprocessing.Queue): A queue for distributing tasks among processes.
        - submit_task_queue (multiprocessing.Queue): A queue for submitting completed tasks.

        Returns:
        None
        """
        manager = kwargs["manager"]
        task_queue = kwargs["task_queue"]
        submit_task_queue = kwargs["submit_task_queue"]

        self.max_processes = self.get_max_processes()
        self.max_threads_per_process = self.get_max_threads_per_process()
        self.manager = manager
        self.num_processes = 0  # Tracks the number of active processes
        self.task_queue = task_queue
        self.potential_processes = self.manager.Queue()  # Queue for assigning task to partially or non occupied process
        self.task_queues = self.manager.dict()  # Dictionary to hold process-specific task queues
        self.submit_task_queue = submit_task_queue # Queue for submitting completed tasks

        logging.info("Load balancer initialized with max_processes=%d and max_threads_per_process=%d", 
                     self.max_processes, self.max_threads_per_process)

    @abstractmethod
    def get_max_processes(self) -> int:
        """
        Retrieve the maximum number of processes that can be spawned.

        This method is intended to be overridden by subclasses to define the desired maximum number of processes.
        The load balancer will spawn new processes up to this limit to distribute tasks.

        Returns:
        int: The maximum number of processes that can be spawned.
        """
        pass

    @abstractmethod
    def get_max_threads_per_process(self) -> int:
        """
        Abstract method to retrieve the maximum number of threads that can be spawned per process.

        This method is intended to be overridden by subclasses to define the desired maximum number of threads per process.
        The load balancer will create a thread pool for each process up to this limit to distribute tasks.

        Parameters:
        None

        Returns:
        int: The maximum number of threads that can be spawned per process.
        """
        pass

    @abstractmethod
    def run(self, task):
        """
        Execute a task and return the result.

        This method is intended to be overridden by subclasses to define the specific logic for executing tasks.
        The load balancer will call this method for each task that needs to be processed.

        Parameters:
        - task (any): The task to be executed. The type of the task can vary depending on the specific requirements of the load balancer.

        Returns:
        any: The result of executing the task. The type of the result can vary depending on the specific requirements of the load balancer.
        """
        pass

    def start(self):
        """
        Start the load balancer to distribute tasks to child processes with FCFS enabled.

        This function continuously monitors the task queue for new tasks. When a new task is received,
        it checks if the number of active processes is less than the maximum allowed processes. If so,
        a new process is spawned. Then, it retrieves the next available process from the potential processes queue
        and assigns the task to that process.

        Parameters:
        None

        Returns:
        None
        """
        logging.info("Load balancer started")

        while True:
            task = self.task_queue.get()  # Wait for a new task
            logging.info("Received task: %s", str(task))

            # Check if we need to spawn a new process
            if self.num_processes < self.max_processes:
                self.create_process()

            # Get the next available process
            pid = self.potential_processes.get()
            logging.info("Assigning task to process with PID: %d", pid)
            self.assign_task_to_process(pid, task)

    def create_process(self):
        """
        Create a new worker process and assign it a task queue.

        This function spawns a new worker process using the multiprocessing module.
        It also creates a task queue for the new process and stores it to the task_queues dictionary.
        The PID of the new process is added to the potential_processes queue to indicate that it is available for task assignment.

        Parameters:
        None

        Returns:
        None
        """
        self.num_processes += 1
        proc = Process(target=self.process_worker, args=(self.num_processes,))
        proc.start()

        logging.info("Spawned new process with PID: %d", proc.pid)

        # Create a queue for the new process and store its PID in the potential queue
        self.task_queues[proc.pid] = self.manager.Queue()
        
        # Add the {max_threads_per_process} slots to the potential queue for processing new tasks
        for _ in range(self.max_threads_per_process):
            self.potential_processes.put(proc.pid)

    def assign_task_to_process(self, pid, task):
        """
        Assign a task to the appropriate process's queue.

        This function takes a process ID (pid) and a task as input parameters.
        It retrieves the task queue associated with the given process ID from the task_queues dictionary.
        Then, it places the task into the queue, indicating that the task should be processed by the corresponding process.

        Parameters:
        - pid (int): The process ID to which the task should be assigned.
        - task (any): The task to be assigned to the process.

        Returns:
        None
        """
        logging.info("Task assigned to process PID: %d", pid)
        self.task_queues[pid].put(task)

    def assign_task_to_thread(self, task):
        """
        Assign a task to a worker thread for execution.

        This function creates a new worker thread and assigns the given task to it for execution.
        The thread is started immediately after being created.

        Parameters:
        - task (any): The task to be executed by the worker thread. This can be of any type, depending on the requirements of the load balancer.

        Returns:
        None
        """
        logging.info("Task assigned to a new thread :: %s", str(task))
        thread = Thread(target=self.thread_worker, args=(task,))
        thread.start()

    def process_worker(self, id):
        """
        Worker process function that manages its own thread pool.

        This function is responsible for creating and managing worker threads within a child process.
        It retrieves the task queue associated with the current process from the task_queues dictionary,
        and then continuously retrieves tasks from the queue to be executed by worker threads.

        Parameters:
        - id (int): The unique identifier of the process. This parameter is not used in the function's logic, but it is included for consistency with the other methods.

        Returns:
        None
        """
        pid = os.getpid()
        logging.info("Process started with PID: %d", pid)

        self.setup_process(id)

        while pid not in self.task_queues:
            pass  # Wait until the task queue for this process is available

        child_process_task_queue = self.task_queues[pid]

        while True:
            task = child_process_task_queue.get()
            logging.info("Process PID: %d received task: %s", pid, str(task))
            self.assign_task_to_thread(task)

    @abstractmethod
    def setup_process(self, id):
        """
        Set up process-specific environments.

        This method is intended to be overridden by subclasses to define any necessary setup steps
        that need to be performed within each child process. This could include setting up environment variables,
        loading specific libraries, or initializing any required resources.

        Parameters:
        - id (int): The unique identifier of the process. This parameter is not used in the function's logic, but it is included for consistency with the other methods.

        Returns:
        None
        """
        pass

    def thread_worker(self, task):
        """
        Execute the given task inside a worker thread.

        This function is responsible for executing a task within a worker thread.
        It retrieves the task from the process-specific task queue, executes the task using the `run` method,
        and then submits the result to the submit task queue using the `submit_task` method.
        After submitting the result, it marks the process as available again by adding its PID to the potential processes queue.

        Parameters:
        - task (any): The task to be executed by the worker thread. This can be of any type, depending on the requirements of the load balancer.

        Returns:
        None
        """
        pid = os.getpid()
        logging.info("Thread executing task in Process PID: %d", pid)
        result = self.run(task)
        logging.info("Task execution completed in Process PID: %d", pid)
        self.submit_task(result)  # Send result back to the submit queue
        self.potential_processes.put(pid)  # Mark process as available again

    def submit_task(self, task):
        """
        Submit a task to the next stage (e.g., a result queue or another balancer).

        This function is responsible for submitting a task to the next stage in the processing pipeline.
        The task can be a result of a completed computation, a data object to be processed further, or any other relevant data.
        The task is submitted to the submit_task_queue, which can be a result queue, another load balancer, or any other component
        that is responsible for processing the submitted task.

        Parameters:
        - task (any): The task to be submitted to the next stage. The type of the task can vary depending on the specific requirements of the load balancer.

        Returns:
        None

        The function logs the submission of the task using the logging module, and then places the task into the submit_task_queue for further processing.
        """
        logging.info("Submitting task result: %s", str(task))
        self.submit_task_queue.put(task)