from pydantic import BaseModel


class ToolItem(BaseModel):
    name: str
    category: str
    slug: str
    backend_supported: bool = False
    premium: bool = False


class ToolCategory(BaseModel):
    category: str
    tools: list[ToolItem]
