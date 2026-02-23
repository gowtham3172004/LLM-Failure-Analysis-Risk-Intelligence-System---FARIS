"""
FARIS Ingestion Service — The Truth Engine

Smart ingestion pipeline that extracts and refines context from:
- URLs (web pages, articles, documentation)
- PDF files (research papers, reports, manuals)

The Context Refiner uses SentenceTransformers to rank text chunks
and select only the top-K most relevant chunks to the question,
eliminating noise from navigation, ads, and boilerplate.
"""

import io
import re
import asyncio
from typing import Optional

import httpx
import structlog
import trafilatura
from pypdf import PdfReader

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MAX_URL_FETCH_TIMEOUT = 30  # seconds
MAX_PDF_SIZE_MB = 20
CHUNK_SIZE = 512  # characters per chunk (roughly ~100 tokens)
CHUNK_OVERLAP = 64
TOP_K_CHUNKS = 5  # number of most-relevant chunks to keep
MIN_CHUNK_LENGTH = 40  # ignore tiny fragments


class IngestionError(Exception):
    """Raised when ingestion fails."""
    pass


# ---------------------------------------------------------------------------
# URL Ingestion
# ---------------------------------------------------------------------------
async def fetch_from_url(url: str) -> str:
    """
    Scrape and clean text from a URL using trafilatura.

    Removes ads, navigation, and boilerplate content.

    Args:
        url: The web page URL to scrape.

    Returns:
        Cleaned plain-text content.

    Raises:
        IngestionError: If the URL is unreachable or yields no content.
    """
    logger.info("ingestion.url.fetch", url=url)

    # Validate URL format
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    html: Optional[str] = None

    # --- Strategy 1: try trafilatura's own URL fetcher first (handles cookies, redirects, cf) ---
    try:
        downloaded = await asyncio.to_thread(
            trafilatura.fetch_url, url
        )
        if downloaded and len(downloaded) > 200:
            html = downloaded
            logger.info("ingestion.url.trafilatura_fetcher_ok", url=url)
    except Exception as exc:
        logger.warning("ingestion.url.trafilatura_fetcher_fail", url=url, err=str(exc))

    # --- Strategy 2: fallback to httpx with browser-like headers ---
    if not html:
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(MAX_URL_FETCH_TIMEOUT, connect=15.0),
                follow_redirects=True,
                verify=False,  # Some sites have cert issues
            ) as client:
                response = await client.get(url, headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                })
                response.raise_for_status()
                html = response.text
        except httpx.HTTPStatusError as exc:
            raise IngestionError(
                f"URL returned HTTP {exc.response.status_code}: {url}"
            )
        except httpx.ConnectError:
            raise IngestionError(f"Cannot connect to URL: {url}")
        except httpx.TimeoutException:
            raise IngestionError(f"URL request timed out after {MAX_URL_FETCH_TIMEOUT}s: {url}")
        except Exception as exc:
            raise IngestionError(f"Failed to fetch URL: {exc}")

    if not html:
        raise IngestionError(f"Could not fetch content from URL: {url}")

    # Extract clean text with trafilatura
    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        favor_precision=True,
    )

    if not text or len(text.strip()) < 50:
        raise IngestionError(
            "Could not extract meaningful text from URL. "
            "The page may be JavaScript-rendered or behind a paywall."
        )

    logger.info("ingestion.url.success", url=url, chars=len(text))
    return text.strip()


