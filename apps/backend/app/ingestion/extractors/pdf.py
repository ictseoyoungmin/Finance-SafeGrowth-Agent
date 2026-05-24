from io import BytesIO


def extract_pdf_text(raw_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return raw_bytes.decode("utf-8", errors="ignore")

    try:
        reader = PdfReader(BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        return raw_bytes.decode("utf-8", errors="ignore")
