from fastapi import APIRouter

from app.api.v1.endpoints.pdf_tools import router as pdf_router
from app.api.v1.endpoints.image_tools import router as image_router
from app.api.v1.endpoints.catalog import router as catalog_router
from app.api.v1.endpoints.media_tools import router as media_router

api_router = APIRouter()
api_router.include_router(image_router, prefix="/images", tags=["images"])
api_router.include_router(pdf_router, prefix="/pdf", tags=["pdf"])
api_router.include_router(catalog_router, prefix="/tools", tags=["tools"])

api_router.include_router(media_router, prefix="/media", tags=["media"])
