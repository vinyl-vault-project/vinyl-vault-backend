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

The repository currently contains the backend foundation and the first MVP APIs:

- Django configuration;
- PostgreSQL connection through environment variables;
- Docker development environment;
- API health-check endpoint;
- OpenAPI schema and Swagger UI;
- CORS configuration for frontend integration;
- custom user model with email-based authentication;
- JWT registration, login, refresh, logout, and current-user endpoints;
- catalog database models for releases and physical products;
- an authenticated, server-side Cart API with stock and ownership validation.

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
|-- catalog/
|   |-- models/           # Music catalog and physical product models
|   |-- api/
|   |   |-- serializers/  # Release, Artist, Track, Product, SavedRelease schemas
|   |   |-- viewsets/     # Release, Artist and SavedRelease API views
|   |   `-- pagination.py
|   |-- urls.py           # Catalog and Saved Albums routes
|   `-- admin.py          # Catalog administration configuration
|-- orders/
|   |-- models/           # Cart and order persistence models
|   |-- serializers/      # Separate Cart and Order API schemas
|   |-- services/         # Atomic order checkout operations
|   |-- views/            # Separate Cart and Order API views
|   `-- urls.py           # Cart and Order routes
|-- tests/
|   |-- users/            # User model and authentication API tests
|   |-- catalog/          # Catalog and Saved Albums model and API tests
|   `-- orders/           # Cart model and API tests
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
| `GET` | `/api/v1/releases/` | List releases with search, filters and ordering |
| `GET` | `/api/v1/releases/{slug}/` | Return one release with tracklist and products |
| `GET` | `/api/v1/artists/{slug}/` | Return artist details and related releases |
| `GET` | `/api/v1/catalog/filters/` | Return available genres, styles, countries and year range |
| `GET` | `/api/v1/saved/` | List the authenticated user's saved albums |
| `POST` | `/api/v1/saved/` | Save an album |
| `DELETE` | `/api/v1/saved/{id}/` | Remove a saved album |
| `GET` | `/api/v1/cart/` | Return the authenticated user's cart |
| `POST` | `/api/v1/cart/items/` | Add a product to the cart |
| `PATCH` | `/api/v1/cart/items/{item_id}/` | Update a cart item quantity |
| `DELETE` | `/api/v1/cart/items/{item_id}/` | Remove an item from the cart |
| `GET` | `/api/v1/docs/` | Interactive Swagger UI |
| `GET` | `/api/v1/schema/` | OpenAPI schema |
| varies | `/admin/` | Django administration site |

The health endpoint is public and can be used as a basic connectivity check by
the frontend, Docker, or deployment infrastructure. It currently confirms that
the Django application responds; it does not verify PostgreSQL availability.

## Authentication

The API uses JWT bearer authentication. Access tokens authorize API requests,
while refresh tokens are used to obtain new access tokens. Registration, login,
token refresh, and logout are public endpoints. Protected endpoints such as
`/api/v1/auth/me/` and all Cart endpoints require a valid access token.

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

## Catalog API
 
Catalog endpoints are public — available to both Guests and authenticated Users.
 
### List and search releases
 
```
GET /api/v1/releases/
```
 
| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=DJ Shadow` | Album title OR artist name, case-insensitive, partial match |
| `artist` | `?artist=dj-shadow` | Exact filter by artist slug |
| `country` | `?country=United Kingdom` | Filters on `Product.pressing_country`; comma-separated values are OR'd |
| `genre` | `?genre=electronic` | Comma-separated values are OR'd |
| `style` | `?style=idm,ambient` | Comma-separated values are OR'd |
| `year_from`, `year_to` | `?year_from=1990&year_to=2000` | `release_year` range |
| `ordering` | `?ordering=price` / `-price` / `title` / `-title` | Sort order |
 
Different parameter groups are combined with AND. Results are paginated (see below). An empty result returns `200 OK` with `"results": []`, never `404`.
 
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "slug": "endtroducing",
      "title": "Endtroducing.....",
      "cover_url": "https://...",
      "release_year": 1996,
      "artists": [{"id": 1, "name": "DJ Shadow", "slug": "dj-shadow", "image_url": "...", "origin_country": "US"}],
      "price": "20.00"
    }
  ]
}
```
 
### Release detail
 
```
GET /api/v1/releases/{slug}/
```
Returns full release information including tracklist and available products:
```json
{
  "id": 1,
  "slug": "endtroducing",
  "title": "Endtroducing.....",
  "description": "...",
  "release_year": 1996,
  "cover_url": "https://...",
  "artists": [{"id": 1, "name": "DJ Shadow", "slug": "dj-shadow"}],
  "genres": [{"id": 1, "name": "Electronic", "slug": "electronic"}],
  "styles": [{"id": 1, "name": "Trip Hop", "slug": "trip-hop"}],
  "tracks": [
    {"id": 1, "side": "A", "position": 1, "title": "Best Foot Forward", "duration_seconds": 48, "audio_preview_url": "https://..."}
  ],
  "products": [
    {"id": 1, "pressing_country": "US", "price": "20.00", "stock_quantity": 5, "is_active": true}
  ]
}
```
Returns `404 Not Found` if no release matches the given slug.
 
### Artist detail
 
