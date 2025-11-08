"""
Tests for forced password change feature.
Based on requirements from docs/parents-force-password-change.md
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from app.models import Parent
from app.auth import hash_password
from sqlmodel import select

client = TestClient(app)


@pytest.fixture
def admin_token():
    """Get admin JWT token for authenticated requests."""
    response = client.post('/api/admin/login', json={
        'username': 'admin',
        'password': 'changeme'
    })
    assert response.status_code == 200
    return response.json()['token']


@pytest.fixture
def test_parent_email():
    """Unique email for test parent."""
    import uuid
    return f'test_force_pwd_{uuid.uuid4().hex[:8]}@example.com'


def test_admin_create_parent_sets_force_password_change(admin_token, test_parent_email):
    """Test that newly created parent has force_password_change=True."""
    response = client.post('/api/admin/parents', 
        headers={'Authorization': f'Bearer {admin_token}'},
        json={
            'email': test_parent_email,
            'password': 'temp123'
        }
    )
    assert response.status_code == 200
    
    # Verify in database
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == test_parent_email)
        parent = session.exec(stmt).first()
        assert parent is not None
        assert parent.force_password_change is True
        assert parent.password_changed_at is None


def test_parent_login_with_force_password_returns_flag(admin_token, test_parent_email):
    """Test that login with force_password_change=True returns require_password_change flag."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login
    response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['require_password_change'] is True


def test_protected_endpoint_blocked_when_force_password_change(admin_token, test_parent_email):
    """Test that /parents/me returns 403 when force_password_change=True."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login and get token
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    token = login_response.json()['token']
    
    # Try to access protected endpoint
    response = client.get('/api/parents/me', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 403
    detail = response.json()['detail']
    assert detail['code'] == 'password_change_required'


def test_campaigns_endpoint_blocked_when_force_password_change(admin_token, test_parent_email):
    """Test that /parents/campaigns returns 403 when force_password_change=True."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    token = login_response.json()['token']
    
    # Try to get campaigns
    response = client.get('/api/parents/campaigns',
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 403
    detail = response.json()['detail']
    assert detail['code'] == 'password_change_required'


def test_change_password_initial_success(admin_token, test_parent_email):
    """Test successful password change clears force_password_change and sets timestamp."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    old_token = login_response.json()['token']
    
    # Change password
    response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {old_token}'},
        json={
            'old_password': 'temp123',
            'new_password': 'newpass123'
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert data['require_password_change'] is False
    
    # Verify in database
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == test_parent_email)
        parent = session.exec(stmt).first()
        assert parent.force_password_change is False
        assert parent.password_changed_at is not None


def test_login_after_password_change_no_flag(admin_token, test_parent_email):
    """Test that login after password change does not return require_password_change."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login and change password
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    token = login_response.json()['token']
    
    client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': 'temp123', 'new_password': 'newpass123'}
    )
    
    # Login with new password
    response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'newpass123'
    })
    assert response.status_code == 200
    data = response.json()
    assert 'token' in data
    assert 'require_password_change' not in data or data.get('require_password_change') is False


def test_protected_endpoints_accessible_after_password_change(admin_token, test_parent_email):
    """Test that /parents/me works after password change."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login and change password
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    token = login_response.json()['token']
    
    change_response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': 'temp123', 'new_password': 'newpass123'}
    )
    new_token = change_response.json()['token']
    
    # Access protected endpoint
    response = client.get('/api/parents/me',
        headers={'Authorization': f'Bearer {new_token}'}
    )
    assert response.status_code == 200
    assert response.json()['email'] == test_parent_email


def test_change_password_wrong_old_password(admin_token, test_parent_email):
    """Test that wrong old password is rejected."""
    # Create parent
    client.post('/api/admin/parents',
        headers={'Authorization': f'Bearer {admin_token}'},
        json={'email': test_parent_email, 'password': 'temp123'}
    )
    
    # Login
    login_response = client.post('/api/parents/login', json={
        'email': test_parent_email,
        'password': 'temp123'
    })
    token = login_response.json()['token']
    
    # Try to change with wrong old password
    response = client.post('/api/parents/change-password-initial',
        headers={'Authorization': f'Bearer {token}'},
        json={'old_password': 'wrong', 'new_password': 'newpass123'}
    )
    assert response.status_code == 401
    assert 'invalid' in response.json()['detail'].lower()


def test_change_password_requires_token(test_parent_email):
    """Test that password change requires authentication."""
    response = client.post('/api/parents/change-password-initial', json={
        'old_password': 'temp123',
        'new_password': 'newpass123'
    })
    assert response.status_code in [401, 403]
