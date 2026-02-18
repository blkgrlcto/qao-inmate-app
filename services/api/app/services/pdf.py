"""PDF text extraction."""
import io
from typing import Optional

import pymupdf


def extract_text_from_pdf(data: bytes) -> Optional[str]:
    """Extract text from PDF bytes. Returns None if not a valid PDF."""
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
        chunks = []
        for page in doc:
            chunks.append(page.get_text())
        doc.close()
        text = "\n".join(chunks).strip()
        return text if text else None
    except (pymupdf.FitzException, Exception):
        return None
