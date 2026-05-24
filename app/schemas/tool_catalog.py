from pydantic import BaseModel, Field


class ToolItem(BaseModel):
    name: str
    category: str
    slug: str
    description: str = ""
    backend_supported: bool = False
    premium: bool = False
    status: str = Field(default="active")
    tags: list[str] = Field(default_factory=list)


class ToolCategory(BaseModel):
    category: str
    tools: list[ToolItem]
