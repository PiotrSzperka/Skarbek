from fastapi import FastAPI
from .api import router as api_router
from .api import parents as parents_router
from .db import init_db
from .middleware import AdminAuthMiddleware

app = FastAPI(title="Skarbek API")
app.add_middleware(AdminAuthMiddleware)
app.include_router(api_router, prefix="/api")
app.include_router(parents_router.router, prefix="/api")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
