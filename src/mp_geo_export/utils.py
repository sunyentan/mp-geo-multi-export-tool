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
    if hasattr(item, 'skyboxImages'):  # PanoExport/SweepExport
        properties["type"] = "sweep"
        if item.skyboxImages:
            properties["skybox_images"] = item.skyboxImages
    elif hasattr(item, 'text') and hasattr(item, 'label'):  # NoteExport has both
        properties["text"] = item.text
        properties["type"] = "note"
    elif hasattr(item, 'label'):  # TagExport
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
    
    def format_elapsed(self) -> str:
        """Format elapsed time with appropriate precision."""
        if self.elapsed <= 0:
            return "0s"
        elif self.elapsed >= 10:
            return f"{self.elapsed:.1f}s"
        elif self.elapsed >= 1:
            return f"{self.elapsed:.2f}s"
        elif self.elapsed >= 0.1:
            return f"{self.elapsed:.3f}s"
        elif self.elapsed >= 0.001:  # 1ms and above
            ms = self.elapsed * 1000
            return f"{ms:.1f}ms"
        else:  # Less than 1ms
            us = self.elapsed * 1000000
            if us >= 1:
                return f"{us:.0f}μs"
            else:
                return "<1μs"  # For extremely small times


