def test_create_student_returns_201(client):
    response = client.post(
        "/api/v1/students",
        json={"name": "Aameer", "email": "aameer@example.com", "age": 25},
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Aameer"
    assert "id" in data


def test_get_all_students_empty(client):
    response = client.get("/api/v1/students")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_student_missing_fields_returns_400(client):
    response = client.post("/api/v1/students", json={"email": "a@example.com"})
    assert response.status_code == 400
    data = response.get_json()
    assert data["missing"] == ["name", "age"]


def test_create_student_invalid_values_returns_400(client):
    response = client.post(
        "/api/v1/students",
        json={"name": "", "email": "invalid-email", "age": 150},
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid data" in data["error"]
    assert len(data["details"]) == 3

def test_create_duplicate_email_returns_409(client):
    student = {"name": "Aameer", "email": "aameer@example.com", "age": 25}
    first = client.post("/api/v1/students", json=student)
    assert first.status_code == 201
    second = client.post("/api/v1/students", json=student)
    assert second.status_code == 409

def test_get_student_returns_200(client):
    created = client.post(
        "/api/v1/students",
        json={"name": "Aameer", "email": "aameer@example.com", "age": 25},
    )
    student_id = created.get_json()["id"]
    response = client.get(f"/api/v1/students/{student_id}")
    assert response.status_code == 200
    assert response.get_json()["email"] == "aameer@example.com"

def test_get_missing_student_returns_404(client):
    response = client.get("/api/v1/students/999")
    assert response.status_code == 404


def test_update_student_returns_200(client):
    created = client.post(
        "/api/v1/students",
        json={"name": "Aameer", "email": "aameer@example.com", "age": 25},
    )
    student_id = created.get_json()["id"]
    response = client.patch(f"/api/v1/students/{student_id}", json={"age": 30})
    assert response.status_code == 200
    data = response.get_json()
    assert data["age"] == 30
    assert data["name"] == "Aameer"

def test_delete_student_returns_204(client):
    created = client.post(
        "/api/v1/students",
        json={"name": "Aameer", "email": "aameer@example.com", "age": 25},
    )
    student_id = created.get_json()["id"]
    response = client.delete(f"/api/v1/students/{student_id}")
    assert response.status_code == 204
    response = client.get(f"/api/v1/students/{student_id}")
    assert response.status_code == 404
    