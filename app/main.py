from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.router import api_router
from app.core import settings
from app.schemas.tool_responses import SystemHealth

STARTED_AT = datetime.now(tz=timezone.utc)

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
app.include_router(api_router, prefix="/api/v1")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request, "app_name": settings.app_name})


@app.get("/tools/{slug}", response_class=HTMLResponse)
async def tool_page(request: Request, slug: str) -> HTMLResponse:
    return templates.TemplateResponse("tool.html", {"request": request, "slug": slug, "app_name": settings.app_name})


@app.get("/api/v1/system/health", response_model=SystemHealth)
async def system_health() -> SystemHealth:
    uptime = (datetime.now(tz=timezone.utc) - STARTED_AT).total_seconds()
    return SystemHealth(
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        uptime_seconds=uptime,
        available_modules=["catalog", "image_tools", "pdf_tools", "instant_tools", "templates"],
    )
