"""
Regression tests for the partial-post-update bug and consistent error shapes.

Covers:
- Omitting category_id preserves the current category (was the bug).
- Sending category_id=null explicitly clears the category.
- Sending an unknown category_id returns 404.
- Every representative HTTP error code (400, 401, 403, 404, 409) carries
  the required keys: error, message, details.
"""
from tests.conftest import register_user, login_user, auth_headers


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(client):
    register_user(client)
    token = login_user(client)
    hdrs = auth_headers(token)
    return hdrs


def _create_category(client, headers, name="Tech"):
    resp = client.post("/api/categories/", json={"name": name}, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()


def _create_post_in_category(client, headers, category_id):
    resp = client.post(
        "/api/posts/",
        json={"title": "Original Title", "content": "Body", "category_id": category_id},
        headers=headers,
    )
    assert resp.status_code == 201
    return resp.get_json()


def _assert_has_details(resp, expected_status):
    assert resp.status_code == expected_status, (
        f"Expected {expected_status}, got {resp.status_code}: {resp.get_data(as_text=True)}"
    )
    body = resp.get_json()
    assert body is not None, "Response is not JSON"
    for key in ("error", "message", "details"):
        assert key in body, f"Missing '{key}' in error response: {body}"
    assert isinstance(body["details"], dict), f"'details' must be a dict: {body}"
    return body


# ---------------------------------------------------------------------------
# Partial-update regression: category_id handling
# ---------------------------------------------------------------------------

def test_update_title_only_preserves_category_id(client):
    """
    Regression: when category_id is omitted from the update payload,
    the post's category must NOT be cleared.
    """
    hdrs = _setup(client)
    cat = _create_category(client, hdrs)
    post = _create_post_in_category(client, hdrs, cat["id"])

    assert post["category_id"] == cat["id"]

    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"title": "Updated Title"},
        headers=hdrs,
    )
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["title"] == "Updated Title"
    assert updated["category_id"] == cat["id"], (
        f"category_id was unexpectedly changed: expected {cat['id']}, got {updated['category_id']}"
    )


def test_update_category_id_null_clears_category(client):
    """
    Explicitly sending category_id=null must detach the post from its category.
    """
    hdrs = _setup(client)
    cat = _create_category(client, hdrs, name="Science")
    post = _create_post_in_category(client, hdrs, cat["id"])

    assert post["category_id"] == cat["id"]

    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"category_id": None},
        headers=hdrs,
    )
    assert resp.status_code == 200
    updated = resp.get_json()
    assert updated["category_id"] is None, (
        f"Expected category_id to be null after explicit null, got: {updated['category_id']}"
    )


def test_update_unknown_category_id_returns_404(client):
    """
    Sending a non-existent numeric category_id must return 404.
    """
    hdrs = _setup(client)
    resp = client.post(
        "/api/posts/",
        json={"title": "T", "content": "C"},
        headers=hdrs,
    )
    assert resp.status_code == 201
    post = resp.get_json()

    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"category_id": 99999},
        headers=hdrs,
    )
    _assert_has_details(resp, 404)


# ---------------------------------------------------------------------------
# Error-shape assertions: every code carries error + message + details
# ---------------------------------------------------------------------------

def test_400_has_required_keys(client):
    """Validation error (400) must carry error, message, details."""
    hdrs = _setup(client)
    resp = client.post("/api/posts/", json={"content": "no title"}, headers=hdrs)
    body = _assert_has_details(resp, 400)
    assert body["error"] == "ValidationError"


def test_401_missing_jwt_has_required_keys(client):
    """Missing JWT (401) must carry error, message, details."""
    resp = client.post("/api/posts/", json={"title": "T", "content": "C"})
    body = _assert_has_details(resp, 401)
    assert body["error"] == "Unauthorized"


def test_403_non_owner_has_required_keys(client):
    """Forbidden (403) must carry error, message, details."""
    hdrs = _setup(client)
    resp = client.post(
        "/api/posts/", json={"title": "T", "content": "C"}, headers=hdrs
    )
    post = resp.get_json()

    register_user(client, username="attacker_reg", email="attacker_reg@example.com")
    other_tok = login_user(client, email="attacker_reg@example.com")
    resp = client.put(
        f"/api/posts/{post['id']}",
        json={"title": "X"},
        headers=auth_headers(other_tok),
    )
    body = _assert_has_details(resp, 403)
    assert body["error"] == "Forbidden"


def test_404_missing_post_has_required_keys(client):
    """Not-found (404) must carry error, message, details."""
    resp = client.get("/api/posts/99999")
    body = _assert_has_details(resp, 404)
    assert body["error"] == "NotFound"


def test_409_duplicate_user_has_required_keys(client):
    """Conflict (409) must carry error, message, details."""
    register_user(client)
    resp = register_user(client, username="dup_user2")
    body = _assert_has_details(resp, 409)
    assert body["error"] == "Conflict"
