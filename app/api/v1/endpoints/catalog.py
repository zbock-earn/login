from fastapi import APIRouter, Query

from app.services.catalog_service import get_catalog, get_catalog_metrics, get_tag_frequencies

router = APIRouter()


@router.get("/catalog")
async def catalog(include_stats: bool = Query(default=True)) -> dict:
    categories = get_catalog()
    payload: dict = {"categories": [c.model_dump() for c in categories]}
    if include_stats:
        metrics = get_catalog_metrics(categories)
        payload["stats"] = {
            "total_tools": metrics.total_tools,
            "total_categories": metrics.total_categories,
            "backend_supported": metrics.backend_supported,
            "premium_tools": metrics.premium_tools,
            "hot_tags": get_tag_frequencies(categories),
        }
    return payload
