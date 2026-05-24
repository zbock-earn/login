from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from app.schemas.tool_catalog import ToolCategory, ToolItem


@dataclass(frozen=True)
class CatalogMetrics:
    total_tools: int
    total_categories: int
    backend_supported: int
    premium_tools: int


def slugify(name: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in name).split())


def _tool_definitions() -> dict[str, list[dict]]:
    return {
        "Media & Video Tools": [
            {"name": "Video to GIF Converter", "backend": True, "premium": False, "tags": ["video", "gif", "convert"], "description": "Convert MP4/WebM clips into animated GIF output."},
            {"name": "Video Audio Extractor (MP4 to MP3)", "backend": True, "premium": False, "tags": ["video", "audio", "mp3"], "description": "Extract MP3 audio tracks from uploaded MP4 files."},
        ],
        "Image & Graphic Tools": [
            {"name": "Image Compressor (JPEG/PNG size reducer)", "backend": True, "premium": False, "tags": ["image", "compress"]},
            {"name": "Image Format Converter (PNG to WebP, JPG to PNG, etc.)", "backend": True, "premium": False, "tags": ["image", "format", "convert"]},
            {"name": "Image Resizer (Width/Height editor)", "backend": True, "premium": False, "tags": ["image", "resize"]},
            {"name": "Image Cropper", "backend": True, "premium": False, "tags": ["image", "crop"]},
            {"name": "Background Remover (using free API integration)", "backend": True, "premium": True, "tags": ["image", "ai", "background"]},
            {"name": "Color Picker from Image", "backend": False, "premium": False, "tags": ["color", "image"]},
            {"name": "Palette Generator", "backend": False, "premium": False, "tags": ["palette", "design"]},
            {"name": "Text to Image Placeholder Generator", "backend": False, "premium": False, "tags": ["placeholder", "image"]},
            {"name": "Image Blur/Sharpen Tool", "backend": True, "premium": False, "tags": ["image", "blur", "sharpen"]},
            {"name": "Base64 to Image & Vice Versa", "backend": False, "premium": False, "tags": ["base64", "image"]},
        ],
        "PDF & Document Tools": [
            {"name": "PDF Merger (Combine multiple PDFs)", "backend": True, "premium": False, "tags": ["pdf", "merge"]},
            {"name": "PDF Splitter", "backend": True, "premium": False, "tags": ["pdf", "split"]},
            {"name": "PDF to Word Converter (Simple text extraction)", "backend": True, "premium": False, "tags": ["pdf", "word"]},
            {"name": "Word to PDF", "backend": True, "premium": False, "tags": ["word", "pdf"]},
            {"name": "PDF Password Remover", "backend": True, "premium": True, "tags": ["pdf", "security"]},
            {"name": "Image to PDF Converter", "backend": True, "premium": False, "tags": ["image", "pdf"]},
            {"name": "EPUB to PDF Converter", "backend": True, "premium": True, "tags": ["epub", "pdf"]},
            {"name": "TXT to PDF", "backend": True, "premium": False, "tags": ["txt", "pdf"]},
        ],
        "Text & Content Tools": [
            {"name": "Case Converter (UPPERCASE, lowercase, Title Case)", "backend": False, "premium": False, "tags": ["text", "case"]},
            {"name": "Word & Character Counter", "backend": False, "premium": False, "tags": ["text", "counter"]},
            {"name": "Remove Duplicate Lines", "backend": False, "premium": False, "tags": ["text", "cleanup"]},
            {"name": "Text Reverser", "backend": False, "premium": False, "tags": ["text", "reverse"]},
            {"name": "Lorem Ipsum Placeholder Generator", "backend": False, "premium": False, "tags": ["lorem", "placeholder"]},
            {"name": "Find and Replace Text", "backend": False, "premium": False, "tags": ["text", "replace"]},
            {"name": "URL Encoder / Decoder", "backend": False, "premium": False, "tags": ["url", "encode"]},
            {"name": "HTML Entity Encoder / Decoder", "backend": False, "premium": False, "tags": ["html", "encode"]},
            {"name": "Markdown to HTML Converter", "backend": False, "premium": False, "tags": ["markdown", "html"]},
            {"name": "Text Diff Checker (Compare two texts)", "backend": False, "premium": False, "tags": ["diff", "compare"]},
            {"name": "Slug Generator (Text to URL-friendly-slug)", "backend": False, "premium": False, "tags": ["slug", "seo"]},
            {"name": "Binary to Text & Vice Versa", "backend": False, "premium": False, "tags": ["binary", "text"]},
        ],
        "Calculators & Converters": [
            {"name": "Currency Converter (Live API integration)", "backend": True, "premium": True, "tags": ["currency", "api"]},
            {"name": "Age Calculator (Date of birth to exact age)", "backend": False, "premium": False, "tags": ["age", "date"]},
            {"name": "Percentage Calculator", "backend": False, "premium": False, "tags": ["percentage", "math"]},
            {"name": "GST / Tax Calculator", "backend": False, "premium": False, "tags": ["gst", "tax"]},
            {"name": "Loan / EMI Calculator", "backend": False, "premium": False, "tags": ["loan", "emi"]},
            {"name": "Unit Converter (Length, Weight, Temperature, Speed)", "backend": False, "premium": False, "tags": ["unit", "convert"]},
            {"name": "Hex to RGB & RGB to Hex Converter", "backend": False, "premium": False, "tags": ["hex", "rgb"]},
            {"name": "Binary/Octal/Hexadecimal Converter", "backend": False, "premium": False, "tags": ["binary", "octal", "hex"]},
            {"name": "Time Zone Converter", "backend": False, "premium": False, "tags": ["time", "timezone"]},
            {"name": "Crypto Price Ticker / Converter", "backend": True, "premium": True, "tags": ["crypto", "ticker"]},
        ],
        "Developer & Cyber Tools": [
            {"name": "Strong Password Generator", "backend": False, "premium": False, "tags": ["password", "security"]},
            {"name": "QR Code Generator (with download option)", "backend": False, "premium": False, "tags": ["qr", "generator"]},
            {"name": "QR Code Scanner (using web camera)", "backend": False, "premium": False, "tags": ["qr", "scanner"]},
            {"name": "HTML Formatter / Minifier", "backend": False, "premium": False, "tags": ["html", "formatter"]},
            {"name": "CSS Formatter / Minifier", "backend": False, "premium": False, "tags": ["css", "formatter"]},
            {"name": "JSON Formatter / Validator", "backend": False, "premium": False, "tags": ["json", "validator"]},
            {"name": "User Agent Finder", "backend": False, "premium": False, "tags": ["useragent", "browser"]},
            {"name": "MD5 / SHA-256 Hash Generator", "backend": False, "premium": False, "tags": ["md5", "sha256", "hash"]},
            {"name": "IP Address Finder (Shows user's public IP)", "backend": True, "premium": False, "tags": ["ip", "network"]},
            {"name": "Website Ping / Status Checker", "backend": True, "premium": True, "tags": ["ping", "status"]},
        ],
    }


def get_catalog() -> list[ToolCategory]:
    categories: list[ToolCategory] = []
    for category, tools in _tool_definitions().items():
        items = [
            ToolItem(
                name=t["name"], category=category, slug=slugify(t["name"]),
                description=t.get("description", f"{t['name']} utility for {category.lower()} workflows."),
                backend_supported=t.get("backend", False), premium=t.get("premium", False), tags=t.get("tags", [])
            ) for t in tools
        ]
        categories.append(ToolCategory(category=category, tools=items))
    return categories


def get_catalog_metrics(categories: list[ToolCategory]) -> CatalogMetrics:
    flattened = [tool for cat in categories for tool in cat.tools]
    return CatalogMetrics(len(flattened), len(categories), sum(t.backend_supported for t in flattened), sum(t.premium for t in flattened))


def get_tag_frequencies(categories: list[ToolCategory]) -> dict[str, int]:
    counter: Counter[str] = Counter(tag for c in categories for t in c.tools for tag in t.tags)
    return dict(counter.most_common(25))
