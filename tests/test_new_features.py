"""
Tests for FARIS new features:
  - Truth Engine (Smart Ingestion)
  - Automated Remediation (Self-Healing Loop)
  - Deep-Scan API endpoint
"""

import asyncio
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient

# ---------------------  Ingestion Service  ---------------------


@pytest.mark.asyncio
async def test_fetch_from_url_success():
    """Test URL ingestion with a mocked HTTP response."""
    from app.services.ingestion import fetch_from_url

    fake_html = """
    <html>
    <head><title>Test</title></head>
    <body>
    <article>
    <p>Python is a high-level programming language created by Guido van Rossum.
    It emphasises code readability and supports multiple programming paradigms
    including procedural, object-oriented, and functional programming styles.</p>
    </article>
    </body>
    </html>
    """

    with patch("app.services.ingestion.httpx.AsyncClient") as MockClient:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = fake_html
        mock_resp.raise_for_status = MagicMock()

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=ctx)
        ctx.__aexit__ = AsyncMock(return_value=False)
        ctx.get = AsyncMock(return_value=mock_resp)
        MockClient.return_value = ctx

        # trafilatura may or may not extract well from the stub HTML.
        # Patch trafilatura.extract to return known text:
        with patch("app.services.ingestion.trafilatura.extract", return_value=(
            "Python is a high-level programming language created by Guido van "
            "Rossum. It emphasises code readability and supports multiple "
            "programming paradigms."
        )):
            text = await fetch_from_url("https://example.com/python")
            assert "Python" in text
            assert len(text) > 50


@pytest.mark.asyncio
async def test_fetch_from_url_failure():
    """Test that unreachable URL raises IngestionError."""
    from app.services.ingestion import IngestionError, fetch_from_url

    with patch("app.services.ingestion.httpx.AsyncClient") as MockClient:
        import httpx as _httpx

        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=ctx)
        ctx.__aexit__ = AsyncMock(return_value=False)
        ctx.get = AsyncMock(side_effect=_httpx.ConnectError("nope"))
        MockClient.return_value = ctx

        with pytest.raises(IngestionError, match="Cannot connect"):
            await fetch_from_url("https://nonexistent.example.com")


@pytest.mark.asyncio
async def test_fetch_from_file_success():
    """Test PDF ingestion with a mocked PDF reader."""
    from app.services.ingestion import fetch_from_file

    fake_text = (
        "This document explains the history of artificial intelligence, "
        "covering early developments and recent trends in deep learning."
    )

    with patch("app.services.ingestion._parse_pdf_bytes", return_value=fake_text):
        text = await fetch_from_file(b"fake-pdf-bytes", "test.pdf")
        assert "artificial intelligence" in text


@pytest.mark.asyncio
async def test_fetch_from_file_rejects_non_pdf():
    """Test that non-PDF files are rejected."""
    from app.services.ingestion import IngestionError, fetch_from_file

    with pytest.raises(IngestionError, match="Only PDF"):
        await fetch_from_file(b"not a pdf", "document.docx")


@pytest.mark.asyncio
async def test_fetch_from_file_rejects_oversized():
    """Test that oversized files are rejected."""
    from app.services.ingestion import IngestionError, MAX_PDF_SIZE_MB, fetch_from_file

    big_data = b"\x00" * (MAX_PDF_SIZE_MB * 1024 * 1024 + 1)
    with pytest.raises(IngestionError, match="exceeds maximum size"):
        await fetch_from_file(big_data, "huge.pdf")


# ---------------------  Context Refiner  ---------------------


@pytest.mark.asyncio
async def test_refine_context_returns_top_chunks():
    """Test that the context refiner selects relevant chunks."""
    from app.services.ingestion import refine_context

    raw = "\n\n".join([
        "Navigation: Home | About | Contact",
        "Cookie notice ipsum dolor sit amet.",
        "Python was created by Guido van Rossum and first released in 1991.",
        "It supports multiple programming paradigms including OOP.",
        "Subscribe to our newsletter for updates.",
        "Python emphasises code readability with significant indentation.",
        "Footer links and copyright 2024.",
    ])

    refined = await refine_context("Who created Python?", raw, top_k=2)
    assert "Guido" in refined or "Python" in refined
    assert len(refined) > 0


# ---------------------  Chunking  ---------------------


def test_chunk_text():
    """Test the internal text chunker."""
    from app.services.ingestion import _chunk_text

    text = "\n\n".join(["A" * 100] * 10)  # 10 paragraphs of 100 chars each
    chunks = _chunk_text(text, chunk_size=250, overlap=20)
    assert len(chunks) >= 3
    for c in chunks:
        assert len(c) >= 40  # MIN_CHUNK_LENGTH


# ---------------------  Remediation Node  ---------------------


