import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_admin_token_persistence():
    # login and obtain token
    c1 = TestClient(app)
    r = c1.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert r.status_code == 200
    token = r.json().get('token')
    assert token

    headers = {'Authorization': f'Bearer {token}'}

    # use token in same client to create a parent
    r2 = c1.post('/api/admin/parents', json={'email': 'persist1@example.com', 'name': 'Persist One', 'password': 'p1'}, headers=headers)
    assert r2.status_code == 200

    # simulate a new tab / new client re-using the stored token
    c2 = TestClient(app)
    r3 = c2.post('/api/admin/parents', json={'email': 'persist2@example.com', 'name': 'Persist Two', 'password': 'p2'}, headers=headers)
    assert r3.status_code == 200

    # tamper token -> should be rejected
    bad_headers = {'Authorization': f'Bearer {token}x'}
    r4 = c2.post('/api/admin/parents', json={'email': 'persist3@example.com', 'name': 'Persist Three', 'password': 'p3'}, headers=bad_headers)
    assert r4.status_code == 401
