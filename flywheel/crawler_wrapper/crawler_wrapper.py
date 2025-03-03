from flywheel.utils.load_balancer import AbstractLoadBalancer

class CrawlerParserLoadBalancer(AbstractLoadBalancer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def configure(self, **kwargs):
        """Update the parameters of CrawlerParserLoadBalancer."""
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        super().configure(**kwargs)
        
    def get_max_processes(self):
        return 10
    
    def get_max_threads_per_process(self):
        return 1
    
    def run(self, task):
        pass