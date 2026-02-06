import { cn } from "@/lib/utils";
import { Check, X, Minus } from "lucide-react";

interface Claim {
  id: string;
  text: string;
  supported: "yes" | "no" | "partial";
  notes: string;
}

interface ClaimAnalysisTableProps {
  claims: Claim[];
}

const supportedStyles = {
  yes: {
    icon: Check,
    bg: "bg-risk-low/10",
    text: "text-risk-low",
  },
  no: {
    icon: X,
    bg: "bg-risk-high/10",
    text: "text-risk-high",
  },
  partial: {
    icon: Minus,
    bg: "bg-risk-medium/10",
    text: "text-risk-medium",
  },
};

export default function ClaimAnalysisTable({ claims }: ClaimAnalysisTableProps) {
  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <table className="w-full">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Claim
            </th>
            <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground w-28">
              Supported
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground w-1/3">
              Notes
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {claims.map((claim) => {
            const style = supportedStyles[claim.supported];
            const Icon = style.icon;
            return (
              <tr key={claim.id} className="hover:bg-muted/30 transition-colors">
                <td className="px-4 py-4 text-sm text-foreground font-mono">
                  {claim.text}
                </td>
                <td className="px-4 py-4 text-center">
                  <span
                    className={cn(
                      "inline-flex items-center justify-center w-8 h-8 rounded-full",
                      style.bg
                    )}
                  >
                    <Icon className={cn("h-4 w-4", style.text)} />
                  </span>
                </td>
                <td className="px-4 py-4 text-sm text-muted-foreground">
                  {claim.notes}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
