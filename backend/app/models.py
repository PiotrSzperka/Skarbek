from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class CampaignBase(SQLModel):
    title: str
    description: Optional[str] = None
    target_amount: Optional[float] = 0.0
    due_date: Optional[datetime] = None
    active: bool = True


class Campaign(CampaignBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # new fields for admin management
    is_closed: bool = Field(default=False)
    deleted_at: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    pass


class Parent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: Optional[str] = None
    email: Optional[str] = None
    pupil_id: Optional[str] = None
    password_hash: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    # admin-visible flag: when True, parent is hidden from normal admin lists
    is_hidden: bool = Field(default=False)
    # force password change on first login
    force_password_change: bool = Field(default=True)
    password_changed_at: Optional[datetime] = None


class Contribution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    campaign_id: int
    parent_id: int
    amount_expected: Optional[float] = 0.0
    amount_paid: Optional[float] = 0.0
    status: Optional[str] = "pending"
    paid_at: Optional[datetime] = None
    note: Optional[str] = None


class AdminUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password_hash: str
    role: Optional[str] = "admin"
    created_at: datetime = Field(default_factory=datetime.utcnow)
