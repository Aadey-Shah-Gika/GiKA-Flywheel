from flywheel.utils.load_balancer import AbstractLoadBalancer

class FilterLoadBalancer(AbstractLoadBalancer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def get_max_processes(self):
        return 9
    
    def get_max_threads_per_process(self):
        return 1
    
    def run(self, task):
        
        print("\n[DEBUG] -- FilterLoadBalancer :: run | task:", task, "\n")
        
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