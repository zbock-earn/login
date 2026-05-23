from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ApiMessage(BaseModel):
    message: str


class ToolExecutionResult(BaseModel):
    tool_slug: str
    status: str = Field(default="success")
    message: str
    output: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class SystemHealth(BaseModel):
    app_name: str
    version: str
    environment: str
    uptime_seconds: float
    available_modules: list[str]
