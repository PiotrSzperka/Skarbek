from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from app.models import Campaign, Parent


def test_admin_create_contribution_and_include_hidden():
    client = TestClient(app)
    with get_db() as session:
        camp = Campaign(title='contribtest', target_amount=10.0)
        session.add(camp)
        session.commit()
        session.refresh(camp)

        pvis = Parent(name='Vis', email='vis@example.com', is_hidden=False)
        phid = Parent(name='Hid', email='hid@example.com', is_hidden=True)
        session.add(pvis)
        session.add(phid)
        session.commit()
        session.refresh(pvis)
        session.refresh(phid)

        camp_id = camp.id
        pvis_id = pvis.id
        phid_id = phid.id

    # login admin
    rlogin = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert rlogin.status_code == 200
    token = rlogin.json()['token']

    # create contribution for visible parent
    r = client.post('/api/admin/contributions', headers={'Authorization': f'Bearer {token}'}, json={'campaign_id': camp_id, 'parent_id': pvis_id, 'amount_expected': 10.0})
    assert r.status_code == 200
    data = r.json()
    assert data['campaign_id'] == camp_id or data.get('campaign_id') == camp_id

    # roster without hidden
    r2 = client.get(f'/api/admin/campaigns/{camp_id}/roster', headers={'Authorization': f'Bearer {token}'})
    assert r2.status_code == 200
    rows = r2.json()['rows']
    emails = [r['parent_email'] for r in rows]
    assert 'vis@example.com' in emails
    assert 'hid@example.com' not in emails

    # roster with hidden
    r3 = client.get(f'/api/admin/campaigns/{camp_id}/roster?include_hidden=true', headers={'Authorization': f'Bearer {token}'})
    assert r3.status_code == 200
    rows3 = r3.json()['rows']
    emails3 = [r['parent_email'] for r in rows3]
    assert 'hid@example.com' in emails3