# ---------------------------------------------------------------------------
# PDF Ingestion
# ---------------------------------------------------------------------------
async def fetch_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Extract text from an uploaded PDF file.

    Args:
        file_bytes: Raw bytes of the uploaded file.
        filename:   Original filename (used for logging & validation).

    Returns:
        Concatenated plain-text from all PDF pages.

    Raises:
        IngestionError: If the file is not a valid PDF or is empty.
    """
    logger.info("ingestion.pdf.parse", filename=filename, size_kb=len(file_bytes) // 1024)

    if len(file_bytes) > MAX_PDF_SIZE_MB * 1024 * 1024:
        raise IngestionError(
            f"PDF exceeds maximum size of {MAX_PDF_SIZE_MB} MB."
        )

    if not filename.lower().endswith(".pdf"):
        raise IngestionError(
            "Only PDF files are supported. Please upload a .pdf file."
        )

    try:
        # Run blocking PDF parsing in a thread pool
        text = await asyncio.to_thread(_parse_pdf_bytes, file_bytes)
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(f"Failed to parse PDF: {exc}")

    if not text or len(text.strip()) < 50:
        raise IngestionError(
            "Could not extract meaningful text from the PDF. "
            "It may be image-based or encrypted."
        )

    logger.info("ingestion.pdf.success", filename=filename, chars=len(text))
    return text.strip()


def _parse_pdf_bytes(data: bytes) -> str:
    """Synchronous helper — extracts text from PDF bytes."""
    reader = PdfReader(io.BytesIO(data))

    if reader.is_encrypted:
        raise IngestionError("PDF is encrypted and cannot be read.")

    pages_text: list[str] = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text.strip())

    return "\n\n".join(pages_text)


# ---------------------------------------------------------------------------
# Context Refiner — Semantic Chunk Ranking
# ---------------------------------------------------------------------------
def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks for semantic ranking.

    Uses sentence-boundary-aware splitting where possible.
    """
    # Split on paragraph / double-newline boundaries first
    paragraphs = re.split(r"\n{2,}", text)
    chunks: list[str] = []

    buffer = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(buffer) + len(para) + 1 <= chunk_size:
            buffer = f"{buffer} {para}".strip() if buffer else para
        else:
            if buffer and len(buffer) >= MIN_CHUNK_LENGTH:
                chunks.append(buffer)
            # If the paragraph itself is too long, split it
            if len(para) > chunk_size:
                words = para.split()
                sub = ""
                for w in words:
                    if len(sub) + len(w) + 1 <= chunk_size:
                        sub = f"{sub} {w}".strip() if sub else w
                    else:
                        if sub and len(sub) >= MIN_CHUNK_LENGTH:
                            chunks.append(sub)
                        sub = w
                buffer = sub
            else:
                buffer = para

    if buffer and len(buffer) >= MIN_CHUNK_LENGTH:
        chunks.append(buffer)

    return chunks


async def refine_context(
    question: str,
    raw_text: str,
    top_k: int = TOP_K_CHUNKS,
) -> str:
    """
    Rank text chunks by semantic similarity to the question and return
    only the top-K most relevant chunks.

    This is the "Context Refiner" — it filters noise from scraped/PDF text
    and keeps only the content that actually relates to the user's question.

    Args:
        question: The user's original question.
        raw_text: The full raw text from URL or PDF.
        top_k:    Number of top chunks to keep.

    Returns:
        A refined context string composed of the most relevant chunks.
    """
    chunks = _chunk_text(raw_text)

    if not chunks:
        logger.warning("ingestion.refine.no_chunks")
        return raw_text[:2000]  # fallback: first 2k chars

    if len(chunks) <= top_k:
        # Already small enough — no need to rank
        return "\n\n".join(chunks)

    logger.info("ingestion.refine.ranking", total_chunks=len(chunks), top_k=top_k)

    # Lazy import to avoid heavyweight torch/sentence_transformers at module load
    from app.core.embeddings.encoder import get_embedding_encoder

    # Use SentenceTransformers to rank
    encoder = get_embedding_encoder()
    ranked = await asyncio.to_thread(
        encoder.find_most_similar,
        query=question,
        candidates=chunks,
        top_k=top_k,
        threshold=0.0,
    )

    # Sort by original position (preserves reading order)
    ranked.sort(key=lambda r: r["index"])

    refined = "\n\n".join(r["text"] for r in ranked)
    logger.info(
        "ingestion.refine.done",
        original_chars=len(raw_text),
        refined_chars=len(refined),
        chunks_selected=len(ranked),
    )
    return refined
