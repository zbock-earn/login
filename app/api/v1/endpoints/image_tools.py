from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.image_service import (
    background_remove_placeholder,
    base64_to_image,
    blur_or_sharpen,
    compress_image,
    convert_image_format,
    crop_image,
    image_to_base64,
    placeholder_image,
    resize_image,
)

router = APIRouter()
SUPPORTED_OUTPUTS = {
    "JPG": ("JPEG", "jpg", "image/jpeg"),
    "JPEG": ("JPEG", "jpg", "image/jpeg"),
    "PNG": ("PNG", "png", "image/png"),
    "WEBP": ("WEBP", "webp", "image/webp"),
    "BMP": ("BMP", "bmp", "image/bmp"),
    "GIF": ("GIF", "gif", "image/gif"),
    "TIFF": ("TIFF", "tiff", "image/tiff"),
    "TIF": ("TIFF", "tif", "image/tiff"),
    "ICO": ("ICO", "ico", "image/x-icon"),
    "AVIF": ("AVIF", "avif", "image/avif"),
}


def _validate_image(file: UploadFile) -> None:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed.")


@router.post("/compress")
async def compress_image_endpoint(file: UploadFile = File(...), quality: int = Form(default=70)) -> StreamingResponse:
    _validate_image(file)
    compressed = await compress_image(await file.read(), quality=quality)
    return StreamingResponse(iter([compressed]), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="compressed_{file.filename}"'})


@router.post("/convert-format")
async def universal_convert_endpoint(
    file: UploadFile = File(...),
    input_format: str = Form(default="AUTO"),
    target_format: str = Form(...),
) -> StreamingResponse:
    _validate_image(file)
    fmt_key = target_format.upper().strip()
    if fmt_key not in SUPPORTED_OUTPUTS:
        raise HTTPException(status_code=400, detail=f"Unsupported target format: {target_format}")
    pil_fmt, ext, mime = SUPPORTED_OUTPUTS[fmt_key]
    raw = await file.read()
    try:
        content = await convert_image_format(raw, target_format=pil_fmt)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Conversion failed from {input_format} to {target_format}: {exc}") from exc

    basename = (file.filename or "image").rsplit(".", 1)[0]
    return StreamingResponse(
        iter([content]),
        media_type=mime,
        headers={"Content-Disposition": f'attachment; filename="{basename}_converted.{ext}"'},
    )


@router.post("/resize")
async def resize_endpoint(file: UploadFile = File(...), width: int = Form(...), height: int = Form(...)) -> StreamingResponse:
    _validate_image(file)
    content = await resize_image(await file.read(), width=width, height=height)
    return StreamingResponse(iter([content]), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="resized_{file.filename}"'})


@router.post("/crop")
async def crop_endpoint(file: UploadFile = File(...), x: int = Form(...), y: int = Form(...), w: int = Form(...), h: int = Form(...)) -> StreamingResponse:
    _validate_image(file)
    content = await crop_image(await file.read(), x, y, w, h)
    return StreamingResponse(iter([content]), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="cropped_{file.filename}"'})


@router.post("/background-remove")
async def background_remove_endpoint(file: UploadFile = File(...)) -> StreamingResponse:
    _validate_image(file)
    content = await background_remove_placeholder(await file.read())
    return StreamingResponse(iter([content]), media_type="image/png", headers={"Content-Disposition": 'attachment; filename="bg_removed.png"'})


@router.post("/blur-sharpen")
async def blur_sharpen_endpoint(file: UploadFile = File(...), mode: str = Form(...), intensity: float = Form(default=2.0)) -> StreamingResponse:
    _validate_image(file)
    content = await blur_or_sharpen(await file.read(), mode=mode, intensity=intensity)
    return StreamingResponse(iter([content]), media_type="application/octet-stream", headers={"Content-Disposition": f'attachment; filename="filtered_{file.filename}"'})


@router.post("/to-base64")
async def to_base64_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    _validate_image(file)
    encoded = await image_to_base64(await file.read())
    return JSONResponse({"base64": encoded})


@router.post("/from-base64")
async def from_base64_endpoint(payload: str = Form(...)) -> StreamingResponse:
    content = await base64_to_image(payload)
    return StreamingResponse(iter([content]), media_type="application/octet-stream", headers={"Content-Disposition": 'attachment; filename="decoded_image.png"'})


@router.post("/placeholder")
async def placeholder_endpoint(width: int = Form(...), height: int = Form(...), bg_hex: str = Form(default="#cccccc"), text: str = Form(default="Placeholder")) -> StreamingResponse:
    content = await placeholder_image(width, height, bg_hex, text)
    return StreamingResponse(iter([content]), media_type="image/png", headers={"Content-Disposition": 'attachment; filename="placeholder.png"'})
