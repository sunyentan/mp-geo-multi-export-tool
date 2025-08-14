from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn
from rich.status import Status

from .api import ApiClient
from .auth import get_auth_header
from .config import api_url
from .models import GeoPoint, LatLng, NoteExport, PanoExport, TagExport, ModelExport, ModelGeoCoordinates, Quaternion
from .utils import Timer, console, write_json, write_geojson, to_geojson_feature


app = typer.Typer(add_completion=False, help="Export Matterport panos, tags, notes with geocoordinates.")
export_app = typer.Typer(help="Export data as JSON/GeoJSON")
app.add_typer(export_app, name="export")


def _default_pretty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False





@export_app.command("sweeps")
def export_sweeps_cmd(
    model_id: str = typer.Option(..., "--model-id", "-m", help="Matterport model ID"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output path or '-' for stdout"),
    format: str = typer.Option("json", "--format", "-f", case_sensitive=False, help="json or geojson"),

    include_skybox: bool = typer.Option(False, "--include-skybox/--no-include-skybox"),
    concurrency: int = typer.Option(8, "--concurrency"),
    max_rps: float = typer.Option(5.0, "--max-rps"),
    retries: int = typer.Option(3, "--retries"),
    timeout: float = typer.Option(30.0, "--timeout"),
    api_key: str | None = typer.Option(None, "--api-key"),
    api_secret: str | None = typer.Option(None, "--api-secret"),
    url: str | None = typer.Option(None, "--url"),
    save_to_keyring: bool = typer.Option(True, "--save-to-keyring/--no-save-to-keyring"),
    pretty: bool = typer.Option(None, "--pretty/--no-pretty", help="Pretty output; default true for TTY"),
) -> None:
    if not model_id:
        raise typer.BadParameter("--model-id is required")
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    # Show progress when running interactively, unless explicitly outputting to stdout
    quiet = str(out) == "-" or (out is None and not sys.stdout.isatty())
    with Timer() as t:
        # Fetch locations with progress indicator
        if quiet:
            locs = client.fetch_locations(model_id, "2k")
        else:
            with Status("Fetching locations & sweeps...", console=c) as status:
                def update_status(msg: str) -> None:
                    status.update(f"Fetching locations & sweeps... {msg}")
                locs = client.fetch_locations(model_id, "2k", on_progress=update_status)
        
        points = [{"x": l["position"]["x"], "y": l["position"]["y"], "z": l["position"]["z"]} for l in locs]
        
        # Geocode with enhanced progress bar
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=c
            )
            with progress:
                task = progress.add_task("Geocoding sweep locations", total=len(points))
                def inc(completed: int, rate: float) -> None:
                    progress.update(task, completed=completed, description=f"Geocoding sweep locations ({rate:.1f}/s)")
                geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps, on_progress=inc)
        exports: list[PanoExport] = []
        for i, loc in enumerate(locs):
            geo = geos[i]
            panos = loc.get("panos") or []
            for idx, pano in enumerate(panos):
                sky = pano.get("skybox", {}).get("children") if include_skybox else None
                if include_skybox and (not sky or len(sky) != 6):
                    continue
                exports.append(
                    PanoExport(
                        id=f"{loc['id']}_pano{idx+1}",
                        local=GeoPoint(**loc["position"]),
                        geo=LatLng(**geo),
                        skyboxImages=sky if include_skybox else None,
                    )
                )
        if format.lower() == "json":
            write_json([e.model_dump() for e in exports], out, pretty)
        elif format.lower() == "geojson":
            features = [to_geojson_feature(e) for e in exports]
            write_geojson(features, out, pretty)
        else:
            raise typer.BadParameter(f"Unsupported format: {format}. Use 'json' or 'geojson'.")
        if not quiet:
            c.print(f"[green]Exported {len(exports)} sweeps.[/green]")


