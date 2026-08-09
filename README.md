# Vinyl Vault Backend

Backend API for an online vinyl record store. The project is built with Django
and Django REST Framework and uses PostgreSQL as its database.

## Technology stack

- Python 3.12
- Django 5.2
- Django REST Framework
- Simple JWT for access and refresh token authentication
- PostgreSQL 16
- pgAdmin 4
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
- CORS configuration for frontend integration;
- custom user model with email-based authentication;
- JWT registration, login, refresh, logout, and current-user endpoints.

## Project structure

```text
vinyl-vault-backend/
|-- config/
|   |-- settings.py       # Global Django and API configuration
|   |-- urls.py           # Root URL routing
|   |-- health.py         # API health-check view
|   |-- asgi.py
|   `-- wsgi.py
|-- users/
|   |-- models.py         # Custom user model and manager
|   |-- serializers.py    # Registration and authentication schemas
|   |-- validators.py     # Password complexity validation
|   |-- views.py          # JWT authentication API views
|   `-- urls.py           # Authentication routes
|-- tests/
|   `-- users/            # User model and authentication API tests
|-- .env.example          # Environment variable template
|-- .dockerignore
|-- .gitignore
|-- docker-compose.yml    # Backend, PostgreSQL, and pgAdmin services
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
docker compose up --build -d
```

Compose starts:

- `backend` on `http://localhost:8000`;
- `db` as a PostgreSQL 16 container;
- `pgadmin` on `http://localhost:3333`.

The backend waits until the PostgreSQL health check succeeds before it starts.

### 3. Connect pgAdmin to PostgreSQL

Open `http://localhost:3333` and sign in with `PGADMIN_DEFAULT_EMAIL` and
`PGADMIN_DEFAULT_PASSWORD` from `.env`.

Register a new server in pgAdmin with the following values:

| Setting | Value |
| --- | --- |
| Name | `Vinyl Vault Local` |
| Host name/address | `db` |
| Port | `5432` |
| Maintenance database | value of `POSTGRES_DB` from `.env` |
| Username | value of `POSTGRES_USER` from `.env` |
| Password | value of `POSTGRES_PASSWORD` from `.env` |

Use `db`, not `localhost`, as the database host. Both pgAdmin and PostgreSQL run
inside the same Docker Compose network, where the PostgreSQL service is
available by its service name.

The pgAdmin login credentials and PostgreSQL credentials are separate. The
first pair opens the pgAdmin web interface; the second pair connects pgAdmin to
the project database.

### 4. Apply database migrations

```bash
docker compose exec backend python manage.py migrate
```

If the local database was created before the custom user model was added, it
must be recreated. Only do this when the local data can be discarded:

```bash
docker compose down -v
docker compose up --build -d
docker compose exec backend python manage.py migrate
```

The `-v` option permanently deletes the local PostgreSQL and pgAdmin volumes.

### 5. Verify the application

Open `http://localhost:8000/api/v1/health/` or run:

```bash
curl http://localhost:8000/api/v1/health/
```

Expected response:

```json
{"status":"ok"}
```

### 6. View logs

```bash
docker compose logs -f backend
```

Press `Ctrl+C` to stop following the logs. The containers continue running in
the background.

### 7. Stop the project

```bash
docker compose down
```

This keeps the PostgreSQL data in the `postgres_data` volume and pgAdmin's saved
connections in the `pgadmin_data` volume. Running `docker compose down -v`
deletes both volumes, including all local database data and saved pgAdmin
settings.

## Available endpoints

| Method | URL | Purpose |
| --- | --- | --- |
| `GET` | `/api/v1/health/` | Check that the backend responds to HTTP requests |
| `POST` | `/api/v1/auth/register/` | Register a user and receive a JWT token pair |
| `POST` | `/api/v1/auth/login/` | Log in with email and password |
| `POST` | `/api/v1/auth/token/refresh/` | Exchange a refresh token for a new access token |
| `POST` | `/api/v1/auth/logout/` | Blacklist a refresh token |
| `GET` | `/api/v1/auth/me/` | Return the authenticated user's profile |
| `GET` | `/api/v1/docs/` | Interactive Swagger UI |
| `GET` | `/api/v1/schema/` | OpenAPI schema |
| varies | `/admin/` | Django administration site |

The health endpoint is public and can be used as a basic connectivity check by
the frontend, Docker, or deployment infrastructure. It currently confirms that
the Django application responds; it does not verify PostgreSQL availability.

## Authentication

The API uses JWT bearer authentication. Access tokens authorize API requests,
while refresh tokens are used to obtain new access tokens. Registration, login,
token refresh, and logout are public endpoints. `/api/v1/auth/me/` requires a
valid access token.

### Register

```http
POST /api/v1/auth/register/
Content-Type: application/json
```

```json
{
  "username": "vinyl_fan",
  "email": "fan@example.com",
  "password": "StrongPassword123!"
}
```

The password is entered once and is never returned by the API. A successful
registration creates the account and immediately returns `access` and `refresh`
tokens, so the user does not need to log in again:

```json
{
  "user": {
    "id": 1,
    "username": "vinyl_fan",
    "email": "fan@example.com",
    "first_name": "",
    "last_name": "",
    "phone": "",
    "address": ""
  },
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

Passwords must satisfy Django's configured password validators. They must also
contain at least one uppercase letter, one lowercase letter, one digit, and one
special character.

### Log in

Authentication uses email rather than username:

```http
POST /api/v1/auth/login/
Content-Type: application/json
```

```json
{
  "email": "fan@example.com",
  "password": "StrongPassword123!"
}
```

Successful login returns a token pair:

```json
{
  "access": "<access-token>",
  "refresh": "<refresh-token>"
}
```

### Authorize a request

Send the access token in the `Authorization` header:

```http
GET /api/v1/auth/me/
Authorization: Bearer <access-token>
```

The current-user endpoint returns:

```json
{
  "id": 1,
  "username": "vinyl_fan",
  "email": "fan@example.com",
  "first_name": "",
  "last_name": "",
  "phone": "",
  "address": ""
}
```

### Refresh a token

```http
POST /api/v1/auth/token/refresh/
Content-Type: application/json
```

```json
{
  "refresh": "<refresh-token>"
}
```

The response contains a new access token:

```json
{
  "access": "<new-access-token>"
}
```

### Log out

```http
POST /api/v1/auth/logout/
Content-Type: application/json
```

```json
{
  "refresh": "<refresh-token>"
}
```

Logout blacklists the refresh token. The frontend must also remove its stored
access and refresh tokens.

## Frontend integration

The local API base URL is:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

The default frontend origin is configured in `.env.example`:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

Multiple allowed origins must be separated with commas:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

## Running tests

With Docker:

```bash
docker compose exec backend python manage.py test
```

Without Docker, from an activated virtual environment:

```bash
python manage.py test
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
