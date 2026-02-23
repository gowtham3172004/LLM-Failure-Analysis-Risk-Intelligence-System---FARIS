import { useLocation, Link, Navigate } from "react-router-dom";
import RiskScoreBadge from "@/components/RiskScoreBadge";
import FailureCard from "@/components/FailureCard";
import ClaimAnalysisTable from "@/components/ClaimAnalysisTable";
import RecommendationCard from "@/components/RecommendationCard";
import { ArrowLeft, FileText, AlertTriangle, Lightbulb, CheckCircle, Zap, Globe, FileUp, Sparkles } from "lucide-react";
import type { AnalysisResponse, FailureType as ApiFailureType } from "@/lib/api";
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

interface LocationState {
  analysisResult: AnalysisResponse;
  formData: {
    modelName?: string;
    temperature?: string;
  };
}

export default function Result() {
  const location = useLocation();
  const state = location.state as LocationState | null;

  // Redirect to analyze page if no data
  if (!state?.analysisResult) {
    return <Navigate to="/analyze" replace />;
  }

  const { analysisResult, formData } = state;
  const { risk_assessment, failures, claims, recommendations, explanation, remediation, context_source, warnings } = analysisResult;

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

  const contextSourceLabel = context_source === "url" ? "URL" : context_source === "pdf" ? "PDF" : context_source === "manual" ? "Manual" : null;
  const ContextIcon = context_source === "url" ? Globe : context_source === "pdf" ? FileUp : null;

  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-5xl">
          {/* Back Link */}
          <Link
            to="/analyze"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-6"
          >
            <ArrowLeft className="h-4 w-4" />
            New Analysis
          </Link>

          {/* Source Badge */}
          {contextSourceLabel && (
            <div className="mb-4 flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 px-3 py-1 text-xs font-semibold text-blue-400">
                <Zap className="h-3 w-3" />
                FARIS Analysis
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
                {ContextIcon && <ContextIcon className="h-3 w-3" />}
                Source: {contextSourceLabel}
              </span>
            </div>
          )}

          {/* Warnings Banner */}
          {warnings && warnings.length > 0 && (
            <div className="mb-4 rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  {warnings.map((w, i) => (
                    <p key={i} className="text-sm text-yellow-400">{w}</p>
                  ))}
                </div>
              </div>
            </div>
          )}

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
                    ? "This output exhibits reliability issues. Review the detailed breakdown below before considering deployment."
                    : "This output appears reliable based on our analysis. Review the details below for more information."}
                </p>
                {formData?.modelName && (
                  <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground font-mono">
                    <span>Model: {formData.modelName}</span>
                    {formData.temperature && <span>Temp: {formData.temperature}</span>}
                    <span>Domain: {risk_assessment.domain} ({risk_assessment.domain_multiplier}x)</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Remediation Result */}
          {remediation?.attempted && remediation.corrected_answer && (
            <section className="mb-10">
              <div className="flex items-center gap-2 mb-4">
                <Sparkles className="h-5 w-5 text-blue-400" />
                <h2 className="text-xl font-semibold text-foreground">Auto-Remediated Answer</h2>
                <span className="ml-2 inline-flex items-center gap-1 rounded-full bg-green-500/10 border border-green-500/30 px-2.5 py-0.5 text-xs font-medium text-green-400">
                  <CheckCircle className="h-3 w-3" />
                  Corrected
                </span>
              </div>
              <div className="rounded-xl border border-green-500/30 bg-green-500/5 p-6">
                <div className="mb-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-green-400 mb-2">
                    Corrected Answer
                  </h3>
                  <p className="text-foreground leading-relaxed whitespace-pre-line font-mono text-sm">
                    {remediation.corrected_answer}
                  </p>
                </div>
                {remediation.explanation && (
                  <div className="border-t border-green-500/20 pt-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-green-400 mb-2">
                      What Was Fixed
                    </h3>
                    <p className="text-muted-foreground text-sm leading-relaxed whitespace-pre-line">
                      {remediation.explanation}
                    </p>
                  </div>
                )}
              </div>
            </section>
          )}

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
              <span>Analysis ID: {analysisResult.analysis_id}</span>
              <span>Processing Time: {analysisResult.metadata.processing_time_ms}ms</span>
              <span>Timestamp: {new Date(analysisResult.metadata.timestamp).toLocaleString()}</span>
              {context_source && <span>Context Source: {context_source}</span>}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
