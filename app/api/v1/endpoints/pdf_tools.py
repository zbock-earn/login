from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.pdf_service import (
    images_to_pdf,
    merge_pdfs,
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


@router.post('/pdf-to-word')
async def pdf_to_word_endpoint(file: UploadFile = File(...), output: str = Form(default="txt")) -> StreamingResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF accepted")
    text = await pdf_to_text(await file.read())
    if output.lower() == 'txt':
        return StreamingResponse(iter([text.encode('utf-8')]), media_type='text/plain', headers={'Content-Disposition': 'attachment; filename="converted.txt"'})
    return StreamingResponse(iter([text.encode('utf-8')]), media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers={'Content-Disposition': 'attachment; filename="converted.docx"'})


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
    raw = await file.read()
    # Placeholder parser: extracts plain text from epub bytes best-effort
    text = raw.decode('utf-8', errors='ignore')[:20000]
    content = await text_to_pdf(text, title='EPUB to PDF')
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="epub.pdf"'})


@router.post('/txt-to-pdf')
async def txt_to_pdf_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    text = (await file.read()).decode('utf-8', errors='ignore')
    content = await text_to_pdf(text, title='TXT to PDF')
    return StreamingResponse(iter([content]), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="text.pdf"'})
