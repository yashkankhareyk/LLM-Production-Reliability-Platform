"""
Universal file parser — converts CSV, PDF, TXT into text chunks
ready for vector embedding.
"""
import csv
import io
import logging
from typing import List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """
    Split long text into overlapping chunks.
    
    Why: Vector search works better on smaller, focused chunks
    than on one giant document.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence or newline
        if end < len(text):
            # Look for natural break point
            for sep in ["\n\n", "\n", ". ", ", ", " "]:
                break_point = text.rfind(sep, start, end)
                if break_point > start:
                    end = break_point + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


def parse_txt(content: str, source_name: str) -> Tuple[List[str], List[str]]:
    """Parse plain text file into chunks."""
    chunks = chunk_text(content)
    sources = [f"{source_name}:chunk-{i+1}" for i in range(len(chunks))]
    return chunks, sources


def parse_csv(content: str, source_name: str) -> Tuple[List[str], List[str]]:
    """
    Parse CSV — each row becomes a readable text entry.
    Also creates summary chunks for groups of rows.
    """
    texts = []
    sources = []

    try:
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames

        if not headers:
            return [], []

        rows = list(reader)
        logger.info(
            f"CSV parsed: {len(rows)} rows, columns: {headers}"
        )

        # Each row → one text entry
        for i, row in enumerate(rows):
            parts = [
                f"{key}: {value}"
                for key, value in row.items()
                if value and str(value).strip()
            ]
            if parts:
                text = ". ".join(parts) + "."
                texts.append(text)
                sources.append(f"{source_name}:row-{i+1}")

        # Summary chunks (groups of 10 rows)
        for i in range(0, len(rows), 10):
            batch = rows[i : i + 10]
            summary = f"Records from {source_name} (rows {i+1} to {i+len(batch)}):\n"
            for row in batch:
                parts = [
                    f"{key}: {value}"
                    for key, value in row.items()
                    if value and str(value).strip()
                ]
                summary += "- " + ", ".join(parts) + "\n"
            texts.append(summary)
            sources.append(f"{source_name}:summary-{i+1}-{i+len(batch)}")

    except Exception as e:
        logger.error(f"CSV parse error: {e}")

    return texts, sources


def parse_pdf(content_bytes: bytes, source_name: str) -> Tuple[List[str], List[str]]:
    """Parse PDF file into text chunks per page."""
    texts = []
    sources = []

    try:
        import fitz  # pymupdf

        doc = fitz.open(stream=content_bytes, filetype="pdf")
        logger.info(f"PDF parsed: {len(doc)} pages")

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text().strip()

            if not page_text:
                continue

            # Chunk each page (pages can be long)
            page_chunks = chunk_text(page_text)

            for j, chunk in enumerate(page_chunks):
                texts.append(chunk)
                sources.append(
                    f"{source_name}:page-{page_num+1}:chunk-{j+1}"
                )

        doc.close()

    except ImportError:
        logger.error("pymupdf not installed: pip install pymupdf")
    except Exception as e:
        logger.error(f"PDF parse error: {e}")

    return texts, sources


def parse_file(
    filename: str,
    content: bytes,
) -> Tuple[List[str], List[str]]:
    """
    Auto-detect file type and parse accordingly.
    
    Returns:
        texts: list of text chunks for embedding
        sources: list of source labels for each chunk
    """
    ext = Path(filename).suffix.lower()

    if ext == ".csv":
        text_content = content.decode("utf-8")
        return parse_csv(text_content, filename)

    elif ext == ".pdf":
        return parse_pdf(content, filename)

    elif ext in [".txt", ".md"]:
        text_content = content.decode("utf-8")
        return parse_txt(text_content, filename)

    else:
        logger.warning(f"Unsupported file type: {ext}")
        return [], []