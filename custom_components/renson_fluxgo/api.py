"""Small client for the observed Renson Flux Go local API."""

import requests


class FluxGoApi:
    def __init__(self, host: str, api_key: str):
        self.base_url = f"http://{host}/api/v1"
        self.headers = {"x-api-key": api_key, "Accept": "application/json"}

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

    def clear_boost(self):
        payload = {"enable": True, "level": 30, "timeout": 5}
        for direction in ("extract", "supply"):
            self.put(f"/decision/room/0/{direction}/boost", payload)
