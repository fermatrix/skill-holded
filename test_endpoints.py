#!/usr/bin/env python3
"""
test_endpoints.py — smoke-test all skill-holded read endpoints.

Reads the FIRST alias found in ../skill-holded.env, then calls every
GET endpoint and reports whether it succeeds or fails, with a sample
of the response so you can verify the field names are correct.

Usage:
    python test_endpoints.py
    python test_endpoints.py SPIRAL   # override alias
"""

import sys
import os
import json
import re

# ── locate env file ────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE   = os.path.join(os.path.dirname(SCRIPT_DIR), "skill-holded.env")

# ── load env ───────────────────────────────────────────────────────────────────
def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

# ── pick first alias ───────────────────────────────────────────────────────────
def first_alias(env):
    for key in env:
        m = re.match(r"^HOLDED_(.+)_API_KEY$", key)
        if m and env[key]:
            return m.group(1)
    raise RuntimeError("No HOLDED_*_API_KEY with a value found in env file")

# ── pretty-print result ────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(label, data):
    if isinstance(data, list):
        count = len(data)
        sample = data[0] if data else {}
        print(f"  {GREEN}OK{RESET} {label}: {count} item(s)")
        if sample:
            print(f"    fields: {', '.join(sample.keys())}")
    elif isinstance(data, dict):
        if "error" in data:
            fail(label, data.get("error", "unknown error"))
            return
        print(f"  {GREEN}OK{RESET} {label}: dict with {len(data)} keys")
        print(f"    fields: {', '.join(data.keys())}")
    else:
        print(f"  {YELLOW}??{RESET} {label}: unexpected type {type(data).__name__}")

def fail(label, err):
    print(f"  {RED}FAIL{RESET} {label}: {err}")

def section(title):
    print(f"\n{BOLD}{'-'*60}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'-'*60}{RESET}")

# ── test runner ────────────────────────────────────────────────────────────────
def run(label, fn):
    try:
        result = fn()
        ok(label, result)
    except Exception as e:
        fail(label, str(e)[:200])

# ── main ───────────────────────────────────────────────────────────────────────
def main():
    if not os.path.exists(ENV_FILE):
        print(f"ERROR: env file not found: {ENV_FILE}")
        sys.exit(1)

    env = load_env(ENV_FILE)

    # allow override from command line
    if len(sys.argv) > 1:
        alias = sys.argv[1].upper()
    else:
        alias = first_alias(env)

    print(f"\n{BOLD}skill-holded endpoint smoke test{RESET}")
    print(f"Env file : {ENV_FILE}")
    print(f"Alias    : {alias}")

    # inject into environ so HoldedClient can find it
    for k, v in env.items():
        os.environ.setdefault(k, v)

    # add scripts/ to path
    sys.path.insert(0, os.path.join(SCRIPT_DIR, "scripts"))
    from holded_client import HoldedClient
    client = HoldedClient(alias)

    # safety guard: block any write operations so this script is read-only
    def _no_write(*args, **kwargs):
        raise RuntimeError("BLOCKED: test_endpoints.py is read-only — no POST/PUT/DELETE allowed")
    client.post   = _no_write
    client.put    = _no_write
    client.delete = _no_write

    # ── contacts ───────────────────────────────────────────────────────────────
    section("CONTACTS  /invoicing/v1/contacts")
    from contacts import list_contacts, search_contacts, get_contact

    run("contacts.list(page=1)",         lambda: list_contacts(client, page=1))
    run("contacts.search('a', limit=3)", lambda: search_contacts(client, "a", limit=3))

    # try get on first contact if list worked
    try:
        first = list_contacts(client, page=1)
        if first:
            cid = first[0]["id"]
            run(f"contacts.get({cid[:8]}…)", lambda: get_contact(client, cid))
    except Exception:
        pass

    # ── documents ──────────────────────────────────────────────────────────────
    from documents import list_documents, get_document, DOC_TYPES

    seen = set()
    for dt in DOC_TYPES.values():
        if dt in seen:
            continue
        seen.add(dt)
        section(f"DOCUMENTS  type={dt}")
        run(f"documents.list({dt}, last 2y)",
            lambda t=dt: list_documents(client, t))
        run(f"documents.list({dt}, 2025-01-01 to 2025-12-31)",
            lambda t=dt: list_documents(client, t,
                                        date_from="2025-01-01",
                                        date_to="2025-12-31"))

    # get() on first invoice/purchaseorder to verify line items include account_id
    for probe_type in ("invoice", "purchaseorder"):
        try:
            docs = list_documents(client, probe_type)
            if docs:
                did = docs[0]["id"]
                def _get_doc(t=probe_type, d=did):
                    result   = get_document(client, t, d)
                    products = result.get("products", [])
                    if products and "accountingAccountId" not in products[0]:
                        raise RuntimeError("accountingAccountId missing from products")
                    return result
                run(f"documents.get({probe_type}, {did[:8]}…) — lines+account_id",
                    _get_doc)
                break
        except Exception:
            pass

    # ── products ───────────────────────────────────────────────────────────────
    section("PRODUCTS  /invoicing/v1/products")
    from products import list_products, search_products, list_warehouses

    run("products.list(page=1)",             lambda: list_products(client, page=1))
    run("products.list(kind=service)",       lambda: list_products(client, kind="service"))
    run("products.search('a', limit=3)",     lambda: search_products(client, "a", limit=3))
    run("products.warehouses()",             lambda: list_warehouses(client))

    # ── taxes ───────────────────────────────────────────────────────────────────
    section("TAXES  /invoicing/v1/taxes")
    from accounting import list_taxes, search_taxes, list_ledger, list_accounts

    run("taxes.list()",          lambda: list_taxes(client))
    run("taxes.search('IVA')",   lambda: search_taxes(client, "IVA"))

    # ── accounting ──────────────────────────────────────────────────────────────
    # Estos endpoints están documentados en la API de Holded (accounting/v1).
    # Algunas API keys devuelven HTML en lugar de JSON (sin acceso a reporting).
    # El test los incluye igualmente para detectar si el acceso está disponible.
    import datetime as _dt
    _year = _dt.date.today().year

    section("ACCOUNTING  /accounting/v1/dailyledger")
    run(f"ledger.list({_year})",
        lambda: list_ledger(client, page=1))
    run(f"ledger.list({_year-1})",
        lambda y=_year-1: list_ledger(client, page=1,
                                      date_from=f"{y}-01-01",
                                      date_to=f"{y}-12-31"))

    section("ACCOUNTING  /accounting/v1/chartofaccounts")
    run("accounts.list()",
        lambda: list_accounts(client))
    run("accounts.list(include_empty=1)",
        lambda: list_accounts(client, include_empty=1))
    run(f"accounts.list({_year})",
        lambda y=_year: list_accounts(client,
                                      date_from=f"{y}-01-01",
                                      date_to=f"{y}-12-31"))

    print(f"\n{BOLD}Done.{RESET}\n")

if __name__ == "__main__":
    main()
