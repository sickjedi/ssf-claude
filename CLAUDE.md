# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

- **Python 3.13** · Flask 3.1 · SQLAlchemy 2.x · Flask-Migrate (Alembic) · Flask-Login · Flask-WTF
- **Database:** PostgreSQL (psycopg2-binary)
- **Frontend:** Bootstrap 5 (CDN), Jinja2 templates

## Commands

```bash
# Activate virtual environment (Windows)
.venv\Scripts\activate

# Run development server
python run.py

# Database migrations
flask db init       # first time only
flask db migrate -m "description"
flask db upgrade

# Install dependencies
pip install -r requirements.txt
```

Set `FLASK_APP=run.py` if flask CLI commands don't find the app.

## Environment Setup

Copy `.env.example` to `.env` and fill in:
- `SECRET_KEY` — long random string
- `DATABASE_URL` — `postgresql://user:password@localhost:5432/ssf_db`

## Architecture

**App factory** in `app/__init__.py` — extensions (db, login_manager, migrate, csrf) are initialised there and blueprints are registered with URL prefixes.

```
app/
├── __init__.py          # create_app() factory
├── models/
│   ├── member.py        # Member — NGO person record (stub, fields TBD)
│   └── user.py          # User + Role enum, password hashing, permission helpers
├── auth/                # /auth blueprint — login / logout
│   ├── forms.py
│   └── routes.py
├── members/             # /members blueprint — member CRUD
│   └── routes.py
└── templates/
    ├── base.html
    ├── auth/login.html
    └── members/index.html
```

## Data Model

**Key relationship:** every `User` must link to exactly one `Member` (one-to-one via `member_id` FK, unique).

**Roles** (enum on `User`):

| Role | Delete | Write | Read |
|------|--------|-------|------|
| `admin` | ✓ | ✓ | ✓ |
| `president` | ✓ | ✓ | ✓ |
| `secretary` | — | ✓ | ✓ |
| `viewer` | — | — | ✓ |

Use `current_user.can_delete` / `current_user.can_write` in routes and templates to gate access.

## Conventions

- Blueprint modules import their `routes` module at the bottom of `__init__.py` to avoid circular imports.
- Passwords are hashed with Werkzeug (`set_password` / `check_password` on `User`).
- CSRF protection is global via `CSRFProtect`; all POST forms must include `{{ form.hidden_tag() }}`.
- The `Member` model is a stub — additional fields will be added when the full model is provided.
