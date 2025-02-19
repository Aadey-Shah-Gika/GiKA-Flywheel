import requests

# TODO: Improve code design for readability and maintainability

# Define the proxy settings
PROXY = "socks5h://127.0.0.1:9051"  # Replace with your actual SOCKS proxy

# URL to check the proxy IP
CHECK_IP_URL = "https://check.torproject.org/api/ip"  # This service will return the IP it sees

# Function to get the IP seen by the server
def get_end_ip():
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    try:
        response = requests.get(CHECK_IP_URL, proxies=proxies, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        return str(e)

# Pytest test to check proxy functionality and print the IP
def test_proxy():
    result = get_end_ip()
    print(result)