import AnalysisForm from "@/components/AnalysisForm";
import { AlertCircle, CheckCircle2, HelpCircle, Zap } from "lucide-react";

const whatWeAnalyze = [
  "Factual accuracy and hallucination detection",
  "Logical consistency and reasoning gaps",
  "Implicit assumptions and their validity",
  "Confidence calibration and uncertainty",
  "Completeness of response coverage",
];

const whatWeDoNot = [
  "Generate or modify LLM responses",
  "Access model internals or weights",
  "Store your data beyond the session",
  "Make deployment decisions for you",
];

export default function Analyze() {
  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-5xl">
          {/* Header */}
          <div className="mb-10 text-center">
            <h1 className="text-3xl font-bold text-foreground">Analyze LLM Output</h1>
            <p className="mt-2 text-muted-foreground">
              Provide the question and LLM response to analyze for potential failure modes.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Form Panel */}
            <div className="lg:col-span-2">
              <div className="rounded-xl border border-border bg-card p-6">
                <AnalysisForm />
              </div>
            </div>

            {/* Info Panel */}
            <div className="space-y-6">
              {/* What We Analyze */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <CheckCircle2 className="h-5 w-5 text-risk-low" />
                  <h3 className="font-semibold text-foreground">What FARIS Analyzes</h3>
                </div>
                <ul className="space-y-2">
                  {whatWeAnalyze.map((item) => (
                    <li
                      key={item}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="mt-1.5 h-1 w-1 rounded-full bg-risk-low shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* What We Do NOT */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <AlertCircle className="h-5 w-5 text-risk-high" />
                  <h3 className="font-semibold text-foreground">What We Don't Do</h3>
                </div>
                <ul className="space-y-2">
                  {whatWeDoNot.map((item) => (
                    <li
                      key={item}
                      className="flex items-start gap-2 text-sm text-muted-foreground"
                    >
                      <span className="mt-1.5 h-1 w-1 rounded-full bg-risk-high shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Truth Engine Info */}
              <div className="rounded-xl border border-blue-500/30 bg-blue-500/5 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="h-5 w-5 text-blue-400" />
                  <h3 className="font-semibold text-foreground">Truth Engine</h3>
                </div>
                <p className="text-sm text-muted-foreground mb-3">
                  Supply a URL or PDF as ground truth to enable enhanced 
                  verification and automatic remediation of detected failures.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-start gap-2">
                    <span className="mt-1.5 h-1 w-1 rounded-full bg-blue-400 shrink-0" />
                    URL scraping & PDF extraction
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1.5 h-1 w-1 rounded-full bg-blue-400 shrink-0" />
                    Semantic context refinement
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="mt-1.5 h-1 w-1 rounded-full bg-blue-400 shrink-0" />
                    Automated answer correction
                  </li>
                </ul>
              </div>

              {/* Failure Categories */}
              <div className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center gap-2 mb-4">
                  <HelpCircle className="h-5 w-5 text-muted-foreground" />
                  <h3 className="font-semibold text-foreground">Failure Categories</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {[
                    { name: "Hallucination", color: "bg-failure-hallucination/20 text-failure-hallucination" },
                    { name: "Logical Gap", color: "bg-failure-logic/20 text-failure-logic" },
                    { name: "Missing Assumption", color: "bg-failure-assumptions/20 text-failure-assumptions" },
                    { name: "Overconfidence", color: "bg-failure-overconfidence/20 text-failure-overconfidence" },
                    { name: "Incomplete", color: "bg-failure-underspecification/20 text-failure-underspecification" },
                  ].map((cat) => (
                    <span
                      key={cat.name}
                      className={`px-2 py-1 rounded text-xs font-medium ${cat.color}`}
                    >
                      {cat.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
