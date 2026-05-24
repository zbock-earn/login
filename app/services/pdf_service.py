from __future__ import annotations

import html
import zipfile
from io import BytesIO

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


async def merge_pdfs(files: list[bytes]) -> bytes:
    writer = PdfWriter()
    for file_data in files:
        writer.append(BytesIO(file_data))
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


async def split_pdf(file_bytes: bytes, pages: list[int] | None = None) -> bytes:
    reader = PdfReader(BytesIO(file_bytes))
    writer = PdfWriter()
    total = len(reader.pages)
    selected = pages if pages else list(range(1, total + 1))
    for p in selected:
        if 1 <= p <= total:
            writer.add_page(reader.pages[p - 1])
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


async def pdf_to_text(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()


async def remove_pdf_password(file_bytes: bytes, password: str = "") -> bytes:
    reader = PdfReader(BytesIO(file_bytes))
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = BytesIO(); writer.write(out); out.seek(0)
    return out.read()


async def images_to_pdf(images: list[bytes]) -> bytes:
    pil_images = [Image.open(BytesIO(img)).convert("RGB") for img in images]
    out = BytesIO(); first, rest = pil_images[0], pil_images[1:]
    first.save(out, format="PDF", save_all=True, append_images=rest)
    out.seek(0); return out.read()


async def text_to_pdf(text: str, title: str = "Document") -> bytes:
    out = BytesIO(); c = canvas.Canvas(out, pagesize=A4); w, h = A4
    c.setFont("Helvetica-Bold", 14); c.drawString(50, h - 50, title)
    c.setFont("Helvetica", 10); y = h - 80
    for line in text.splitlines() or [""]:
        if y < 50:
            c.showPage(); c.setFont("Helvetica", 10); y = h - 50
        c.drawString(50, y, line[:120]); y -= 14
    c.save(); out.seek(0); return out.read()


async def pdf_to_html(file_bytes: bytes) -> str:
    text = await pdf_to_text(file_bytes)
    body = "<br/>".join(html.escape(line) for line in text.splitlines())
    return f"<html><body><h1>Converted PDF</h1><p>{body}</p></body></html>"


async def pdf_to_epub_placeholder(file_bytes: bytes) -> bytes:
    text = await pdf_to_text(file_bytes)
    return f"EPUB_PLACEHOLDER\n\n{text}".encode("utf-8")


async def pdf_to_images_zip(file_bytes: bytes, fmt: str = "PNG") -> bytes:
    reader = PdfReader(BytesIO(file_bytes))
    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, page in enumerate(reader.pages, start=1):
            # placeholder rendered page image card
            img = Image.new("RGB", (1240, 1754), "white")
            b = BytesIO(); img.save(b, format=fmt.upper()); b.seek(0)
            zf.writestr(f"page_{i}.{fmt.lower()}", b.read())
    out.seek(0)
    return out.read()


async def any_to_pdf(name: str, content: bytes) -> bytes:
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else "txt"
    if ext in {"txt", "md", "doc", "docx", "epub", "pptx"}:
        text = content.decode("utf-8", errors="ignore")
        return await text_to_pdf(text or f"Converted from {ext.upper()}", title=f"{ext.upper()} to PDF")
    if ext in {"jpg", "jpeg", "png", "webp", "bmp"}:
        return await images_to_pdf([content])
    raise ValueError("Unsupported input format for any-to-pdf")
