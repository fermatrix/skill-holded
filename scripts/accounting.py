#!/usr/bin/env python3
"""
Holded accounting operations.

Documented accounting endpoints (accounting/v1):
  - /accounting/v1/dailyledger    — Daily ledger entries
  - /accounting/v1/chartofaccounts — Chart of accounts

NOTE: Some API keys (e.g. read-only sub-keys) may receive HTML instead of JSON
from the accounting endpoints, indicating the key lacks reporting access.
Only taxes are always available via /invoicing/v1/taxes.
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


def list_ledger(client, page=1, date_from=None, date_to=None):
    """List daily ledger entries. Endpoint: /accounting/v1/dailyledger
    date_from / date_to: YYYY-MM-DD strings. Both are mandatory per API;
    defaults to Jan 1 – Dec 31 of the current year.
    """
    import datetime, time

    def _to_ts(date_str):
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return int(time.mktime(dt.timetuple()))

    year = datetime.date.today().year
    params = {
        "page":     page,
        "starttmp": _to_ts(date_from or f"{year}-01-01"),
        "endtmp":   _to_ts(date_to   or f"{year}-12-31"),
    }

    return client.get("accounting/v1/dailyledger", params=params)


def list_accounts(client, date_from=None, date_to=None, include_empty=0):
    """List chart of accounts. Endpoint: /accounting/v1/chartofaccounts
    date_from / date_to: YYYY-MM-DD strings (optional).
    include_empty: 0 = exclude empty accounts, 1 = include.
    """
    import datetime, time

    def _to_ts(date_str):
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return int(time.mktime(dt.timetuple()))

    params = {"includeEmpty": include_empty}
    if date_from:
        params["starttmp"] = _to_ts(date_from)
    if date_to:
        params["endtmp"] = _to_ts(date_to)

    return client.get("accounting/v1/chartofaccounts", params=params)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: accounting.py <ALIAS> <command> [args...]",
            "commands": {
                "taxes":    "accounting.py MYCO taxes",
                "search":   "accounting.py MYCO search <query>",
                "ledger":   "accounting.py MYCO ledger [page] [date_from] [date_to]",
                "accounts": "accounting.py MYCO accounts [date_from] [date_to] [include_empty]",
            },
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

        elif cmd == "ledger":
            page      = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            date_from = sys.argv[4] if len(sys.argv) > 4 else None
            date_to   = sys.argv[5] if len(sys.argv) > 5 else None
            results   = list_ledger(client, page=page, date_from=date_from, date_to=date_to)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "accounts":
            date_from     = sys.argv[3] if len(sys.argv) > 3 else None
            date_to       = sys.argv[4] if len(sys.argv) > 4 else None
            include_empty = int(sys.argv[5]) if len(sys.argv) > 5 else 0
            results       = list_accounts(client, date_from=date_from, date_to=date_to, include_empty=include_empty)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}. Available: taxes, search, ledger, accounts")

    except RuntimeError as e:
        error_exit(str(e))
