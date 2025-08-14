from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = "https://api.matterport.com/api/graphql"


def api_url(override: str | None = None) -> str:
    return override or os.getenv("MATTERPORT_API_URL") or DEFAULT_URL


