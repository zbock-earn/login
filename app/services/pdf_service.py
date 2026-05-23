from io import BytesIO

from pypdf import PdfWriter


async def merge_pdfs(files: list[bytes]) -> bytes:
    writer = PdfWriter()
    for file_data in files:
        writer.append(BytesIO(file_data))

    output = BytesIO()
    writer.write(output)
    output.seek(0)
    return output.read()
