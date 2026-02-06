import { Shield, AlertTriangle, Target, Eye, Zap, BookOpen } from "lucide-react";

const philosophyPoints = [
  {
    icon: AlertTriangle,
    title: "Failure-First Engineering",
    description: "Traditional AI development focuses on capability. We focus on understanding failure modes first. You can't deploy reliably what you don't understand deeply.",
  },
  {
    icon: Eye,
    title: "Observability, Not Generation",
    description: "FARIS never generates answers. It only analyzes existing outputs. This separation ensures we evaluate without bias from our own generation capabilities.",
  },
  {
    icon: Target,
    title: "Black-Box Analysis",
    description: "We don't require access to model internals, weights, or logits. FARIS works with any LLM output, treating the model as a complete black box.",
  },
  {
    icon: Shield,
    title: "Deployment Risk Quantification",
    description: "Every failure mode contributes to a quantified risk score. This enables data-driven decisions about when and where to deploy LLM systems.",
  },
  {
    icon: Zap,
    title: "Actionable Mitigations",
    description: "Detection without remediation is incomplete. Every failure type comes with engineering-focused recommendations for mitigation.",
  },
  {
    icon: BookOpen,
    title: "Research-Backed Taxonomy",
    description: "Our failure classification is grounded in academic research on LLM reliability, not ad-hoc categories. Each type represents documented failure patterns.",
  },
];

const faqs = [
  {
    question: "Why focus on failures instead of capabilities?",
    answer: "Capabilities are well-studied. Failures are not. Most LLM deployments fail not because the model lacks capability, but because specific failure modes weren't anticipated. Understanding failure modes enables proactive engineering.",
  },
  {
    question: "How is FARIS different from LLM evaluation benchmarks?",
    answer: "Benchmarks measure average performance on curated datasets. FARIS analyzes individual outputs in your specific context. We're not asking 'how good is this model?' but 'is this specific output safe to use?'",
  },
  {
    question: "Can FARIS guarantee an output is safe?",
    answer: "No. FARIS provides risk assessment, not guarantees. We identify known failure patterns and quantify risk. Novel failure modes may exist that we haven't classified. Use FARIS as one layer in a defense-in-depth strategy.",
  },
  {
    question: "What models does FARIS work with?",
    answer: "Any model that produces text output. GPT-4, Claude, Gemini, Llama, Mistral, or any other LLM. We analyze the output, not the model architecture.",
  },
];

export default function About() {
  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Hero */}
          <div className="text-center mb-16">
            <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              System Philosophy
            </h1>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              FARIS represents a paradigm shift in how we approach LLM reliability. 
              Instead of asking "what can this model do?", we ask "how can this model fail?"
            </p>
          </div>

          {/* Why Failures Matter */}
          <section className="mb-16">
            <div className="rounded-xl border border-border bg-card p-8">
              <h2 className="text-xl font-semibold text-foreground mb-4">
                Why LLM Failures Matter
              </h2>
              <div className="prose prose-neutral dark:prose-invert max-w-none">
                <p className="text-muted-foreground leading-relaxed">
                  Large language models are being deployed in increasingly critical applications: 
                  customer service, code generation, medical information, legal research, and more. 
                  Yet our understanding of <em>how</em> and <em>why</em> they fail remains primitive.
                </p>
                <p className="text-muted-foreground leading-relaxed mt-4">
                  A model can score 90% on a benchmark while still producing dangerous outputs 
                  in production. Hallucinations appear authoritative. Logical inconsistencies 
                  hide in long-form text. Overconfident claims mislead users into false certainty.
                </p>
                <p className="text-muted-foreground leading-relaxed mt-4">
                  FARIS exists because the industry needs better tools to understand LLM failures—
                  not after they cause harm, but before deployment.
                </p>
              </div>
            </div>
          </section>

          {/* Philosophy Points */}
          <section className="mb-16">
            <h2 className="text-xl font-semibold text-foreground mb-6">Core Principles</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {philosophyPoints.map((point) => (
                <div
                  key={point.title}
                  className="rounded-lg border border-border bg-card p-6"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                      <point.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-foreground mb-2">{point.title}</h3>
                      <p className="text-sm text-muted-foreground">{point.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Technical Overview */}
          <section className="mb-16">
            <h2 className="text-xl font-semibold text-foreground mb-6">Technical Overview</h2>
            <div className="rounded-xl border border-border bg-card p-8">
              <div className="space-y-6">
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Architecture</h3>
                  <p className="text-sm text-muted-foreground">
                    FARIS uses a LangGraph-based orchestration pipeline with parallel detector 
                    execution. Each failure detector runs independently, allowing for efficient 
                    analysis and easy extension with new failure types.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Detection Methods</h3>
                  <p className="text-sm text-muted-foreground">
                    Detectors combine heuristic analysis, semantic similarity checks, and 
                    LLM-based reasoning. We use embedding models for claim verification and 
                    structured prompts for failure classification.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground mb-2">Risk Scoring</h3>
                  <p className="text-sm text-muted-foreground">
                    The final risk score aggregates individual failure detections weighted by 
                    severity and confidence. Domain-specific adjustments account for the varying 
                    criticality of failures in different contexts.
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* FAQs */}
          <section>
            <h2 className="text-xl font-semibold text-foreground mb-6">Frequently Asked Questions</h2>
            <div className="space-y-4">
              {faqs.map((faq) => (
                <div
                  key={faq.question}
                  className="rounded-lg border border-border bg-card p-6"
                >
                  <h3 className="font-semibold text-foreground mb-2">{faq.question}</h3>
                  <p className="text-sm text-muted-foreground">{faq.answer}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
