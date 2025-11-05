import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_admin_create_parent_and_parent_login():
    client = TestClient(app)

    # Admin login (init_db seeds admin with password 'changeme')
    r = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    admin_token = r.json().get('token')
    assert admin_token

    headers = {'Authorization': f'Bearer {admin_token}'}

    # Create parent via admin endpoint
    parent_payload = {
        'email': 'int-test-parent@example.com',
        'name': 'IT Parent',
        'password': 'itpass123'
    }
    r2 = client.post('/api/admin/parents', json=parent_payload, headers=headers)
    assert r2.status_code == 200, f"create parent failed: {r2.status_code} {r2.text}"
    parent = r2.json()
    assert parent['email'] == parent_payload['email']

    # Parent login
    r3 = client.post('/api/parents/login', json={'email': parent_payload['email'], 'password': parent_payload['password']})
    assert r3.status_code == 200, f"parent login failed: {r3.status_code} {r3.text}"
    parent_token = r3.json().get('token')
    assert parent_token

    # GET /api/parents/me
    r4 = client.get('/api/parents/me', headers={'Authorization': f'Bearer {parent_token}'})
    assert r4.status_code == 200
    me = r4.json()
    assert me['email'] == parent_payload['email']
    assert me['name'] == parent_payload['name']
