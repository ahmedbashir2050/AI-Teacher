def test_create_college(client):
    response = client.post("/api/colleges/", json={"name": "Another Test College"})
    assert response.status_code == 200
    assert response.json()["name"] == "Another Test College"

def test_read_colleges(client):
    response = client.get("/api/colleges/")
    assert response.status_code == 200
    assert len(response.json()) > 0
