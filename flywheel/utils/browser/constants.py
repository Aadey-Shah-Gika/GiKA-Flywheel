from stem import Signal

TOR_DEFAULT_CONFIG = {
    "port": "9051",
    "password": "google",
    "signal": Signal.NEWNYM,
    "headers": {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "sec-ch-prefers-color-scheme": "dark",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-arch": '"x86"',
        "sec-ch-ua-bitness": '"64"',
        "sec-ch-ua-form-factors": '"Desktop"',
        "sec-ch-ua-full-version": '"132.0.6834.111"',
        "sec-ch-ua-full-version-list": '"Not A(Brand";v="8.0.0.0", "Chromium";v="132.0.6834.111", "Google Chrome";v="132.0.6834.111"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-model": '""',
        "sec-ch-ua-platform": '"Windows"',
        "sec-ch-ua-platform-version": '"15.0.0"',
        "sec-ch-ua-wow64": "?0",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-origin",
    },
    "proxies": {
        'http': 'socks5h://127.0.0.1:9050',  # Tor's default SOCKS5 proxy
        'https': 'socks5h://127.0.0.1:9050',
    },
    "max_identity_renewals_retries": 5,  # Max tries for changing identity
    # Delay between identity renewal attempts (seconds)
    "identity_retry_delay": 5,
    "requests_per_identity": 20,  # Number of fetches per identity before renewal
    "max_request_retries": 5,  # Max retries for a single request
}
