from tests.conftest import register_user, login_user, auth_headers


def _setup(client):
    register_user(client)
    token = login_user(client)
    return auth_headers(token)


def test_list_categories_empty(client):
    resp = client.get("/api/categories/")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_category_requires_auth(client):
    resp = client.post("/api/categories/", json={"name": "Tech"})
    assert resp.status_code == 401


def test_create_category_success(client):
    headers = _setup(client)
    resp = client.post("/api/categories/", json={"name": "Tech"}, headers=headers)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "Tech"
    assert "id" in data


def test_create_category_duplicate(client):
    headers = _setup(client)
    client.post("/api/categories/", json={"name": "Tech"}, headers=headers)
    resp = client.post("/api/categories/", json={"name": "Tech"}, headers=headers)
    assert resp.status_code == 409


def test_update_category(client):
    headers = _setup(client)
    resp = client.post("/api/categories/", json={"name": "Tech"}, headers=headers)
    cat_id = resp.get_json()["id"]

    resp = client.put(f"/api/categories/{cat_id}", json={"name": "Science"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "Science"


def test_delete_category_success(client):
    headers = _setup(client)
    resp = client.post("/api/categories/", json={"name": "ToDelete"}, headers=headers)
    cat_id = resp.get_json()["id"]

    resp = client.delete(f"/api/categories/{cat_id}", headers=headers)
    assert resp.status_code == 204


def test_delete_category_with_posts_returns_409(client):
    headers = _setup(client)
    resp = client.post("/api/categories/", json={"name": "Busy"}, headers=headers)
    cat_id = resp.get_json()["id"]

    client.post("/api/posts/", json={
        "title": "Post in category",
        "content": "Some content",
        "category_id": cat_id,
    }, headers=headers)

    resp = client.delete(f"/api/categories/{cat_id}", headers=headers)
    assert resp.status_code == 409
