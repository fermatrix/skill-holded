#!/usr/bin/env python3
"""
Holded accounting operations — chart of accounts, daily ledger, taxes, treasury.
Uses /api/accounting/v1/ endpoints.
"""

import sys
import json
from holded_client import HoldedClient, error_exit

BASE = "accounting/v1"


def list_accounts(client, page=1):
    """List accounting accounts (chart of accounts)."""
    result = client.get(f"{BASE}/accounts", params={"page": page})
    if isinstance(result, list):
        return [
            {
                "id":       a.get("id", ""),
                "code":     a.get("num", "") or a.get("code", ""),
                "name":     a.get("name", ""),
                "type":     a.get("type", ""),
                "subtype":  a.get("subtype", "") or "",
                "balance":  a.get("balance", 0),
                "currency": a.get("currency", "EUR"),
            }
            for a in result
        ]
    return []


def search_accounts(client, query, limit=20):
    """Search accounting accounts by code or name."""
    query_lower = query.lower()
    matches = []
    page = 1
    while len(matches) < limit:
        accounts = client.get(f"{BASE}/accounts", params={"page": page})
        if not accounts or not isinstance(accounts, list):
            break
        for a in accounts:
            code = (a.get("num") or a.get("code") or "").lower()
            name = (a.get("name") or "").lower()
            if query_lower in code or query_lower in name:
                matches.append({
                    "id":      a.get("id", ""),
                    "code":    a.get("num", "") or a.get("code", ""),
                    "name":    a.get("name", ""),
                    "type":    a.get("type", ""),
                    "balance": a.get("balance", 0),
                })
                if len(matches) >= limit:
                    break
        if len(accounts) < 50:
            break
        page += 1
    return matches


def get_ledger(client, account_id, date_from=None, date_to=None):
    """Get daily ledger entries for an account."""
    params = {}
    if date_from: params["dateFrom"] = date_from
    if date_to:   params["dateTo"]   = date_to
    result = client.get(f"{BASE}/dailyledger/{account_id}", params=params or None)
    if isinstance(result, list):
        return [
            {
                "date":        e.get("date", ""),
                "description": e.get("desc", "") or e.get("description", ""),
                "debit":       e.get("debit", 0),
                "credit":      e.get("credit", 0),
                "balance":     e.get("balance", 0),
                "document":    e.get("docNumber", "") or "",
                "contact":     e.get("contactName", "") or "",
            }
            for e in result
        ]
    return []


def list_taxes(client):
    """List all configured taxes."""
    result = client.get(f"{BASE}/taxes")
    if isinstance(result, list):
        return [
            {
                "id":        t.get("id", ""),
                "name":      t.get("name", ""),
                "rate":      t.get("tax", 0),
                "type":      t.get("type", ""),
                "purchase":  t.get("purchase", False),
            }
            for t in result
        ]
    return []


def list_treasury(client, page=1):
    """List treasury accounts (bank accounts, cash)."""
    result = client.get(f"{BASE}/treasury", params={"page": page})
    if isinstance(result, list):
        return [
            {
                "id":       t.get("id", ""),
                "name":     t.get("name", ""),
                "type":     t.get("type", ""),
                "balance":  t.get("balance", 0),
                "currency": t.get("currency", "EUR"),
                "iban":     t.get("iban", "") or "",
            }
            for t in result
        ]
    return []


def get_treasury_movements(client, account_id, date_from=None, date_to=None, page=1):
    """Get movements for a treasury account."""
    params = {"page": page}
    if date_from: params["dateFrom"] = date_from
    if date_to:   params["dateTo"]   = date_to
    result = client.get(f"{BASE}/treasury/{account_id}/movements", params=params)
    if isinstance(result, list):
        return [
            {
                "id":          m.get("id", ""),
                "date":        m.get("date", ""),
                "description": m.get("desc", "") or m.get("description", ""),
                "amount":      m.get("amount", 0),
                "type":        m.get("type", ""),
                "document":    m.get("docNumber", "") or "",
                "contact":     m.get("contactName", "") or "",
                "balance":     m.get("balance", 0),
            }
            for m in result
        ]
    return []


def get_profit_loss(client, date_from, date_to):
    """Get profit & loss report for a period."""
    params = {"dateFrom": date_from, "dateTo": date_to}
    result = client.get(f"{BASE}/reports/profitloss", params=params)
    return result if result else {"error": "No P&L data returned"}


def get_balance_sheet(client, date):
    """Get balance sheet as of a given date (YYYY-MM-DD)."""
    result = client.get(f"{BASE}/reports/balancesheet", params={"date": date})
    return result if result else {"error": "No balance sheet data returned"}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: accounting.py <ALIAS> <command> [args...]",
            "commands": {
                "accounts":    "accounting.py ENZO accounts [page]",
                "search":      "accounting.py ENZO search <query> [limit]",
                "ledger":      "accounting.py ENZO ledger <account_id> [date_from] [date_to]",
                "taxes":       "accounting.py ENZO taxes",
                "treasury":    "accounting.py ENZO treasury [page]",
                "movements":   "accounting.py ENZO movements <treasury_id> [date_from] [date_to] [page]",
                "profitloss":  "accounting.py ENZO profitloss <date_from> <date_to>",
                "balancesheet":"accounting.py ENZO balancesheet <date>",
            }
        }, indent=2))
        sys.exit(1)

    alias = sys.argv[1]
    cmd   = sys.argv[2]

    try:
        client = HoldedClient(alias)

        if cmd == "accounts":
            page    = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            results = list_accounts(client, page=page)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "search":
            query   = sys.argv[3]
            limit   = int(sys.argv[4]) if len(sys.argv) > 4 else 20
            results = search_accounts(client, query, limit=limit)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "ledger":
            account_id = sys.argv[3]
            date_from  = sys.argv[4] if len(sys.argv) > 4 else None
            date_to    = sys.argv[5] if len(sys.argv) > 5 else None
            results    = get_ledger(client, account_id, date_from=date_from, date_to=date_to)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "taxes":
            results = list_taxes(client)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "treasury":
            page    = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            results = list_treasury(client, page=page)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "movements":
            account_id = sys.argv[3]
            date_from  = sys.argv[4] if len(sys.argv) > 4 else None
            date_to    = sys.argv[5] if len(sys.argv) > 5 else None
            page       = int(sys.argv[6]) if len(sys.argv) > 6 else 1
            results    = get_treasury_movements(client, account_id,
                                                date_from=date_from, date_to=date_to,
                                                page=page)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "profitloss":
            result = get_profit_loss(client, sys.argv[3], sys.argv[4])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "balancesheet":
            result = get_balance_sheet(client, sys.argv[3])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}")

    except RuntimeError as e:
        error_exit(str(e))
