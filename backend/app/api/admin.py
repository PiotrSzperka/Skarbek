from fastapi import APIRouter, HTTPException, Depends, Request
from ..models import AdminUser, Contribution, Campaign, CampaignCreate, Parent
from ..auth import verify_password, create_token
from ..db import get_db
from sqlmodel import select

router = APIRouter()


@router.post('/login')
def login(payload: dict):
    username = payload.get('username')
    password = payload.get('password')
    with get_db() as session:
        stmt = select(AdminUser).where(AdminUser.username == username)
        user = session.exec(stmt).first()
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail='invalid credentials')
        token = create_token({'sub': user.username})
        return {'token': token}


@router.post('/campaigns-raw')
async def create_campaign_raw(request: Request):
    print("=" * 60)
    print("DEBUG RAW - Endpoint hit!")
    print(f"  Method: {request.method}")
    print(f"  URL: {request.url}")
    print(f"  Headers: {dict(request.headers)}")

    try:
        raw_body = await request.body()
        print(f"  Raw body length: {len(raw_body)}")
        print(f"  Raw body: {raw_body}")
        print(f"  Raw body decoded: {raw_body.decode('utf-8')}")
    except Exception as e:
        print(f"  Error reading raw body: {e}")

    print("=" * 60)
    return {"received": "ok", "body_length": len(raw_body) if 'raw_body' in locals() else 0}


