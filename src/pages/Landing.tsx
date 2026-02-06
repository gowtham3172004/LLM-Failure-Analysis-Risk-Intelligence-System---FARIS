import { Link } from "react-router-dom";
import { ArrowRight, AlertTriangle, Target, Shield, BarChart3 } from "lucide-react";

const features = [
  {
    icon: AlertTriangle,
    title: "Failure Detection",
    description: "Identify hallucinations, logical inconsistencies, and missing assumptions in LLM outputs.",
  },
  {
    icon: Target,
    title: "Claim-Level Analysis",
    description: "Decompose answers into individual claims and verify each against evidence.",
  },
  {
    icon: BarChart3,
    title: "Risk Scoring",
    description: "Quantify deployment risk with explainable scores based on failure severity.",
  },
  {
    icon: Shield,
    title: "Actionable Recommendations",
    description: "Get engineering-focused mitigation strategies for detected failures.",
  },
];

const principles = [
  {
    title: "Failure-First AI Engineering",
    description: "We analyze why LLMs fail—not what they generate.",
  },
  {
    title: "Black-Box Model Analysis",
    description: "No access to model internals required. Works with any LLM output.",
  },
  {
    title: "No Answer Generation",
    description: "FARIS evaluates existing outputs. It never generates answers.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="container py-24 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
              Understand Why LLMs Fail
              <br />
              <span className="text-muted-foreground">Before You Deploy Them</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto">
              FARIS analyzes LLM outputs, classifies failure modes, explains root causes, 
              and assigns deployment risk scores. Built for AI engineers who need reliability.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90"
              >
                Analyze LLM Output
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/taxonomy"
                className="inline-flex items-center gap-2 rounded-lg border border-border px-6 py-3 text-sm font-semibold text-foreground transition-all hover:bg-accent"
              >
                View Failure Taxonomy
              </Link>
            </div>
          </div>
        </div>

        {/* Visual Pipeline */}
        <div className="container pb-16">
          <div className="mx-auto max-w-4xl">
            <div className="rounded-xl border border-border bg-card p-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-center">
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
                    <span className="font-mono text-sm text-muted-foreground">INPUT</span>
                  </div>
                  <span className="text-xs text-muted-foreground">Q + A + Context</span>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-failure-hallucination/20">
                    <AlertTriangle className="h-5 w-5 text-failure-hallucination" />
                  </div>
                  <span className="text-xs text-muted-foreground">Failure Types</span>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-risk-medium/20">
                    <BarChart3 className="h-5 w-5 text-risk-medium" />
                  </div>
                  <span className="text-xs text-muted-foreground">Risk Score</span>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-risk-low/20">
                    <Shield className="h-5 w-5 text-risk-low" />
                  </div>
                  <span className="text-xs text-muted-foreground">Recommendations</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-b border-border py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-2xl font-bold text-foreground">Analysis Capabilities</h2>
            <p className="mt-2 text-muted-foreground">
              Comprehensive failure detection for production LLM systems.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-lg border border-border bg-card p-6 transition-all hover:border-primary/50"
              >
                <feature.icon className="h-8 w-8 text-primary mb-4" />
                <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Principles */}
      <section className="py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-2xl font-bold text-foreground">Design Principles</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {principles.map((principle) => (
              <div key={principle.title} className="text-center">
                <h3 className="font-semibold text-foreground mb-2">{principle.title}</h3>
                <p className="text-sm text-muted-foreground">{principle.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
