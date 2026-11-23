"""Minimal klient for Kassalapp API (https://kassal.app/api). Kun standardbiblioteket."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://kassal.app/api/v1"


class KassalClient:
    def __init__(self, api_key: str | None = None, per_minute: int = 60):
        self.api_key = api_key or os.environ.get("KASSAL_API_KEY")
        if not self.api_key:
            raise RuntimeError("Mangler KASSAL_API_KEY (miljøvariabel eller .env)")
        self.min_interval = 60.0 / per_minute
        self._last = 0.0

    def _get(self, path: str, params: dict | None = None) -> dict:
        query = urllib.parse.urlencode({k: v for k, v in (params or {}).items() if v is not None}, doseq=True)
        url = f"{BASE_URL}{path}" + (f"?{query}" if query else "")
        for attempt in range(5):
            wait = self.min_interval - (time.monotonic() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.monotonic()
            req = urllib.request.Request(url, headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "User-Agent": "matglede-prototype/0.1",
            })
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as e:
                if e.code == 429 or e.code >= 500:
                    retry = e.headers.get("Retry-After")
                    time.sleep(float(retry) if retry and retry.isdigit() else 2 ** attempt * 5)
                    continue
                if e.code == 404:
                    return {"data": None}
                raise
        raise RuntimeError(f"Ga opp etter gjentatte feil: {url}")

    def search_products(self, search: str, store: str | None = None, size: int = 50) -> list[dict]:
        data = self._get("/products", {"search": search, "store": store, "size": size, "sort": "date_desc"})
        return data.get("data") or []


def load_dotenv(path: str = ".env") -> None:
    """Les KEY=VALUE fra en .env-fil inn i os.environ (overskriver ikke eksisterende)."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
