"use client";

import * as React from "react";
import { Card } from "@/components/ui/card";
import { KeyboardButton } from "@/components/ui/keyboard-button";
import { FileText, Copy, ExternalLink, Mic, Wand2, Link as LinkIcon, Sparkles, Facebook } from "lucide-react";
import { apiPost } from "@/lib/api";

interface StatementTemplate {
  id: string;
  name: string;
  description: string;
  tone: "formal" | "empathetic" | "defensive" | "proactive";
}

const STATEMENT_TEMPLATES: StatementTemplate[] = [
  {
    id: "formal",
    name: "Formal Acknowledgment",
    description: "Professional response acknowledging concerns",
    tone: "formal",
  },
  {
    id: "empathetic",
    name: "Empathetic Response",
    description: "Understanding and compassionate tone",
    tone: "empathetic",
  },
  {
    id: "defensive",
    name: "Fact Correction",
    description: "Clarify misinformation with data",
    tone: "defensive",
  },
  {
    id: "proactive",
    name: "Proactive Announcement",
    description: "Positive forward-looking statement",
    tone: "proactive",
  },
];

interface OfficialStatementGeneratorProps {
  sentimentLabel: string;
  negativePercent: number;
  neutralPercent: number;
  positivePercent: number;
  credibilityScore: number;
  hasMisinformation: boolean;
  sources: Array<{
    title: string;
    snippet: string;
    sentiment?: string | null;
    metadata?: Record<string, unknown>;
  }>;
  focusAreas?: string[];
}

