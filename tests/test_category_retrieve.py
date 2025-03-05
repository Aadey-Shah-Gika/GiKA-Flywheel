import json
import time
import requests
from rich import print

from urllib.parse import urlparse

from submodules.browser import Browser

def get_headers():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://www.virustotal.com/',
        'Content-Type': 'application/json',
        'X-Tool': 'vt-ui-main',
        'x-app-version': 'v1x343x11',
        'Accept-Ianguage': 'en-US,en;q=0.9,es;q=0.8',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=4',
    }

    session = requests.Session()
    session.headers.update(headers)
    
    session.get('https://www.virustotal.com/')
    response = session.get('https://www.virustotal.com/ui/user_notifications')
    
    print("response: ", response.text)

    return session.headers

def extract_domain(url: str) -> str:
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"

def getUrlDomains():
    domains = set()  # Using a set to ensure uniqueness
    with open('./tests/queries.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        for result in data:
            for url in result['URLS']:
                domain = extract_domain(url['url'])  
                domains.add(domain)  # Add the extracted domain to the set
    return list(domains)  # Returning the set of unique domains


def test_fetching():
    
    print(get_headers())
    return
    
    urls_set = getUrlDomains()
    
    urls = urls_set
    
    categories = {}
    
    control_port = 9151
    socks_port = 9051
    proxies = {
        "http": f"socks5h://127.0.0.1:{socks_port}",
        "https": f"socks5h://127.0.0.1:{socks_port}",
    }
    browser = Browser(port=control_port, proxies=proxies, requests_per_identity=3)
    browser.renew_tor_identity()
    
    for i in range(len(urls)):
        time.sleep(3.5)
        url = urls[i]
        raw_response = getCategories(url, browser)
        formatted_response = list(raw_response.values())
        categories[url] = formatted_response
        print('Fetching Category of URL Number:', i + 1)
        with open('./tests/data/categories.json', 'w', encoding='utf8') as file:
            json.dump(categories, file, indent=4)

def getCategories(url, browser):
    
    proxies = browser.getProxy()
    # browser.decrease_remaining_fetches()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Referer': 'https://www.virustotal.com/',
        'content-type': 'application/json',
        'X-Tool': 'vt-ui-main',
        'x-app-version': 'v1x343x11',
        'Accept-Ianguage': 'en-US,en;q=0.9,es;q=0.8',
        'X-VT-Anti-Abuse-Header': 'MTk1OTk0ODkxOTMtWkc5dWRDQmlaU0JsZG1scy0xNzQxMDA2NzQ1LjgzOA==',
        'Sec-GPC': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Priority': 'u=4',
    }

    params = {
        'limit': '2',
        'relationships[comment]': 'author,item',
        'query': url,
    }

    response = requests.get('https://www.virustotal.com/ui/search', params=params, headers=headers, proxies=proxies)
    
    if response.status_code >= 400:
        print(response.text)
        exit(1)
    
    try:
    
        data = response.json()
        categories = data['data'][0]['attributes']['categories']
        return categories
        
    except Exception as e:
        print("Error occurred:", e)
        return {}