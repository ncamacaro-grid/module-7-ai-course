"""
Tests verifying that /openapi.json contains the correct BearerAuth security
scheme and that it is applied to exactly the right operations.
"""

BEARER_AUTH = [{"BearerAuth": []}]

PROTECTED_OPERATIONS = [
    ("/api/categories/",               "post"),
    ("/api/categories/{category_id}",  "put"),
    ("/api/categories/{category_id}",  "delete"),
    ("/api/posts/",                    "post"),
    ("/api/posts/{post_id}",           "put"),
    ("/api/posts/{post_id}",           "delete"),
    ("/api/posts/{post_id}/comments",  "post"),
    ("/api/comments/{comment_id}",     "delete"),
]

PUBLIC_OPERATIONS = [
    ("/api/auth/register",             "post"),
    ("/api/auth/login",                "post"),
    ("/api/categories/",               "get"),
    ("/api/posts/",                    "get"),
    ("/api/posts/{post_id}",           "get"),
    ("/api/posts/{post_id}/comments",  "get"),
]


def _get_spec(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    return resp.get_json()


# ---------------------------------------------------------------------------
# Security scheme present in components
# ---------------------------------------------------------------------------

def test_bearer_auth_scheme_exists(client):
    spec = _get_spec(client)
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert "BearerAuth" in schemes, (
        f"Expected 'BearerAuth' in components.securitySchemes, got: {list(schemes.keys())}"
    )


def test_bearer_auth_type_is_http(client):
    spec = _get_spec(client)
    scheme = spec["components"]["securitySchemes"]["BearerAuth"]
    assert scheme.get("type") == "http", (
        f"Expected type='http', got: {scheme.get('type')}"
    )


def test_bearer_auth_scheme_is_bearer(client):
    spec = _get_spec(client)
    scheme = spec["components"]["securitySchemes"]["BearerAuth"]
    assert scheme.get("scheme") == "bearer", (
        f"Expected scheme='bearer', got: {scheme.get('scheme')}"
    )


def test_bearer_auth_format_is_jwt(client):
    spec = _get_spec(client)
    scheme = spec["components"]["securitySchemes"]["BearerAuth"]
    assert scheme.get("bearerFormat") == "JWT", (
        f"Expected bearerFormat='JWT', got: {scheme.get('bearerFormat')}"
    )


# ---------------------------------------------------------------------------
# Protected operations carry BearerAuth
# ---------------------------------------------------------------------------

def test_protected_operations_require_bearer_auth(client):
    spec = _get_spec(client)
    paths = spec.get("paths", {})
    for path, method in PROTECTED_OPERATIONS:
        operation = paths.get(path, {}).get(method)
        assert operation is not None, (
            f"Operation {method.upper()} {path} not found in spec"
        )
        security = operation.get("security")
        assert security == BEARER_AUTH, (
            f"{method.upper()} {path}: expected security={BEARER_AUTH}, got {security}"
        )


# ---------------------------------------------------------------------------
# Public operations do NOT carry BearerAuth
# ---------------------------------------------------------------------------

def test_public_operations_have_no_bearer_auth(client):
    spec = _get_spec(client)
    paths = spec.get("paths", {})
    for path, method in PUBLIC_OPERATIONS:
        operation = paths.get(path, {}).get(method)
        if operation is None:
            continue
        security = operation.get("security")
        assert security != BEARER_AUTH, (
            f"{method.upper()} {path} should NOT require BearerAuth but got {security}"
        )