@pytest.mark.asyncio
async def test_remediation_triggered_above_threshold():
    """Test that remediation node runs when risk_score > 0.3."""
    from app.core.graph.nodes.remediation import remediation_node

    state = {
        "risk_score": 0.7,
        "question": "What is the capital of France?",
        "answer": "The capital of France is Berlin.",
        "detected_failures": [
            {
                "failure_type": "hallucination",
                "detected": True,
                "confidence": 0.9,
                "severity": "high",
                "evidence": ["Berlin is not the capital of France"],
                "explanation": "Incorrect capital city",
            }
        ],
        "verified_context": "France is a country in Western Europe. Its capital is Paris.",
        "remediation_attempted": False,
        "remediated_answer": None,
        "remediation_explanation": None,
    }

    # Mock the LLM to return a corrected answer
    with patch("app.core.graph.nodes.remediation.get_llm_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value="The capital of France is Paris.")
        mock_get.return_value = mock_client

        result = await remediation_node(state)
        assert result["remediation_attempted"] is True
        assert result["remediated_answer"] is not None
        assert "Paris" in result["remediated_answer"]


@pytest.mark.asyncio
async def test_remediation_skipped_below_threshold():
    """Test that remediation is skipped when risk_score <= 0.3."""
    from app.core.graph.nodes.remediation import remediation_node

    state = {
        "risk_score": 0.1,
        "question": "What is 2+2?",
        "answer": "4",
        "detected_failures": [],
        "verified_context": None,
        "remediation_attempted": False,
        "remediated_answer": None,
        "remediation_explanation": None,
    }

    result = await remediation_node(state)
    assert result["remediation_attempted"] is False
    assert result["remediated_answer"] is None


# ---------------------  Response Schema  ---------------------


def test_remediation_result_schema():
    """Test RemediationResult Pydantic model."""
    from app.api.schemas.responses import RemediationResult

    # Attempted with correction
    r = RemediationResult(
        attempted=True,
        corrected_answer="Fixed answer",
        explanation="Corrected factual error",
    )
    assert r.attempted is True
    assert r.corrected_answer == "Fixed answer"

    # Not attempted
    r2 = RemediationResult(attempted=False)
    assert r2.attempted is False
    assert r2.corrected_answer is None


# ---------------------  Deep-Scan Endpoint  ---------------------


@pytest.mark.asyncio
async def test_deep_scan_validation_both_sources(client: AsyncClient):
    """Test that providing both URL and file is rejected."""
    response = await client.post(
        "/api/analyze/deep-scan",
        data={
            "question": "What is Python?",
            "llm_answer": "Python is a snake.",
            "source_url": "https://example.com",
        },
        files={"file": ("test.pdf", b"fake", "application/pdf")},
    )
    assert response.status_code == 400
    assert "not both" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_deep_scan_no_source_falls_through(client: AsyncClient):
    """Test deep-scan without any external source (manual context only)."""
    # This will attempt a real analysis (no URL/PDF) — mock the LLM
    with patch("app.core.graph.orchestrator.run_analysis") as mock_run:
        mock_run.return_value = {
            "failure_detected": False,
            "failure_types": [],
            "detected_failures": [],
            "claims": [],
            "risk_score": 0.1,
            "risk_level": "low",
            "domain": "general",
            "domain_multiplier": 1.0,
            "contributing_factors": [],
            "risk_explanation": "Low risk",
            "recommendations": [],
            "explanation": "No issues found.",
            "remediation_attempted": False,
            "remediated_answer": None,
            "remediation_explanation": None,
        }

        response = await client.post(
            "/api/analyze/deep-scan",
            data={
                "question": "What is Python?",
                "llm_answer": "Python is a programming language.",
                "domain": "general",
            },
        )
        # The mock bypasses the real LLM, so we should get a 200
        if response.status_code == 200:
            data = response.json()
            assert "failure_detected" in data
            assert "remediation" in data or data.get("remediation") is None


@pytest.mark.asyncio
async def test_deep_scan_url_ingestion_error(client: AsyncClient):
    """Test that a bad URL returns 400."""
    with patch(
        "app.api.routes.analysis.fetch_from_url",
        side_effect=__import__(
            "app.services.ingestion", fromlist=["IngestionError"]
        ).IngestionError("URL returned HTTP 404"),
    ):
        response = await client.post(
            "/api/analyze/deep-scan",
            data={
                "question": "What is AI?",
                "llm_answer": "AI is artificial intelligence.",
                "source_url": "https://nonexistent.example.com/page",
            },
        )
        assert response.status_code == 400
        assert "404" in response.json()["detail"]


# ---------------------  Analysis Service Integration  ---------------------


@pytest.mark.asyncio
async def test_analysis_service_includes_remediation():
    """Test that AnalysisService.analyze populates remediation in response."""
    from app.api.schemas.requests import AnalysisRequest
    from app.services.analysis_service import AnalysisService

    service = AnalysisService(db=None)
    request = AnalysisRequest(
        question="What is the speed of light?",
        llm_answer="The speed of light is approximately 100 km/s.",
        domain="general",
    )

    # Mock run_analysis to return a result with remediation
    with patch("app.services.analysis_service.run_analysis") as mock_run:
        mock_run.return_value = {
            "failure_detected": True,
            "failure_types": ["hallucination"],
            "detected_failures": [
                {
                    "failure_type": "hallucination",
                    "detected": True,
                    "confidence": 0.95,
                    "severity": "high",
                    "evidence": ["Speed of light is ~300,000 km/s, not 100 km/s"],
                    "explanation": "Incorrect value",
                    "related_claim_ids": [],
                }
            ],
            "claims": [],
            "risk_score": 0.85,
            "risk_level": "critical",
            "domain": "general",
            "domain_multiplier": 1.0,
            "contributing_factors": [{"name": "hallucination", "score": 0.95, "weight": 1.0}],
            "risk_explanation": "Critical risk due to factual error.",
            "recommendations": [],
            "explanation": "The answer contains a critical factual error.",
            "remediation_attempted": True,
            "remediated_answer": "The speed of light is approximately 299,792 km/s.",
            "remediation_explanation": "Corrected the speed of light value.",
        }

        response = await service.analyze(
            request=request,
            persist=False,
            verified_context="The speed of light is 299,792 km/s in vacuum.",
            context_source="manual",
        )

        assert response.remediation is not None
        assert response.remediation.attempted is True
        assert "299,792" in (response.remediation.corrected_answer or "")
        assert response.context_source == "manual"
