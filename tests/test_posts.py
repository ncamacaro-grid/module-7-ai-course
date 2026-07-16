from tests.conftest import register_user, login_user, auth_headers


def _setup(client):
    register_user(client)
    token = login_user(client)
    return auth_headers(token)


def _create_post(client, headers, title="Hello World", content="Some content"):
    resp = client.post("/api/posts/", json={"title": title, "content": content}, headers=headers)
    assert resp.status_code == 201
    return resp.get_json()


def test_list_posts_empty(client):
    resp = client.get("/api/posts/")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_post_requires_auth(client):
    resp = client.post("/api/posts/", json={"title": "T", "content": "C"})
    assert resp.status_code == 401


def test_create_post_success(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    assert post["title"] == "Hello World"
    assert "id" in post
    assert "password" not in post


def test_create_post_missing_title(client):
    headers = _setup(client)
    resp = client.post("/api/posts/", json={"content": "No title"}, headers=headers)
    assert resp.status_code == 400


def test_create_post_invalid_category(client):
    headers = _setup(client)
    resp = client.post("/api/posts/", json={
        "title": "T", "content": "C", "category_id": 9999
    }, headers=headers)
    assert resp.status_code == 400


def test_get_post(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.get(f"/api/posts/{post['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Hello World"


def test_get_post_not_found(client):
    resp = client.get("/api/posts/9999")
    assert resp.status_code == 404


def test_update_post_owner(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.put(f"/api/posts/{post['id']}", json={"title": "Updated"}, headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Updated"


def test_update_post_non_owner(client):
    headers = _setup(client)
    post = _create_post(client, headers)

    register_user(client, username="other", email="other@example.com")
    other_token = login_user(client, email="other@example.com")
    other_headers = auth_headers(other_token)

    resp = client.put(f"/api/posts/{post['id']}", json={"title": "Hack"}, headers=other_headers)
    assert resp.status_code == 403


def test_delete_post_owner(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.delete(f"/api/posts/{post['id']}", headers=headers)
    assert resp.status_code == 204


def test_delete_post_non_owner(client):
    headers = _setup(client)
    post = _create_post(client, headers)

    register_user(client, username="other", email="other@example.com")
    other_token = login_user(client, email="other@example.com")
    other_headers = auth_headers(other_token)

    resp = client.delete(f"/api/posts/{post['id']}", headers=other_headers)
    assert resp.status_code == 403


def test_list_posts_pagination(client):
    headers = _setup(client)
    for i in range(5):
        _create_post(client, headers, title=f"Post {i}", content="content")

    resp = client.get("/api/posts/?page=1&per_page=3")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 3

    resp = client.get("/api/posts/?page=2&per_page=3")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
