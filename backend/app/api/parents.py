import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select

from ..auth import hash_password, verify_password, create_token, decode_token
from ..db import get_db
from ..email import GmailEmailClient, gmail_client
from ..models import Parent, Campaign, Contribution
from ..utils import generate_readable_password

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_email_client() -> GmailEmailClient:
    return gmail_client


@router.post('/admin/parents')
def admin_create_parent(
    payload: dict,
    request: Request,
    email_client: GmailEmailClient = Depends(_get_email_client),
):
    user = getattr(request.state, 'user', None)
    if user != 'admin':
        raise HTTPException(status_code=403, detail='admin privileges required')

    name = payload.get('name')
    email = payload.get('email')
    if not email:
        raise HTTPException(status_code=400, detail='email required')

    temporary_password = generate_readable_password(length=10)

    with get_db() as session:
        stmt = select(Parent).where(Parent.email == email)
        existing = session.exec(stmt).first()
        if existing:
            raise HTTPException(status_code=400, detail='parent already exists')
        parent = Parent(
            name=name,
            email=email,
            password_hash=hash_password(temporary_password),
            force_password_change=True,
        )
        session.add(parent)
        try:
            email_client.send_temporary_password_email(email, temporary_password, parent_name=name)
        except Exception:
            session.rollback()
            logger.exception('Nie udało się wysłać tymczasowego hasła do %s', email)
            raise HTTPException(status_code=500, detail='failed to send temporary password email')
        session.commit()
        session.refresh(parent)
        return {"id": parent.id, "name": parent.name, "email": parent.email}


@router.post('/parents/login')
def parent_login(payload: dict):
    email = payload.get('email')
    password = payload.get('password')
    if not email or not password:
        raise HTTPException(status_code=400, detail='email and password required')
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == email)
        p = session.exec(stmt).first()
        if not p or not p.password_hash or not verify_password(password, p.password_hash):
            raise HTTPException(status_code=401, detail='invalid credentials')
        token = create_token({'sub': p.email, 'role': 'parent'}, expires_minutes=60*24*7)
        response = {'token': token}
        if p.force_password_change:
            response['require_password_change'] = True
        return response


def get_parent_from_token(request: Request):
    auth = request.headers.get('authorization')
    if not auth or not auth.lower().startswith('bearer '):
        return None
    token = auth.split(None, 1)[1]
    payload = decode_token(token)
    if not payload or payload.get('role') != 'parent':
        return None
    return payload.get('sub')


def check_password_change_required(parent: Parent):
    """Raise 403 if parent must change password"""
    if parent.force_password_change:
        raise HTTPException(
            status_code=403,
            detail={'code': 'password_change_required', 'message': 'Password change required before accessing resources'}
        )


@router.post('/parents/change-password-initial')
def parent_change_password_initial(payload: dict, request: Request):
    sub = get_parent_from_token(request)
    if not sub:
        raise HTTPException(status_code=401, detail='unauthorized')
    
    old_password = payload.get('old_password')
    new_password = payload.get('new_password')
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail='old_password and new_password required')
    
    if old_password == new_password:
        raise HTTPException(status_code=400, detail='new password must be different from old password')
    
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == sub)
        p = session.exec(stmt).first()
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        
        if not verify_password(old_password, p.password_hash):
            raise HTTPException(status_code=401, detail='invalid old password')
        
        from datetime import datetime
        p.password_hash = hash_password(new_password)
        p.force_password_change = False
        p.password_changed_at = datetime.utcnow()
        session.add(p)
        session.commit()
        session.refresh(p)
        
        token = create_token({'sub': p.email, 'role': 'parent'}, expires_minutes=60*24*7)
        return {'token': token, 'require_password_change': False}


@router.get('/parents/me')
def parent_me(request: Request):
    sub = get_parent_from_token(request)
    if not sub:
        raise HTTPException(status_code=401, detail='unauthorized')
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == sub)
        p = session.exec(stmt).first()
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        check_password_change_required(p)
        return {"id": p.id, "name": p.name, "email": p.email}


@router.get('/parents/campaigns')
def parent_campaigns(request: Request):
    sub = get_parent_from_token(request)
    if not sub:
        raise HTTPException(status_code=401, detail='unauthorized')
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == sub)
        p = session.exec(stmt).first()
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        check_password_change_required(p)

        # get active campaigns
        stmt = select(Campaign).where(Campaign.active == True)
        camps = session.exec(stmt).all()
        results = []
        for c in camps:
            stmt2 = select(Contribution).where(Contribution.campaign_id == c.id, Contribution.parent_id == p.id)
            contrib = session.exec(stmt2).first()
            contrib_obj = None
            if contrib:
                contrib_obj = {"id": contrib.id, "amount_paid": contrib.amount_paid, "status": contrib.status, "paid_at": contrib.paid_at, "note": contrib.note}
            results.append({"campaign": {"id": c.id, "title": c.title, "description": c.description, "target_amount": c.target_amount, "due_date": c.due_date, "active": c.active}, "contribution": contrib_obj})
        return results


@router.get('/parents/contributions')
def parent_contributions(request: Request):
    sub = get_parent_from_token(request)
    if not sub:
        raise HTTPException(status_code=401, detail='unauthorized')
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == sub)
        p = session.exec(stmt).first()
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        check_password_change_required(p)
        stmt2 = select(Contribution).where(Contribution.parent_id == p.id)
        items = session.exec(stmt2).all()
        return [{"id": it.id, "campaign_id": it.campaign_id, "amount_paid": it.amount_paid, "status": it.status, "paid_at": it.paid_at, "note": it.note} for it in items]


@router.post('/parents/contributions')
def parent_submit_contribution(payload: dict, request: Request):
    sub = get_parent_from_token(request)
    if not sub:
        raise HTTPException(status_code=401, detail='unauthorized')
    campaign_id = payload.get('campaign_id')
    amount = payload.get('amount')
    note = payload.get('note')
    if not campaign_id or not amount:
        raise HTTPException(status_code=400, detail='campaign_id and amount required')
    with get_db() as session:
        stmt = select(Parent).where(Parent.email == sub)
        p = session.exec(stmt).first()
        if not p:
            raise HTTPException(status_code=404, detail='parent not found')
        check_password_change_required(p)
        c = Contribution(campaign_id=campaign_id, parent_id=p.id, amount_expected=0.0, amount_paid=amount, status='pending', note=note)
        session.add(c)
        session.commit()
        session.refresh(c)
        return {"id": c.id, "status": c.status}
