import { useLocation, Link } from "react-router-dom";
import RiskScoreBadge from "@/components/RiskScoreBadge";
import FailureCard from "@/components/FailureCard";
import ClaimAnalysisTable from "@/components/ClaimAnalysisTable";
import RecommendationCard from "@/components/RecommendationCard";
import { ArrowLeft, FileText, AlertTriangle, Lightbulb } from "lucide-react";

// Mock analysis result
const mockResult = {
  riskScore: 0.72,
  riskLevel: "high" as const,
  failureDetected: true,
  failures: [
    {
      type: "hallucination" as const,
      name: "Hallucination",
      confidence: 0.85,
      severity: "high" as const,
      evidence: "The answer claims the technology was 'widely adopted in 2019' without any supporting context or citation. This appears to be fabricated.",
    },
    {
      type: "overconfidence" as const,
      name: "Overconfidence",
      confidence: 0.68,
      severity: "medium" as const,
      evidence: "Uses absolute language like 'definitely' and 'always' without acknowledging uncertainty or edge cases.",
    },
    {
      type: "assumptions" as const,
      name: "Missing Assumptions",
      confidence: 0.54,
      severity: "medium" as const,
      evidence: "The response assumes the user has prior knowledge of the domain without clarifying prerequisites.",
    },
  ],
  explanation: `The analyzed LLM output exhibits multiple failure modes that significantly impact its reliability for production use. 

The most critical issue is a hallucination regarding adoption timelines—the model states specific dates and adoption metrics without grounding in the provided context. This type of fabrication is particularly dangerous as it appears authoritative.

Additionally, the response demonstrates overconfidence through the use of absolute language, which fails to communicate inherent uncertainty in the claims being made. This could mislead users into treating speculative information as fact.

Finally, the answer makes implicit assumptions about user knowledge that may not hold, potentially causing confusion or misinterpretation.`,
  claims: [
    { id: "1", text: "Technology X was widely adopted in 2019", supported: "no" as const, notes: "No evidence in context; likely hallucinated" },
    { id: "2", text: "Performance improved by 40%", supported: "partial" as const, notes: "Improvement mentioned but percentage unverified" },
    { id: "3", text: "Compatible with major frameworks", supported: "yes" as const, notes: "Confirmed in documentation" },
    { id: "4", text: "Requires no configuration", supported: "no" as const, notes: "Context mentions setup steps required" },
  ],
  recommendations: [
    {
      title: "Add Retrieval Grounding",
      description: "Implement RAG (Retrieval-Augmented Generation) to ground claims in verified sources before response generation.",
      priority: "high" as const,
      category: "Architecture",
    },
    {
      title: "Implement Uncertainty Quantification",
      description: "Use calibrated confidence estimates and hedge language for claims that lack strong supporting evidence.",
      priority: "high" as const,
      category: "Prompting",
    },
    {
      title: "Add Clarifying Questions",
      description: "Before providing detailed answers, prompt for clarification on assumed prerequisites or user context.",
      priority: "medium" as const,
      category: "UX",
    },
    {
      title: "Reduce Temperature",
      description: "Lower the sampling temperature to reduce creative fabrication in factual domains.",
      priority: "low" as const,
      category: "Config",
    },
  ],
};

export default function Result() {
  const location = useLocation();
  const formData = location.state;

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

          {/* Summary Banner */}
          <div className="rounded-xl border border-border bg-card p-8 mb-8">
            <div className="flex flex-col md:flex-row items-center gap-8">
              <RiskScoreBadge
                score={mockResult.riskScore}
                level={mockResult.riskLevel}
                size="lg"
              />
              <div className="flex-1 text-center md:text-left">
                <div className="flex items-center justify-center md:justify-start gap-2 mb-2">
                  <AlertTriangle className="h-5 w-5 text-risk-high" />
                  <span className="text-lg font-semibold text-foreground">
                    {mockResult.failures.length} Failure Types Detected
                  </span>
                </div>
                <p className="text-muted-foreground text-sm max-w-lg">
                  This output exhibits significant reliability issues. Review the detailed breakdown below before considering deployment.
                </p>
                {formData?.modelName && (
                  <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground font-mono">
                    <span>Model: {formData.modelName}</span>
                    <span>Temp: {formData.temperature}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Failure Breakdown */}
          <section className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-xl font-semibold text-foreground">Failure Breakdown</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {mockResult.failures.map((failure, idx) => (
                <FailureCard key={idx} {...failure} />
              ))}
            </div>
          </section>

          {/* Explanation */}
          <section className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-xl font-semibold text-foreground">Explanation</h2>
            </div>
            <div className="rounded-xl border border-border bg-card p-6">
              <p className="text-muted-foreground leading-relaxed whitespace-pre-line">
                {mockResult.explanation}
              </p>
            </div>
          </section>

          {/* Claim Analysis */}
          <section className="mb-10">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-xl font-semibold text-foreground">Claim-Level Analysis</h2>
            </div>
            <ClaimAnalysisTable claims={mockResult.claims} />
          </section>

          {/* Recommendations */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <Lightbulb className="h-5 w-5 text-muted-foreground" />
              <h2 className="text-xl font-semibold text-foreground">Recommendations</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {mockResult.recommendations.map((rec, idx) => (
                <RecommendationCard key={idx} {...rec} />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
