from fastapi import APIRouter
from .campaigns import router as campaigns_router
from .admin import router as admin_router

router = APIRouter()
router.include_router(campaigns_router, prefix="/campaigns")
router.include_router(admin_router, prefix="/admin")
