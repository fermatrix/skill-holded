# Changelog

All notable changes to this project are documented here.

---

## [1.0.5] - 2026-03-04

### Fixed
- `documents.py`: `get_document()` — expose `account_id` (`accountingAccountId`) in each line item, enabling lookup of the accounting account per invoice/purchase line
- `test_endpoints.py`: add `get()` probe on first available invoice/purchaseorder to verify `account_id` is present in line items
- `SKILL.md`: document line item fields including `account_id`

---

## [1.0.4] - 2026-03-04

### Added
- `accounting.py`: `list_ledger()` — daily ledger via `GET /accounting/v1/dailyledger` (params: page, date_from, date_to; starttmp/endtmp mandatory, defaults to current year)
- `accounting.py`: `list_accounts()` — chart of accounts via `GET /accounting/v1/chartofaccounts` (params: date_from, date_to, include_empty)
- `test_endpoints.py`: new sections for `ACCOUNTING /accounting/v1/dailyledger` and `/accounting/v1/chartofaccounts` with dynamic year ranges

---

## [1.0.3] - 2026-03-04

### Fixed
- `documents.py`: remove `proforma` and `expense` from DOC_TYPES (Holded returns HTTP 400 for these types)
- `products.py`: `list_warehouses()` — correct endpoint `/invoicing/v1/warehouses` (not `/inventory/v1/warehouses`)
- `accounting.py`: rewritten — Holded does not expose accounting/ledger/treasury via REST API; only taxes available via `/invoicing/v1/taxes`
- `holded_client.py`: `_request()` raises informative `RuntimeError` for non-JSON responses instead of bare `JSONDecodeError`

---

## [1.0.2] - 2026-03-04

### Fixed
- `documents.py`: `_fmt()` — `contact` field is a string ID in Holded API, not a dict; use `contactName` for display name
- `documents.py`: `list_documents()` — replace `page` pagination with `starttmp`/`endtmp` Unix timestamps (Holded API style); rename `contactId` → `contactid`; add `paid` and `sort` params
- `documents.py`: `search_documents()` — use date-range fetch instead of page iteration

---

## [1.0.1] - 2026-03-04

### Fixed
- `documents.py`: use unified Holded endpoint `/invoicing/v1/documents/{docType}` instead of separate per-type endpoints

---

## [1.0.0] - 2026-03-04

### Added
- Initial release
- `holded_client.py` — REST API client with multi-instance alias support
- `contacts.py` — search, list, get, create, update contacts
- `documents.py` — all 10 document types (invoice, creditnote, estimate, order, proforma, waybill, salesreceipt, expense, purchaserefund, purchaseorder): list, search, get, create, pay, send, pdf
- `products.py` — search, list, get, create, update products/services; stock levels; warehouses
- `accounting.py` — chart of accounts, search accounts, daily ledger, taxes, treasury accounts, movements, P&L, balance sheet
