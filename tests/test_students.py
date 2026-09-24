import pytest

VALID = {"name": "Ada Lovelace", "email": "ada@example.com", "age": 20}


def create(client, **overrides):
    return client.post("/students", json={**VALID, **overrides})


def test_create_and_get(client):
    resp = create(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["id"] == 1
    assert body["name"] == "Ada Lovelace"
    assert "created_at" in body

    resp = client.get("/students/1")
    assert resp.status_code == 200
    assert resp.get_json()["email"] == "ada@example.com"


def test_list(client):
    create(client)
    create(client, email="grace@example.com")
    resp = client.get("/students")
    assert [s["id"] for s in resp.get_json()] == [1, 2]


def test_duplicate_email_is_409(client):
    create(client)
    resp = create(client, name="Someone Else")
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"name": ""}, "name"),
        ({"name": "   "}, "name"),
        ({"name": "x" * 101}, "name"),
        ({"email": "no-at-sign"}, "email"),
        ({"age": 4}, "age"),
        ({"age": 101}, "age"),
        ({"age": "20"}, "age"),
        ({"age": True}, "age"),
        ({"id": 99}, "id"),
        ({"created_at": "2020-01-01"}, "created_at"),
    ],
)
def test_validation(client, overrides, field):
    resp = create(client, **overrides)
    assert resp.status_code == 400
    assert field in resp.get_json()["details"]


def test_missing_fields(client):
    resp = client.post("/students", json={})
    assert resp.status_code == 400
    assert set(resp.get_json()["details"]) == {"name", "email", "age"}


def test_non_json_body(client):
    resp = client.post("/students", data="hello")
    assert resp.status_code == 400


def test_age_boundaries_allowed(client):
    assert create(client, age=5).status_code == 201
    assert create(client, age=100, email="b@example.com").status_code == 201


def test_patch(client):
    create(client)
    resp = client.patch("/students/1", json={"age": 21})
    assert resp.status_code == 200
    assert resp.get_json()["age"] == 21
    assert resp.get_json()["name"] == "Ada Lovelace"


def test_patch_to_duplicate_email_is_409(client):
    create(client)
    create(client, email="grace@example.com")
    resp = client.patch("/students/2", json={"email": "ada@example.com"})
    assert resp.status_code == 409


def test_delete(client):
    create(client)
    assert client.delete("/students/1").status_code == 204
    assert client.get("/students/1").status_code == 404


def test_not_found(client):
    assert client.get("/students/42").status_code == 404
    assert client.patch("/students/42", json={"age": 30}).status_code == 404
    assert client.delete("/students/42").status_code == 404
