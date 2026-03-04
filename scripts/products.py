#!/usr/bin/env python3
"""
Holded products/services operations — search, get, create, update, stock.
Uses /api/invoicing/v1/products endpoint.
"""

import sys
import json
from holded_client import HoldedClient, error_exit

ENDPOINT = "invoicing/v1/products"


def _fmt(p):
    """Normalize a product record."""
    return {
        "id":          p.get("id", ""),
        "name":        p.get("name", ""),
        "sku":         p.get("sku", "") or "",
        "description": p.get("desc", "") or "",
        "kind":        p.get("kind", ""),          # product / service
        "type":        p.get("type", ""),
        "price":       p.get("price", 0),
        "cost":        p.get("cost", 0),
        "tax":         p.get("tax", 0),
        "purchase_tax":p.get("purchaseTax", 0),
        "account":     p.get("account", "") or "",
        "purchase_account": p.get("purchaseAccount", "") or "",
        "tags":        p.get("tags", []),
        "stock":       p.get("realStock", None),
        "min_stock":   p.get("minStock", None),
        "unit":        p.get("unit", "") or "",
        "barcode":     p.get("barcode", "") or "",
        "sales_account":   p.get("salesAccount", "") or "",
    }


def list_products(client, page=1, kind=None):
    """List products (paginated, 50 per page). kind: 'product' or 'service'."""
    params = {"page": page}
    if kind:
        params["kind"] = kind
    result = client.get(ENDPOINT, params=params)
    if isinstance(result, list):
        return [_fmt(p) for p in result]
    return []


def search_products(client, query, limit=20, kind=None):
    """Search products by name, SKU, or description."""
    query_lower = query.lower()
    matches = []
    page = 1
    while len(matches) < limit:
        params = {"page": page}
        if kind:
            params["kind"] = kind
        products = client.get(ENDPOINT, params=params)
        if not products or not isinstance(products, list):
            break
        for p in products:
            name = (p.get("name") or "").lower()
            sku  = (p.get("sku")  or "").lower()
            desc = (p.get("desc") or "").lower()
            if query_lower in name or query_lower in sku or query_lower in desc:
                matches.append(_fmt(p))
                if len(matches) >= limit:
                    break
        if len(products) < 50:
            break
        page += 1
    return matches


def get_product(client, product_id):
    """Get a single product by ID."""
    result = client.get(f"{ENDPOINT}/{product_id}")
    if not result or "error" in result:
        return {"error": f"Product {product_id} not found"}
    return _fmt(result)


def create_product(client, name, price, kind="product", sku=None, description=None,
                   cost=None, tax=None, account=None, unit=None, barcode=None):
    """Create a new product or service."""
    data = {"name": name, "price": price, "kind": kind}
    if sku:         data["sku"]             = sku
    if description: data["desc"]            = description
    if cost:        data["cost"]            = cost
    if tax:         data["tax"]             = tax
    if account:     data["account"]         = account
    if unit:        data["unit"]            = unit
    if barcode:     data["barcode"]         = barcode

    result = client.post(ENDPOINT, data)
    if result.get("status") == 1 or result.get("id"):
        product_id = result.get("info", {}).get("id") or result.get("id")
        return {"status": "created", "id": product_id, "name": name}
    return {"error": "Failed to create product", "detail": result}


def update_product(client, product_id, fields):
    """Update product fields. fields is a dict of Holded field names."""
    result = client.put(f"{ENDPOINT}/{product_id}", fields)
    if result.get("status") == 1:
        return {"status": "updated", "id": product_id}
    return {"error": "Failed to update product", "detail": result}


def get_stock(client, product_id):
    """Get stock levels for a product across warehouses."""
    result = client.get(f"{ENDPOINT}/{product_id}/stock")
    if not result or "error" in result:
        return {"error": f"Stock for product {product_id} not found"}
    # Holded returns a list of warehouse stock entries or a dict
    if isinstance(result, list):
        return {
            "product_id": product_id,
            "warehouses": [
                {
                    "warehouse_id":   s.get("warehouseId", ""),
                    "warehouse_name": s.get("warehouseName", ""),
                    "stock":          s.get("realStock", 0),
                    "reserved":       s.get("reservedStock", 0),
                }
                for s in result
            ]
        }
    return result


def list_warehouses(client):
    """List all warehouses."""
    result = client.get("invoicing/v1/warehouses")
    if isinstance(result, list):
        return [
            {
                "id":      w.get("id", ""),
                "name":    w.get("name", ""),
                "address": w.get("address", "") or "",
                "default": w.get("default", False),
            }
            for w in result
        ]
    return []


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Usage: products.py <ALIAS> <command> [args...]",
            "commands": {
                "list":       "products.py ENZO list [page] [kind]",
                "search":     "products.py ENZO search <query> [limit] [kind]",
                "get":        "products.py ENZO get <product_id>",
                "create":     "products.py ENZO create <name> <price> [kind] [sku] [description]",
                "update":     "products.py ENZO update <product_id> <json_fields>",
                "stock":      "products.py ENZO stock <product_id>",
                "warehouses": "products.py ENZO warehouses",
            }
        }, indent=2))
        sys.exit(1)

    alias = sys.argv[1]
    cmd   = sys.argv[2]

    try:
        client = HoldedClient(alias)

        if cmd == "list":
            page    = int(sys.argv[3]) if len(sys.argv) > 3 else 1
            kind    = sys.argv[4]      if len(sys.argv) > 4 else None
            results = list_products(client, page=page, kind=kind)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "search":
            query   = sys.argv[3]
            limit   = int(sys.argv[4]) if len(sys.argv) > 4 else 20
            kind    = sys.argv[5]      if len(sys.argv) > 5 else None
            results = search_products(client, query, limit=limit, kind=kind)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        elif cmd == "get":
            result = get_product(client, sys.argv[3])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "create":
            name   = sys.argv[3]
            price  = float(sys.argv[4])
            kind   = sys.argv[5]      if len(sys.argv) > 5 else "product"
            sku    = sys.argv[6]      if len(sys.argv) > 6 else None
            desc   = sys.argv[7]      if len(sys.argv) > 7 else None
            result = create_product(client, name, price, kind=kind, sku=sku, description=desc)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "update":
            product_id = sys.argv[3]
            fields     = json.loads(sys.argv[4])
            result     = update_product(client, product_id, fields)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "stock":
            result = get_stock(client, sys.argv[3])
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "warehouses":
            results = list_warehouses(client)
            print(json.dumps(results, indent=2, ensure_ascii=False))

        else:
            error_exit(f"Unknown command: {cmd}")

    except RuntimeError as e:
        error_exit(str(e))
