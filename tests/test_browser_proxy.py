import requests
import time
from googlesearch import search
from stem import Signal
from stem.control import Controller

# TODO: Improve code design for readability and maintainability

PROXY = "socks5h://127.0.0.1:9051"
CONTROL_PORT = 9150
HEADER = {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-form-factors": '"Desktop"',
        "sec-ch-ua-full-version-list": '"Not A(Brand";v="8.0.0.0", "Chromium";v="132.0.6834.111", "Google Chrome";v="132.0.6834.111"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-origin",
    }

def renew_tor_ip():
    """Sends a NEWNYM signal to request a new Tor identity."""
    try:
        with Controller.from_port(port=CONTROL_PORT) as controller:
            password = "google"
            controller.authenticate(password=password)
            controller.signal(Signal.NEWNYM)
            time.sleep(5)
            return True
    except Exception as e:
        print(f"ERROR - renewing Tor identity: {str(e)}")
        return False

def is_proxy_working(test_url):
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    
    try:
        response = requests.get(test_url, proxies=proxies, headers=HEADER,timeout=10)
        return response
    except requests.exceptions.RequestException as e:
        return str(e)

def check_ip():
    test_url = "https://check.torproject.org/api/ip"
    response = is_proxy_working(test_url)
    print("\nChecking Identity...")
    print(response.json())
    
def change_identity():
    print("\nChanging Identity...")
    if renew_tor_ip():
        print("Identity Changed Successfully")
        check_ip()
    else:
        print("Failed to Change Identity")

def test_google_search():
    query = "kerala cricket team ranji trophy"
    results = list(search(
                query,
                num_results=10,
                unique=True,
                proxy=PROXY,
                advanced=True
            ))
    
    print("\nGoogle Search Results...")
    print(results)