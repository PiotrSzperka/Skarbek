from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models import Campaign, CampaignCreate
from ..db import get_db
from sqlmodel import Session, select
from ..models import Contribution, Parent

router = APIRouter()


@router.get("/", response_model=List[Campaign])
def list_campaigns(active: Optional[bool] = True):
    with get_db() as session:
        stmt = select(Campaign)
        if active is not None:
            stmt = stmt.where(Campaign.active == active)
        results = session.exec(stmt).all()
        return results


@router.post("/", response_model=Campaign)
def create_campaign(payload: CampaignCreate):
    with get_db() as session:
        c = Campaign.from_orm(payload)
        session.add(c)
        session.commit()
        session.refresh(c)
        return c


@router.get("/{campaign_id}/status")
def parent_status(campaign_id: int, email: str = None, pupilId: str = None):
    if not email and not pupilId:
        raise HTTPException(status_code=400, detail='email or pupilId required')
    with get_db() as session:
        parent = None
        if email:
            parent = session.exec(select(Parent).where(Parent.email == email)).first()
        elif pupilId:
            parent = session.exec(select(Parent).where(Parent.pupil_id == pupilId)).first()
        if not parent:
            return {"status": "not_found"}
        contrib = session.exec(select(Contribution).where(Contribution.campaign_id == campaign_id, Contribution.parent_id == parent.id)).first()
        if not contrib:
            return {"status": "no_record"}
        return {"status": contrib.status, "amount_expected": contrib.amount_expected, "amount_paid": contrib.amount_paid}
