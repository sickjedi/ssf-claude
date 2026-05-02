# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Python 3.13** · Flask 3.1 · SQLAlchemy 2.x · Flask-Migrate (Alembic) · Flask-Login · Flask-WTF
- **Database:** PostgreSQL on Aiven (psycopg2-binary)
- **Frontend:** Bootstrap 5 (CDN), Jinja2 templates
- **PDF generation:** fpdf2 — embeds Windows Arial TTF directly (avoids xhtml2pdf's broken temp-file font loading on Windows)

## Commands

```bash
# Activate virtual environment (Linux)
source .venv/bin/activate

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run development server
python run.py

# Database migrations
flask db migrate -m "description"
flask db upgrade

# Seed super-admin user
flask create-user --super-admin ...

# Seed a regular user + member in an existing org
flask create-user --org-oib <oib> ...

# Create a new organisation (CLI alternative to web UI)
flask create-org --name "..." --oib "..."
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
├── cli.py               # flask create-user / create-org CLI commands
├── validators.py        # reusable WTForms validators (oib_validator — ISO 7064 MOD 11,10)
├── audit.py             # log_action() — writes audit trail entries
├── tenant.py            # _resolve_tenant() + require_tenant() — per-request tenant from session
├── models/
│   ├── organisation.py  # Organisation — top-level tenant; all data is scoped to an org
│   ├── member.py        # Member — NGO person record
│   ├── user.py          # User + Role enum, password hashing, permission helpers
│   ├── customer.py      # Customer (STI base), PersonCustomer, CompanyCustomer
│   ├── invoice.py       # Invoice
│   ├── invoice_item.py  # InvoiceItem
│   └── item.py          # Item — pre-defined catalog for invoice line items
├── admin/               # /admin — super-admin: org CRUD, tenant switching, first-member bootstrap, user password reset
├── auth/                # /auth — login / logout
├── members/             # /members — member CRUD
├── customers/           # /customers — customer CRUD
├── invoices/            # /invoices — invoice CRUD + PDF export
│   └── pdf_generator.py # fpdf2-based PDF; generates invoice layout with embedded Arial font
├── items/               # /items — item catalog CRUD
├── settings/            # /settings — org settings (admin only)
└── templates/
    ├── base.html        # navbar: Members, Customers, Invoices, Items, Settings
    ├── admin/           # index (org list), form (org add/edit + first-member section), users (user list per org), reset_password
    ├── auth/
    ├── members/         # index, form, view
    ├── customers/       # index, form (type toggle JS), view
    ├── invoices/        # index, form (dynamic items JS), view
    ├── items/           # index, form
    └── settings/        # edit
```

## Multi-Tenancy

The app is multi-tenant. Each **Organisation** is an isolated tenant. All Members, Customers, Invoices, and Items are scoped to an Organisation via `organisation_id` FK.

Tenant resolution (`app/tenant.py`):
- **Super admin** — no default tenant; must call `/admin/switch-tenant/<org_id>` to set `session['tenant_id']`.
- **Regular users** — tenant is always `current_user.member.organisation`.
- `g.tenant` is available in every request; all data queries filter by `g.tenant.id`.
- `require_tenant()` aborts 403 if `g.tenant` is None.

Super admin creates organisations at `/admin/organisations/add`. The form has an optional **"Add First Member"** section that bootstraps the org with a President user in a single atomic transaction. Validation for this section is handled by `_first_member_errors()` in `app/admin/routes.py`.

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
- First-member bootstrap on org creation uses `_first_member_errors()` in `admin/routes.py` (same pattern as `_deactivation_errors`); strips whitespace and appends per-field errors.
- Super admin password reset (`/admin/organisations/<org_id>/users/<user_id>/reset-password`) verifies `user.member.organisation_id == org_id` before any write (IDOR guard); catches `ValueError` from `user.set_password()` and surfaces it as a field error.
- Login is blocked if `user.is_active` is False **or** `user.member.is_active` is False.
