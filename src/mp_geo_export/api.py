from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from .queries import GET_GEO, GET_NOTES, GET_SWEEPS, GET_TAGS


class GraphQLError(RuntimeError):
    pass


class ApiClient:
    def __init__(
        self,
        url: str,
        auth_header: str,
        timeout: float = 30.0,
        max_rps: float = 5.0,
        retries: int = 3,
    ) -> None:
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": auth_header,
            "Content-Type": "application/json",
        })
        self.timeout = timeout
        self.max_rps = max_rps
        self.retries = retries
        self._last = 0.0

    def _rate_limit(self) -> None:
        if self.max_rps <= 0:
            return
        min_interval = 1.0 / self.max_rps
        now = time.monotonic()
        delta = now - self._last
        if delta < min_interval:
            time.sleep(min_interval - delta)
        self._last = time.monotonic()

    def _post(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(self.retries + 1):
            try:
                self._rate_limit()
                resp = self.session.post(self.url, json={"query": query, "variables": variables}, timeout=self.timeout)
                resp.raise_for_status()
                payload = resp.json()
                if "errors" in payload:
                    raise GraphQLError(str(payload["errors"]))
                data = payload.get("data")
                if not isinstance(data, dict):
                    raise GraphQLError("Malformed GraphQL response: missing data")
                return data
            except (requests.RequestException, GraphQLError):
                if attempt == self.retries:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Unreachable")

    def fetch_locations(self, model_id: str, resolution: str) -> list[dict[str, Any]]:
        data = self._post(GET_SWEEPS, {"modelId": model_id})
        model = data.get("model") or {}
        locations = model.get("locations") or []
        return locations

    def fetch_tags(self, model_id: str) -> list[dict[str, Any]]:
        data = self._post(GET_TAGS, {"modelId": model_id})
        model = data.get("model") or {}
        return model.get("mattertags") or []

    def fetch_notes(self, model_id: str) -> list[dict[str, Any]]:
        data = self._post(GET_NOTES, {"modelId": model_id})
        model = data.get("model") or {}
        return model.get("notes") or []

    def geocode_point(self, model_id: str, point: dict[str, float]) -> dict[str, Any]:
        data = self._post(GET_GEO, {"modelId": model_id, "point": point})
        model = data.get("model") or {}
        geo = (model.get("geocoordinates") or {}).get("geoLocationOf")
        if not geo:
            raise GraphQLError("Geolocation not available for point")
        return geo  # type: ignore[no-any-return]

    def batch_geocode(
        self,
        model_id: str,
        points: list[dict[str, float]],
        concurrency: int,
        max_rps: float | None = None,
        on_progress: "None | (callable)" = None,  # type: ignore[valid-type]
    ) -> list[dict[str, Any]]:
        if max_rps is not None:
            self.max_rps = max_rps
        results: list[dict[str, Any] | None] = [None] * len(points)
        completed = 0
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_index = {executor.submit(self.geocode_point, model_id, pt): idx for idx, pt in enumerate(points)}
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                results[idx] = future.result()
                completed += 1
                if on_progress:
                    try:
                        on_progress(completed)
                    except Exception:
                        pass
        return [r for r in results if r is not None]


