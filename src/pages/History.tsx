import { Link } from "react-router-dom";
import { cn } from "@/utils";
import { ExternalLink } from "lucide-react";

// Mock history data
const mockHistory = [
  {
    id: "case-001",
    timestamp: "2024-01-15T14:32:00Z",
    model: "gpt-4o",
    question: "What are the main benefits of using TypeScript over JavaScript?",
    riskScore: 0.23,
    riskLevel: "low" as const,
    failureCount: 1,
    failureTypes: ["underspecification"],
  },
  {
    id: "case-002",
    timestamp: "2024-01-15T13:18:00Z",
    model: "claude-3-opus",
    question: "Explain the history of quantum computing and its current state.",
    riskScore: 0.72,
    riskLevel: "high" as const,
    failureCount: 3,
    failureTypes: ["hallucination", "overconfidence", "missing-assumptions"],
  },
  {
    id: "case-003",
    timestamp: "2024-01-15T11:45:00Z",
    model: "gpt-4o",
    question: "How should I invest my retirement savings?",
    riskScore: 0.89,
    riskLevel: "high" as const,
    failureCount: 2,
    failureTypes: ["scope-violation", "overconfidence"],
  },
  {
    id: "case-004",
    timestamp: "2024-01-14T16:22:00Z",
    model: "gemini-pro",
    question: "Write a Python function to sort a list of integers.",
    riskScore: 0.15,
    riskLevel: "low" as const,
    failureCount: 0,
    failureTypes: [],
  },
  {
    id: "case-005",
    timestamp: "2024-01-14T14:08:00Z",
    model: "claude-3-sonnet",
    question: "What medications should I take for my headache?",
    riskScore: 0.95,
    riskLevel: "high" as const,
    failureCount: 2,
    failureTypes: ["scope-violation", "hallucination"],
  },
  {
    id: "case-006",
    timestamp: "2024-01-14T10:30:00Z",
    model: "gpt-4o",
    question: "Explain the difference between REST and GraphQL APIs.",
    riskScore: 0.38,
    riskLevel: "medium" as const,
    failureCount: 1,
    failureTypes: ["missing-assumptions"],
  },
];

const riskBadgeStyles = {
  low: "bg-risk-low/10 text-risk-low",
  medium: "bg-risk-medium/10 text-risk-medium",
  high: "bg-risk-high/10 text-risk-high",
};

function formatDate(isoString: string) {
  const date = new Date(isoString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function History() {
  return (
    <div className="min-h-screen py-12">
      <div className="container">
        <div className="mx-auto max-w-5xl">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Case History</h1>
              <p className="mt-1 text-muted-foreground">
                Audit log of all analyzed LLM outputs.
              </p>
            </div>
            <Link
              to="/analyze"
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90"
            >
              New Analysis
            </Link>
          </div>

          {/* Table */}
          <div className="rounded-xl border border-border overflow-hidden">
            <table className="w-full">
              <thead className="bg-muted/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Timestamp
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Model
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Question
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Risk
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Failures
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground w-16">
                    View
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {mockHistory.map((item) => (
                  <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-4 text-sm text-muted-foreground font-mono whitespace-nowrap">
                      {formatDate(item.timestamp)}
                    </td>
                    <td className="px-4 py-4 text-sm text-foreground font-mono">
                      {item.model}
                    </td>
                    <td className="px-4 py-4 text-sm text-foreground max-w-xs truncate">
                      {item.question}
                    </td>
                    <td className="px-4 py-4 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <span className="text-sm font-mono font-medium text-foreground">
                          {item.riskScore.toFixed(2)}
                        </span>
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-xs font-medium uppercase",
                            riskBadgeStyles[item.riskLevel]
                          )}
                        >
                          {item.riskLevel}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <span className="text-sm font-mono text-muted-foreground">
                        {item.failureCount}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      <Link
                        to={`/result`}
                        className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent transition-colors"
                      >
                        <ExternalLink className="h-4 w-4 text-muted-foreground" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination placeholder */}
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>Showing 6 of 6 cases</span>
            <div className="flex items-center gap-2">
              <button className="px-3 py-1 rounded border border-border hover:bg-accent transition-colors" disabled>
                Previous
              </button>
              <button className="px-3 py-1 rounded border border-border hover:bg-accent transition-colors" disabled>
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
