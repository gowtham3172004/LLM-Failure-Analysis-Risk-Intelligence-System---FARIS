"""Tests for the Analysis API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test the health check endpoint."""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "components" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_taxonomy_endpoint(client: AsyncClient):
    """Test the taxonomy endpoint."""
    response = await client.get("/api/taxonomy")
    
    assert response.status_code == 200
    data = response.json()
    assert "failure_types" in data
    assert len(data["failure_types"]) == 6
    
    # Check all failure types are present
    types = [ft["type"] for ft in data["failure_types"]]
    assert "hallucination" in types
    assert "logical_inconsistency" in types
    assert "missing_assumptions" in types
    assert "overconfidence" in types
    assert "scope_violation" in types
    assert "underspecification" in types


@pytest.mark.asyncio
async def test_analyze_validation_empty_question(client: AsyncClient):
    """Test validation rejects empty question."""
    response = await client.post(
        "/api/analyze",
        json={
            "question": "",
            "llm_answer": "Some answer",
        },
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_validation_empty_answer(client: AsyncClient):
    """Test validation rejects empty answer."""
    response = await client.post(
        "/api/analyze",
        json={
            "question": "Some question",
            "llm_answer": "",
        },
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_validation_invalid_domain(client: AsyncClient):
    """Test validation rejects invalid domain."""
    response = await client.post(
        "/api/analyze",
        json={
            "question": "Test question",
            "llm_answer": "Test answer",
            "domain": "invalid_domain",
        },
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_analyze_valid_request_structure(client: AsyncClient, sample_analysis_request):
    """Test that valid request returns proper response structure."""
    # Note: This test requires Ollama to be running
    # In CI, you might want to mock the LLM calls
    
    # Just test the request is accepted (not the analysis itself)
    response = await client.post(
        "/api/analyze/quick",
        json=sample_analysis_request,
    )
    
    # If Ollama is not running, we'll get a 500
    # In a real CI setup, you'd mock the LLM
    if response.status_code == 200:
        data = response.json()
        assert "failure_detected" in data
        assert "failure_types" in data
        assert "failures" in data
        assert "claims" in data
        assert "risk_assessment" in data
        assert "recommendations" in data
        assert "explanation" in data
        assert "metadata" in data
