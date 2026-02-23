import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";
import { ExternalLink, Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { listCases, type CaseSummary, type RiskLevel } from "@/lib/api";

const riskBadgeStyles: Record<RiskLevel, string> = {
  low: "bg-risk-low/10 text-risk-low",
  medium: "bg-risk-medium/10 text-risk-medium",
  high: "bg-risk-high/10 text-risk-high",
  critical: "bg-risk-high/10 text-risk-high",
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
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 20;

  const fetchCases = async (pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await listCases({ page: pageNum, page_size: pageSize });
      setCases(response.cases);
      setTotal(response.total);
      setHasMore(response.has_more);
      setPage(pageNum);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch cases");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases(1);
  }, []);

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
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchCases(page)}
                className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground hover:bg-accent transition-colors"
              >
                <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
                Refresh
              </button>
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90"
              >
                New Analysis
              </Link>
            </div>
          </div>

          {/* Error State */}
          {error && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 mb-6 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-red-500">{error}</p>
                <p className="text-xs text-red-500/70 mt-1">
                  Make sure the backend server is running at the configured API URL.
                </p>
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && cases.length === 0 && (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && cases.length === 0 && (
            <div className="text-center py-20">
              <p className="text-muted-foreground mb-4">No analysis cases yet.</p>
              <Link
                to="/analyze"
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:opacity-90"
              >
                Run Your First Analysis
              </Link>
            </div>
          )}

          {/* Table */}
          {cases.length > 0 && (
            <>
              <div className="rounded-xl border border-border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Timestamp
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Domain
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
                    {cases.map((item) => (
                      <tr key={item.case_id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-4 text-sm text-muted-foreground font-mono whitespace-nowrap">
                          {formatDate(item.created_at)}
                        </td>
                        <td className="px-4 py-4 text-sm text-foreground font-mono capitalize">
                          {item.domain}
                        </td>
                        <td className="px-4 py-4 text-sm text-foreground max-w-xs truncate">
                          {item.question_preview}
                        </td>
                        <td className="px-4 py-4 text-center">
                          <div className="flex flex-col items-center gap-1">
                            <span className="text-sm font-mono font-medium text-foreground">
                              {item.risk_score.toFixed(2)}
                            </span>
                            <span
                              className={cn(
                                "px-2 py-0.5 rounded text-xs font-medium uppercase",
                                riskBadgeStyles[item.risk_level]
                              )}
                            >
                              {item.risk_level}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4 text-center">
                          <span className="text-sm font-mono text-muted-foreground">
                            {item.failure_count}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-center">
                          <Link
                            to={`/cases/${item.case_id}`}
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

              {/* Pagination */}
              <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
                <span>
                  Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total} cases
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => fetchCases(page - 1)}
                    disabled={page === 1 || loading}
                    className={cn(
                      "px-3 py-1 rounded border border-border transition-colors",
                      page === 1 || loading
                        ? "opacity-50 cursor-not-allowed"
                        : "hover:bg-accent"
                    )}
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => fetchCases(page + 1)}
                    disabled={!hasMore || loading}
                    className={cn(
                      "px-3 py-1 rounded border border-border transition-colors",
                      !hasMore || loading
                        ? "opacity-50 cursor-not-allowed"
                        : "hover:bg-accent"
                    )}
                  >
                    Next
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
