def create(client, title="Купить молоко", content="2 литра"):
    return client.post("/api/notes", json={"title": title, "content": content})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_create_and_get(client):
    r = create(client)
    assert r.status_code == 201
    note = r.get_json()
    assert note["title"] == "Купить молоко"

    r = client.get(f"/api/notes/{note['id']}")
    assert r.status_code == 200
    assert r.get_json()["content"] == "2 литра"


def test_create_validation(client):
    assert client.post("/api/notes", json={}).status_code == 400
    assert client.post("/api/notes", json={"title": "   "}).status_code == 400
    assert client.post("/api/notes", json={"title": "x" * 201}).status_code == 400
    assert client.post("/api/notes", data="не json").status_code == 400


def test_list_pagination_and_search(client):
    for i in range(15):
        create(client, title=f"Заметка {i}", content="python" if i % 2 else "")
    r = client.get("/api/notes?page=2&per_page=10").get_json()
    assert r["total"] == 15
    assert len(r["items"]) == 5

    r = client.get("/api/notes?q=python").get_json()
    assert r["total"] == 7


def test_bad_pagination(client):
    assert client.get("/api/notes?page=abc").status_code == 400


def test_put_and_patch(client):
    note_id = create(client).get_json()["id"]

    r = client.patch(f"/api/notes/{note_id}", json={"content": "3 литра"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "Купить молоко"
    assert r.get_json()["content"] == "3 литра"

    r = client.put(f"/api/notes/{note_id}", json={"title": "Новое"})
    assert r.get_json() == {**r.get_json(), "title": "Новое", "content": ""}

    assert client.patch(f"/api/notes/{note_id}", json={}).status_code == 400


def test_delete(client):
    note_id = create(client).get_json()["id"]
    assert client.delete(f"/api/notes/{note_id}").status_code == 204
    assert client.get(f"/api/notes/{note_id}").status_code == 404
    assert client.delete(f"/api/notes/{note_id}").status_code == 404


def test_cors_header(client):
    r = client.get("/health")
    assert r.headers["Access-Control-Allow-Origin"] == "*"


def test_index_page(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Notes API" in r.get_data(as_text=True)
