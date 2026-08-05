# Vinyl Vault Backend

Backend API for an online vinyl record store. The project is built with Django
and Django REST Framework and uses PostgreSQL as its database.

## Technology stack

- Python 3.12
- Django 5.2
- Django REST Framework
- PostgreSQL 16
- drf-spectacular for OpenAPI and Swagger UI
- django-cors-headers for browser access from the frontend
- Docker and Docker Compose for the shared development environment

## Project status

The repository currently contains the initial backend scaffold:

- Django configuration;
- PostgreSQL connection through environment variables;
- Docker development environment;
- API health-check endpoint;
- OpenAPI schema and Swagger UI;
- CORS configuration for frontend integration.

## Project structure

```text
vinyl-vault-backend/
|-- config/
|   |-- settings.py       # Global Django and API configuration
|   |-- urls.py           # Root URL routing
|   |-- health.py         # API health-check view
|   |-- asgi.py
|   `-- wsgi.py
|-- .env.example          # Environment variable template
|-- .dockerignore
|-- .gitignore
|-- docker-compose.yml    # Backend and PostgreSQL services
|-- Dockerfile
|-- manage.py
|-- requirements.txt
`-- README.md
```

## Prerequisites

For the recommended Docker workflow, install:

- Git;
- Docker Desktop with Docker Compose.

For local execution without Docker, install:

- Python 3.12;
- PostgreSQL;
- Git.

## Quick start with Docker

Docker Compose is the recommended way to run the project because it gives all
developers the same Python and PostgreSQL environment.

### 1. Create the local environment file

PowerShell:

```powershell
Copy-Item .env.example .env
```

Bash:

```bash
cp .env.example .env
```

The values from `.env.example` are intended only for local development. Replace
them with secure values in staging or production. Never commit `.env`.

### 2. Build and start the services

```bash
docker compose up --build
```

Compose starts:

- `backend` on `http://localhost:8000`;
- `db` as a PostgreSQL 16 container.

The backend waits until the PostgreSQL health check succeeds before it starts.

### 3. Apply database migrations

```bash
docker compose exec backend python manage.py migrate
```

### 4. Verify the application

Open `http://localhost:8000/api/v1/health/` or run:

```bash
curl http://localhost:8000/api/v1/health/
```

Expected response:

```json
{"status":"ok"}
```

### 5. View logs

```bash
docker compose logs -f backend
```

Press `Ctrl+C` to stop following the logs. The containers continue running in
the background.

### 6. Stop the project

```bash
docker compose down
```

This keeps the PostgreSQL data in the `postgres_data` Docker volume. Running
`docker compose down -v` also deletes that volume and all local database data.

## Available endpoints

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health/` | Check that the backend responds to HTTP requests |
| `GET` | `/api/docs/` | Interactive Swagger UI |
| `GET` | `/api/schema/` | OpenAPI schema |
| varies | `/admin/` | Django administration site |

The health endpoint is public and can be used as a basic connectivity check by
the frontend, Docker, or deployment infrastructure. It currently confirms that
the Django application responds; it does not verify PostgreSQL availability.

## Frontend integration

The default frontend origin is configured in `.env.example`:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Multiple allowed origins must be separated with commas:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Running without Docker

Docker is recommended, but Django can also be run in a local virtual environment.
An accessible PostgreSQL database and matching values in `.env` are required.

### Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `POSTGRES_HOST=localhost` in `.env` if PostgreSQL is running on the host, then
run:

```powershell
python manage.py migrate
python manage.py runserver
```

### Linux and macOS

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `POSTGRES_HOST=localhost` in `.env` if PostgreSQL is running on the host, then
run:

```bash
python manage.py migrate
python manage.py runserver
```