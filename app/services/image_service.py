from __future__ import annotations

import base64
from io import BytesIO

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def _open_image(image_bytes: bytes) -> Image.Image:
    return Image.open(BytesIO(image_bytes))


def _serialize(img: Image.Image, fmt: str = "PNG", quality: int = 90) -> bytes:
    out = BytesIO()
    save_kwargs = {"optimize": True}
    if fmt.upper() in {"JPEG", "WEBP"}:
        save_kwargs["quality"] = quality
    if fmt.upper() == "JPEG" and img.mode in {"RGBA", "LA", "P"}:
        img = img.convert("RGB")
    img.save(out, format=fmt.upper(), **save_kwargs)
    out.seek(0)
    return out.read()


async def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    img = _open_image(image_bytes)
    fmt = "JPEG" if (img.format or "").upper() not in {"PNG", "WEBP"} else img.format.upper()
    return _serialize(img, fmt=fmt, quality=max(5, min(95, quality)))


async def convert_image_format(image_bytes: bytes, target_format: str) -> bytes:
    img = _open_image(image_bytes)
    return _serialize(img, fmt=target_format, quality=90)


async def resize_image(image_bytes: bytes, width: int, height: int) -> bytes:
    img = _open_image(image_bytes)
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    return _serialize(resized, fmt=img.format or "PNG")


async def crop_image(image_bytes: bytes, x: int, y: int, w: int, h: int) -> bytes:
    img = _open_image(image_bytes)
    cropped = img.crop((x, y, x + w, y + h))
    return _serialize(cropped, fmt=img.format or "PNG")


async def background_remove_placeholder(image_bytes: bytes) -> bytes:
    img = _open_image(image_bytes).convert("RGBA")
    gray = ImageOps.grayscale(img)
    mask = gray.point(lambda p: 255 if p > 245 else 0)
    img.putalpha(ImageOps.invert(mask))
    return _serialize(img, fmt="PNG")


async def blur_or_sharpen(image_bytes: bytes, mode: str, intensity: float) -> bytes:
    img = _open_image(image_bytes)
    if mode == "blur":
        result = img.filter(ImageFilter.GaussianBlur(radius=max(0.1, intensity)))
    else:
        result = ImageEnhance.Sharpness(img).enhance(max(1.0, intensity))
    return _serialize(result, fmt=img.format or "PNG")


async def image_to_base64(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


async def base64_to_image(payload: str) -> bytes:
    if "," in payload:
        payload = payload.split(",", 1)[1]
    return base64.b64decode(payload)


async def placeholder_image(width: int, height: int, bg_hex: str, text: str) -> bytes:
    img = Image.new("RGB", (width, height), bg_hex)
    return _serialize(img, fmt="PNG")