@export_app.command("tags")
def export_tags_cmd(
    model_id: str = typer.Option(..., "--model-id", "-m", help="Matterport model ID"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output path or '-' for stdout"),
    format: str = typer.Option("json", "--format", "-f", case_sensitive=False, help="json or geojson"),
    concurrency: int = typer.Option(8, "--concurrency"),
    max_rps: float = typer.Option(5.0, "--max-rps"),
    retries: int = typer.Option(3, "--retries"),
    timeout: float = typer.Option(30.0, "--timeout"),
    api_key: str | None = typer.Option(None, "--api-key"),
    api_secret: str | None = typer.Option(None, "--api-secret"),
    url: str | None = typer.Option(None, "--url"),
    save_to_keyring: bool = typer.Option(True, "--save-to-keyring/--no-save-to-keyring"),
    pretty: bool = typer.Option(None, "--pretty/--no-pretty", help="Pretty output; default true for TTY"),
) -> None:
    if not model_id:
        raise typer.BadParameter("--model-id is required")
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    # Show progress when running interactively, unless explicitly outputting to stdout
    quiet = str(out) == "-" or (out is None and not sys.stdout.isatty())
    with Timer() as t:
        # Fetch tags with progress indicator
        if quiet:
            tags = client.fetch_tags(model_id)
        else:
            with Status("Fetching tags...", console=c) as status:
                def update_status(msg: str) -> None:
                    status.update(f"Fetching tags... {msg}")
                tags = client.fetch_tags(model_id, on_progress=update_status)
        
        points = [t["anchorPosition"] for t in tags]
        
        # Geocode with enhanced progress bar
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=c
            )
            with progress:
                task = progress.add_task("Geocoding tags", total=len(points))
                def inc(completed: int, rate: float) -> None:
                    progress.update(task, completed=completed, description=f"Geocoding tags ({rate:.1f}/s)")
                geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps, on_progress=inc)
        exports = [
            TagExport(
                id=t["id"],
                label=t.get("label"),
                local=GeoPoint(**t["anchorPosition"]),
                geo=LatLng(**geos[i]),
            )
            for i, t in enumerate(tags)
        ]
        if format.lower() == "json":
            write_json([e.model_dump() for e in exports], out, pretty)
        elif format.lower() == "geojson":
            features = [to_geojson_feature(e) for e in exports]
            write_geojson(features, out, pretty)
        else:
            raise typer.BadParameter(f"Unsupported format: {format}. Use 'json' or 'geojson'.")
        if not quiet:
            c.print(f"[green]Exported {len(exports)} tags.[/green]")


@export_app.command("notes")
def export_notes_cmd(
    model_id: str = typer.Option(..., "--model-id", "-m", help="Matterport model ID"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output path or '-' for stdout"),
    format: str = typer.Option("json", "--format", "-f", case_sensitive=False, help="json or geojson"),
    concurrency: int = typer.Option(8, "--concurrency"),
    max_rps: float = typer.Option(5.0, "--max-rps"),
    retries: int = typer.Option(3, "--retries"),
    timeout: float = typer.Option(30.0, "--timeout"),
    api_key: str | None = typer.Option(None, "--api-key"),
    api_secret: str | None = typer.Option(None, "--api-secret"),
    url: str | None = typer.Option(None, "--url"),
    save_to_keyring: bool = typer.Option(True, "--save-to-keyring/--no-save-to-keyring"),
    pretty: bool = typer.Option(None, "--pretty/--no-pretty", help="Pretty output; default true for TTY"),
) -> None:
    if not model_id:
        raise typer.BadParameter("--model-id is required")
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    # Show progress when running interactively, unless explicitly outputting to stdout
    quiet = str(out) == "-" or (out is None and not sys.stdout.isatty())
    with Timer() as t:
        # Fetch notes with progress indicator
        if quiet:
            notes = client.fetch_notes(model_id)
        else:
            with Status("Fetching notes...", console=c) as status:
                def update_status(msg: str) -> None:
                    status.update(f"Fetching notes... {msg}")
                notes = client.fetch_notes(model_id, on_progress=update_status)
        
        points = [n["anchorPosition"] for n in notes]
        
        # Geocode with enhanced progress bar
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                TextColumn("•"),
                TimeRemainingColumn(),
                console=c
            )
            with progress:
                task = progress.add_task("Geocoding notes", total=len(points))
                def inc(completed: int, rate: float) -> None:
                    progress.update(task, completed=completed, description=f"Geocoding notes ({rate:.1f}/s)")
                geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps, on_progress=inc)
        exports = [
            NoteExport(
                id=n["id"],
                text=n.get("label"),
                local=GeoPoint(**n["anchorPosition"]),
                geo=LatLng(**geos[i]),
            )
            for i, n in enumerate(notes)
        ]
        if format.lower() == "json":
            write_json([e.model_dump() for e in exports], out, pretty)
        elif format.lower() == "geojson":
            features = [to_geojson_feature(e) for e in exports]
            write_geojson(features, out, pretty)
        else:
            raise typer.BadParameter(f"Unsupported format: {format}. Use 'json' or 'geojson'.")
        if not quiet:
            c.print(f"[green]Exported {len(exports)} notes.[/green]")


