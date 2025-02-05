import requests
import time
import json
from stem.control import Controller
from stem import Signal
from .constants import TOR_DEFAULT_CONFIG as TOR_CONFIG


class TorBrowser:
    """
    A class to manage web requests through the TOR network with automatic identity renewal.
    """

    def __init__(self, **config):
        """Initialize TOR settings with provided or default configuration."""
        self.configure_tor(config)
        self.remaining_fetches = self.requests_per_identity

    def configure_tor(self, config):
        """Configure TOR settings using provided values or default values."""
        default_config = {
            "port": TOR_CONFIG["port"],
            "password": TOR_CONFIG["password"],
            "signal": TOR_CONFIG["signal"],
            "headers": TOR_CONFIG["headers"],
            "proxies": TOR_CONFIG["proxies"],
            "max_identity_renewals_retries": TOR_CONFIG["max_identity_renewals_retries"],
            "identity_retry_delay": TOR_CONFIG["identity_retry_delay"],
            "requests_per_identity": TOR_CONFIG["requests_per_identity"],
        }

        # Merge provided config with defaults
        for key, value in default_config.items():
            setattr(self, key, config.get(key, value))

    def renew_tor_identity(self):
        """Renew TOR identity by sending a NEWNYM signal."""
        for _ in range(self.max_identity_renewals_retries):
            try:
                with Controller.from_port(port=self.port) as controller:
                    controller.authenticate(password=self.password)
                    controller.signal(Signal.NEWNYM)
                    time.sleep(self.identity_retry_delay)
                return
            except Exception:
                continue
        raise RuntimeError(
            "Failed to renew TOR circuit after multiple attempts.")

    def _update_remaining_fetches(self):
        """Decrease remaining fetches and renew identity if needed."""
        self.remaining_fetches -= 1
        if self.remaining_fetches <= 0:
            self.renew_tor_identity()
            self.remaining_fetches = self.requests_per_identity

    @staticmethod
    def parse_json_response(response):
        """Extract JSON content from a response object."""
        try:
            content = response.text
            start_index = content.find('{')
            end_index = content.rfind('}')

            if start_index != -1 and end_index != -1:
                content = content[start_index:end_index + 1]

            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Error parsing JSON response: {str(e)}\nContent: {content}"
            )

    def request(self, url, **kwargs):
        """Perform an HTTP GET request through the TOR network."""
        self._update_remaining_fetches()
        try:
            response = requests.get(url, **kwargs, proxies=self.proxies)
            response.raise_for_status()
            return self.parse_json_response(response)
        except requests.RequestException as e:
            raise ConnectionError(f"Request failed: {str(e)}")
