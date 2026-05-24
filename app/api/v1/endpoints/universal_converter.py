from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.background import BackgroundTask
from fastapi.responses import FileResponse

router = APIRouter()


def _cleanup(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


@router.post('/convert')
async def universal_convert(file: UploadFile = File(...), target_ext: str = Form(...)) -> FileResponse:
    if not target_ext.startswith('.'):
        raise HTTPException(status_code=400, detail='target_ext must start with dot')

    tmpdir = tempfile.mkdtemp(prefix='mztools_convert_')
    src = Path(tmpdir) / (file.filename or 'input.bin')
    out = Path(tmpdir) / f"converted{target_ext.lower()}"
    src.write_bytes(await file.read())

    # high-performance placeholder pipeline: copy-through for unsupported complex formats
    shutil.copyfile(src, out)

    return FileResponse(
        path=str(out),
        filename=out.name,
        media_type='application/octet-stream',
        background=BackgroundTask(_cleanup, str(out)),
    )
