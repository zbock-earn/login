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


def _catalog_source() -> dict[str, list[str]]:
    return {
        "Media & Video Tools": [
            "YouTube Video Downloader", "TikTok Video Downloader", "Instagram Reel Downloader", "Video to GIF Converter", "Video Audio Extractor (MP4 to MP3)"
        ],
        "Image & Graphic Tools": [
            "Image Compressor", "Image Format Converter", "Image Resizer", "Image Cropper", "Background Remover", "Color Picker from Image", "Palette Generator", "Text to Image Placeholder Generator", "Image Blur/Sharpen Tool", "Base64 to Image & Vice Versa"
        ],
        "PDF & Document Tools": [
            "PDF Merger", "PDF Splitter", "PDF to Word Converter", "Word to PDF", "PDF Password Remover", "Image to PDF Converter", "EPUB to PDF Converter", "TXT to PDF"
        ],
        "Text & Content Tools": [
            "Case Converter", "Word & Character Counter", "Remove Duplicate Lines", "Text Reverser", "Lorem Ipsum Placeholder Generator", "Find and Replace Text", "URL Encoder / Decoder", "HTML Entity Encoder / Decoder", "Markdown to HTML Converter", "Text Diff Checker", "Slug Generator", "Binary to Text & Vice Versa"
        ],
        "Calculators & Converters": [
            "Currency Converter", "Age Calculator", "Percentage Calculator", "GST / Tax Calculator", "Loan / EMI Calculator", "Unit Converter", "Hex to RGB & RGB to Hex Converter", "Binary/Octal/Hexadecimal Converter", "Time Zone Converter", "Crypto Price Ticker / Converter"
        ],
        "Developer & Cyber Tools": [
            "Strong Password Generator", "QR Code Generator", "QR Code Scanner", "HTML Formatter / Minifier", "CSS Formatter / Minifier", "JSON Formatter / Validator", "User Agent Finder", "MD5 / SHA-256 Hash Generator", "IP Address Finder", "Website Ping / Status Checker"
        ],
    }


def get_catalog() -> list[ToolCategory]:
    data = _catalog_source()
    backend_tools = {
        "Image Compressor", "PDF Merger", "Video to GIF Converter", "Video Audio Extractor (MP4 to MP3)",
        "Image Format Converter", "Image Resizer", "PDF Splitter", "Image to PDF Converter", "Website Ping / Status Checker"
    }
    premium_tools = {
        "Background Remover", "Website Ping / Status Checker", "Currency Converter", "Crypto Price Ticker / Converter",
        "YouTube Video Downloader", "TikTok Video Downloader", "Instagram Reel Downloader"
    }

    categories: list[ToolCategory] = []
    for category, tools in data.items():
        items = [
            ToolItem(
                name=t,
                category=category,
                slug=slugify(t),
                backend_supported=t in backend_tools,
                premium=t in premium_tools,
            )
            for t in tools
        ]
        categories.append(ToolCategory(category=category, tools=items))
    return categories


def get_catalog_metrics(categories: list[ToolCategory]) -> CatalogMetrics:
    flattened = [tool for cat in categories for tool in cat.tools]
    return CatalogMetrics(
        total_tools=len(flattened),
        total_categories=len(categories),
        backend_supported=sum(tool.backend_supported for tool in flattened),
        premium_tools=sum(tool.premium for tool in flattened),
    )


def get_tag_frequencies(categories: list[ToolCategory]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for category in categories:
        for tool in category.tools:
            for token in tool.name.lower().replace("/", " ").replace("&", " ").split():
                if len(token) >= 4:
                    counter[token] += 1
    return dict(counter.most_common(20))
