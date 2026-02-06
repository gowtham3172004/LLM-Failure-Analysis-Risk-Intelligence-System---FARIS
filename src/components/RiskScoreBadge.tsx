import { cn } from "@/lib/utils";

interface RiskScoreBadgeProps {
  score: number;
  level: "low" | "medium" | "high";
  size?: "sm" | "md" | "lg";
}

export default function RiskScoreBadge({
  score,
  level,
  size = "md",
}: RiskScoreBadgeProps) {
  const sizeClasses = {
    sm: "h-16 w-16 text-lg",
    md: "h-24 w-24 text-2xl",
    lg: "h-32 w-32 text-4xl",
  };

  const levelClasses = {
    low: "border-risk-low text-risk-low",
    medium: "border-risk-medium text-risk-medium",
    high: "border-risk-high text-risk-high",
  };

  const labelClasses = {
    low: "bg-risk-low/10 text-risk-low",
    medium: "bg-risk-medium/10 text-risk-medium",
    high: "bg-risk-high/10 text-risk-high",
  };

  return (
    <div className="flex flex-col items-center gap-3">
      <div
        className={cn(
          "flex items-center justify-center rounded-full border-4 font-mono font-bold",
          sizeClasses[size],
          levelClasses[level]
        )}
      >
        {score.toFixed(2)}
      </div>
      <span
        className={cn(
          "px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider",
          labelClasses[level]
        )}
      >
        {level} risk
      </span>
    </div>
  );
}
