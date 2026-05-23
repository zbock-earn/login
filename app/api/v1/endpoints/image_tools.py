from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services.image_service import compress_image

router = APIRouter()


@router.post("/compress")
async def compress_image_endpoint(
    file: UploadFile = File(...),
    quality: int = Form(default=70),
) -> StreamingResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")

    image_bytes = await file.read()
    compressed = await compress_image(image_bytes=image_bytes, quality=quality)

    return StreamingResponse(
        iter([compressed]),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="compressed_{file.filename}"'},
    )
