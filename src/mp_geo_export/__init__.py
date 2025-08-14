from __future__ import annotations

from typing import Any

from .api import ApiClient
from .auth import get_auth_header
from .config import api_url
from .models import LatLng, NoteExport, PanoExport, TagExport

__all__ = [
    "export_panos",
    "export_tags",
    "export_notes",
    "PanoExport",
    "TagExport",
    "NoteExport",
    "LatLng",
]


def _client(**kwargs: Any) -> ApiClient:
    auth = get_auth_header(
        api_key=kwargs.pop("api_key", None),
        api_secret=kwargs.pop("api_secret", None),
        save_to_keyring=kwargs.pop("save_to_keyring", False),
    )
    url = api_url(kwargs.pop("url", None))
    timeout = float(kwargs.pop("timeout", 30.0))
    max_rps = float(kwargs.pop("max_rps", 5.0))
    retries = int(kwargs.pop("retries", 3))
    return ApiClient(url, auth, timeout=timeout, max_rps=max_rps, retries=retries)


def export_panos(
    model_id: str,
    include_skybox: bool = True,
    resolution: str = "2k",
    **kwargs: Any,
) -> list[PanoExport]:
    client = _client(**kwargs)
    locations = client.fetch_locations(model_id, resolution)
    points = [loc["position"] for loc in locations]
    geos = client.batch_geocode(model_id, points, concurrency=int(kwargs.get("concurrency", 8)))
    exports: list[PanoExport] = []
    for i, loc in enumerate(locations):
        geo = geos[i]
        panos = loc.get("panos") or []
        for idx, pano in enumerate(panos):
            sky = pano.get("skybox", {}).get("children") if include_skybox else None
            if include_skybox and (not sky or len(sky) != 6):
                continue
            exports.append(
                PanoExport(
                    id=f"{loc['id']}_pano{idx+1}",
                    local=loc["position"],
                    geo=LatLng(**geo),
                    skyboxImages=sky if include_skybox else None,
                )
            )
    return exports


def export_tags(model_id: str, **kwargs: Any) -> list[TagExport]:
    client = _client(**kwargs)
    tags = client.fetch_tags(model_id)
    geos = client.batch_geocode(model_id, [t["anchorPosition"] for t in tags], concurrency=int(kwargs.get("concurrency", 8)))
    return [
        TagExport(id=t["id"], label=t.get("label"), local=t["anchorPosition"], geo=LatLng(**g))
        for t, g in zip(tags, geos)
    ]


def export_notes(model_id: str, **kwargs: Any) -> list[NoteExport]:
    client = _client(**kwargs)
    notes = client.fetch_notes(model_id)
    geos = client.batch_geocode(model_id, [n["anchorPosition"] for n in notes], concurrency=int(kwargs.get("concurrency", 8)))
    return [
        NoteExport(id=n["id"], text=n.get("label"), local=n["anchorPosition"], geo=LatLng(**g))
        for n, g in zip(notes, geos)
    ]


