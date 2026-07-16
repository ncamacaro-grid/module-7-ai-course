"""
Focused hardening tests covering:
- Standard error shape on every error class
- JWT callbacks (missing / invalid / expired token)
- Ownership enforcement returning standard shape
- Duplicate / conflict returning standard shape
- 404 returning standard shape
- Swagger UI and OpenAPI JSON availability
- Cascade delete of post-with-comments
- Case-insensitive email uniqueness
"""
from datetime import timedelta

from flask_jwt_extended import create_access_token

from tests.conftest import register_user, login_user, auth_headers


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _assert_error_shape(resp, expected_status, expected_error_type):
    """Assert the response matches the standard error envelope.

    Every error response must contain exactly the keys: error, message, details.
    """
    assert resp.status_code == expected_status, (
        f"Expected {expected_status}, got {resp.status_code}: {resp.get_data(as_text=True)}"
    )
    body = resp.get_json()
    assert body is not None, "Response body is not JSON"
    assert "error" in body, f"Missing 'error' key: {body}"
    assert "message" in body, f"Missing 'message' key: {body}"
    assert "details" in body, f"Missing 'details' key: {body}"
    assert isinstance(body["details"], dict), f"'details' must be a dict, got: {body}"
    assert body["error"] == expected_error_type, (
        f"Expected error type {expected_error_type!r}, got {body['error']!r}"
    )
    assert "password_hash" not in str(body), f"Response must not expose password_hash: {body}"
    assert "Traceback" not in str(body), f"Response must not expose stack traces: {body}"
    return body


# ---------------------------------------------------------------------------
# Validation errors → 400 with ValidationError shape
# ---------------------------------------------------------------------------

def test_invalid_registration_payload_returns_400(client):
    resp = client.post("/api/auth/register", json={"username": "u"})
    body = _assert_error_shape(resp, 400, "ValidationError")
    assert "details" in body, f"Expected 'details' in validation error body: {body}"


def test_invalid_post_payload_returns_400(client):
    register_user(client)
    token = login_user(client)
    resp = client.post("/api/posts/", json={"content": "no title"}, headers=auth_headers(token))
    body = _assert_error_shape(resp, 400, "ValidationError")
    assert "details" in body


def test_empty_comment_content_returns_400(client):
    register_user(client)
    token = login_user(client)
    hdrs = auth_headers(token)
    post = client.post("/api/posts/", json={"title": "T", "content": "C"}, headers=hdrs).get_json()
    resp = client.post(f"/api/posts/{post['id']}/comments", json={"content": ""}, headers=hdrs)
    _assert_error_shape(resp, 400, "ValidationError")


# ---------------------------------------------------------------------------
# JWT callbacks → 401 with Unauthorized shape
# ---------------------------------------------------------------------------

def test_missing_jwt_returns_401(client):
    resp = client.post("/api/posts/", json={"title": "T", "content": "C"})
    _assert_error_shape(resp, 401, "Unauthorized")


def test_invalid_jwt_returns_401(client):
    resp = client.post(
        "/api/posts/",
        json={"title": "T", "content": "C"},
        headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
    )
    _assert_error_shape(resp, 401, "Unauthorized")


def test_expired_jwt_returns_401(app, client):
    register_user(client)
    with app.app_context():
        expired_token = create_access_token(
            identity="1", expires_delta=timedelta(seconds=-1)
        )
    resp = client.post(
        "/api/posts/",
        json={"title": "T", "content": "C"},
        headers=auth_headers(expired_token),
    )
    _assert_error_shape(resp, 401, "Unauthorized")


# ---------------------------------------------------------------------------
# Ownership → 403 with Forbidden shape
# ---------------------------------------------------------------------------

def _make_post(client):
    register_user(client, username="owner", email="owner@example.com")
    token = login_user(client, email="owner@example.com")
    hdrs = auth_headers(token)
    post = client.post("/api/posts/", json={"title": "T", "content": "C"}, headers=hdrs).get_json()
    return post


