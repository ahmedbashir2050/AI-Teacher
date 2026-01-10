from pypdf import PdfReader
from typing import IO

def load_pdf(file: IO) -> str:
    """
    Loads a PDF file from a file-like object and extracts its text content.
    """
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text
