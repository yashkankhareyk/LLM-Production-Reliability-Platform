"""
Universal file parser — converts CSV, PDF, TXT into text chunks.
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
    """Split long text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
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


def parse_txt(
    content: str, source_name: str
) -> Tuple[List[str], List[str]]:
    """Parse plain text file into chunks."""
    chunks = chunk_text(content)
    sources = [
        f"{source_name}:chunk-{i+1}"
        for i in range(len(chunks))
    ]
    return chunks, sources


def parse_csv(
    content: str, source_name: str
) -> Tuple[List[str], List[str]]:
    """
    Parse CSV with multiple strategies for better search.
    
    Strategy 1: Individual rows (for specific lookups)
      → "Employee Record: Name is Paula Small. 
         Works in Engineering department. 
         Earns salary of 95000. Performance rating: Exceeds."
    
    Strategy 2: Grouped by key columns (for aggregate queries)
      → "Engineering Department employees: Paula Small (95000), 
         John Davis (88000), ..."
    
    Strategy 3: Summary chunks (for overview queries)
      → "Dataset contains 500 employees across 8 departments..."
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
            f"CSV parsed: {len(rows)} rows, "
            f"columns: {headers}"
        )

        # ── Strategy 1: Rich individual rows ──────────
        # Make each row text MORE UNIQUE by adding
        # natural language instead of key:value pairs
        for i, row in enumerate(rows):
            parts = []
            for key, value in row.items():
                if value and str(value).strip():
                    clean_key = str(key).strip()
                    clean_val = str(value).strip()
                    parts.append(
                        f"{clean_key} is {clean_val}"
                    )

            if parts:
                # Add row identifier for uniqueness
                text = (
                    f"Record {i+1} from {source_name}: "
                    + ". ".join(parts)
                    + "."
                )
                texts.append(text)
                sources.append(
                    f"{source_name}:row-{i+1}"
                )

        # ── Strategy 2: Group by important columns ────
        # Find columns that might be good for grouping
        # (Department, Category, Type, Status, etc.)
        group_columns = []
        for header in headers:
            header_lower = header.lower()
            if any(
                keyword in header_lower
                for keyword in [
                    "department", "dept", "category",
                    "type", "status", "group", "team",
                    "division", "location", "city",
                    "state", "country", "region",
                ]
            ):
                group_columns.append(header)

        # Find name column
        name_column = None
        for header in headers:
            header_lower = header.lower()
            if any(
                keyword in header_lower
                for keyword in [
                    "name", "employee", "person",
                    "customer", "client", "user",
                ]
            ):
                name_column = header
                break

        # Create grouped chunks
        for group_col in group_columns:
            groups = {}
            for row in rows:
                group_val = str(
                    row.get(group_col, "")
                ).strip()
                if group_val:
                    if group_val not in groups:
                        groups[group_val] = []
                    groups[group_val].append(row)

            for group_val, group_rows in groups.items():
                if name_column:
                    names = [
                        str(r.get(name_column, "")).strip()
                        for r in group_rows
                        if r.get(name_column)
                    ]
                    text = (
                        f"{group_col}: {group_val}. "
                        f"Contains {len(group_rows)} records. "
                        f"Names: {', '.join(names[:20])}."
                    )
                else:
                    text = (
                        f"{group_col}: {group_val}. "
                        f"Contains {len(group_rows)} records."
                    )

                # Add sample data from first few rows
                for r in group_rows[:5]:
                    sample_parts = [
                        f"{k}: {v}"
                        for k, v in r.items()
                        if v and str(v).strip()
                    ]
                    text += (
                        " Sample: " + ", ".join(sample_parts) + "."
                    )

                texts.append(text)
                sources.append(
                    f"{source_name}:group-{group_col}-{group_val}"
                )

        # ── Strategy 3: Overall summary ───────────────
        summary = (
            f"This dataset ({source_name}) contains "
            f"{len(rows)} records with columns: "
            f"{', '.join(headers)}."
        )

        # Add unique value counts for key columns
        for header in headers[:5]:
            unique_vals = set(
                str(row.get(header, "")).strip()
                for row in rows
                if row.get(header)
            )
            if len(unique_vals) <= 20:
                summary += (
                    f" Unique {header} values: "
                    f"{', '.join(sorted(unique_vals)[:20])}."
                )
            else:
                summary += (
                    f" {header} has "
                    f"{len(unique_vals)} unique values."
                )

        texts.append(summary)
        sources.append(f"{source_name}:summary")

        logger.info(
            f"CSV chunking: {len(rows)} rows → "
            f"{len(texts)} chunks "
            f"(rows + {len(group_columns)} group columns + summary)"
        )

    except Exception as e:
        logger.error(f"CSV parse error: {e}")

    return texts, sources


def parse_pdf(
    content_bytes: bytes, source_name: str
) -> Tuple[List[str], List[str]]:
    """Parse PDF file into text chunks per page."""
    texts = []
    sources = []

    try:
        import fitz

        doc = fitz.open(stream=content_bytes, filetype="pdf")
        logger.info(f"PDF parsed: {len(doc)} pages")

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text().strip()

            if not page_text:
                continue

            page_chunks = chunk_text(page_text)

            for j, chunk in enumerate(page_chunks):
                texts.append(chunk)
                sources.append(
                    f"{source_name}:page-{page_num+1}:chunk-{j+1}"
                )

        doc.close()

    except ImportError:
        logger.error("pymupdf not installed")
    except Exception as e:
        logger.error(f"PDF parse error: {e}")

    return texts, sources


def parse_file(
    filename: str,
    content: bytes,
) -> Tuple[List[str], List[str]]:
    """Auto-detect file type and parse."""
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