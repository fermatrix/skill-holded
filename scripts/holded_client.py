#!/usr/bin/env python3
"""
Holded REST API client — Python stdlib only, no external dependencies.
Credentials loaded from .env with alias pattern: HOLDED_{ALIAS}_API_KEY
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL   = "https://api.holded.com/api"


def load_env():
    """Load .env file from skill directory."""
    env_path = os.path.join(SKILL_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip())


def error_exit(msg):
    print(json.dumps({"error": msg}))
    sys.exit(1)


class HoldedClient:
    """Holded REST API client."""

    def __init__(self, alias):
        load_env()
        a = alias.upper()
        self.api_key = os.environ.get(f"HOLDED_{a}_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                f"Missing HOLDED_{a}_API_KEY in .env"
            )

        self.headers = {
            "key":          self.api_key,
            "Content-Type": "application/json",
            "Accept":       "application/json",
        }

    # ── Internal request ──────────────────────────────────────────────────

    def _request(self, method, path, data=None, params=None, binary=False):
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        body = json.dumps(data).encode("utf-8") if data is not None else None
        req  = urllib.request.Request(url, data=body, headers=self.headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                content = resp.read()
                if binary:
                    return content
                return json.loads(content.decode()) if content else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            raise RuntimeError(f"HTTP {e.code}: {body[:500]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Connection failed: {e.reason}")

    # ── HTTP helpers ───────────────────────────────────────────────────────

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def get_binary(self, path):
        return self._request("GET", path, binary=True)

    def post(self, path, data=None):
        return self._request("POST", path, data=data or {})

    def put(self, path, data):
        return self._request("PUT", path, data=data)

    def delete(self, path):
        return self._request("DELETE", path)

    # ── Pagination helper ─────────────────────────────────────────────────

    def get_paginated(self, path, page=1, limit=50):
        return self.get(path, params={"page": page})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        error_exit("Usage: holded_client.py <ALIAS>")
    alias = sys.argv[1]
    try:
        client = HoldedClient(alias)
        # Quick connectivity test — list first page of contacts
        result = client.get("invoicing/v1/contacts", params={"page": 1})
        count  = len(result) if isinstance(result, list) else "?"
        print(json.dumps({"status": "connected", "alias": alias, "contacts_returned": count}))
    except RuntimeError as e:
        error_exit(str(e))
