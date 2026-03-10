---
name: skill-holded
description: "Access Holded ERP via REST API. Use for contacts, invoices, estimates, sales orders, purchase orders, expenses, credit notes, proformas, waybills, products, warehouses, accounting accounts, ledger, taxes, and treasury. Supports searching, creating, updating, paying, sending and downloading PDFs for all document types. Triggers: Holded de MYCO, busca contacto en Holded, factura Holded, pedido Holded, producto Holded, contabilidad Holded, tesorería Holded."
---

# Holded ERP Skill

Interact with Holded ERP instances via REST API. Credentials are loaded from `.env`.

## Aliases

Instances are configured by alias in `.env`. Pattern: `HOLDED_{ALIAS}_API_KEY`

To add more instances, add entries to `.env`:
- `HOLDED_{ALIAS}_API_KEY` — Holded API key (from Settings → Integrations → API)

## Scripts Location

All scripts are in `/mnt/skills/user/holded/scripts/`.

---

## 1. Contacts

```bash
python /mnt/skills/user/holded/scripts/contacts.py MYCO search "Nitaki"
python /mnt/skills/user/holded/scripts/contacts.py MYCO search "nitaki" 50
python /mnt/skills/user/holded/scripts/contacts.py MYCO list [page]
python /mnt/skills/user/holded/scripts/contacts.py MYCO get <contact_id>
python /mnt/skills/user/holded/scripts/contacts.py MYCO create "Empresa SA" client email@example.com
python /mnt/skills/user/holded/scripts/contacts.py MYCO update <contact_id> '{"email": "new@example.com"}'
```

Contact `type` values: `client`, `supplier`, `debtor`, `creditor`.

Fields returned: `id`, `name`, `code`, `type`, `email`, `phone`, `mobile`, `vat_number`, `address`, `city`, `postal`, `country`, `notes`, `tags`.

---

## 2. Documents

All document types share the same command structure. Use `doc_type` as the second argument.

**⚠️ INVOICES vs PURCHASES — critical distinction:**
| doc_type | Holded name | Meaning |
|---|---|---|
| `invoice` | invoice | Factura **emitida a un cliente** (venta) |
| `purchase` | purchase | Factura **recibida de un proveedor** (compra) |
| `creditnote` | creditnote | Abono / nota de crédito a cliente |
| `estimate` | estimate | Presupuesto |
| `salesorder` / `order` | salesorder | Pedido de venta |
| `waybill` | waybill | Albarán |
| `salesreceipt` | salesreceipt | Ticket / recibo de venta |
| `purchaserefund` | purchaserefund | Abono de proveedor |
| `purchaseorder` | purchaseorder | Pedido de compra a proveedor |

**Rule:** Use `invoice` for client invoices. Use `purchase` for supplier/vendor invoices. Never mix them.

```bash
# List by date range (Holded uses time ranges, not page numbers)
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice list
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice list 2025-01-01 2025-12-31
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice list 2025-01-01 2025-12-31 <contact_id>
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice list - - <contact_id> 0
# date_from/date_to: YYYY-MM-DD (default: last 2 years)  |  paid: 0=unpaid 1=paid  |  use - to skip optional args

# Search by contact name, doc number, or ref
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice search "Nitaki"
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice search "Nitaki" 20 2025-01-01 2025-12-31
python /mnt/skills/user/holded/scripts/documents.py MYCO estimate search "SPIRAL"
python /mnt/skills/user/holded/scripts/documents.py MYCO purchaseorder search "proveedor"

# Get full details with line items
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice get <doc_id>

# Create (items as JSON array)
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice create <contact_id> <date> \
  '[{"name": "Servicio", "quantity": 1, "price": 1000, "tax": 21}]' \
  "notes text" "due_date" "ref"

# Pay
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice pay <doc_id> <account_id> <date> <amount>

# Send by email
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice send <doc_id> "client@example.com"
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice send <doc_id> '["a@b.com","c@d.com"]'

# Download PDF
python /mnt/skills/user/holded/scripts/documents.py MYCO invoice pdf <doc_id> /mnt/user-data/outputs/doc.pdf
```

**Document line item fields:**
- `name` (required), `quantity` (default 1), `price` (required)
- `discount` (optional, %), `tax` (optional, %)
- `product_id` (optional, links to product catalog)

**Document statuses:** `draft`, `sent`, `accepted`, `paid`, `overdue`, `closed`.

Fields returned: `id`, `doc_type`, `number`, `date`, `due_date`, `status`, `contact_id`, `contact`, `total`, `subtotal`, `tax_total`, `currency`, `notes`, `ref`, `tags`, `products`.

`products` field: `product_id`, `account_id` (accounting account — `accountingAccountId`), `name`, `quantity`, `price`, `discount`, `tax`, `subtotal`, `sku`.

---

## 3. Products & Services

```bash
# List all (paginated)
python /mnt/skills/user/holded/scripts/products.py MYCO list [page] [kind]

# Search by name, SKU, or description
python /mnt/skills/user/holded/scripts/products.py MYCO search "Consultoría" [limit] [kind]

# Get by ID
python /mnt/skills/user/holded/scripts/products.py MYCO get <product_id>

# Create
python /mnt/skills/user/holded/scripts/products.py MYCO create "Servicio Consulting" 1500 service

# Update
python /mnt/skills/user/holded/scripts/products.py MYCO update <product_id> '{"price": 1600}'

# Stock levels across warehouses
python /mnt/skills/user/holded/scripts/products.py MYCO stock <product_id>

# List warehouses
python /mnt/skills/user/holded/scripts/products.py MYCO warehouses
```

`kind` values: `product`, `service`. Fields returned: `id`, `name`, `sku`, `description`, `kind`, `price`, `cost`, `tax`, `stock`, `unit`, `barcode`.

---

## 4. Accounting

```bash
# List taxes
python /mnt/skills/user/holded/scripts/accounting.py MYCO taxes
python /mnt/skills/user/holded/scripts/accounting.py MYCO search "IVA"

# Daily ledger (starttmp/endtmp mandatory; defaults to current year)
python /mnt/skills/user/holded/scripts/accounting.py MYCO ledger
python /mnt/skills/user/holded/scripts/accounting.py MYCO ledger 1 2025-01-01 2025-12-31

# Chart of accounts
python /mnt/skills/user/holded/scripts/accounting.py MYCO accounts
python /mnt/skills/user/holded/scripts/accounting.py MYCO accounts 2025-01-01 2025-12-31 1
```

Taxes fields: `id`, `name`, `rate`, `type`, `purchase`.

> **Note:** Some API keys (e.g. read-only sub-keys) may receive HTML instead of JSON from `dailyledger` and `chartofaccounts`, indicating the key lacks reporting access.

---

## Important Notes

- All dates in **YYYY-MM-DD** format (Holded uses Unix timestamps internally — handled automatically)
- Documents are created in **draft** state by default
- Use `search` before `create` to avoid duplicate contacts or products
- Always show the user a summary before creating or paying documents
- `invoice` = facturas **emitidas a clientes**; `purchase` = facturas **recibidas de proveedores** — never confuse them
- `proforma` and `expense` are NOT valid document types in Holded REST API (HTTP 400)
- Holded `dailyledger` and `chartofaccounts` are available via REST API but require `starttmp`/`endtmp`; some API keys may receive HTML (no reporting access)
