from pathlib import Path
from typing import AsyncIterator

import aiofiles


async def iter_audio_file(path: Path, chunk_size: int = 64 * 1024) -> AsyncIterator[bytes]:
    async with aiofiles.open(path, "rb") as audio_file:
        while chunk := await audio_file.read(chunk_size):
            yield chunk
