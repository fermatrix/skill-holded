# Changelog

All notable changes to this project are documented here.

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