export function OfficialStatementGenerator({
  sentimentLabel,
  negativePercent,
  neutralPercent,
  positivePercent,
  credibilityScore,
  hasMisinformation,
  sources,
  focusAreas = [],
}: OfficialStatementGeneratorProps) {
  const [selectedTemplate, setSelectedTemplate] = React.useState<string>("formal");
  const [generatedStatement, setGeneratedStatement] = React.useState<string>("");
  const [isGenerating, setIsGenerating] = React.useState(false);
  const [copied, setCopied] = React.useState(false);
  const [docLink, setDocLink] = React.useState("");
  const [isExporting, setIsExporting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [exportToFacebook, setExportToFacebook] = React.useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const template = STATEMENT_TEMPLATES.find(t => t.id === selectedTemplate);

      const payload = {
        tone: template?.tone || "formal",
        sentiment_label: sentimentLabel,
        negative_percent: negativePercent,
        neutral_percent: neutralPercent,
        positive_percent: positivePercent,
        credibility_score: credibilityScore,
        has_misinformation: hasMisinformation,
        sources: sources.map(s => ({
          title: s.title,
          snippet: s.snippet,
          sentiment: s.sentiment,
        })),
        focus_areas: focusAreas,
      };

      const response = await apiPost<typeof payload, { statement: string; tone: string }>(
        "/insights/generate-statement",
        payload
      );

      setGeneratedStatement(response.statement);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to generate statement";
      setError(message);
      console.error("Statement generation error:", err);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(generatedStatement);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFacebookDraft = () => {
    // Format for Facebook - shorter version
    const fbFormatted = formatForFacebook(generatedStatement);
    navigator.clipboard.writeText(fbFormatted);

    // Open Facebook in new tab (main feed to create post)
    window.open('https://www.facebook.com/', '_blank');

    alert("✅ Statement copied to clipboard!\n\nFacebook has opened in a new tab.\nPress Ctrl+V (or Cmd+V) to paste your draft post.");
  };

  const handleExportToDoc = async () => {
    if (!docLink) {
      alert("Please enter your Google Docs or Microsoft Word link");
      return;
    }

    setIsExporting(true);

    // Simulate export (replace with actual API integration)
    setTimeout(() => {
      setIsExporting(false);
      alert(`Statement exported to: ${docLink}`);
    }, 2000);
  };

  return (
    <Card className="space-y-5 border border-violet-200 bg-gradient-to-br from-violet-50 to-white p-5">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100">
          <Mic className="h-4 w-4 text-violet-600" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-slate-900">Official Statement Generator</h3>
          <p className="text-xs text-slate-500 flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-amber-500" />
            AI-powered responses for media & public communications
          </p>
        </div>
      </div>

      {/* Template Selection */}
      <div className="space-y-2">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Select Statement Type
        </label>
        <div className="grid gap-2 sm:grid-cols-2">
          {STATEMENT_TEMPLATES.map((template) => (
            <button
              key={template.id}
              onClick={() => setSelectedTemplate(template.id)}
              className={`rounded-xl border px-3 py-2.5 text-left transition-all ${
                selectedTemplate === template.id
                  ? "border-violet-500 bg-violet-50 ring-1 ring-violet-500"
                  : "border-slate-200 bg-white hover:border-violet-300"
              }`}
            >
              <span className={`text-sm font-medium ${
                selectedTemplate === template.id ? "text-violet-700" : "text-slate-700"
              }`}>
                {template.name}
              </span>
              <p className="text-[11px] text-slate-500 mt-0.5">{template.description}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Export Options */}
      <div className="space-y-3">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-400">
          Export Options (Optional)
        </label>

        {/* Document Link Input */}
        <div className="relative">
          <LinkIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={docLink}
            onChange={(e) => setDocLink(e.target.value)}
            placeholder="Paste Google Docs or Word Online link..."
            className="w-full rounded-lg border border-slate-200 bg-white pl-10 pr-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500"
          />
        </div>

        {/* Facebook Draft Toggle */}
        <label className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white px-3 py-2.5 cursor-pointer hover:border-violet-300 transition-colors">
          <input
            type="checkbox"
            checked={exportToFacebook}
            onChange={(e) => setExportToFacebook(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500"
          />
          <div className="flex items-center gap-2">
            <Facebook className="h-4 w-4 text-blue-600" />
            <span className="text-sm text-slate-700">Create Facebook draft post</span>
          </div>
        </label>

        <p className="text-[10px] text-slate-400">
          Supports: Google Docs, Microsoft Word Online, Notion, Facebook
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Generate Button */}
      <KeyboardButton
        variant="primary"
        size="md"
        fullWidth
        icon={<Wand2 className="h-4 w-4" />}
        onClick={handleGenerate}
        disabled={isGenerating}
      >
        {isGenerating ? "AI Generating Statement..." : "Generate Official Statement"}
      </KeyboardButton>

      {/* Generated Statement */}
      {generatedStatement && (
        <div className="space-y-3 pt-2 animate-fade-in">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Generated Statement
              </span>
              <span className="text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                AI Generated
              </span>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
              {generatedStatement}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2">
            <div className="flex flex-col sm:flex-row gap-3">
              <KeyboardButton
                variant="secondary"
                size="sm"
                icon={<Copy className="h-3.5 w-3.5" />}
                onClick={handleCopy}
                fullWidth
              >
                {copied ? "Copied!" : "Copy Text"}
              </KeyboardButton>

              {docLink && (
                <KeyboardButton
                  variant="primary"
                  size="sm"
                  icon={<ExternalLink className="h-3.5 w-3.5" />}
                  onClick={handleExportToDoc}
                  disabled={isExporting}
                  fullWidth
                >
                  {isExporting ? "Exporting..." : "Export to Doc"}
                </KeyboardButton>
              )}
            </div>

            {exportToFacebook && (
              <KeyboardButton
                variant="primary"
                size="sm"
                icon={<Facebook className="h-3.5 w-3.5" />}
                onClick={handleFacebookDraft}
                fullWidth
              >
                Create Facebook Draft
              </KeyboardButton>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}

// Helper function to format statement for Facebook
function formatForFacebook(statement: string): string {
  // Extract key message (first paragraph or first 500 chars)
  const paragraphs = statement.split('\n\n');
  let mainMessage = paragraphs[0] || statement;

  // Truncate if too long (Facebook optimal is 40-80 chars for preview, but posts can be longer)
  if (mainMessage.length > 800) {
    mainMessage = mainMessage.substring(0, 800) + '...';
  }

  // Add hashtags for civic engagement
  const hashtags = '#BaguioCity #CityGovernment #PublicService';

  return `${mainMessage}\n\n${hashtags}`;
}
