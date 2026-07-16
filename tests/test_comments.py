from tests.conftest import register_user, login_user, auth_headers


def _setup(client):
    register_user(client)
    token = login_user(client)
    return auth_headers(token)


def _create_post(client, headers):
    resp = client.post("/api/posts/", json={"title": "Post", "content": "Content"}, headers=headers)
    return resp.get_json()


def _create_comment(client, headers, post_id, content="Great post!"):
    return client.post(f"/api/posts/{post_id}/comments", json={"content": content}, headers=headers)


def test_list_comments_empty(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.get(f"/api/posts/{post['id']}/comments")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_comment_success(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = _create_comment(client, headers, post["id"])
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["content"] == "Great post!"
    assert data["post_id"] == post["id"]


def test_create_comment_requires_auth(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.post(f"/api/posts/{post['id']}/comments", json={"content": "Hi"})
    assert resp.status_code == 401


def test_create_comment_empty_content(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = client.post(f"/api/posts/{post['id']}/comments", json={"content": ""}, headers=headers)
    assert resp.status_code == 400


def test_create_comment_missing_post(client):
    headers = _setup(client)
    resp = _create_comment(client, headers, post_id=9999)
    assert resp.status_code == 404


def test_delete_comment_by_owner(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = _create_comment(client, headers, post["id"])
    comment_id = resp.get_json()["id"]

    resp = client.delete(f"/api/comments/{comment_id}", headers=headers)
    assert resp.status_code == 204


def test_delete_comment_by_post_owner(client):
    post_owner_headers = _setup(client)
    post = _create_post(client, post_owner_headers)

    register_user(client, username="commenter", email="commenter@example.com")
    commenter_token = login_user(client, email="commenter@example.com")
    commenter_headers = auth_headers(commenter_token)

    resp = _create_comment(client, commenter_headers, post["id"])
    comment_id = resp.get_json()["id"]

    resp = client.delete(f"/api/comments/{comment_id}", headers=post_owner_headers)
    assert resp.status_code == 204


def test_delete_comment_unauthorized(client):
    headers = _setup(client)
    post = _create_post(client, headers)
    resp = _create_comment(client, headers, post["id"])
    comment_id = resp.get_json()["id"]

    register_user(client, username="stranger", email="stranger@example.com")
    stranger_token = login_user(client, email="stranger@example.com")
    stranger_headers = auth_headers(stranger_token)

    resp = client.delete(f"/api/comments/{comment_id}", headers=stranger_headers)
    assert resp.status_code == 403
