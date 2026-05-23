from io import BytesIO

from PIL import Image


async def compress_image(image_bytes: bytes, quality: int = 70) -> bytes:
    img = Image.open(BytesIO(image_bytes))
    output = BytesIO()

    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    save_format = "JPEG" if img.format not in ("PNG", "WEBP") else img.format
    save_kwargs = {"optimize": True}
    if save_format == "JPEG":
        save_kwargs["quality"] = quality

    img.save(output, format=save_format, **save_kwargs)
    output.seek(0)
    return output.read()
