from tests.conftest import register_user, login_user


def test_register_success(client):
    resp = register_user(client)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "password_hash" not in data
    assert "password" not in data


def test_register_duplicate_email(client):
    register_user(client)
    resp = register_user(client, username="other")
    assert resp.status_code == 409
    assert "Email" in resp.get_json()["message"]


def test_register_duplicate_username(client):
    register_user(client)
    resp = register_user(client, email="other@example.com")
    assert resp.status_code == 409
    assert "Username" in resp.get_json()["message"]


def test_register_missing_fields(client):
    resp = client.post("/api/auth/register", json={"username": "u"})
    assert resp.status_code == 400


def test_login_success(client):
    register_user(client)
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_login_invalid_password(client):
    register_user(client)
    resp = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 401
