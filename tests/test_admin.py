def test_upload_book(client):
    response = client.post(
        "/api/admin/upload-book/",
        params={"title": "Another Test Book", "language": "English", "course_id": 1},
        files={"file": ("dummy.pdf", open("dummy.pdf", "rb"), "application/pdf")},
        headers={"Authorization": "Bearer admin_token"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Another Test Book"