def test_forbidden_post_update_returns_403(client):
    post = _make_post(client)
    register_user(client, username="attacker", email="attacker@example.com")
    tok = login_user(client, email="attacker@example.com")
    resp = client.put(f"/api/posts/{post['id']}", json={"title": "X"}, headers=auth_headers(tok))
    _assert_error_shape(resp, 403, "Forbidden")


def test_forbidden_post_delete_returns_403(client):
    post = _make_post(client)
    register_user(client, username="attacker2", email="attacker2@example.com")
    tok = login_user(client, email="attacker2@example.com")
    resp = client.delete(f"/api/posts/{post['id']}", headers=auth_headers(tok))
    _assert_error_shape(resp, 403, "Forbidden")


# ---------------------------------------------------------------------------
# Duplicate / conflict → 409 with Conflict shape
# ---------------------------------------------------------------------------

def test_duplicate_email_returns_409(client):
    register_user(client)
    resp = register_user(client, username="different_username")
    _assert_error_shape(resp, 409, "Conflict")


def test_duplicate_username_returns_409(client):
    register_user(client)
    resp = register_user(client, email="different@example.com")
    _assert_error_shape(resp, 409, "Conflict")


def test_duplicate_category_returns_409(client):
    register_user(client)
    token = login_user(client)
    hdrs = auth_headers(token)
    client.post("/api/categories/", json={"name": "Unique"}, headers=hdrs)
    resp = client.post("/api/categories/", json={"name": "Unique"}, headers=hdrs)
    _assert_error_shape(resp, 409, "Conflict")


# ---------------------------------------------------------------------------
# Not found → 404 with NotFound shape
# ---------------------------------------------------------------------------

def test_missing_post_returns_404(client):
    resp = client.get("/api/posts/99999")
    _assert_error_shape(resp, 404, "NotFound")


def test_missing_comment_post_returns_404(client):
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/api/posts/99999/comments",
        json={"content": "hi"},
        headers=auth_headers(token),
    )
    _assert_error_shape(resp, 404, "NotFound")


# ---------------------------------------------------------------------------
# Swagger / OpenAPI availability
# ---------------------------------------------------------------------------

def test_docs_returns_200(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_openapi_json_returns_200_and_valid_json(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict), "openapi.json is not a JSON object"
    assert "openapi" in data, "Missing 'openapi' version key"
    assert "paths" in data, "Missing 'paths' key"


# ---------------------------------------------------------------------------
# Database integrity edge cases
# ---------------------------------------------------------------------------

def test_delete_post_with_comments_cascades_cleanly(client):
    """Deleting a post with comments must not raise an unhandled error."""
    register_user(client)
    token = login_user(client)
    hdrs = auth_headers(token)
    post = client.post("/api/posts/", json={"title": "T", "content": "C"}, headers=hdrs).get_json()
    client.post(f"/api/posts/{post['id']}/comments", json={"content": "first"}, headers=hdrs)
    client.post(f"/api/posts/{post['id']}/comments", json={"content": "second"}, headers=hdrs)

    resp = client.delete(f"/api/posts/{post['id']}", headers=hdrs)
    assert resp.status_code == 204

    assert client.get(f"/api/posts/{post['id']}").status_code == 404
    assert client.get(f"/api/posts/{post['id']}/comments").status_code == 404


def test_case_insensitive_email_uniqueness(client):
    """User@Example.COM and user@example.com must be treated as the same address."""
    resp = register_user(client, email="User@Example.COM")
    assert resp.status_code == 201

    resp = register_user(client, username="other_user", email="user@example.com")
    _assert_error_shape(resp, 409, "Conflict")


def test_case_insensitive_email_login(client):
    """A user registered with mixed-case email can log in with lowercase."""
    register_user(client, email="Mixed@Example.COM")
    resp = client.post(
        "/api/auth/login",
        json={"email": "mixed@example.com", "password": "secret123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()
