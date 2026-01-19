from langchain_text_splitters import RecursiveCharacterTextSplitter

# Production-grade fixed chunk sizes for academic material
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text(text: str) -> list[str]:
    """
    Splits a long text into smaller chunks of a specified size.
    Uses fixed production-grade parameters.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    return text_splitter.split_text(text)
