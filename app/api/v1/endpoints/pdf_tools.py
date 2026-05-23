from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.pdf_service import (
    any_to_pdf,
    images_to_pdf,
    merge_pdfs,
    pdf_to_epub_placeholder,
    pdf_to_html,
    pdf_to_images_zip,
    pdf_to_text,
    remove_pdf_password,
    split_pdf,
    text_to_pdf,
)

router = APIRouter()


@router.post("/merge")
async def merge_pdf_endpoint(files: list[UploadFile] = File(...)) -> StreamingResponse:
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 PDF files.")
    payload = [await f.read() for f in files if f.content_type == "application/pdf"]
    if len(payload) != len(files):
        raise HTTPException(status_code=400, detail="All files must be PDFs")
    merged = await merge_pdfs(payload)
    return StreamingResponse(iter([merged]), media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="merged.pdf"'})


@router.post('/split')
async def split_pdf_endpoint(file: UploadFile = File(...), pages: str = Form(default="")) -> StreamingResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF accepted")
    page_list = [int(x.strip()) for x in pages.split(',') if x.strip().isdigit()] if pages else None
    content = await split_pdf(await file.read(), page_list)
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="split.pdf"'})


@router.post('/pdf-convert')
async def pdf_convert_endpoint(file: UploadFile = File(...), target_format: str = Form(...)) -> StreamingResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF accepted")
    tf = target_format.lower()
    raw = await file.read()
    if tf in {"txt", "doc", "docx"}:
        text = await pdf_to_text(raw)
        fname = f"converted.{ 'docx' if tf in {'doc','docx'} else 'txt'}"
        mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if tf in {'doc','docx'} else 'text/plain'
        return StreamingResponse(iter([text.encode('utf-8')]), media_type=mime, headers={'Content-Disposition': f'attachment; filename="{fname}"'})
    if tf == "html":
        html_out = await pdf_to_html(raw)
        return StreamingResponse(iter([html_out.encode('utf-8')]), media_type='text/html', headers={'Content-Disposition': 'attachment; filename="converted.html"'})
    if tf == "epub":
        epub = await pdf_to_epub_placeholder(raw)
        return StreamingResponse(iter([epub]), media_type='application/epub+zip', headers={'Content-Disposition': 'attachment; filename="converted.epub"'})
    if tf in {"jpeg", "jpg", "png"}:
        zip_bytes = await pdf_to_images_zip(raw, fmt="JPEG" if tf in {"jpeg", "jpg"} else "PNG")
        return StreamingResponse(iter([zip_bytes]), media_type='application/zip', headers={'Content-Disposition': 'attachment; filename="pdf_pages.zip"'})
    raise HTTPException(status_code=400, detail="Unsupported target format")


@router.post('/any-to-pdf')
async def any_to_pdf_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    raw = await file.read()
    try:
        content = await any_to_pdf(file.filename or 'input.txt', raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="converted.pdf"'})


@router.post('/word-to-pdf')
async def word_to_pdf_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    raw = await file.read()
    text = raw.decode('utf-8', errors='ignore')
    content = await text_to_pdf(text, title='Word to PDF')
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="word_to_pdf.pdf"'})


@router.post('/password-remover')
async def password_remover_endpoint(file: UploadFile = File(...), password: str = Form(default="")) -> StreamingResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF accepted")
    content = await remove_pdf_password(await file.read(), password)
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="unlocked.pdf"'})


@router.post('/image-to-pdf')
async def image_to_pdf_endpoint(files: list[UploadFile] = File(...)) -> StreamingResponse:
    payload = [await f.read() for f in files]
    content = await images_to_pdf(payload)
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="images.pdf"'})


@router.post('/epub-to-pdf')
async def epub_to_pdf_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    content = await any_to_pdf(file.filename or 'book.epub', await file.read())
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="epub.pdf"'})


@router.post('/txt-to-pdf')
async def txt_to_pdf_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    content = await any_to_pdf(file.filename or 'text.txt', await file.read())
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="text.pdf"'})
