import { AlertTriangle, Brain, HelpCircle, Gauge, Target, FileQuestion } from "lucide-react";

const failureTypes = [
  {
    id: "hallucination",
    name: "Hallucination",
    icon: AlertTriangle,
    color: "text-failure-hallucination",
    bgColor: "bg-failure-hallucination/10",
    borderColor: "border-l-failure-hallucination",
    definition: "The model generates information that is factually incorrect, fabricated, or not grounded in the provided context.",
    example: "Claiming a historical event occurred on a specific date when no such information was provided or the date is incorrect.",
    riskImpact: "High. Users may make decisions based on false information, leading to real-world consequences.",
    mitigation: "Implement retrieval-augmented generation (RAG), add source citations, use lower temperature settings.",
  },
  {
    id: "logical-inconsistency",
    name: "Logical Inconsistency",
    icon: Brain,
    color: "text-failure-logic",
    bgColor: "bg-failure-logic/10",
    borderColor: "border-l-failure-logic",
    definition: "The response contains contradictions, non-sequiturs, or reasoning that doesn't follow logically.",
    example: "Stating 'X is always true' in one paragraph and 'X is sometimes false' in another without acknowledgment.",
    riskImpact: "Medium-High. Undermines trust and can lead to confusion in multi-step reasoning tasks.",
    mitigation: "Use chain-of-thought prompting, implement self-consistency checks, add logical verification steps.",
  },
  {
    id: "missing-assumptions",
    name: "Missing Assumptions",
    icon: HelpCircle,
    color: "text-failure-assumptions",
    bgColor: "bg-failure-assumptions/10",
    borderColor: "border-l-failure-assumptions",
    definition: "The model makes implicit assumptions about user knowledge, context, or intent without stating them.",
    example: "Providing advanced technical instructions without clarifying required prerequisites or experience level.",
    riskImpact: "Medium. Can cause confusion, incorrect application, or user frustration.",
    mitigation: "Add clarifying questions, explicitly state assumptions, provide context-appropriate responses.",
  },
  {
    id: "overconfidence",
    name: "Overconfidence",
    icon: Gauge,
    color: "text-failure-overconfidence",
    bgColor: "bg-failure-overconfidence/10",
    borderColor: "border-l-failure-overconfidence",
    definition: "The model expresses certainty about claims that are uncertain, speculative, or contested.",
    example: "Using 'definitely', 'always', or 'never' for claims that have exceptions or limited evidence.",
    riskImpact: "Medium-High. Users may not apply appropriate skepticism to uncertain information.",
    mitigation: "Implement uncertainty quantification, use hedging language, train on calibrated confidence.",
  },
  {
    id: "scope-violation",
    name: "Scope Violation",
    icon: Target,
    color: "text-failure-scope",
    bgColor: "bg-failure-scope/10",
    borderColor: "border-l-failure-scope",
    definition: "The response goes beyond the boundaries of what was asked or the model's designated capabilities.",
    example: "Providing medical diagnoses when asked for general health information, or offering legal advice.",
    riskImpact: "Variable. Can be dangerous in regulated domains (medical, legal, financial).",
    mitigation: "Implement guardrails, add domain classifiers, use system prompts with clear boundaries.",
  },
  {
    id: "underspecification",
    name: "Underspecification",
    icon: FileQuestion,
    color: "text-failure-underspecification",
    bgColor: "bg-failure-underspecification/10",
    borderColor: "border-l-failure-underspecification",
    definition: "The response lacks sufficient detail, precision, or specificity to be actionable or useful.",
    example: "Answering 'How do I fix this error?' with 'Try debugging it' without concrete steps.",
    riskImpact: "Low-Medium. Reduces utility but typically doesn't cause direct harm.",
    mitigation: "Use follow-up prompts for detail, implement structured output formats, add completeness checks.",
  },
];

export default function Taxonomy() {
  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-3xl font-bold text-foreground">Failure Taxonomy</h1>
            <p className="mt-2 text-muted-foreground max-w-2xl mx-auto">
              A comprehensive classification of LLM failure modes. Each type represents a distinct way that language model outputs can be unreliable or harmful.
            </p>
          </div>

          {/* Failure Types */}
          <div className="space-y-6">
            {failureTypes.map((failure) => (
              <div
                key={failure.id}
                className={`rounded-xl border border-border bg-card p-6 border-l-4 ${failure.borderColor}`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-lg ${failure.bgColor}`}>
                    <failure.icon className={`h-6 w-6 ${failure.color}`} />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-xl font-semibold text-foreground mb-3">{failure.name}</h2>
                    
                    <div className="space-y-4">
                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                          Definition
                        </h3>
                        <p className="text-sm text-foreground">{failure.definition}</p>
                      </div>

                      <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                          Example
                        </h3>
                        <p className="text-sm text-muted-foreground italic">"{failure.example}"</p>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                            Risk Impact
                          </h3>
                          <p className="text-sm text-muted-foreground">{failure.riskImpact}</p>
                        </div>
                        <div>
                          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-1">
                            Mitigation
                          </h3>
                          <p className="text-sm text-muted-foreground">{failure.mitigation}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
