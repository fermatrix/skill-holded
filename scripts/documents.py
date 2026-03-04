#!/usr/bin/env python3
"""
Holded documents operations — list, get, create, pay, send, download PDF.
Covers all document types: invoice, creditnote, estimate, order, proforma,
waybill, salesreceipt, expense, purchaserefund, purchaseorder.
"""

import sys
import json
import datetime
from holded_client import HoldedClient, error_exit


def _to_ts(date_str):
    """Convert YYYY-MM-DD to Unix timestamp (int)."""
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    return int(dt.timestamp())


def _default_range():
    """Default range: from 2 years ago to today."""
    today = datetime.date.today()
    two_years_ago = today.replace(year=today.year - 2)
    return _to_ts(str(two_years_ago)), _to_ts(str(today))

# Map of user-facing alias → Holded unified API docType name
# Note: 'proforma' and 'expense' are NOT valid types in Holded unified endpoint (HTTP 400)
DOC_TYPES = {
    "invoice":       "invoice",
    "creditnote":    "creditnote",
    "estimate":      "estimate",
    "order":         "salesorder",
    "salesorder":    "salesorder",
    "waybill":       "waybill",
    "salesreceipt":  "salesreceipt",
    "purchaserefund":"purchaserefund",
    "purchaseorder": "purchaseorder",
}

BASE = "invoicing/v1/documents"


def _endpoint(doc_type):
    key = doc_type.lower()
    if key not in DOC_TYPES:
        raise RuntimeError(
            f"Unknown document type '{doc_type}'. "
            f"Valid types: {', '.join(DOC_TYPES)}"
        )
    return f"{BASE}/{DOC_TYPES[key]}"


def _fmt(d, doc_type):
    """Normalize a document record.
    Holded returns contact as a string ID and contactName as the display name.
    """
    return {
        "id":          d.get("id", ""),
        "doc_type":    doc_type,
        "number":      d.get("docNumber") or d.get("number", ""),
        "date":        d.get("date", ""),
        "due_date":    d.get("dueDate", ""),
        "status":      d.get("status", ""),
        "contact_id":  d.get("contact", "") or d.get("contactId", ""),
        "contact":     d.get("contactName", "") or "",
        "total":       d.get("total", 0),
        "subtotal":    d.get("subtotal", 0),
        "tax_total":   d.get("taxTotal", 0),
        "currency":    d.get("currency", "EUR"),
        "notes":       d.get("notes", "") or "",
        "ref":         d.get("ref", "") or "",
        "tags":        d.get("tags", []),
    }


def list_documents(client, doc_type, date_from=None, date_to=None,
                   contact_id=None, paid=None, sort=None):
    """
    List documents using Holded's time-range pagination.
    date_from / date_to: YYYY-MM-DD strings (default: last 2 years).
    contact_id: filter by Holded contact ID.
    paid: '0' (unpaid) or '1' (paid).
    sort: 'date' or other Holded sort values.
    """
    if date_from:
        start_ts = _to_ts(date_from)
    else:
        start_ts, _ = _default_range()

    if date_to:
        end_ts = _to_ts(date_to)
    else:
        _, end_ts = _default_range()

    params = {"starttmp": start_ts, "endtmp": end_ts}
    if contact_id: params["contactid"] = contact_id
    if paid is not None: params["paid"] = paid
    if sort:       params["sort"]      = sort

    result = client.get(_endpoint(doc_type), params=params)
    if isinstance(result, list):
        return [_fmt(d, doc_type) for d in result]
    return []


def search_documents(client, doc_type, query, limit=20, date_from=None, date_to=None):
    """Search documents by contact name, number, or ref within a date range."""
    query_lower = query.lower()
    docs = list_documents(client, doc_type, date_from=date_from, date_to=date_to)
    matches = []
    for d in docs:
        name   = (d.get("contact")  or "").lower()
        number = (d.get("number")   or "").lower()
        ref    = (d.get("ref")      or "").lower()
        if query_lower in name or query_lower in number or query_lower in ref:
            matches.append(d)
            if len(matches) >= limit:
                break
    return matches


def get_document(client, doc_type, doc_id):
    """Get a single document by ID with full line details."""
    result = client.get(f"{_endpoint(doc_type)}/{doc_id}")
    if not result or "error" in result:
        return {"error": f"Document {doc_id} not found"}
    doc = _fmt(result, doc_type)
    # Include line items if present
    lines = result.get("items") or result.get("lines") or []
    doc["lines"] = [
        {
            "product_id":   ln.get("productId", ""),
            "account_id":   ln.get("accountingAccountId", "") or "",
            "name":         ln.get("name", "") or ln.get("desc", ""),
            "quantity":     ln.get("units", 0),
            "price":        ln.get("cost", 0),
            "discount":     ln.get("discount", 0),
            "tax":          ln.get("tax", 0),
            "subtotal":     ln.get("subtotal", 0),
            "sku":          ln.get("sku", "") or "",
        }
        for ln in lines
    ]
    return doc


def create_document(client, doc_type, contact_id, date, items, notes=None,
                    due_date=None, ref=None, currency=None):
    """
    Create a new document.

    items: list of dicts with keys:
        name (str), quantity (float), price (float),
        discount (float, optional), tax (float, optional),
        product_id (str, optional)
    """
    data = {
        "contactId": contact_id,
        "date":      date,
        "items":     [
            {
                "name":     it["name"],
                "units":    it.get("quantity", 1),
                "cost":     it["price"],
                **({"discount": it["discount"]} if it.get("discount") else {}),
                **({"tax":      it["tax"]}      if it.get("tax")      else {}),
                **({"productId":it["product_id"]} if it.get("product_id") else {}),
            }
            for it in items
        ],
    }
    if notes:    data["notes"]    = notes
    if due_date: data["dueDate"]  = due_date
    if ref:      data["ref"]      = ref
    if currency: data["currency"] = currency

    result = client.post(_endpoint(doc_type), data)
    if result.get("status") == 1 or result.get("id"):
        doc_id = result.get("info", {}).get("id") or result.get("id")
        return {"status": "created", "id": doc_id, "doc_type": doc_type}
    return {"error": "Failed to create document", "detail": result}


