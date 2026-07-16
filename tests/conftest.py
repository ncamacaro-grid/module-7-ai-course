import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    return app


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, db):
    return app.test_client()


def register_user(client, username="testuser", email="test@example.com", password="secret123"):
    return client.post("/api/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
    })


def login_user(client, email="test@example.com", password="secret123"):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    return resp.get_json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}
