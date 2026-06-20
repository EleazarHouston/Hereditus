# Hereditus

Multiplayer web-based genetics colony-building game built with Django 5.1 and PostgreSQL.

## Requirements

- Python 3.12
- PostgreSQL 16 (SQLite is sufficient for fast local tests, not concurrency tests)

## Setup

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock
cp .env.example .env
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

Set `DATABASE_URL` in `.env` to a PostgreSQL database before running the application.
The development settings module loads `.env`; production never loads it.

## Configuration

Required production variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS` (comma-separated)
- `CSRF_TRUSTED_ORIGINS` (comma-separated)
- `LOG_DIR`

Settings modules:

- `webapp.settings.development` (default through `webapp.settings`)
- `webapp.settings.test`
- `webapp.settings.production`

## Verification

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/mypy main_game webapp
.venv/bin/pytest
```

PostgreSQL is required to execute tests marked `concurrency`; they are skipped on SQLite.
Coverage uses branch measurement and an 80% target:

```bash
.venv/bin/coverage run -m pytest
.venv/bin/coverage report
```

## Deployment

Set `DJANGO_SETTINGS_MODULE=webapp.settings.production`, provide all required variables,
apply migrations, collect static files, and run the WSGI/ASGI server behind TLS termination.
Validate configuration with:

```bash
python manage.py check --deploy --settings=webapp.settings.production
```

The deprecated pre-Django implementation is retained under `legacy/` and excluded from
production lint, typing, tests, and coverage.