def pay_document(client, doc_type, doc_id, account_id, date, amount,
                 payment_method=None, notes=None):
    """Mark a document as paid."""
    data = {
        "accountId": account_id,
        "date":      date,
        "amount":    amount,
    }
    if payment_method: data["paymentMethod"] = payment_method
    if notes:          data["notes"]         = notes

    result = client.post(f"{_endpoint(doc_type)}/{doc_id}/pay", data)
    if result.get("status") == 1:
        return {"status": "paid", "id": doc_id}
    return {"error": "Failed to pay document", "detail": result}


def send_document(client, doc_type, doc_id, emails, subject=None, body=None):
    """Send a document by email."""
    data = {"emails": emails if isinstance(emails, list) else [emails]}
    if subject: data["subject"] = subject
    if body:    data["body"]    = body

    result = client.post(f"{_endpoint(doc_type)}/{doc_id}/send", data)
    if result.get("status") == 1:
        return {"status": "sent", "id": doc_id}
    return {"error": "Failed to send document", "detail": result}


def get_pdf(client, doc_type, doc_id, output_path):
    """Download PDF of a document and save to output_path."""
    import os
    content = client.get_binary(f"{_endpoint(doc_type)}/{doc_id}/pdf")
    if not content:
        return {"error": "No PDF content returned"}
    with open(output_path, "wb") as f:
        f.write(content)
    return {"status": "downloaded", "path": output_path, "size_bytes": len(content)}


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(json.dumps({
            "error": "Usage: documents.py <ALIAS> <doc_type> <command> [args...]",
            "doc_types": list(DOC_TYPES.keys()),
            "commands": {
                "list":   "documents.py ENZO invoice list [date_from] [date_to] [contact_id] [paid] [sort]",
                "search": "documents.py ENZO invoice search <query> [limit] [date_from] [date_to]",
                "get":    "documents.py ENZO invoice get <doc_id>",
                "create": "documents.py ENZO invoice create <contact_id> <date> <items_json> [notes] [due_date] [ref]",
                "pay":    "documents.py ENZO invoice pay <doc_id> <account_id> <date> <amount> [method] [notes]",
                "send":   "documents.py ENZO invoice send <doc_id> <email_or_emails_json> [subject] [body]",
                "pdf":    "documents.py ENZO invoice pdf <doc_id> <output_path>",
            },
            "notes": "date format: YYYY-MM-DD  |  paid: 0=unpaid 1=paid"
        }, indent=2))
        sys.exit(1)

    alias    = sys.argv[1]
    doc_type = sys.argv[2]
    cmd      = sys.argv[3]

    try:
        client = HoldedClient(alias)

        if cmd == "list":
            date_from  = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "-" else None
            date_to    = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] != "-" else None
            contact_id = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != "-" else None
            paid       = sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] != "-" else None
            sort       = sys.argv[8] if len(sys.argv) > 8 else None
            results    = list_documents(client, doc_type, date_from=date_from,
                                        date_to=date_to, contact_id=contact_id,
                                        paid=paid, sort=sort)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "search":
            query     = sys.argv[4] if len(sys.argv) > 4 else ""
            limit     = int(sys.argv[5]) if len(sys.argv) > 5 else 20
            date_from = sys.argv[6] if len(sys.argv) > 6 and sys.argv[6] != "-" else None
            date_to   = sys.argv[7] if len(sys.argv) > 7 and sys.argv[7] != "-" else None
            results   = search_documents(client, doc_type, query, limit=limit,
                                         date_from=date_from, date_to=date_to)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "get":
            result = get_document(client, doc_type, sys.argv[4])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "create":
            contact_id = sys.argv[4]
            date       = sys.argv[5]
            items      = json.loads(sys.argv[6])
            notes      = sys.argv[7]  if len(sys.argv) > 7  else None
            due_date   = sys.argv[8]  if len(sys.argv) > 8  else None
            ref        = sys.argv[9]  if len(sys.argv) > 9  else None
            result     = create_document(client, doc_type, contact_id, date, items,
                                         notes=notes, due_date=due_date, ref=ref)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "pay":
            doc_id     = sys.argv[4]
            account_id = sys.argv[5]
            date       = sys.argv[6]
            amount     = float(sys.argv[7])
            method     = sys.argv[8] if len(sys.argv) > 8 else None
            notes      = sys.argv[9] if len(sys.argv) > 9 else None
            result     = pay_document(client, doc_type, doc_id, account_id,
                                      date, amount, payment_method=method, notes=notes)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "send":
            doc_id  = sys.argv[4]
            raw     = sys.argv[5]
            emails  = json.loads(raw) if raw.startswith("[") else raw
            subject = sys.argv[6] if len(sys.argv) > 6 else None
            body    = sys.argv[7] if len(sys.argv) > 7 else None
            result  = send_document(client, doc_type, doc_id, emails,
                                    subject=subject, body=body)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "pdf":
            doc_id      = sys.argv[4]
            output_path = sys.argv[5]
            result      = get_pdf(client, doc_type, doc_id, output_path)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}")

    except RuntimeError as e:
        error_exit(str(e))
