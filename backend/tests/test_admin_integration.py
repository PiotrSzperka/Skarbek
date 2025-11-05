import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def admin_token(client):
    r = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert r.status_code == 200
    return r.json()['token']

def test_admin_create_list_hide_flow(client):
    token = admin_token(client)

    # create parent
    r = client.post('/api/admin/parents', headers={'Authorization': f'Bearer {token}'}, json={'name': 'T', 'email': 't+int@example.com', 'password': 'p'})
    assert r.status_code == 200
    pid = r.json()['id']

    # list parents (hidden default excluded)
    r = client.get('/api/admin/parents', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    data = r.json()
    assert any(p['id'] == pid for p in data)

    # hide parent
    r = client.post(f'/api/admin/parents/{pid}/hide', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200

    # by default list doesn't show hidden
    r = client.get('/api/admin/parents', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    data = r.json()
    assert not any(p['id'] == pid for p in data)

    # include hidden
    r = client.get('/api/admin/parents?include_hidden=true', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    data = r.json()
    assert any(p['id'] == pid for p in data)