@router.post('/campaigns-new')
async def create_campaign_new(request: Request):
    print("=" * 60)
    print("DEBUG - NEW Campaign creation endpoint hit!")

    try:
        # Get the raw body
        raw_body = await request.body()
        print(f"Raw body: {raw_body}")
        body_str = raw_body.decode('utf-8')
        print(f"Body string: {body_str}")

        # Parse JSON manually
        import json
        data = json.loads(body_str)
        print(f"Parsed data: {data}")

        # Create campaign from parsed data
        title = data.get('title')
        if not title:
            raise HTTPException(status_code=422, detail="title is required")

        target_amount = data.get('target_amount', 0.0)
        description = data.get('description')
        due_date = data.get('due_date')
        active = data.get('active', True)

        print(f"Creating campaign: title={title}, amount={target_amount}")

        with get_db() as session:
            c = Campaign(
                title=title,
                description=description,
                target_amount=float(target_amount),
                due_date=due_date,
                active=active
            )
            session.add(c)
            session.commit()
            session.refresh(c)
            print(f"Campaign created successfully with ID: {c.id}")

            # Return the campaign data manually as dict
            return {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "target_amount": c.target_amount,
                "due_date": c.due_date,
                "active": c.active,
                "created_at": c.created_at.isoformat() if c.created_at else None
            }

    except Exception as e:
        print(f"Error in campaign creation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    print("=" * 60)


@router.post('/campaigns/')
async def create_campaign(request: Request):
    print("=" * 60)
    print("DEBUG - Campaign creation endpoint hit")

    try:
        # Get the raw body
        raw_body = await request.body()
        print(f"Raw body: {raw_body}")
        body_str = raw_body.decode('utf-8')
        print(f"Body string: {body_str}")

        # Parse JSON manually
        import json
        data = json.loads(body_str)
        print(f"Parsed data: {data}")

        # Create campaign from parsed data
        title = data.get('title')
        if not title:
            raise HTTPException(status_code=422, detail="title is required")

        target_amount = data.get('target_amount', 0.0)
        description = data.get('description')
        due_date = data.get('due_date')
        active = data.get('active', True)

        print(f"Creating campaign: title={title}, amount={target_amount}")

        with get_db() as session:
            c = Campaign(
                title=title,
                description=description,
                target_amount=float(target_amount),
                due_date=due_date,
                active=active
            )
            session.add(c)
            session.commit()
            session.refresh(c)
            print(f"Campaign created successfully with ID: {c.id}")

            # Return the campaign data manually as dict
            return {
                "id": c.id,
                "title": c.title,
                "description": c.description,
                "target_amount": c.target_amount,
                "due_date": c.due_date,
                "active": c.active,
                "created_at": c.created_at
            }

    except Exception as e:
        print(f"Error in campaign creation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    print("=" * 60)


@router.post('/campaigns-debug')
def create_campaign_debug(payload: dict):
    print("DEBUG RAW - Received payload:", payload)
    print("DEBUG RAW - Title type:", type(payload.get('title')))
    print("DEBUG RAW - Title value:", repr(payload.get('title')))
    return {"received": payload}


@router.post('/contributions/mark-paid')
def mark_paid(payload: dict):
    cid = payload.get('campaign_id')
    pid = payload.get('parent_id')
    amount = payload.get('amount', 0)
    note = payload.get('note')
    with get_db() as session:
        stmt = select(Contribution).where(Contribution.campaign_id == cid, Contribution.parent_id == pid)
        c = session.exec(stmt).first()
        if not c:
            raise HTTPException(status_code=404, detail='contribution not found')
        c.amount_paid = amount
        c.status = 'paid'
        c.paid_at = __import__('datetime').datetime.utcnow()
        c.note = note
        session.add(c)
        session.commit()
        session.refresh(c)
        return c


@router.get('/contributions')
def list_contributions():
    # Return active campaigns with their contributions and parent info
    with get_db() as session:
        stmt = select(Campaign).where(Campaign.active == True)
        camps = session.exec(stmt).all()
        results = []
        for c in camps:
            stmt2 = select(Contribution).where(Contribution.campaign_id == c.id)
            contribs = session.exec(stmt2).all()
            contribs_out = []
            for co in contribs:
                stmtp = select(Parent).where(Parent.id == co.parent_id)
                p = session.exec(stmtp).first()
                contribs_out.append({
                    'id': co.id,
                    'parent_id': co.parent_id,
                    'parent_email': p.email if p else None,
                    'parent_name': p.name if p else None,
                    'amount_expected': co.amount_expected,
                    'amount_paid': co.amount_paid,
                    'status': co.status,
                    'paid_at': co.paid_at,
                    'note': co.note,
                })
            results.append({'campaign': {'id': c.id, 'title': c.title, 'target_amount': c.target_amount}, 'contributions': contribs_out})
        return results


# New: per-campaign roster (list parents + contribution if any)
@router.get('/campaigns/{campaign_id}/roster')
def campaign_roster(campaign_id: int, include_hidden: bool = False):
    with get_db() as session:
        # load campaign
        c = session.get(Campaign, campaign_id)
        if not c:
            raise HTTPException(status_code=404, detail='campaign not found')

        # build parent list with LEFT JOIN to contributions for this campaign
        # simple approach: query all parents and then per-parent contribution
        if include_hidden:
            stmtp = select(Parent)
        else:
            try:
                stmtp = select(Parent).where(Parent.is_hidden == False)
            except Exception:
                stmtp = select(Parent)

        parents = session.exec(stmtp).all()
        rows = []
        for p in parents:
            stmtc = select(Contribution).where(Contribution.campaign_id == campaign_id, Contribution.parent_id == p.id)
            contrib = session.exec(stmtc).first()
            rows.append({
                'parent_id': p.id,
                'parent_name': p.name,
                'parent_email': p.email,
                'contribution': None if not contrib else {
                    'id': contrib.id,
                    'amount_expected': contrib.amount_expected,
                    'amount_paid': contrib.amount_paid,
                    'status': contrib.status,
                    'paid_at': contrib.paid_at,
                    'note': contrib.note,
                }
            })

        return {'campaign': {'id': c.id, 'title': c.title, 'target_amount': c.target_amount}, 'rows': rows}


# New: allow admin to create a contribution record for (campaign, parent)
@router.post('/contributions')
def admin_create_contribution(payload: dict):
    cid = payload.get('campaign_id')
    pid = payload.get('parent_id')
    amount_expected = payload.get('amount_expected')
    if not cid or not pid:
        raise HTTPException(status_code=400, detail='campaign_id and parent_id required')
    with get_db() as session:
        # ensure campaign and parent exist
        camp = session.get(Campaign, cid)
        parent = session.get(Parent, pid)
        if not camp or not parent:
            raise HTTPException(status_code=404, detail='campaign or parent not found')
        # if contribution exists, return it (idempotent)
        stmt = select(Contribution).where(Contribution.campaign_id == cid, Contribution.parent_id == pid)
        existing = session.exec(stmt).first()
        if existing:
            return existing
        c = Contribution(campaign_id=cid, parent_id=pid, amount_expected=amount_expected or 0.0, amount_paid=0.0, status='pending')
        session.add(c)
        session.commit()
        session.refresh(c)
        return c


# --- Admin management endpoints (parents + campaigns) ---


@router.get('/parents')
def admin_list_parents(include_hidden: bool = False):
    """Return parents; by default exclude hidden parents unless include_hidden=true"""
    with get_db() as session:
        if include_hidden:
            stmt = select(Parent)
        else:
            # if DB doesn't have is_hidden (older DB), assume visible
            try:
                stmt = select(Parent).where(Parent.is_hidden == False)
            except Exception:
                stmt = select(Parent)
        parents = session.exec(stmt).all()
        return parents


@router.put('/parents/{parent_id}')
def admin_update_parent(parent_id: int, payload: dict):
    with get_db() as session:
        p = session.get(Parent, parent_id)
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        # allow updating name and email
        name = payload.get('name')
        email = payload.get('email')
        if email:
            p.email = email
        if name:
            p.name = name
        session.add(p)
        session.commit()
        session.refresh(p)
        return p


@router.post('/parents/{parent_id}/change-password')
def admin_change_parent_password(parent_id: int, payload: dict):
    new_password = payload.get('new_password')
    if not new_password:
        raise HTTPException(status_code=400, detail='new_password required')
    from ..auth import hash_password
    with get_db() as session:
        p = session.get(Parent, parent_id)
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        p.password_hash = hash_password(new_password)
        session.add(p)
        session.commit()
        return {'status': 'ok'}


@router.post('/parents/{parent_id}/hide')
def admin_hide_parent(parent_id: int):
    with get_db() as session:
        p = session.get(Parent, parent_id)
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        try:
            p.is_hidden = True
        except Exception:
            # older DB without column: best effort - ignore
            pass
        session.add(p)
        session.commit()
        session.refresh(p)
        return p


@router.post('/parents/{parent_id}/unhide')
def admin_unhide_parent(parent_id: int):
    with get_db() as session:
        p = session.get(Parent, parent_id)
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        try:
            p.is_hidden = False
        except Exception:
            pass
        session.add(p)
        session.commit()
        session.refresh(p)
        return p


@router.put('/campaigns/{campaign_id}')
def admin_update_campaign(campaign_id: int, payload: dict):
    with get_db() as session:
        c = session.get(Campaign, campaign_id)
        if not c:
            raise HTTPException(status_code=404, detail='campaign not found')
        # If campaign is closed, don't allow editing certain fields
        try:
            closed = getattr(c, 'is_closed', False)
        except Exception:
            closed = False
        if closed:
            # allow only description edits for closed campaigns
            if 'title' in payload or 'target_amount' in payload:
                raise HTTPException(status_code=409, detail='campaign is closed')
        # apply allowed updates
        for k in ('title', 'description', 'target_amount', 'due_date', 'active'):
            if k in payload:
                setattr(c, k, payload[k])
        session.add(c)
        session.commit()
        session.refresh(c)
        return c


@router.post('/campaigns/{campaign_id}/close')
def admin_close_campaign(campaign_id: int):
    with get_db() as session:
        c = session.get(Campaign, campaign_id)
        if not c:
            raise HTTPException(status_code=404, detail='campaign not found')
        try:
            c.is_closed = True
        except Exception:
            # if DB doesn't have this field, ignore
            pass
        session.add(c)
        session.commit()
        session.refresh(c)
        return {'status': 'closed'}


@router.delete('/campaigns/{campaign_id}')
def admin_delete_campaign(campaign_id: int):
    with get_db() as session:
        c = session.get(Campaign, campaign_id)
        if not c:
            raise HTTPException(status_code=404, detail='campaign not found')
        # soft-delete if supported
        try:
            from datetime import datetime
            c.deleted_at = datetime.utcnow()
            session.add(c)
        except Exception:
            # fallback hard delete
            session.delete(c)
        session.commit()
        return {'status': 'deleted'}
