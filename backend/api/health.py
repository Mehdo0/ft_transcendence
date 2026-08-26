from fastapi import APIRouter

from core.health import check_database


router = APIRouter()


@router.get("/api/health", include_in_schema=False)
async def health():
    check_database()
    return {"status": "ok"}
