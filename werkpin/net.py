import re
import requests
from urllib3.util import parse_url

class Net:
    def __init__(self, url):
        self.session = requests.Session()
        self.url = parse_url(url)
        self.header_version = None
        self._verify()
    
    def _verify(self):
        r = self.session.get(f"{self.url}/console")
        if r.status_code != 200:
            raise Exception("Cannot connect to console on {self.url}")
        if "Werkzeug" not in r.text:
            raise Exception("Werkzeug not found in response")
        # Try to get version from Headers
        if "Server" not in r.headers:
            return
        version = r.headers.get("Server")
        m = re.match(r"Werkzeug/([\d.]+)", version)
        if m:
            self.header_version = m.group(1)
