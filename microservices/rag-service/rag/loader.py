from typing import IO

from pypdf import PdfReader


def load_pdf(file: IO) -> list[dict]:
    """
    Loads a PDF file from a file-like object and extracts its text content page by page.
    Returns a list of dicts with 'text' and 'page' keys.
    """
    reader = PdfReader(file)
    pages_content = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            pages_content.append({"text": page_text, "page": i + 1})
    return pages_content
