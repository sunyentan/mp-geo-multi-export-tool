from __future__ import annotations

import json
from typing import Any

import pytest
import responses

from mp_geo_export.api import ApiClient, GraphQLError


API_URL = "https://example.test/graphql"


def _gql(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    return {"query": query, "variables": variables}


@responses.activate
def test_fetch_and_geocode_success() -> None:
    client = ApiClient(API_URL, auth_header="Basic test")

    # Mock sweeps
    responses.add(
        responses.POST,
        API_URL,
        json={
            "data": {
                "model": {
                    "locations": [
                        {
                            "id": "loc1",
                            "position": {"x": 1, "y": 2, "z": 3},
                            "panos": [
                                {"skybox": {"children": [f"u{i}" for i in range(6)]}},
                            ],
                        }
                    ]
                }
            }
        },
        status=200,
    )

    # Mock geocode
    responses.add(
        responses.POST,
        API_URL,
        json={
            "data": {
                "model": {"geocoordinates": {"geoLocationOf": {"lat": 1.0, "long": 2.0, "alt": 3.0}}}
            }
        },
        status=200,
    )

    locs = client.fetch_locations("M", "2k")
    assert len(locs) == 1
    geo = client.geocode_point("M", {"x": 1, "y": 2, "z": 3})
    assert geo["lat"] == 1.0
    # batch geocode preserves length
    out = client.batch_geocode("M", [{"x": 1, "y": 2, "z": 3}], concurrency=2)
    assert len(out) == 1


@responses.activate
def test_graphql_error_bubbles_up() -> None:
    client = ApiClient(API_URL, auth_header="Basic test", retries=0)
    responses.add(
        responses.POST,
        API_URL,
        json={"errors": [{"message": "boom"}]},
        status=200,
    )
    with pytest.raises(GraphQLError):
        client.fetch_tags("M")


