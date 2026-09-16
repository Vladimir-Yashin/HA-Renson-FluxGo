"""Small client for the observed Renson Flux Go local API."""

import requests

# Fixed header value in the captured web session with Flux Go Wall 400 SW ver 2.8.2
# This value is hardcoded in .js file too, but it *may change* in future SW versions.
# Technically it is only needed in /decision/sensor_values requests
SENSOR_SERVICE_KEY = "Avatar_11"

class FluxGoApi:
    def __init__(self, host: str, api_key: str):
        self.base_url = f"http://{host}/api/v1"
        self.headers = {
            "X-API-Key": api_key,
            "X-API-Service-Key": SENSOR_SERVICE_KEY,
            "Accept": "application/json"
        }

    def get(self, path: str):
        response = requests.get(
            f"{self.base_url}{path}", headers=self.headers, timeout=5
        )
        response.raise_for_status()
        return response.json()

    def put(self, path: str, payload=None):
        response = requests.put(
            f"{self.base_url}{path}", headers=self.headers, json=payload, timeout=5
        )
        response.raise_for_status()
        return response.json() if response.content else None

    def verify_token(self):
        response = requests.put(
            f"{self.base_url}/authentication/verify", headers=self.headers, timeout=5
        )
        response.raise_for_status()

    def set_boost(self, level: int, minutes: int):
        payload = {"enable": True, "level": level, "timeout": minutes * 60}
        for direction in ("extract", "supply"):
            self.put(f"/decision/room/0/{direction}/boost", payload)

