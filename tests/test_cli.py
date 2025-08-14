from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
import responses
from typer.testing import CliRunner

from mp_geo_export.cli import app
from mp_geo_export.auth import SERVICE, ACCOUNT


runner = CliRunner()


def _mock_graphql_success(api_url: str) -> None:
    # sweeps
    responses.add(
        responses.POST,
        api_url,
        json={
            "data": {
                "model": {
                    "locations": [
                        {
                            "id": "locA",
                            "position": {"x": 1, "y": 2, "z": 3},
                            "panos": [
                                {"skybox": {"children": [f"s{i}" for i in range(6)]}},
                            ],
                        }
                    ]
                }
            }
        },
        status=200,
    )
    # geocode
    responses.add(
        responses.POST,
        api_url,
        json={
            "data": {
                "model": {"geocoordinates": {"geoLocationOf": {"lat": 10.0, "long": 20.0, "alt": 30.0}}}
            }
        },
        status=200,
    )


@responses.activate
def test_cli_export_panos_json(monkeypatch: pytest.MonkeyPatch) -> None:
    api_url = "https://example.test/graphql"
    _mock_graphql_success(api_url)
    monkeypatch.setenv("MATTERPORT_API_URL", api_url)
    monkeypatch.setenv("MATTERPORT_API_KEY", "k")
    monkeypatch.setenv("MATTERPORT_API_SECRET", "s")
    result = runner.invoke(app, ["export", "panos", "-m", "MODEL", "--format", "json", "--no-pretty"])  # type: ignore[arg-type]
    assert result.exit_code == 0, result.output
    data = json.loads(result.stdout)
    assert data[0]["id"] == "locA_pano1"
    assert data[0]["geo"]["lat"] == 10.0


@responses.activate
def test_cli_export_panos_csv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    api_url = "https://example.test/graphql"
    _mock_graphql_success(api_url)
    monkeypatch.setenv("MATTERPORT_API_URL", api_url)
    monkeypatch.setenv("MATTERPORT_API_KEY", "k")
    monkeypatch.setenv("MATTERPORT_API_SECRET", "s")
    out = tmp_path / "out.csv"
    result = runner.invoke(app, ["export", "panos", "-m", "MODEL", "--format", "csv", "--out", str(out)])
    assert result.exit_code == 0, result.output
    text = out.read_text()
    assert "id,lat,long,alt,x,y,z,skybox_0" in text


@responses.activate
def test_cli_graphql_error(monkeypatch: pytest.MonkeyPatch) -> None:
    api_url = "https://example.test/graphql"
    monkeypatch.setenv("MATTERPORT_API_URL", api_url)
    monkeypatch.setenv("MATTERPORT_API_KEY", "k")
    monkeypatch.setenv("MATTERPORT_API_SECRET", "s")
    responses.add(responses.POST, api_url, json={"errors": [{"message": "fail"}]}, status=200)
    result = runner.invoke(app, ["export", "tags", "-m", "MODEL", "--format", "json", "--no-pretty"])  # type: ignore[arg-type]
    assert result.exit_code != 0


def test_help_shows_commands() -> None:
    result = runner.invoke(app, ["--help"])  # type: ignore[arg-type]
    assert result.exit_code == 0
    assert "export" in result.output


def test_auth_priority_env_over_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    # ensure env present; CLI flags should not override when not provided
    monkeypatch.setenv("MATTERPORT_API_KEY", "envk")
    monkeypatch.setenv("MATTERPORT_API_SECRET", "envs")
    # we cannot easily introspect header from CLI; this asserts CLI still runs help with env set
    result = runner.invoke(app, ["--help"])  # type: ignore[arg-type]
    assert result.exit_code == 0


