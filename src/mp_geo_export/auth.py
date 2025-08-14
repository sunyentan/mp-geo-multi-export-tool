from __future__ import annotations

import base64
import getpass
import os
from typing import Optional

import keyring

SERVICE = "mp-geo-export"
ACCOUNT = "matterport-basic"


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def get_auth_header(
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None,
    save_to_keyring: bool = False,
) -> str:
    # Priority: keyring -> env -> explicit args -> prompt
    key: Optional[str]
    secret: Optional[str]

    stored = keyring.get_password(SERVICE, ACCOUNT)
    if stored:
        try:
            key, secret = stored.split(":", 1)
        except ValueError:
            key, secret = None, None
    else:
        key, secret = None, None

    if not (key and secret):
        key = os.getenv("MATTERPORT_API_KEY")
        secret = os.getenv("MATTERPORT_API_SECRET")

    if not (key and secret):
        key = api_key
        secret = api_secret

    if not (key and secret):
        print("Enter Matterport API credentials:")
        key = (key or input("API key: ").strip())
        secret = (secret or getpass.getpass("API secret: ").strip())
        if save_to_keyring:
            keyring.set_password(SERVICE, ACCOUNT, f"{key}:{secret}")

    token = _b64(f"{key}:{secret}")
    return f"Basic {token}"


