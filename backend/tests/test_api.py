import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db
from app.models import Campaign


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    # use sqlite file in tmp path for isolation
    from sqlmodel import create_engine
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file}"
    new_engine = create_engine(url, echo=False)
    import app.db as dbmod
    # monkeypatch get_engine to return our temp engine
    monkeypatch.setattr(dbmod, "get_engine", lambda: new_engine)
    dbmod.init_db()
    yield


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_campaigns_empty_then_create():
    client = TestClient(app)
    r = client.get("/api/campaigns/")
    assert r.status_code == 200
    assert r.json() == []

    payload = {"title": "Test zbiórka", "description": "Opis", "target_amount": 100}
    r2 = client.post("/api/campaigns/", json=payload)
    assert r2.status_code == 200
    data = r2.json()
    assert data["title"] == payload["title"]


def test_parent_status_and_mark_paid():
    client = TestClient(app)
    # create campaign
    payload = {"title": "Zb", "description": "Opis", "target_amount": 50}
    r = client.post("/api/campaigns/", json=payload)
    camp = r.json()
    # create parent and contribution directly via DB
    from app.db import get_db
    from app.models import Parent, Contribution
    with get_db() as session:
        p = Parent(name='Jan', email='jan@example.com', pupil_id='P1')
        session.add(p)
        session.commit()
        session.refresh(p)
        parent_id = p.id
        c = Contribution(campaign_id=camp['id'], parent_id=parent_id, amount_expected=50)
        session.add(c)
        session.commit()

    # check status
    r2 = client.get(f"/api/campaigns/{camp['id']}/status", params={'email': 'jan@example.com'})
    assert r2.status_code == 200
    assert r2.json()['status'] == 'pending'

    # login admin and mark paid
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert login.status_code == 200
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    r3 = client.post('/api/admin/contributions/mark-paid', json={'campaign_id': camp['id'], 'parent_id': parent_id, 'amount': 50}, headers=headers)
    assert r3.status_code == 200
    assert r3.json()['status'] == 'paid'


# Testy wymuszania zmiany hasła przy pierwszym logowaniu
def test_parent_force_password_change_on_create():
    """Test: Nowo utworzony parent ma force_password_change=True"""
    client = TestClient(app)
    
    # login admin
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # create parent
    payload = {
        'name': 'Jan Kowalski',
        'email': 'jan@test.pl',
        'password': 'temp123'
    }
    r = client.post('/api/admin/parents', json=payload, headers=headers)
    assert r.status_code == 200
    
    # verify in DB
    from app.db import get_db
    from app.models import Parent
    with get_db() as session:
        parent = session.query(Parent).filter(Parent.email == 'jan@test.pl').first()
        assert parent is not None
        assert parent.force_password_change is True


def test_parent_login_returns_require_password_change():
    """Test: Login zwraca require_password_change=true dla nowego rodzica"""
    client = TestClient(app)
    
    # create parent via admin
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Anna Nowak',
        'email': 'anna@test.pl',
        'password': 'temp456'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    # parent login
    r = client.post('/api/parents/login', json={'email': 'anna@test.pl', 'password': 'temp456'})
    assert r.status_code == 200
    data = r.json()
    assert 'token' in data
    assert data['require_password_change'] is True


def test_parent_protected_endpoints_blocked_before_password_change():
    """Test: Chronione endpointy zwracają 403 gdy force_password_change=True"""
    client = TestClient(app)
    
    # create parent and get token
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Piotr Test',
        'email': 'piotr@test.pl',
        'password': 'temp789'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    r = client.post('/api/parents/login', json={'email': 'piotr@test.pl', 'password': 'temp789'})
    parent_token = r.json()['token']
    parent_headers = {'Authorization': f'Bearer {parent_token}'}
    
    # try to access protected endpoints
    r1 = client.get('/api/parents/me', headers=parent_headers)
    assert r1.status_code == 403
    assert r1.json()['detail']['code'] == 'password_change_required'
    
    r2 = client.get('/api/parents/campaigns', headers=parent_headers)
    assert r2.status_code == 403
    assert r2.json()['detail']['code'] == 'password_change_required'
    
    r3 = client.get('/api/parents/contributions', headers=parent_headers)
    assert r3.status_code == 403
    assert r3.json()['detail']['code'] == 'password_change_required'


