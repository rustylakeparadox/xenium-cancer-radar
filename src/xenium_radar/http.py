import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class HttpClient:
    def __init__(self, config: dict):
        network = config.get("network", config)
        self.timeout = network.get("timeout", 20)
        self.session = requests.Session()
        retry = Retry(total=network.get("retries", 3), backoff_factor=network.get("backoff_factor", .5), status_forcelist=(429, 500, 502, 503, 504), allowed_methods=("GET", "HEAD"))
        self.session.mount("https://", HTTPAdapter(max_retries=retry)); self.session.mount("http://", HTTPAdapter(max_retries=retry))
        self.session.headers["User-Agent"] = network.get("user_agent", "XeniumCancerDataRadar/0.1")
    def get(self, url, **kwargs): kwargs.setdefault("timeout", self.timeout); return self.session.get(url, **kwargs)
    def head(self, url, **kwargs): kwargs.setdefault("timeout", self.timeout); kwargs.setdefault("allow_redirects", True); return self.session.head(url, **kwargs)
