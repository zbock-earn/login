from fastapi import APIRouter

from app.services.catalog_service import get_catalog

router = APIRouter()


@router.get("/catalog")
async def catalog() -> list[dict]:
    categories = get_catalog()
    return [c.model_dump() for c in categories]
