"""Tests for the Cases API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_cases_empty(client: AsyncClient):
    """Test listing cases when database is empty."""
    response = await client.get("/api/cases")
    
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert data["total"] == 0
    assert data["cases"] == []


@pytest.mark.asyncio
async def test_list_cases_pagination(client: AsyncClient):
    """Test pagination parameters."""
    response = await client.get("/api/cases?page=1&page_size=5")
    
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


@pytest.mark.asyncio
async def test_list_cases_invalid_page(client: AsyncClient):
    """Test invalid page number."""
    response = await client.get("/api/cases?page=0")
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_list_cases_invalid_page_size(client: AsyncClient):
    """Test invalid page size."""
    response = await client.get("/api/cases?page_size=200")
    
    assert response.status_code == 422  # Validation error (max 100)


@pytest.mark.asyncio
async def test_get_case_not_found(client: AsyncClient):
    """Test getting a non-existent case."""
    response = await client.get("/api/cases/non-existent-uuid")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_case_not_found(client: AsyncClient):
    """Test deleting a non-existent case."""
    response = await client.delete("/api/cases/non-existent-uuid")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_statistics(client: AsyncClient):
    """Test getting statistics."""
    response = await client.get("/api/cases/statistics/summary")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_cases" in data
    assert "cases_with_failures" in data
    assert "failure_rate" in data
    assert "by_domain" in data
    assert "by_failure_type" in data
    assert "by_risk_level" in data


@pytest.mark.asyncio
async def test_filter_cases_by_domain(client: AsyncClient):
    """Test filtering cases by domain."""
    response = await client.get("/api/cases?domain=general")
    
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data


@pytest.mark.asyncio
async def test_filter_cases_by_risk_level(client: AsyncClient):
    """Test filtering cases by risk level."""
    response = await client.get("/api/cases?risk_level=high")
    
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
