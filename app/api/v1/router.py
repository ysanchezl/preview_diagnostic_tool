from fastapi import APIRouter

from app.api.v1.routes import diagnostics, enrichment

router = APIRouter()
router.include_router(diagnostics.router, prefix="/diagnostics", tags=["diagnostics"])
router.include_router(enrichment.router, prefix="/diagnostics", tags=["enrichment"])
