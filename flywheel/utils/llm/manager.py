from .llm_interface import LLMInterface

import requests

class LlmManager(LLMInterface):

    def __init__(self, **kwargs):
        pass

    def get_response(self, query):
        response = requests.post("http://localhost:5000/infer", json={
            "type": "text-generation",
            "model_name": "meta-llama/Llama-3.1-8B-Instruct",
            "input_text": query,
            "temperature": 0.9,
            "max_new_tokens": 1024
        })
        
        json_response = response.json()
        
        print(json_response)
        
        formatted_response = [[], [], []]
        
        for response in json_response:
            for i in range(3):
                formatted_response[i].append(response[-1]["generated_text"][i])
        
        
        
        return formatted_response
