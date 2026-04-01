# skill-holded — Holded ERP Claude Skill

Access Holded ERP from Claude via REST API. Manage contacts, all document types (invoices, estimates, orders, expenses, etc.), products, warehouses, accounting accounts, and treasury.

## Features

- **Contacts** — search (name/email/code/VAT), list, get, create, update
- **Documents** — all 10 types: invoice, creditnote, estimate, order, proforma, waybill, salesreceipt, expense, purchaserefund, purchaseorder
  - List, search, get details with line items, create, pay, send by email, download PDF
- **Products & Services** — search, get, create, update, stock levels per warehouse
- **Warehouses** — list all warehouses
- **Accounting** — chart of accounts, daily ledger, taxes
- **Treasury** — bank/cash accounts, movements, P&L, balance sheet
- **Multi-instance** — connect multiple Holded organizations via aliases

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/fermatrix/skill-holded.git
```

### 2. Prerequisites

- Python 3.8+ (no external packages required — uses stdlib only)
- Holded API key (from Settings → Integrations → API)

### 3. Configure Credentials

Copy `.env.example` to `.env` in the skill directory and fill in your API key(s):

```bash
HOLDED_MYCO_API_KEY=your-holded-api-key-here
```

Multiple organizations:

```bash
HOLDED_MYCO_API_KEY=key-for-enzo
HOLDED_CLIENT2_API_KEY=key-for-client2
```

### 4. Build and Install

```powershell
./build-skill.ps1 -Version 1.0.0
```

Upload the generated `.skill` file in Claude → Settings → Skills.

## Usage

See [SKILL.md](SKILL.md) for full command reference.

Quick examples:

```bash
python .../contacts.py MYCO search "Nitaki"
python .../documents.py MYCO invoice search "Nitaki"
python .../documents.py MYCO invoice get 12345
python .../documents.py MYCO invoice pdf 12345 /mnt/user-data/outputs/inv.pdf
python .../products.py MYCO search "Consultoría"
python .../accounting.py MYCO treasury
python .../accounting.py MYCO profitloss 2025-01-01 2025-12-31
```

## License

MIT

---

**Maintainer:** Fermatrix
**Repository:** https://github.com/fermatrix/skill-holded

## Changes (2026-04-01)

- Contact search now matches VAT/NIF in addition to name/email/code
