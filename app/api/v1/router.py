from fastapi import APIRouter

from app.api.v1.routes import diagnostics

router = APIRouter()
router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