def test_parent_change_password_initial_success():
    """Test: Endpoint change-password-initial prawidłowo zmienia hasło i czyści flagę"""
    client = TestClient(app)
    
    # create parent
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Maria Test',
        'email': 'maria@test.pl',
        'password': 'temp999'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    r = client.post('/api/parents/login', json={'email': 'maria@test.pl', 'password': 'temp999'})
    parent_token = r.json()['token']
    parent_headers = {'Authorization': f'Bearer {parent_token}'}
    
    # change password
    change_payload = {
        'old_password': 'temp999',
        'new_password': 'newpass123'
    }
    r2 = client.post('/api/parents/change-password-initial', json=change_payload, headers=parent_headers)
    assert r2.status_code == 200
    data = r2.json()
    assert 'token' in data
    assert data['require_password_change'] is False
    
    # verify in DB
    from app.db import get_db
    from app.models import Parent
    with get_db() as session:
        parent = session.query(Parent).filter(Parent.email == 'maria@test.pl').first()
        assert parent.force_password_change is False
        assert parent.password_changed_at is not None


def test_parent_change_password_validation():
    """Test: Walidacja przy zmianie hasła (stare błędne, nowe == stare)"""
    client = TestClient(app)
    
    # create parent
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Test Validation',
        'email': 'valid@test.pl',
        'password': 'temp111'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    r = client.post('/api/parents/login', json={'email': 'valid@test.pl', 'password': 'temp111'})
    parent_token = r.json()['token']
    parent_headers = {'Authorization': f'Bearer {parent_token}'}
    
    # błędne stare hasło
    r1 = client.post('/api/parents/change-password-initial', 
                     json={'old_password': 'wrong', 'new_password': 'newpass123'}, 
                     headers=parent_headers)
    assert r1.status_code == 401
    assert 'invalid old password' in r1.json()['detail']
    
    # nowe hasło == stare
    r2 = client.post('/api/parents/change-password-initial', 
                     json={'old_password': 'temp111', 'new_password': 'temp111'}, 
                     headers=parent_headers)
    assert r2.status_code == 400
    assert 'different' in r2.json()['detail']


def test_parent_login_after_password_change_no_requirement():
    """Test: Po zmianie hasła login nie wymaga ponownej zmiany"""
    client = TestClient(app)
    
    # create parent
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Final Test',
        'email': 'final@test.pl',
        'password': 'temp222'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    # first login
    r1 = client.post('/api/parents/login', json={'email': 'final@test.pl', 'password': 'temp222'})
    parent_token = r1.json()['token']
    parent_headers = {'Authorization': f'Bearer {parent_token}'}
    
    # change password
    client.post('/api/parents/change-password-initial', 
                json={'old_password': 'temp222', 'new_password': 'newpass222'}, 
                headers=parent_headers)
    
    # login with new password
    r2 = client.post('/api/parents/login', json={'email': 'final@test.pl', 'password': 'newpass222'})
    assert r2.status_code == 200
    data = r2.json()
    # When password change not required, the key is not present (only added when True)
    assert data.get('require_password_change') != True
    
    # verify access to protected endpoints
    new_token = data['token']
    new_headers = {'Authorization': f'Bearer {new_token}'}
    
    r3 = client.get('/api/parents/me', headers=new_headers)
    assert r3.status_code == 200
    assert r3.json()['email'] == 'final@test.pl'


def test_parent_contributions_access_after_password_change():
    """Test: Po zmianie hasła rodzic ma dostęp do POST /parents/contributions"""
    client = TestClient(app)
    
    # create campaign
    campaign_payload = {"title": "Test Camp", "description": "Desc", "target_amount": 100}
    camp_r = client.post("/api/campaigns/", json=campaign_payload)
    campaign_id = camp_r.json()['id']
    
    # create parent
    login = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    token = login.json()['token']
    headers = {'Authorization': f'Bearer {token}'}
    
    payload = {
        'name': 'Contrib Test',
        'email': 'contrib@test.pl',
        'password': 'temp333'
    }
    client.post('/api/admin/parents', json=payload, headers=headers)
    
    # login and change password
    r1 = client.post('/api/parents/login', json={'email': 'contrib@test.pl', 'password': 'temp333'})
    parent_token = r1.json()['token']
    parent_headers = {'Authorization': f'Bearer {parent_token}'}
    
    client.post('/api/parents/change-password-initial', 
                json={'old_password': 'temp333', 'new_password': 'newpass333'}, 
                headers=parent_headers)
    
    # login with new password
    r2 = client.post('/api/parents/login', json={'email': 'contrib@test.pl', 'password': 'newpass333'})
    new_token = r2.json()['token']
    new_headers = {'Authorization': f'Bearer {new_token}'}
    
    # POST contribution should work
    contrib_payload = {'campaign_id': campaign_id, 'amount': 50}
    r3 = client.post('/api/parents/contributions', json=contrib_payload, headers=new_headers)
    assert r3.status_code == 200
