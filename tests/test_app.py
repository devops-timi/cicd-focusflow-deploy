import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client

def test_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"FocusFlow" in response.data

def test_add_task(client):
    client.post("/", data={"title": "Write Jenkinsfile"})
    response = client.get("/")
    assert b"Write Jenkinsfile" in response.data

def test_toggle_task(client):
    client.post("/", data={"title": "Toggle Me"})
    response = client.post("/toggle/1")
    assert response.status_code == 204
