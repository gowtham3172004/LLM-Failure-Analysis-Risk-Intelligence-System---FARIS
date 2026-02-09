import { cn } from "@/utils";
import { Lightbulb, ArrowRight } from "lucide-react";

interface RecommendationCardProps {
  title: string;
  description: string;
  priority: "low" | "medium" | "high";
  category: string;
}

const priorityStyles = {
  low: "border-l-risk-low",
  medium: "border-l-risk-medium",
  high: "border-l-risk-high",
};

export default function RecommendationCard({
  title,
  description,
  priority,
  category,
}: RecommendationCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-5 border-l-4 transition-all hover:bg-accent/30",
        priorityStyles[priority]
      )}
    >
      <div className="flex items-start gap-3">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <Lightbulb className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-card-foreground">{title}</h4>
            <span className="text-xs font-mono text-muted-foreground uppercase">
              {category}
            </span>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {description}
          </p>
          <button className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
            Learn more <ArrowRight className="h-3 w-3" />
          </button>
        </div>
      </div>
    </div>
  );
}
