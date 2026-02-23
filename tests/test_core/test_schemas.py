"""Unit tests for core components."""

import pytest
from app.api.schemas.requests import AnalysisRequest, Domain
from app.api.schemas.responses import FailureType, Severity, RiskLevel


class TestAnalysisRequest:
    """Tests for AnalysisRequest schema."""
    
    def test_valid_request(self):
        """Test creating a valid request."""
        request = AnalysisRequest(
            question="What is the capital of France?",
            llm_answer="The capital of France is Paris.",
            domain=Domain.GENERAL,
        )
        
        assert request.question == "What is the capital of France?"
        assert request.llm_answer == "The capital of France is Paris."
        assert request.domain == Domain.GENERAL
    
    def test_default_domain(self):
        """Test default domain is general."""
        request = AnalysisRequest(
            question="Test question",
            llm_answer="Test answer",
        )
        
        assert request.domain == Domain.GENERAL
    
    def test_optional_context(self):
        """Test optional context field."""
        request = AnalysisRequest(
            question="Test question",
            llm_answer="Test answer",
            context="Additional context",
        )
        
        assert request.context == "Additional context"
    
    def test_optional_model_metadata(self):
        """Test optional model_metadata field."""
        request = AnalysisRequest(
            question="Test question",
            llm_answer="Test answer",
            model_metadata={
                "model_name": "test-model",
                "temperature": 0.7,
                "source": "test",
            },
        )
        
        assert request.model_metadata is not None
        assert request.model_metadata.model_name == "test-model"


class TestEnums:
    """Tests for enum values."""
    
    def test_domain_values(self):
        """Test all domain values exist."""
        domains = [d.value for d in Domain]
        assert "general" in domains
        assert "finance" in domains
        assert "medical" in domains
        assert "legal" in domains
        assert "code" in domains
    
    def test_failure_type_values(self):
        """Test all failure types exist."""
        types = [t.value for t in FailureType]
        assert "hallucination" in types
        assert "logical_inconsistency" in types
        assert "missing_assumptions" in types
        assert "overconfidence" in types
        assert "scope_violation" in types
        assert "underspecification" in types
    
    def test_severity_values(self):
        """Test all severity levels exist."""
        severities = [s.value for s in Severity]
        assert "low" in severities
        assert "medium" in severities
        assert "high" in severities
        assert "critical" in severities
    
    def test_risk_level_values(self):
        """Test all risk levels exist."""
        levels = [r.value for r in RiskLevel]
        assert "low" in levels
        assert "medium" in levels
        assert "high" in levels
        assert "critical" in levels


class TestResponseStructure:
    """Tests for response schema structure."""
    
    def test_failure_detail_structure(self):
        """Test FailureDetail has required fields."""
        from app.api.schemas.responses import FailureDetail
        
        failure = FailureDetail(
            failure_type=FailureType.HALLUCINATION,
            detected=True,
            confidence=0.85,
            severity=Severity.HIGH,
            evidence=["evidence1"],
            related_claim_ids=["claim1"],
            explanation="Test explanation",
        )
        
        assert failure.failure_type == FailureType.HALLUCINATION
        assert failure.detected is True
        assert failure.severity == Severity.HIGH
        assert failure.confidence == 0.85
        assert failure.explanation == "Test explanation"
        assert failure.related_claim_ids == ["claim1"]
        assert failure.evidence == ["evidence1"]
    
    def test_risk_assessment_structure(self):
        """Test RiskAssessment has required fields."""
        from app.api.schemas.responses import RiskAssessment
        
        risk = RiskAssessment(
            risk_score=0.75,
            risk_level=RiskLevel.HIGH,
            domain="general",
            domain_multiplier=1.0,
            contributing_factors=[{"factor": "factor1"}, {"factor": "factor2"}],
            explanation="Test risk explanation",
        )
        
        assert risk.risk_score == 0.75
        assert risk.risk_level == RiskLevel.HIGH
        assert risk.domain == "general"
        assert risk.domain_multiplier == 1.0
        assert len(risk.contributing_factors) == 2
        assert risk.explanation == "Test risk explanation"
