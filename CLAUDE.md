# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Python 3.13** · Flask 3.1 · SQLAlchemy 2.x · Flask-Migrate (Alembic) · Flask-Login · Flask-WTF
- **Database:** PostgreSQL on Aiven (psycopg2-binary)
- **Frontend:** Bootstrap 5 (CDN), Jinja2 templates
- **PDF generation:** fpdf2 — embeds Windows Arial TTF directly (avoids xhtml2pdf's broken temp-file font loading on Windows)

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run development server
python run.py

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Seed first admin user
flask create-user
```

Set `FLASK_APP=run.py` if flask CLI commands don't find the app.

## Environment Setup

Copy `.env.example` to `.env` and fill in:
- `SECRET_KEY` — long random string
- `DATABASE_URL` — `postgres://...` (config.py automatically rewrites to `postgresql://`)

## Architecture

**App factory** in `app/__init__.py` — extensions (db, login_manager, migrate, csrf) initialised there, blueprints registered with URL prefixes.

```
app/
├── __init__.py          # create_app() factory
├── cli.py               # flask create-user command
├── validators.py        # reusable WTForms validators (oib_validator — ISO 7064 MOD 11,10)
├── models/
│   ├── member.py        # Member — NGO person record
│   ├── user.py          # User + Role enum, password hashing, permission helpers
│   ├── customer.py      # Customer (STI base), PersonCustomer, CompanyCustomer
│   ├── invoice.py       # Invoice
│   ├── invoice_item.py  # InvoiceItem
│   ├── item.py          # Item — pre-defined catalog for invoice line items
│   └── settings.py      # Settings — single-row org config; Settings.get() creates if missing
├── auth/                # /auth — login / logout
├── members/             # /members — member CRUD
├── customers/           # /customers — customer CRUD
├── invoices/            # /invoices — invoice CRUD + PDF export
│   └── pdf_generator.py # fpdf2-based PDF; generates invoice layout with embedded Arial font
├── items/               # /items — item catalog CRUD
├── settings/            # /settings — org settings (admin only)
└── templates/
    ├── base.html        # navbar: Members, Customers, Invoices, Items, Settings
    ├── auth/
    ├── members/         # index, form, view
    ├── customers/       # index, form (type toggle JS), view
    ├── invoices/        # index, form (dynamic items JS), view
    ├── items/           # index, form
    └── settings/        # edit
```

## Data Model

**User → Member:** every `User` must link to exactly one `Member` (one-to-one, `member_id` FK unique). Members can exist without a user account.

**Roles** (enum on `User`):

| Role | Delete | Write | Read |
|------|--------|-------|------|
| `admin` | ✓ | ✓ | ✓ |
| `president` | ✓ | ✓ | ✓ |
| `vice_president` | — | ✓ | ✓ |
| `secretary` | — | ✓ | ✓ |
| `viewer` | — | — | ✓ |

Use `current_user.can_delete` / `current_user.can_write` in routes and templates to gate access.

`president`, `vice_president`, and `secretary` are **unique roles** — only one active user may hold each. Enforced in `members/routes.py` via `_role_conflict()` on save.

**Customer** uses single-table inheritance (STI) with `customer_type` discriminator (`person` / `company`). Use `customer.display_name` for the name regardless of type.

**Invoice → InvoiceItem:** one-to-many, cascade delete. `invoice.total` and `item.subtotal` are computed properties. Invoice numbers are auto-generated as `01/2026` (sequential per year, zero-padded). Item prices are snapshotted at creation time; `item_id` FK is nullable (catalog item may be deleted later).

## Conventions

- Blueprint `__init__.py` imports `routes` at the bottom to avoid circular imports.
- Passwords hashed with Werkzeug (`set_password` / `check_password` on `User`).
- CSRF: global via `CSRFProtect`. WTForms forms use `{{ form.hidden_tag() }}`; manual POST forms use `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`.
- Invoice items are submitted as `item_name[]`, `item_price[]`, `item_quantity[]` arrays and parsed manually in the route (not via WTForms FieldList).
- Delete is blocked if protected relations exist (member with user account, customer with invoices).
- Member `oib` and `email_address` are unique — checked in routes on add and edit.
- OIB is validated with the ISO 7064 MOD 11,10 checksum algorithm (`app/validators.py`). Used on member OIB and company OIB fields.
- Deactivating a member (`is_active = False`) requires both `end_date` and `end_reason` — enforced in `members/routes.py` via `_deactivation_errors()`.
- Login is blocked if `user.is_active` is False **or** `user.member.is_active` is False.
