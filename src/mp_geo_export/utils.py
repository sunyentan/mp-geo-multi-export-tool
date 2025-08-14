from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

from rich.console import Console


def write_json(data: object, out_path: Path | None, pretty: bool) -> None:
    text = json.dumps(data, indent=2 if pretty else None)
    if out_path is None or str(out_path) == "-":
        sys.stdout.write(text + ("\n" if pretty else ""))
    else:
        Path(out_path).write_text(text)


def write_geojson(features: list[dict[str, Any]], out_path: Path | None, pretty: bool) -> None:
    """Write a GeoJSON FeatureCollection."""
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    write_json(geojson, out_path, pretty)


def to_geojson_feature(item: Any) -> dict[str, Any]:
    """Convert a PanoExport, TagExport, or NoteExport to a GeoJSON Feature."""
    # Extract coordinates [longitude, latitude] - note the order!
    coordinates = [item.geo.long, item.geo.lat]
    if item.geo.alt is not None:
        coordinates.append(item.geo.alt)
    
    properties = {
        "id": item.id,
        "local_coordinates": {
            "x": item.local.x,
            "y": item.local.y, 
            "z": item.local.z
        }
    }
    
    # Add type-specific properties
    if hasattr(item, 'skyboxImages') and item.skyboxImages:
        properties["skybox_images"] = item.skyboxImages
        properties["type"] = "sweep"
    elif hasattr(item, 'label'):
        if hasattr(item, 'text'):  # NoteExport
            properties["text"] = item.text
            properties["type"] = "note"
        else:  # TagExport
            properties["label"] = item.label
            properties["type"] = "tag"
    
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": coordinates
        },
        "properties": properties
    }


def console() -> Console:
    return Console()


class Timer:
    def __init__(self) -> None:
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *exc_info) -> None:  # type: ignore[no-untyped-def]
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start


