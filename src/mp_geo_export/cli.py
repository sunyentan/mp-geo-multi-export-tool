from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import List

import typer
from rich.progress import Progress

from .api import ApiClient
from .auth import get_auth_header
from .config import api_url
from .models import GeoPoint, LatLng, NoteExport, PanoExport, TagExport
from .utils import Timer, console, write_json, write_geojson, to_geojson_feature


app = typer.Typer(add_completion=False, help="Export Matterport panos, tags, notes with geocoordinates.")
export_app = typer.Typer(help="Export data as JSON/GeoJSON")
app.add_typer(export_app, name="export")


def _default_pretty() -> bool:
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _env_model_id() -> str | None:
    return os.getenv("MP_MODEL_ID")


@export_app.command("sweeps")
def export_sweeps_cmd(
    model_id: str = typer.Option(None, "--model-id", "-m", help="Matterport model ID", show_default=False),
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
    resolved_model_id = model_id or _env_model_id()
    if not resolved_model_id:
        raise typer.BadParameter("--model-id is required (or set env MP_MODEL_ID)")
    model_id = resolved_model_id
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    quiet = out is None or str(out) == "-"
    with Timer() as t:
        if not quiet:
            c.log("Fetching locations & sweeps…")
        locs = client.fetch_locations(model_id, "2k")
        points = [{"x": l["position"]["x"], "y": l["position"]["y"], "z": l["position"]["z"]} for l in locs]
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            with Progress() as progress:
                task = progress.add_task("Geocoding sweep locations", total=len(points))
                def inc(_: int) -> None:
                    progress.advance(task)
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
            c.print(f"[green]Exported {len(exports)} sweeps in {t.elapsed:.2f}s.[/green]")


@export_app.command("tags")
def export_tags_cmd(
    model_id: str = typer.Option(None, "--model-id", "-m", help="Matterport model ID", show_default=False),
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
    resolved_model_id = model_id or _env_model_id()
    if not resolved_model_id:
        raise typer.BadParameter("--model-id is required (or set env MP_MODEL_ID)")
    model_id = resolved_model_id
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    quiet = out is None or str(out) == "-"
    with Timer() as t:
        if not quiet:
            c.log("Fetching tags…")
        tags = client.fetch_tags(model_id)
        points = [t["anchorPosition"] for t in tags]
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            with Progress() as progress:
                task = progress.add_task("Geocoding tags", total=len(points))
                def inc(_: int) -> None:
                    progress.advance(task)
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
            c.print(f"[green]Exported {len(exports)} tags in {t.elapsed:.2f}s.[/green]")


@export_app.command("notes")
def export_notes_cmd(
    model_id: str = typer.Option(None, "--model-id", "-m", help="Matterport model ID", show_default=False),
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
    resolved_model_id = model_id or _env_model_id()
    if not resolved_model_id:
        raise typer.BadParameter("--model-id is required (or set env MP_MODEL_ID)")
    model_id = resolved_model_id
    if pretty is None:
        pretty = _default_pretty()
    auth = get_auth_header(api_key=api_key, api_secret=api_secret, save_to_keyring=save_to_keyring)
    client = ApiClient(api_url(url), auth_header=auth, timeout=timeout, max_rps=max_rps, retries=retries)
    c = console()
    quiet = out is None or str(out) == "-"
    with Timer() as t:
        if not quiet:
            c.log("Fetching notes…")
        notes = client.fetch_notes(model_id)
        points = [n["anchorPosition"] for n in notes]
        if quiet:
            geos = client.batch_geocode(model_id, points, concurrency=concurrency, max_rps=max_rps)
        else:
            with Progress() as progress:
                task = progress.add_task("Geocoding notes", total=len(points))
                def inc(_: int) -> None:
                    progress.advance(task)
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
        else:
            headers = ["id", "text", "lat", "long", "alt", "x", "y", "z"]
            rows = [[e.id, e.text or "", e.geo.lat, e.geo.long, e.geo.alt, e.local.x, e.local.y, e.local.z] for e in exports]
            write_csv(rows, headers if csv_headers else [], out)
        if not quiet:
            c.print(f"[green]Exported {len(exports)} notes in {t.elapsed:.2f}s.[/green]")