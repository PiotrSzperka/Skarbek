import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.main import app
from app.db import get_db
from app.models import Parent
from app.utils import READABLE_CHARACTERS

client = TestClient(app)


def _create_parent(admin_token, email, fake_email_client, name='Test Parent'):
    response = client.post(
        '/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': email, 'name': name}
    )
    assert response.status_code == 200
    return response, fake_email_client.sent[-1]


@pytest.fixture
def admin_token():
    response = client.post('/api/admin/login', json={
        'username': 'admin',
        'password': 'changeme'
    })
    assert response.status_code == 200
    return response.json()['token']


@pytest.fixture
def test_parent_email():
    import uuid
    return f'test_force_pwd_{uuid.uuid4().hex[:8]}@example.com'


def test_admin_create_parent_sets_force_password_change(admin_token, test_parent_email, fake_email_client):
    response, sent = _create_parent(admin_token, test_parent_email, fake_email_client, name='Force Parent')
    assert response.json()['email'] == test_parent_email
    assert sent['to_email'] == test_parent_email
    assert sent['parent_name'] == 'Force Parent'
    password = sent['password']
    assert len(password) == 10
    assert all(ch in READABLE_CHARACTERS for ch in password)

    with get_db() as session:
        stmt = select(Parent).where(Parent.email == test_parent_email)
        parent = session.exec(stmt).first()
        assert parent is not None
        assert parent.force_password_change is True
        assert parent.password_changed_at is None


def test_parent_login_with_force_password_returns_flag(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temporary_password = sent['password']

    response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temporary_password
    })
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['require_password_change'] is True


def test_protected_endpoint_blocked_when_force_password_change(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    token = login_response.json()['token']

    response = client.get('/api/parents/me', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    detail = response.json()['detail']
    assert detail['code'] == 'password_change_required'


def test_campaigns_endpoint_blocked_when_force_password_change(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    token = login_response.json()['token']

    response = client.get('/api/parents/campaigns', headers={'Authorization': f'Bearer {token}'})
    assert response.status_code == 403
    detail = response.json()['detail']
    assert detail['code'] == 'password_change_required'


def test_change_password_initial_success(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    old_token = login_response.json()['token']

    response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {old_token}'},
        json={'old_password': temp_password, 'new_password': 'newpass123'}
    )
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['require_password_change'] is False

    with get_db() as session:
        stmt = select(Parent).where(Parent.email == test_parent_email)
        parent = session.exec(stmt).first()
        assert parent.force_password_change is False
        assert parent.password_changed_at is not None


def test_login_after_password_change_no_flag(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    token = login_response.json()['token']

    client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': temp_password, 'new_password': 'newpass123'}
    )

    response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'newpass123'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert 'require_password_change' not in data or data.get('require_password_change') is False


def test_protected_endpoints_accessible_after_password_change(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    token = login_response.json()['token']

    change_response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': temp_password, 'new_password': 'newpass123'}
    )
    new_token = change_response.json()['token']

    response = client.get('/api/parents/me', headers={'Authorization': f'Bearer {new_token}'})
    assert response.status_code == 200
    assert response.json()['email'] == test_parent_email


def test_change_password_wrong_old_password(admin_token, test_parent_email, fake_email_client):
    _, sent = _create_parent(admin_token, test_parent_email, fake_email_client)
    temp_password = sent['password']

    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': temp_password
    })
    token = login_response.json()['token']

    response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': 'wrong', 'new_password': 'newpass123'}
    )
    assert response.status_code == 401
    assert 'invalid' in response.json()['detail'].lower()


def test_change_password_requires_token(test_parent_email):
    response = client.post('/api/parents/change-password-initial', json={
        'old_password': 'temp123',
        'new_password': 'newpass123'
    })
    assert response.status_code in [401, 403]
