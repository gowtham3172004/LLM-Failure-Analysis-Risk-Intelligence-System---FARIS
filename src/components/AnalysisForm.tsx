import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/utils";
import { Play, Loader2 } from "lucide-react";

export default function AnalysisForm() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    question: "",
    answer: "",
    modelName: "",
    temperature: "0.7",
    source: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Simulate analysis delay
    await new Promise((resolve) => setTimeout(resolve, 2000));

    setIsLoading(false);
    navigate("/result", { state: formData });
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const isValid = formData.question.trim() && formData.answer.trim();

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Question */}
      <div className="space-y-2">
        <label
          htmlFor="question"
          className="block text-sm font-medium text-foreground"
        >
          Question / Prompt
        </label>
        <textarea
          id="question"
          name="question"
          rows={3}
          placeholder="What question was asked to the LLM?"
          value={formData.question}
          onChange={handleChange}
          className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
        />
      </div>

      {/* Answer */}
      <div className="space-y-2">
        <label
          htmlFor="answer"
          className="block text-sm font-medium text-foreground"
        >
          LLM Answer
        </label>
        <textarea
          id="answer"
          name="answer"
          rows={8}
          placeholder="Paste the LLM's response here..."
          value={formData.answer}
          onChange={handleChange}
          className="w-full rounded-lg border border-input bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
        />
      </div>

      {/* Model Metadata */}
      <div className="rounded-lg border border-border p-4 space-y-4">
        <h3 className="text-sm font-medium text-foreground">Model Metadata</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <label
              htmlFor="modelName"
              className="block text-xs font-medium text-muted-foreground"
            >
              Model Name
            </label>
            <input
              type="text"
              id="modelName"
              name="modelName"
              placeholder="e.g., gpt-4o"
              value={formData.modelName}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="temperature"
              className="block text-xs font-medium text-muted-foreground"
            >
              Temperature
            </label>
            <input
              type="text"
              id="temperature"
              name="temperature"
              placeholder="0.7"
              value={formData.temperature}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
          <div className="space-y-2">
            <label
              htmlFor="source"
              className="block text-xs font-medium text-muted-foreground"
            >
              Source (optional)
            </label>
            <input
              type="text"
              id="source"
              name="source"
              placeholder="API, Playground..."
              value={formData.source}
              onChange={handleChange}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
            />
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className={cn(
          "w-full flex items-center justify-center gap-2 rounded-lg px-6 py-4 font-semibold text-sm transition-all",
          isValid && !isLoading
            ? "bg-primary text-primary-foreground hover:opacity-90"
            : "bg-muted text-muted-foreground cursor-not-allowed"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Play className="h-4 w-4" />
            Run Failure Analysis
          </>
        )}
      </button>
    </form>
  );
}