@export_app.command("model")
def export_model_cmd(
    model_id: str = typer.Option(..., "--model-id", "-m", help="Matterport model ID"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output path or '-' for stdout"),
    format: str = typer.Option("json", "--format", "-f", case_sensitive=False, help="json or geojson"),
    timeout: float = typer.Option(30.0, "--timeout"),
    api_key: str | None = typer.Option(None, "--api-key"),
    api_secret: str | None = typer.Option(None, "--api-secret"),
    url: str | None = typer.Option(None, "--url"),
    save_to_keyring: bool = typer.Option(True, "--save-to-keyring/--no-save-to-keyring"),
    pretty: bool = typer.Option(None, "--pretty/--no-pretty", help="Pretty output; default true for TTY"),
) -> None:
    if not model_id:
        raise typer.BadParameter("--model-id is required")
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout)
    c = console()
    # Show progress when running interactively, unless explicitly outputting to stdout
    quiet = str(out) == "-" or (out is None and not sys.stdout.isatty())
    with Timer() as t:
        # Fetch model geocoordinates with progress indicator
        if quiet:
            model_data = client.fetch_model_geocoordinates(model_id)
        else:
            with Status("Fetching model geocoordinates...", console=c) as status:
                def update_status(msg: str) -> None:
                    status.update(f"Fetching model geocoordinates... {msg}")
                model_data = client.fetch_model_geocoordinates(model_id, on_progress=update_status)
        
        # Build the model export
        geocoords_data = model_data.get("geocoordinates") or {}
        translation = geocoords_data.get("translation")
        rotation = geocoords_data.get("rotation")
        
        geocoords = ModelGeoCoordinates(
            source=geocoords_data.get("source"),
            altitude=geocoords_data.get("altitude"),
            latitude=geocoords_data.get("latitude"),
            longitude=geocoords_data.get("longitude"),
            translation=GeoPoint(**translation) if translation else None,
            rotation=Quaternion(**rotation) if rotation else None,
        )
        
        export = ModelExport(
            id=model_data.get("id", model_id),
            geocoordinates=geocoords
        )
        
        if format.lower() == "json":
            write_json(export.model_dump(), out, pretty)
        elif format.lower() == "geojson":
            # For GeoJSON, create a feature with the lat/lng if available
            if geocoords.latitude is not None and geocoords.longitude is not None:
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [geocoords.longitude, geocoords.latitude, geocoords.altitude]
                    },
                    "properties": export.model_dump()
                }
                write_geojson([feature], out, pretty)
            else:
                # Fallback to JSON if no coordinates available
                write_json(export.model_dump(), out, pretty)
        else:
            raise typer.BadParameter(f"Unsupported format: {format}. Use 'json' or 'geojson'.")
        
        if not quiet:
            c.print(f"[green]Exported model geocoordinates.[/green]")