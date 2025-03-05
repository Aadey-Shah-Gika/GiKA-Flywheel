import os
from datetime import datetime
import logging

from .constants import DEFAULT_LOAD_BALANCER_CONFIG as default_config, TASK_STORAGE_DIR

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_timestamp_str():
    """
    Generate a timestamp string in the format 'YYYY-MM-DD HH:MM:SS'.

    Parameters:
    None

    Returns:
    str: A timestamp string in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

class QueryGeneratorTaskManager:
    """
    Load balancer responsible for handling query generation tasks.
    
    This class receives tasks, processes them in batches, and submits the results
    to the next stage in the pipeline.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the load balancer with required queues and configurations.

        Parameters:
        - **kwargs: Dictionary containing configuration options and shared queues.
            - manager: Multiprocessing manager for shared objects.
            - task_queue: Queue containing tasks to be processed.
            - submit_task_queue: Queue where processed tasks are submitted.
            - max_tasks_once (optional): Maximum tasks to process at once (default from config).
        """
        self.manager = kwargs['manager']
        self.task_queue = kwargs['task_queue']
        self.submit_task_queue = kwargs['submit_task_queue']
        
        # Set the max number of tasks that can be processed at once
        self.max_tasks_once = kwargs.get('max_tasks_once', default_config['max_tasks_once'])
        
        logging.info("QueryGeneratorLoadBalancer initialized with max_tasks_once=%d", self.max_tasks_once)
    
    def save_tasks(self, tasks):
        """
        Save the received tasks to a file for logging, debugging and analysis purposes.

        Parameters:
        - tasks (list): List of tasks to be saved.
        """
        if not os.path.exists(TASK_STORAGE_DIR):
            os.makedirs(TASK_STORAGE_DIR)  # Ensure the directory exists
        
        file_name = f"context_{get_timestamp_str()}"
        file_path = os.path.join(TASK_STORAGE_DIR, f"{file_name}.txt")
        
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(str(tasks))
        
        logging.info("Saved tasks to %s", file_path)
    
    def run(self, task):
        """
        Process a given task by generating queries.

        Parameters:
        - task (list): List of input tasks to process.

        Returns:
        - dict: Dictionary containing the original task and generated results.
        """
        logging.info("Processing task: %s", str(task))
        
        results = self.generate_queries(task)  # Generate queries (assumes method is implemented)
        
        response = {
            "task": task,
            "result": results
        }
        
        logging.info("Task processing completed: %s", str(response))
        return response
    
    def submit_task(self, task):
        """
        Submit processed tasks to the next stage (e.g., another load balancer or processing unit).

        Parameters:
        - task (dict): Processed task containing results.
        
        Returns:
        - None
        """
        logging.info("Submitting processed tasks...")
        
        for i, queries in enumerate(task['result']):
            for query in queries:
                cur_task = {
                    "task": task['task'][i],
                    "result": query
                }
                self.submit_task_queue.put(cur_task)
                logging.info("Submitted task: %s", str(cur_task))
    
    def start(self):
        """
        Start processing tasks from the queue in batches.
        It collects multiple tasks if possible before processing to maximize efficiency.
        """
        logging.info("QueryGeneratorLoadBalancer started")
        
        while True:
            raw_tasks = self.task_queue.get()  # Wait for a task
            tasks = raw_tasks['result']
            
            logging.info("Received new batch of tasks")
            
            # Try to accumulate tasks up to max_tasks_once
            while len(tasks) < self.max_tasks_once and not self.task_queue.empty():
                extra_tasks = self.task_queue.get()
                tasks.extend(extra_tasks['result'])
                logging.info("Added extra tasks to batch, new size: %d", len(tasks))
            
            self.save_tasks(tasks)  # Save tasks to file for tracking
            
            response = self.run(tasks)  # Process the tasks
            self.submit_task(response)  # Submit processed tasks
            
            logging.info("Batch processing completed and results submitted")