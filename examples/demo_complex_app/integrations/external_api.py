import requests
from typing import Any, Dict


class ExternalAPI:
    def __init__(self, base_url: str = "https://httpbin.org") -> None:
        self.base_url = base_url

    def notify_create(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # POST to httpbin as a stand-in for an external provider
        try:
            r = requests.post(f"{self.base_url}/post", json=item, timeout=3)
            return {"status": r.status_code}
        except Exception as e:
            return {"error": str(e)}