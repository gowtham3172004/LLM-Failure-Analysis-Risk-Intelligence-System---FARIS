import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import RiskScoreBadge from "@/components/RiskScoreBadge";
import FailureCard from "@/components/FailureCard";
import ClaimAnalysisTable from "@/components/ClaimAnalysisTable";
import RecommendationCard from "@/components/RecommendationCard";
import { ArrowLeft, FileText, AlertTriangle, Lightbulb, CheckCircle, Loader2 } from "lucide-react";
import { getCase, type AnalysisResponse, type FailureType as ApiFailureType, ApiError } from "@/lib/api";
import type { FailureType as CardFailureType } from "@/components/FailureCard";

// Map API failure types to card failure types
const failureTypeMap: Record<ApiFailureType, CardFailureType> = {
  hallucination: "hallucination",
  logical_inconsistency: "logic",
  missing_assumptions: "assumptions",
  overconfidence: "overconfidence",
  scope_violation: "scope",
  underspecification: "underspecification",
};

// Map API failure types to display names
const failureNameMap: Record<ApiFailureType, string> = {
  hallucination: "Hallucination",
  logical_inconsistency: "Logical Inconsistency",
  missing_assumptions: "Missing Assumptions",
  overconfidence: "Overconfidence",
  scope_violation: "Scope Violation",
  underspecification: "Underspecification",
};

export default function CaseDetail() {
  const { caseId } = useParams<{ caseId: string }>();
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!caseId) return;

    const fetchCase = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCase(caseId);
        setAnalysisResult(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load case details");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCase();
  }, [caseId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !analysisResult) {
    return (
      <div className="min-h-screen py-12">
        <div className="container">
          <div className="mx-auto max-w-5xl text-center">
            <p className="text-red-500 mb-4">{error || "Case not found"}</p>
            <Link
              to="/history"
              className="text-primary hover:underline"
            >
              Back to History
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const { risk_assessment, failures, claims, recommendations, explanation } = analysisResult;

  // Filter only detected failures
  const detectedFailures = failures.filter((f) => f.detected);

  // Map risk level to component format
  const riskLevelMap: Record<string, "low" | "medium" | "high"> = {
    low: "low",
    medium: "medium",
    high: "high",
    critical: "high",
  };

  // Convert claims to table format
  const claimsForTable = claims.map((claim) => ({
    id: claim.claim_id,
    text: claim.claim_text,
    supported: claim.is_supported ? ("yes" as const) : claim.issues.length > 0 ? ("no" as const) : ("partial" as const),
    notes: claim.issues.length > 0 ? claim.issues.join(", ") : "No issues detected",
  }));

  // Convert recommendations to card format
  const recommendationsForCards = recommendations.map((rec) => ({
    title: rec.title,
    description: rec.description,
    priority: rec.priority <= 2 ? ("high" as const) : rec.priority <= 3 ? ("medium" as const) : ("low" as const),
    category: failureNameMap[rec.failure_type] || "General",
  }));

  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-5xl">
          {/* Back Link */}
          <Link
            to="/history"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to History
          </Link>

          {/* Summary Banner */}
          <div className="rounded-xl border border-border bg-card p-8 mb-8">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <RiskScoreBadge
                score={risk_assessment.risk_score}
                level={riskLevelMap[risk_assessment.risk_level] || "medium"}
                size="lg"
              />
              <div className="flex-1 text-center md:text-left">
                <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                  {detectedFailures.length > 0 ? (
                    <>
                      <AlertTriangle className="h-5 w-5 text-risk-high" />
                      <span className="text-lg font-semibold text-foreground">
                        {detectedFailures.length} Failure Type{detectedFailures.length !== 1 ? "s" : ""} Detected
                      </span>
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-5 w-5 text-risk-low" />
                      <span className="text-lg font-semibold text-foreground">
                        No Failures Detected
                      </span>
                    </>
                  )}
                </div>
                <p className="text-muted-foreground text-sm max-w-lg">
                  {detectedFailures.length > 0
                    ? "This output exhibits reliability issues. Review the detailed breakdown below."
                    : "This output appears reliable based on our analysis."}
                </p>
                <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground font-mono">
                  <span>Domain: {risk_assessment.domain} ({risk_assessment.domain_multiplier}x)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Original Question & Answer */}
          <section className="mb-10">
            <div className="rounded-xl border border-border bg-card">
              <div className="p-6 border-b border-border">
                <h3 className="font-semibold text-foreground mb-2">Question</h3>
                <p className="text-muted-foreground font-mono text-sm whitespace-pre-wrap">
                  {analysisResult.question}
                </p>
              </div>
              <div className="p-6">
                <h3 className="font-semibold text-foreground mb-2">LLM Answer</h3>
                <p className="text-muted-foreground font-mono text-sm whitespace-pre-wrap">
                  {analysisResult.llm_answer}
                </p>
              </div>
            </div>
          </section>

          {/* Failure Breakdown */}
          {detectedFailures.length > 0 && (
            <section className="mb-10">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-xl font-semibold text-foreground">Failure Breakdown</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {detectedFailures.map((failure, idx) => (
                  <FailureCard
                    key={idx}
                    type={failureTypeMap[failure.failure_type]}
                    name={failureNameMap[failure.failure_type]}
                    confidence={failure.confidence}
                    severity={failure.severity as "low" | "medium" | "high"}
                    evidence={failure.evidence.join(" ") || failure.explanation}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Explanation */}
          <section className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-xl font-semibold text-foreground">Explanation</h2>
            </div>
            <div className="rounded-xl border border-border bg-card p-6">
              <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                {explanation || risk_assessment.explanation || "Analysis complete."}
              </p>
            </div>
          </section>

          {/* Claim Analysis */}
          {claimsForTable.length > 0 && (
            <section className="mb-10">
              <div className="flex items-center gap-2 mb-4">
                <FileText className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-xl font-semibold text-foreground">Claim-Level Analysis</h2>
              </div>
              <ClaimAnalysisTable claims={claimsForTable} />
            </section>
          )}

          {/* Recommendations */}
          {recommendationsForCards.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <Lightbulb className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-xl font-semibold text-foreground">Recommendations</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendationsForCards.map((rec, idx) => (
                  <RecommendationCard key={idx} {...rec} />
                ))}
              </div>
            </section>
          )}

          {/* Analysis Metadata */}
          <section className="mt-10 pt-6 border-t border-border">
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground font-mono">
              <span>Case ID: {caseId}</span>
              <span>Processing Time: {analysisResult.metadata.processing_time_ms}ms</span>
              <span>Timestamp: {new Date(analysisResult.metadata.timestamp).toLocaleString()}</span>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
