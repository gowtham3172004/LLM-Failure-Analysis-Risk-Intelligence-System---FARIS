import { Link } from "react-router-dom";
import { ArrowRight, AlertTriangle, Target, Shield, BarChart3, Zap, Globe, Sparkles, Brain } from "lucide-react";

const features = [
  {
    icon: AlertTriangle,
    title: "Failure Detection",
    description: "Identify hallucinations, logical gaps, missing assumptions, and overconfidence in any LLM output.",
  },
  {
    icon: Target,
    title: "Claim-Level Analysis",
    description: "Decompose answers into individual claims and verify each against evidence independently.",
  },
  {
    icon: BarChart3,
    title: "Risk Scoring",
    description: "Quantified deployment risk scores to inform production decisions with domain-aware multipliers.",
  },
  {
    icon: Shield,
    title: "Actionable Insights",
    description: "Concrete engineering-focused recommendations to improve LLM reliability and safety.",
  },
];

const whyFaris = [
  {
    icon: Brain,
    title: "Failure-First Engineering",
    description: "We analyze what can go wrong, not what went right. This perspective shift is critical for reliable AI systems.",
  },
  {
    icon: Shield,
    title: "No Answer Generation",
    description: "FARIS never generates answers. It only evaluates existing outputs, eliminating evaluation bias.",
  },
  {
    icon: Target,
    title: "Claim-Level Granularity",
    description: "Every statement is analyzed independently, providing precise identification of problematic claims.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-transparent to-purple-600/5" />
        <div className="container relative py-24 md:py-32">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm text-muted-foreground">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
              AI Observability Platform
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl md:text-6xl">
              Understand Why LLMs Fail
              <br />
              <span className="text-muted-foreground">Before You Deploy Them</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground leading-relaxed max-w-2xl mx-auto">
              FARIS analyzes LLM outputs, classifies failure modes, explains root causes, 
              and assigns deployment risk scores — so you can ship with confidence.
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
          <div className="mx-auto max-w-5xl">
            <div className="rounded-xl border border-border bg-card p-8">
              <div className="flex flex-col md:flex-row items-center justify-between gap-4 text-center">
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
                    <span className="font-mono text-sm text-muted-foreground">INPUT</span>
                  </div>
                  <span className="text-xs text-muted-foreground">Q + A</span>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-500/20">
                    <Globe className="h-5 w-5 text-blue-400" />
                  </div>
                  <span className="text-xs text-muted-foreground">Truth Engine</span>
                </div>
                <ArrowRight className="h-5 w-5 text-muted-foreground hidden md:block" />
                <div className="flex flex-col items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-failure-hallucination/20">
                    <AlertTriangle className="h-5 w-5 text-failure-hallucination" />
                  </div>
                  <span className="text-xs text-muted-foreground">Failure Detection</span>
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
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-green-500/20">
                    <Sparkles className="h-5 w-5 text-green-400" />
                  </div>
                  <span className="text-xs text-muted-foreground">Auto-Remediate</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features — Comprehensive Failure Analysis */}
      <section className="border-b border-border py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-2xl font-bold text-foreground">Comprehensive Failure Analysis</h2>
            <p className="mt-2 text-muted-foreground">
              FARIS provides deep insight into LLM behavior, identifying exactly where and why outputs fail.
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

      {/* New: Truth Engine + Remediation Spotlight */}
      <section className="border-b border-border py-20">
        <div className="container">
          <div className="mx-auto max-w-5xl">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {/* Truth Engine Card */}
              <div className="rounded-xl border border-blue-500/30 bg-gradient-to-br from-blue-600/5 to-purple-600/5 p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20">
                    <Globe className="h-5 w-5 text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">Truth Engine</h3>
                    <span className="text-xs text-blue-400 font-medium">NEW</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  Ingest ground-truth context from URLs or PDFs. The Context Refiner uses 
                  semantic similarity to extract only the most relevant chunks, eliminating 
                  noise and boilerplate.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-blue-400" />
                    Web pages scraped & cleaned with Trafilatura
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-blue-400" />
                    PDF text extraction with PyPDF
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-blue-400" />
                    SentenceTransformer-powered chunk ranking
                  </li>
                </ul>
              </div>

              {/* Remediation Card */}
              <div className="rounded-xl border border-green-500/30 bg-gradient-to-br from-green-600/5 to-emerald-600/5 p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-500/20">
                    <Sparkles className="h-5 w-5 text-green-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground">Auto-Remediation</h3>
                    <span className="text-xs text-green-400 font-medium">NEW</span>
                  </div>
                </div>
                <p className="text-sm text-muted-foreground mb-4">
                  When failures are detected and risk exceeds the threshold, FARIS generates 
                  a corrected answer — strictly grounded in verified context. No hallucinations, 
                  no speculation.
                </p>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-green-400" />
                    Triggers when risk score &gt; 0.3
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-green-400" />
                    Grounded in verified context only
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="h-1 w-1 rounded-full bg-green-400" />
                    Explains what was corrected and why
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why FARIS? */}
      <section className="border-b border-border py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center mb-12">
            <h2 className="text-2xl font-bold text-foreground">Why FARIS?</h2>
            <p className="mt-2 text-muted-foreground">
              Built on principles that matter for production AI systems.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {whyFaris.map((item) => (
              <div key={item.title} className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                    <item.icon className="h-6 w-6 text-primary" />
                  </div>
                </div>
                <h3 className="font-semibold text-foreground mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-bold text-foreground mb-4">Ready to Analyze Your LLM?</h2>
            <p className="text-muted-foreground mb-8">
              Start understanding failure modes in your AI systems today.
            </p>
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-8 py-4 text-sm font-semibold text-primary-foreground transition-all hover:opacity-90"
            >
              <Zap className="h-4 w-4" />
              Start Analysis
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <span className="text-sm text-muted-foreground">
              FARIS — LLM Failure Analysis & Risk Intelligence
            </span>
            <div className="flex items-center gap-6 text-sm text-muted-foreground">
              <Link to="/about" className="hover:text-foreground transition-colors">About</Link>
              <Link to="/taxonomy" className="hover:text-foreground transition-colors">Taxonomy</Link>
              <Link to="/history" className="hover:text-foreground transition-colors">History</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