```
GET /api/v1/artists/{slug}/
```
Populates the Artist Information Modal — there is no separate Artist page.
```json
{
  "id": 1,
  "name": "DJ Shadow",
  "slug": "dj-shadow",
  "image_url": "https://...",
  "biography": "American record producer...",
  "related_releases": [
    {"slug": "endtroducing", "title": "Endtroducing.....", "release_year": 1996, "cover_url": "https://..."}
  ]
}
```
`related_releases` is `[]`, not an error, if the artist has no releases. Returns `404 Not Found` if no artist matches the given slug.
 
### Available filters
 
```
GET /api/v1/catalog/filters/
```
Used to populate the Filters Modal dynamically.
```json
{
  "genres": [{"name": "Electronic", "slug": "electronic"}],
  "styles": [{"name": "IDM", "slug": "idm"}],
  "countries": ["UK", "US", "Germany", "Japan"],
  "year_range": {"min": 1955, "max": 2019}
}
```
 
## Saved Albums API
 
The Saved Albums API is available only to authenticated users. Send the JWT access token with every request.
 
### List saved albums
 
```
GET /api/v1/saved/
Authorization: Bearer <access-token>
```
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 3,
      "release": {"id": 1, "slug": "endtroducing", "title": "Endtroducing.....", "cover_url": "...", "artists": [{"name": "DJ Shadow"}]},
      "created_at": "2026-08-21T12:00:00Z"
    }
  ]
}
```
An empty list returns `"results": []`, `"count": 0`.
 
### Save an album
 
```
POST /api/v1/saved/
Authorization: Bearer <access-token>
Content-Type: application/json
 
{ "release_id": 1 }
```
Returns `201 Created` with the created record. Returns `400 Bad Request` if the release is already saved by this user (`unique(user, release)`).
 
### Remove a saved album
 
```
DELETE /api/v1/saved/{id}/
Authorization: Bearer <access-token>
```
`{id}` is the `SavedRelease` record id from the list response, not the release id. Returns `204 No Content`. Returns `404 Not Found` if the record does not exist or belongs to another user — intentionally not `403`, to avoid confirming another user's saved albums.

## Cart API

The Cart API is available only to authenticated users. Send the JWT access token
with every Cart request:

```http
Authorization: Bearer <access-token>
```

Each user has one server-side cart. The backend creates it automatically when it
is first requested or when the first product is added. Guest carts are not
supported.

### Get the current cart

```http
GET /api/v1/cart/
Authorization: Bearer <access-token>
```

An empty cart returns `200 OK` with an empty `items` array and a total of
`"0.00"`. A populated cart has the following structure:

```json
{
  "id": 1,
  "items": [
    {
      "id": 12,
      "product": {
        "id": 7,
        "release": {
          "id": 5,
          "slug": "endtroducing",
          "title": "Endtroducing.....",
          "cover_url": "https://example.com/covers/endtroducing.jpg",
          "release_year": 1996,
          "artists": [
            {
              "id": 2,
              "name": "DJ Shadow",
              "slug": "dj-shadow"
            }
          ]
        },
        "price": "34.99",
        "stock_quantity": 4,
        "is_active": true
      },
      "quantity": 2,
      "subtotal": "69.98",
      "added_at": "2026-08-17T10:30:00Z"
    }
  ],
  "total": "69.98",
  "created_at": "2026-08-17T10:20:00Z",
  "updated_at": "2026-08-17T10:30:00Z"
}
```

Cart prices are not stored as snapshots. `price`, `subtotal`, and `total` use the
current `Product.price` whenever the cart is returned.

### Add a product

```http
POST /api/v1/cart/items/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "product_id": 7,
  "quantity": 2
}
```

`quantity` is optional and defaults to `1`. A successful request returns
`201 Created` with the created CartItem representation.

The same Product cannot appear in one cart more than once. Repeating the request
for a Product that is already present returns `409 Conflict`; use the quantity
update endpoint instead.

### Update quantity

```http
PATCH /api/v1/cart/items/12/
Authorization: Bearer <access-token>
Content-Type: application/json
```

```json
{
  "quantity": 3
}
```

A successful request returns `200 OK` with the updated CartItem. Quantity must
be at least `1` and cannot exceed the Product's current `stock_quantity`.

### Remove an item

```http
DELETE /api/v1/cart/items/12/
Authorization: Bearer <access-token>
```

A successful deletion returns `204 No Content`.

### Validation and status codes

| Status | Meaning |
| --- | --- |
| `200 OK` | Cart retrieved or quantity updated |
| `201 Created` | Product added to the cart |
| `204 No Content` | Cart item removed |
| `400 Bad Request` | Invalid Product, inactive Product, or invalid/out-of-stock quantity |
| `401 Unauthorized` | A valid JWT access token was not provided |
| `404 Not Found` | The CartItem does not exist or belongs to another user |
| `409 Conflict` | The Product is already present in the cart |

Cart operations never reserve or decrement stock. Current stock and prices must
be validated again during Checkout, which is outside the scope of this API.

## Pagination
 
`GET /api/v1/releases/` and `GET /api/v1/saved/` use `PageNumberPagination` (global `DEFAULT_PAGINATION_CLASS` in `settings.py`). Response format:
```json
{
  "count": 42,
  "next": "http://localhost:8000/api/v1/releases/?page=2",
  "previous": null,
  "results": [ /* items */ ]
}
```
Parameters: `?page=2`, and `?page_size=20` where enabled. Endpoints that return a single object (`GET /releases/{slug}/`, `GET /artists/{slug}/`, `GET /cart/`) are not wrapped in this format — they return the object directly.

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
