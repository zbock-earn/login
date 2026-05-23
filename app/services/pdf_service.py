from __future__ import annotations

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
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n\n".join(parts).strip()


async def remove_pdf_password(file_bytes: bytes, password: str = "") -> bytes:
    reader = PdfReader(BytesIO(file_bytes))
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()


async def images_to_pdf(images: list[bytes]) -> bytes:
    pil_images = [Image.open(BytesIO(img)).convert("RGB") for img in images]
    out = BytesIO()
    first, rest = pil_images[0], pil_images[1:]
    first.save(out, format="PDF", save_all=True, append_images=rest)
    out.seek(0)
    return out.read()


async def text_to_pdf(text: str, title: str = "Document") -> bytes:
    out = BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, h - 50, title)
    c.setFont("Helvetica", 10)
    y = h - 80
    for line in text.splitlines() or [""]:
        if y < 50:
            c.showPage(); c.setFont("Helvetica", 10); y = h - 50
        c.drawString(50, y, line[:120])
        y -= 14
    c.save()
    out.seek(0)
    return out.read()
