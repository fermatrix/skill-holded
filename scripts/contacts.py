#!/usr/bin/env python3
"""
Holded contacts operations — search, get, create, update.
Uses /api/invoicing/v1/contacts endpoint.
"""

import sys
import json
from holded_client import HoldedClient, error_exit

ENDPOINT = "invoicing/v1/contacts"


def _fmt(c):
    """Normalize a contact record."""
    return {
        "id":         c.get("id", ""),
        "name":       c.get("name", ""),
        "code":       c.get("code", "") or "",
        "type":       c.get("type", ""),           # client / supplier / debtor / creditor
        "email":      c.get("email", "") or "",
        "phone":      c.get("phone", "") or "",
        "mobile":     c.get("mobile", "") or "",
        "vat_number": c.get("vatNumber", "") or "",
        "address":    c.get("address", "") or "",
        "city":       c.get("city", "") or "",
        "postal":     c.get("postalCode", "") or "",
        "country":    c.get("country", "") or "",
        "notes":      c.get("notes", "") or "",
        "tags":       c.get("tags", []),
        "billing":    c.get("billAddress") or {},
    }


def list_contacts(client, page=1):
    """List contacts (paginated, 50 per page)."""
    result = client.get(ENDPOINT, params={"page": page})
    if isinstance(result, list):
        return [_fmt(c) for c in result]
    return []


def search_contacts(client, query, limit=20):
    """Search contacts by name (fetches pages until limit reached)."""
    query_lower = query.lower()
    matches = []
    page = 1
    while len(matches) < limit:
        contacts = client.get(ENDPOINT, params={"page": page})
        if not contacts or not isinstance(contacts, list):
            break
        for c in contacts:
            if query_lower in (c.get("name") or "").lower() or \
               query_lower in (c.get("email") or "").lower() or \
               query_lower in (c.get("code") or "").lower():
                matches.append(_fmt(c))
                if len(matches) >= limit:
                    break
        if len(contacts) < 50:
            break  # last page
        page += 1
    return matches


def get_contact(client, contact_id):
    """Get a single contact by ID."""
    result = client.get(f"{ENDPOINT}/{contact_id}")
    if not result or "error" in result:
        return {"error": f"Contact {contact_id} not found"}
    return _fmt(result)


def create_contact(client, name, contact_type="client", email=None, phone=None,
                   vat_number=None, address=None, city=None, postal=None,
                   country=None, notes=None, code=None):
    """Create a new contact."""
    data = {"name": name, "type": contact_type}
    if email:      data["email"]      = email
    if phone:      data["phone"]      = phone
    if vat_number: data["vatNumber"]  = vat_number
    if address:    data["address"]    = address
    if city:       data["city"]       = city
    if postal:     data["postalCode"] = postal
    if country:    data["country"]    = country
    if notes:      data["notes"]      = notes
    if code:       data["code"]       = code

    result = client.post(ENDPOINT, data)
    if result.get("status") == 1 or result.get("id"):
        contact_id = result.get("info", {}).get("id") or result.get("id")
        return {"status": "created", "id": contact_id, "name": name}
    return {"error": "Failed to create contact", "detail": result}


def update_contact(client, contact_id, fields):
    """Update contact fields. fields is a dict of Holded field names."""
    result = client.put(f"{ENDPOINT}/{contact_id}", fields)
    if result.get("status") == 1:
        return {"status": "updated", "id": contact_id}
    return {"error": "Failed to update contact", "detail": result}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: contacts.py <ALIAS> <command> [args...]",
            "commands": {
                "search": "contacts.py MYCO search <query> [limit]",
                "list":   "contacts.py MYCO list [page]",
                "get":    "contacts.py MYCO get <contact_id>",
                "create": "contacts.py MYCO create <name> [type] [email] [phone] [vat] [address] [city] [postal] [country]",
                "update": "contacts.py MYCO update <contact_id> <json_fields>",
            }
        }, indent=2))
        sys.exit(1)

    alias = sys.argv[1]
    cmd   = sys.argv[2]

    try:
        client = HoldedClient(alias)

        if cmd == "search":
            query   = sys.argv[3] if len(sys.argv) > 3 else ""
            limit   = int(sys.argv[4]) if len(sys.argv) > 4 else 20
            results = search_contacts(client, query, limit=limit)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "list":
            page    = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            results = list_contacts(client, page=page)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "get":
            result = get_contact(client, sys.argv[3])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "create":
            name    = sys.argv[3]
            ctype   = sys.argv[4]  if len(sys.argv) > 4  else "client"
            email   = sys.argv[5]  if len(sys.argv) > 5  else None
            phone   = sys.argv[6]  if len(sys.argv) > 6  else None
            vat     = sys.argv[7]  if len(sys.argv) > 7  else None
            address = sys.argv[8]  if len(sys.argv) > 8  else None
            city    = sys.argv[9]  if len(sys.argv) > 9  else None
            postal  = sys.argv[10] if len(sys.argv) > 10 else None
            country = sys.argv[11] if len(sys.argv) > 11 else None
            result  = create_contact(client, name, contact_type=ctype, email=email,
                                     phone=phone, vat_number=vat, address=address,
                                     city=city, postal=postal, country=country)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "update":
            contact_id = sys.argv[3]
            fields     = json.loads(sys.argv[4])
            result     = update_contact(client, contact_id, fields)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}")

    except RuntimeError as e:
        error_exit(str(e))
