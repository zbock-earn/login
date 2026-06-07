from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.web.routes import router

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.mount("/generated", StaticFiles(directory=settings.generated_dir), name="generated")
app.include_router(router)
