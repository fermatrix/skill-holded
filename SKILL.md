---
name: skill-holded
description: "Access Holded ERP via REST API. Use for contacts, invoices, estimates, sales orders, purchase orders, expenses, credit notes, proformas, waybills, products, warehouses, accounting accounts, ledger, taxes, and treasury. Supports searching, creating, updating, paying, sending and downloading PDFs for all document types. Triggers: Holded de ENZO, busca contacto en Holded, factura Holded, pedido Holded, producto Holded, contabilidad Holded, tesorería Holded."
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
python /mnt/skills/user/holded/scripts/contacts.py ENZO search "Nitaki"
python /mnt/skills/user/holded/scripts/contacts.py ENZO search "nitaki" 50
python /mnt/skills/user/holded/scripts/contacts.py ENZO list [page]
python /mnt/skills/user/holded/scripts/contacts.py ENZO get <contact_id>
python /mnt/skills/user/holded/scripts/contacts.py ENZO create "Empresa SA" client email@example.com
python /mnt/skills/user/holded/scripts/contacts.py ENZO update <contact_id> '{"email": "new@example.com"}'
```

Contact `type` values: `client`, `supplier`, `debtor`, `creditor`.

Fields returned: `id`, `name`, `code`, `type`, `email`, `phone`, `mobile`, `vat_number`, `address`, `city`, `postal`, `country`, `notes`, `tags`.

---

## 2. Documents

All document types share the same command structure. Use `doc_type` as the second argument.

**Document types:** `invoice`, `creditnote`, `estimate`, `order`, `proforma`, `waybill`, `salesreceipt`, `expense`, `purchaserefund`, `purchaseorder`

```bash
# List (paginated)
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice list [page] [contact_id] [status]

# Search by contact name, doc number, or ref
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice search "Nitaki" [limit]
python /mnt/skills/user/holded/scripts/documents.py ENZO estimate search "SPIRAL"
python /mnt/skills/user/holded/scripts/documents.py ENZO purchaseorder search "proveedor"

# Get full details with line items
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice get <doc_id>

# Create (items as JSON array)
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice create <contact_id> <date> \
  '[{"name": "Servicio", "quantity": 1, "price": 1000, "tax": 21}]' \
  "notes text" "due_date" "ref"

# Pay
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice pay <doc_id> <account_id> <date> <amount>

# Send by email
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice send <doc_id> "client@example.com"
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice send <doc_id> '["a@b.com","c@d.com"]'

# Download PDF
python /mnt/skills/user/holded/scripts/documents.py ENZO invoice pdf <doc_id> /mnt/user-data/outputs/doc.pdf
```

**Document line item fields:**
- `name` (required), `quantity` (default 1), `price` (required)
- `discount` (optional, %), `tax` (optional, %)
- `product_id` (optional, links to product catalog)

**Document statuses:** `draft`, `sent`, `accepted`, `paid`, `overdue`, `closed`.

Fields returned: `id`, `doc_type`, `number`, `date`, `due_date`, `status`, `contact_id`, `contact`, `total`, `subtotal`, `tax_total`, `currency`, `notes`, `ref`, `tags`, `lines`.

---

## 3. Products & Services

```bash
# List all (paginated)
python /mnt/skills/user/holded/scripts/products.py ENZO list [page] [kind]

# Search by name, SKU, or description
python /mnt/skills/user/holded/scripts/products.py ENZO search "Consultoría" [limit] [kind]

# Get by ID
python /mnt/skills/user/holded/scripts/products.py ENZO get <product_id>

# Create
python /mnt/skills/user/holded/scripts/products.py ENZO create "Servicio Consulting" 1500 service

# Update
python /mnt/skills/user/holded/scripts/products.py ENZO update <product_id> '{"price": 1600}'

# Stock levels across warehouses
python /mnt/skills/user/holded/scripts/products.py ENZO stock <product_id>

# List warehouses
python /mnt/skills/user/holded/scripts/products.py ENZO warehouses
```

`kind` values: `product`, `service`. Fields returned: `id`, `name`, `sku`, `description`, `kind`, `price`, `cost`, `tax`, `stock`, `unit`, `barcode`.

---

## 4. Accounting

```bash
# Chart of accounts
python /mnt/skills/user/holded/scripts/accounting.py ENZO accounts [page]

# Search accounts by code or name
python /mnt/skills/user/holded/scripts/accounting.py ENZO search "705" [limit]
python /mnt/skills/user/holded/scripts/accounting.py ENZO search "ventas"

# Daily ledger for an account
python /mnt/skills/user/holded/scripts/accounting.py ENZO ledger <account_id> [date_from] [date_to]
# date format: YYYY-MM-DD

# Configured taxes
python /mnt/skills/user/holded/scripts/accounting.py ENZO taxes

# Treasury accounts (banks, cash)
python /mnt/skills/user/holded/scripts/accounting.py ENZO treasury [page]

# Treasury account movements
python /mnt/skills/user/holded/scripts/accounting.py ENZO movements <treasury_id> [date_from] [date_to] [page]

# P&L report
python /mnt/skills/user/holded/scripts/accounting.py ENZO profitloss 2025-01-01 2025-12-31

# Balance sheet
python /mnt/skills/user/holded/scripts/accounting.py ENZO balancesheet 2025-12-31
```

---

## Important Notes

- All dates in **YYYY-MM-DD** format (Holded uses Unix timestamps internally — handled automatically)
- Documents are created in **draft** state by default
- Use `search` before `create` to avoid duplicate contacts or products
- `pay` requires a valid treasury account ID — use `accounting.py ENZO treasury` to list them
- Always show the user a summary before creating or paying documents
