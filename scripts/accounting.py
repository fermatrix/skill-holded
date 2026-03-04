#!/usr/bin/env python3
"""
Holded accounting operations.

NOTE: Holded does NOT expose accounting/ledger/treasury via REST API.
Those endpoints return HTML (the webapp). Only taxes are available
via /invoicing/v1/taxes.
"""

import sys
import json
from holded_client import HoldedClient, error_exit


def list_taxes(client):
    """List all configured taxes. Endpoint: /invoicing/v1/taxes"""
    result = client.get("invoicing/v1/taxes")
    if isinstance(result, list):
        return [
            {
                "id":       t.get("id", ""),
                "name":     t.get("name", ""),
                "rate":     t.get("tax", 0),
                "type":     t.get("type", ""),
                "purchase": t.get("purchase", False),
            }
            for t in result
        ]
    return []


def search_taxes(client, query):
    """Search taxes by name."""
    query_lower = query.lower()
    taxes = list_taxes(client)
    return [t for t in taxes if query_lower in t["name"].lower()]


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: accounting.py <ALIAS> <command> [args...]",
            "commands": {
                "taxes":  "accounting.py ENZO taxes",
                "search": "accounting.py ENZO search <query>",
            },
            "note": "Holded accounting/ledger/treasury are not available via REST API."
        }, indent=2))
        sys.exit(1)

    alias = sys.argv[1]
    cmd   = sys.argv[2]

    try:
        client = HoldedClient(alias)

        if cmd == "taxes":
            results = list_taxes(client)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "search":
            query   = sys.argv[3] if len(sys.argv) > 3 else ""
            results = search_taxes(client, query)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}. Available: taxes, search")

    except RuntimeError as e:
        error_exit(str(e))
