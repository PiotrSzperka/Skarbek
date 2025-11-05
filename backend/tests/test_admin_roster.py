from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from app.models import Campaign, Parent, Contribution


def test_campaign_roster_roundtrip():
    client = TestClient(app)
    # create a campaign, two parents and one contribution using DB session
    with get_db() as session:
        camp = Campaign(title='rostest', target_amount=100.0)
        session.add(camp)
        session.commit()
        session.refresh(camp)

        p1 = Parent(name='A', email='a@example.com')
        p2 = Parent(name='B', email='b@example.com')
        session.add(p1)
        session.add(p2)
        session.commit()
        session.refresh(p1)
        session.refresh(p2)

        contrib = Contribution(campaign_id=camp.id, parent_id=p1.id, amount_expected=50.0, amount_paid=50.0, status='paid')
        session.add(contrib)
        session.commit()
        # capture ids before session closes to avoid DetachedInstanceError
        camp_id = camp.id
        p1_id = p1.id
        p2_id = p2.id
    # authenticate as admin to call admin endpoint
    rlogin = client.post('/api/admin/login', json={'username': 'admin', 'password': 'changeme'})
    assert rlogin.status_code == 200, rlogin.text
    token = rlogin.json().get('token')

    # call roster endpoint
    r = client.get(f"/api/admin/campaigns/{camp_id}/roster", headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200, r.text
    body = r.json()
    assert 'campaign' in body and 'rows' in body
    assert body['campaign']['id'] == camp_id
    rows = body['rows']
    # should contain both parents
    ids = set([row['parent_email'] for row in rows])
    assert 'a@example.com' in ids and 'b@example.com' in ids
    # parent a should have contribution
    for row in rows:
        if row['parent_email'] == 'a@example.com':
            assert row['contribution'] is not None
        if row['parent_email'] == 'b@example.com':
            assert row['contribution'] is None
