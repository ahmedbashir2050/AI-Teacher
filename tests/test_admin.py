import uuid

def test_upload_book(client):
    # Get the faculty and semester from the test data
    faculty_id = client.get("/api/faculties/").json()[0]["id"]
    department_id = client.get(f"/api/departments/{faculty_id}").json()[0]["id"]
    semester_id = client.get(f"/api/semesters/{department_id}").json()[0]["id"]

    with open("dummy.pdf", "rb") as f:
        response = client.post(
            "/api/admin/upload-book/",
            params={
                "title": "Another Test Book",
                "language": "English",
                "semester_id": semester_id,
                "faculty_id": faculty_id,
            },
            files={"file": ("dummy.pdf", f, "application/pdf")},
            headers={"Authorization": "Bearer admin_token"}
        )
    assert response.status_code == 200
    assert response.json()["title"] == "Another Test Book"
    assert response.json()["qdrant_collection"] == f"faculty_{faculty_id}_semester_{semester_id}"
