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
