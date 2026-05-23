from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.pdf_service import merge_pdfs

router = APIRouter()


@router.post("/merge")
async def merge_pdf_endpoint(files: list[UploadFile] = File(...)) -> StreamingResponse:
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="Please upload at least 2 PDF files.")

    pdf_bytes: list[bytes] = []
    for file in files:
        if file.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail=f"{file.filename} is not a PDF")
        pdf_bytes.append(await file.read())

    merged = await merge_pdfs(pdf_bytes)
    return StreamingResponse(
        iter([merged]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="merged.pdf"'},
    )
