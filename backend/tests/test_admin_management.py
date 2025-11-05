import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db import init_db, get_db
from app.models import Parent, Campaign


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    from sqlmodel import create_engine
    db_file = tmp_path / "test.db"
    url = f"sqlite:///{db_file}"
    new_engine = create_engine(url, echo=False)
    import app.db as dbmod
    monkeypatch.setattr(dbmod, "get_engine", lambda: new_engine)
    dbmod.init_db()
    yield


def admin_auth_headers(client: TestClient):
    r = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert r.status_code == 200
    token = r.json()['token']
    return {'Authorization': f'Bearer {token}'}


def test_parent_hide_and_list():
    client = TestClient(app)
    # create two parents
    with get_db() as s:
        p1 = Parent(name='A', email='a@example.com')
        p2 = Parent(name='B', email='b@example.com')
        s.add(p1); s.add(p2); s.commit(); s.refresh(p1); s.refresh(p2)
        pid1 = p1.id; pid2 = p2.id

    headers = admin_auth_headers(client)

    # hide parent 2
    r = client.post(f'/api/admin/parents/{pid2}/hide', headers=headers)
    assert r.status_code == 200

    # list parents (default) should only show parent 1
    r2 = client.get('/api/admin/parents', headers=headers)
    assert r2.status_code == 200
    data = r2.json()
    emails = [p['email'] for p in data]
    assert 'a@example.com' in emails
    assert 'b@example.com' not in emails

    # with include_hidden should show both
    r3 = client.get('/api/admin/parents', params={'include_hidden': 'true'}, headers=headers)
    assert r3.status_code == 200
    emails2 = [p['email'] for p in r3.json()]
    assert 'b@example.com' in emails2


def test_change_parent_password_and_unhide():
    client = TestClient(app)
    with get_db() as s:
        p = Parent(name='C', email='c@example.com')
        s.add(p); s.commit(); s.refresh(p)
        pid = p.id

    headers = admin_auth_headers(client)
    r = client.post(f'/api/admin/parents/{pid}/change-password', json={'new_password': 'newpass'}, headers=headers)
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'

    # hide then unhide
    r2 = client.post(f'/api/admin/parents/{pid}/hide', headers=headers)
    assert r2.status_code == 200
    r3 = client.post(f'/api/admin/parents/{pid}/unhide', headers=headers)
    assert r3.status_code == 200


def test_campaign_close_edit_delete():
    client = TestClient(app)
    # create campaign
    r = client.post('/api/campaigns/', json={'title': 'Camp', 'description': 'd', 'target_amount': 10})
    assert r.status_code == 200
    camp = r.json()
    cid = camp['id']

    headers = admin_auth_headers(client)

    # close campaign
    rc = client.post(f'/api/admin/campaigns/{cid}/close', headers=headers)
    assert rc.status_code == 200
    assert rc.json()['status'] == 'closed'

    # try to edit protected fields -> should be 409
    rput = client.put(f'/api/admin/campaigns/{cid}', json={'title': 'New', 'target_amount': 20}, headers=headers)
    assert rput.status_code == 409

    # delete campaign
    rd = client.delete(f'/api/admin/campaigns/{cid}', headers=headers)
    assert rd.status_code == 200
    assert rd.json()['status'] == 'deleted'
