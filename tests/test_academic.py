import uuid

def test_create_faculty(client):
    response = client.post("/api/faculties/", json={"name": "Test Faculty"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test Faculty"

def test_read_faculties(client):
    response = client.get("/api/faculties/")
    assert response.status_code == 200
    assert len(response.json()) > 0
