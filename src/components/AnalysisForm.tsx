import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Loader2, AlertCircle, Globe, Upload, X, Zap } from "lucide-react";
import { analyzeOutput, type Domain, ApiError } from "@/lib/api";

export default function AnalysisForm() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({
    question: "",
    answer: "",
    domain: "general" as Domain,
    sourceUrl: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeOutput({
        question: formData.question,
        llm_answer: formData.answer,
        domain: formData.domain,
        source_url: formData.sourceUrl || undefined,
        file: selectedFile || undefined,
      });
      navigate("/result", { state: { analysisResult: response, formData } });
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 429) {
          setError("API rate limit reached. Please wait 1-2 minutes and try again.");
        } else {
          setError(`Analysis failed: ${err.message}`);
        }
      } else {
        setError("An unexpected error occurred. Please check if the backend server is running.");
      }
      console.error("Analysis error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
    setError(null);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Only PDF files are supported.");
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        setError("File size must be under 20 MB.");
        return;
      }
      setSelectedFile(file);
      setFormData((prev) => ({ ...prev, sourceUrl: "" }));
      setError(null);
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const isValid = formData.question.trim() && formData.answer.trim();

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Display */}
      {error && (
        <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
          <div className="text-sm text-red-400">{error}</div>
        </div>
      )}

      {/* Question */}
      <div className="space-y-2">
        <label htmlFor="question" className="block text-sm font-medium text-foreground">
          Question / Prompt <span className="text-red-500">*</span>
        </label>
        <textarea
          id="question"
          name="question"
          rows={3}
          placeholder="What question was asked to the LLM?"
          value={formData.question}
          onChange={handleChange}
          className="w-full rounded-lg border border-input bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono"
        />
      </div>

      {/* Answer */}
      <div className="space-y-2">
        <label htmlFor="answer" className="block text-sm font-medium text-foreground">
          LLM Answer <span className="text-red-500">*</span>
        </label>
        <textarea
          id="answer"
          name="answer"
          rows={8}
          placeholder="Paste the LLM's response here..."
          value={formData.answer}
          onChange={handleChange}
          className="w-full rounded-lg border border-input bg-secondary px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono"
        />
      </div>

      {/* Ground-Truth Source: URL or PDF */}
      <div className="space-y-4 rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
        <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Globe className="h-4 w-4 text-blue-400" />
          Ground-Truth Source
          <span className="text-xs font-normal text-muted-foreground">(optional — improves accuracy)</span>
        </h3>

        {/* URL */}
        <div className="space-y-2">
          <label htmlFor="sourceUrl" className="block text-xs font-medium text-muted-foreground">
            Source URL
          </label>
          <input
            type="url"
            id="sourceUrl"
            name="sourceUrl"
            placeholder="https://en.wikipedia.org/wiki/Example"
            value={formData.sourceUrl}
            onChange={(e) => {
              handleChange(e);
              if (e.target.value) clearFile();
            }}
            disabled={!!selectedFile}
            className="w-full rounded-md border border-input bg-secondary px-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono disabled:opacity-50"
          />
        </div>

        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          <span>OR</span>
          <div className="h-px flex-1 bg-border" />
        </div>

        {/* PDF Upload */}
        <div className="space-y-2">
          <label className="block text-xs font-medium text-muted-foreground">
            Upload PDF
          </label>
          {selectedFile ? (
            <div className="flex items-center gap-3 rounded-md border border-input bg-secondary px-3 py-2.5">
              <Upload className="h-4 w-4 text-blue-400" />
              <span className="flex-1 text-sm text-foreground font-mono truncate">
                {selectedFile.name}
              </span>
              <span className="text-xs text-muted-foreground">
                {(selectedFile.size / 1024).toFixed(0)} KB
              </span>
              <button
                type="button"
                onClick={clearFile}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={!!formData.sourceUrl}
              className="w-full flex items-center justify-center gap-2 rounded-md border border-dashed border-input bg-secondary/50 px-3 py-4 text-sm text-muted-foreground hover:border-blue-500/50 hover:text-foreground transition-colors disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              Choose PDF file (max 20 MB)
            </button>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="hidden"
          />
        </div>
      </div>

      {/* Domain Selection */}
      <div className="space-y-2">
        <label htmlFor="domain" className="block text-sm font-medium text-foreground">
          Domain
        </label>
        <select
          id="domain"
          name="domain"
          value={formData.domain}
          onChange={handleChange}
          className="w-full rounded-lg border border-input bg-secondary px-4 py-3 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          <option value="general">General (1.0x multiplier)</option>
          <option value="code">Code (1.3x multiplier)</option>
          <option value="finance">Finance (1.5x multiplier)</option>
          <option value="legal">Legal (1.8x multiplier)</option>
          <option value="medical">Medical (2.0x multiplier)</option>
        </select>
        <p className="text-xs text-muted-foreground">
          Higher-stakes domains apply higher risk multipliers
        </p>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={!isValid || isLoading}
        className={cn(
          "w-full flex items-center justify-center gap-2 rounded-lg px-6 py-4 font-semibold text-sm transition-all",
          isValid && !isLoading
            ? "bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90 shadow-lg shadow-blue-500/25"
            : "bg-muted text-muted-foreground cursor-not-allowed"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Running Analysis...
          </>
        ) : (
          <>
            <Zap className="h-4 w-4" />
            Analyze LLM Output
          </>
        )}
      </button>
    </form>
  );
}
