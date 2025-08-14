from __future__ import annotations

from pydantic import BaseModel


class GeoPoint(BaseModel):
    x: float
    y: float
    z: float


class LatLng(BaseModel):
    lat: float
    long: float
    alt: float | None = None


class PanoExport(BaseModel):
    id: str
    local: GeoPoint
    geo: LatLng
    skyboxImages: list[str] | None = None


class TagExport(BaseModel):
    id: str
    label: str | None = None
    local: GeoPoint
    geo: LatLng


class NoteExport(BaseModel):
    id: str
    text: str | None = None
    local: GeoPoint
    geo: LatLng


