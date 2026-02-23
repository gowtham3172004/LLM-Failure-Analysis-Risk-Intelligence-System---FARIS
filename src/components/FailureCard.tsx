import { cn } from "@/lib/utils";

export type FailureType =
  | "hallucination"
  | "logic"
  | "assumptions"
  | "overconfidence"
  | "scope"
  | "underspecification";

interface FailureCardProps {
  type: FailureType;
  name: string;
  confidence: number;
  severity: "low" | "medium" | "high";
  evidence: string;
}

const typeColors: Record<FailureType, string> = {
  hallucination: "border-l-failure-hallucination",
  logic: "border-l-failure-logic",
  assumptions: "border-l-failure-assumptions",
  overconfidence: "border-l-failure-overconfidence",
  scope: "border-l-failure-scope",
  underspecification: "border-l-failure-underspecification",
};

const severityBadge: Record<string, string> = {
  low: "bg-risk-low/10 text-risk-low",
  medium: "bg-risk-medium/10 text-risk-medium",
  high: "bg-risk-high/10 text-risk-high",
};

export default function FailureCard({
  type,
  name,
  confidence,
  severity,
  evidence,
}: FailureCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-5 border-l-4 animate-fade-in",
        typeColors[type]
      )}
    >
      <div className="flex items-start justify-between gap-4 mb-3">
        <h3 className="font-semibold text-card-foreground">{name}</h3>
        <span
          className={cn(
            "px-2 py-0.5 rounded text-xs font-medium uppercase",
            severityBadge[severity]
          )}
        >
          {severity}
        </span>
      </div>

      <div className="flex items-center gap-4 mb-4 text-sm text-muted-foreground">
        <span className="font-mono">
          Confidence: <strong className="text-foreground">{(confidence * 100).toFixed(0)}%</strong>
        </span>
      </div>

      <div className="border-t border-border pt-3">
        <p className="text-sm text-muted-foreground leading-relaxed">
          <span className="font-medium text-foreground">Evidence: </span>
          {evidence}
        </p>
      </div>
    </div>
  );
}
