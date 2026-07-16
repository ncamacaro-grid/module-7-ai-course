# Module 7 – Blog Platform REST API

A Flask REST API for a blogging platform built as part of an AI course exercise.

## Features

- JWT authentication (register / login)
- Blog post CRUD with pagination
- Comment system
- Category management
- Full-text search across posts
- OpenAPI / Swagger UI documentation
- Marshmallow request validation
- SQLite local database
- pytest test suite

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | Flask 3 |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-JWT-Extended |
| API / Swagger | flask-smorest |
| Validation | Marshmallow |
| DB | SQLite (dev) / in-memory (tests) |
| Tests | pytest + pytest-flask |

## Project Structure

```
app/
  __init__.py        Application factory
  config.py          Config classes (dev / testing)
  extensions.py      db + jwt singletons
  errors.py          Centralised error handlers
  models/            SQLAlchemy models
  schemas/           Marshmallow schemas
  routes/            flask-smorest blueprints
tests/
  conftest.py        Fixtures and helpers
  test_auth.py
  test_categories.py
  test_posts.py
  test_comments.py
  test_search.py
run.py               Dev entry-point
requirements.txt
```

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Run the development server

```bash
python run.py
```

The server starts at **http://127.0.0.1:5000**.

## Swagger UI

Open **http://127.0.0.1:5000/docs** in your browser.

OpenAPI JSON is available at **http://127.0.0.1:5000/openapi.json**.

## Run tests

```bash
python -m pytest
```

Verbose output with test names:

```bash
python -m pytest -v
```

## API Endpoints

### Auth

| Method | URL | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | – | Register new user |
| POST | `/api/auth/login` | – | Login, receive JWT |

**Register example:**
```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'
```

**Login example:**
```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"secret123"}'
```

### Categories

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/categories/` | – | List all categories |
| POST | `/api/categories/` | JWT | Create category |
| PUT | `/api/categories/<id>` | JWT | Update category |
| DELETE | `/api/categories/<id>` | JWT | Delete category (409 if posts exist) |

### Posts

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/posts/` | – | List posts (paginated) |
| POST | `/api/posts/` | JWT | Create post |
| GET | `/api/posts/<id>` | – | Get single post |
| PUT | `/api/posts/<id>` | JWT (owner) | Update post |
| DELETE | `/api/posts/<id>` | JWT (owner) | Delete post |

Pagination query params: `?page=1&per_page=20`

### Comments

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/posts/<post_id>/comments` | – | List comments for a post |
| POST | `/api/posts/<post_id>/comments` | JWT | Add comment |
| DELETE | `/api/comments/<id>` | JWT (comment or post owner) | Delete comment |

### Search

| Method | URL | Auth | Description |
|---|---|---|---|
| GET | `/api/search/?q=<keyword>` | – | Search posts by title/content |

## Error Response Format

All errors return consistent JSON:

```json
{
  "error": "NotFound",
  "message": "The requested URL was not found on the server."
}
```

Validation errors include a `details` field:

```json
{
  "error": "ValidationError",
  "message": "Invalid request payload",
  "details": {
    "json": {
      "email": ["Not a valid email address."]
    }
  }
}
```

## HTTP Status Codes

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request / validation error |
| 401 | Unauthorized |
| 403 | Forbidden (ownership check) |
| 404 | Not Found |
| 409 | Conflict (duplicate / referential) |
| 422 | Unprocessable Entity (schema error) |
| 500 | Internal Server Error |
