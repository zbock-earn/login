from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    # Allows both `python app/main.py` from the project root and `python main.py`
    # from inside the app directory on Windows without ModuleNotFoundError.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
