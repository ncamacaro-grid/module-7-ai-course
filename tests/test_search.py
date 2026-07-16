from tests.conftest import register_user, login_user, auth_headers


def _setup(client):
    register_user(client)
    token = login_user(client)
    return auth_headers(token)


def _create_post(client, headers, title, content):
    return client.post("/api/posts/", json={"title": title, "content": content}, headers=headers)


def test_search_missing_query(client):
    resp = client.get("/api/search/")
    assert resp.status_code == 400


def test_search_blank_query(client):
    resp = client.get("/api/search/?q=   ")
    assert resp.status_code == 400


def test_search_by_title(client):
    headers = _setup(client)
    _create_post(client, headers, title="Flask tutorial", content="Learn Flask here")
    _create_post(client, headers, title="Django guide", content="Learn Django here")

    resp = client.get("/api/search/?q=Flask")
    assert resp.status_code == 200
    results = resp.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Flask tutorial"


def test_search_by_content(client):
    headers = _setup(client)
    _create_post(client, headers, title="Post 1", content="Unique phrase here")
    _create_post(client, headers, title="Post 2", content="Something else")

    resp = client.get("/api/search/?q=Unique+phrase")
    assert resp.status_code == 200
    results = resp.get_json()
    assert len(results) == 1
    assert results[0]["title"] == "Post 1"


def test_search_no_results(client):
    headers = _setup(client)
    _create_post(client, headers, title="Hello", content="World")

    resp = client.get("/api/search/?q=zzznomatch")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_search_case_insensitive(client):
    headers = _setup(client)
    _create_post(client, headers, title="Python Tips", content="Some content")

    resp = client.get("/api/search/?q=python")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1
