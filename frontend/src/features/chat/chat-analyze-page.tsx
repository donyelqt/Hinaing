"use client";

import React from "react";
import { Send, RefreshCw, Sparkles, User, Menu, X, BarChart3, Shield, FileText, ArrowRight } from "lucide-react";
import clsx from "clsx";
import { Sidebar } from "../shared/components";
import { ActivePage } from "../shared/types/navigation";

// --- Types ---

interface AnalysisSource {
    title: string;
    snippet: string;
    url?: string | null;
    sentiment?: string | null;
    credibility_score?: number | null;
    credibility_tier?: string | null;
    verification_status?: string | null;
}

interface AnalysisInsight {
    category: string;
    title: string;
    detail: string;
    evidence: string[];
}

interface SimpleSource {
    title: string;
    url: string | null;
}

interface AnalysisData {
    mode?: "analyze" | "simple" | "followup" | "simple_fallback";
    session_id?: string;
    overall_sentiment?: {
        label: string;
        summary: string;
        scores?: { positive: number; negative: number; neutral: number };
    };
    insights?: AnalysisInsight[];
    sources?: AnalysisSource[];
    credibility?: {
        avg_score: number;
        high_percent: number;
        low_percent: number;
    };
    document_count?: number;
    insights_count?: number;
    alerts?: string[];
}

interface StreamEvent {
    type: "progress" | "result" | "error";
    stage: string;
    message: string;
    progress: number;
    data?: AnalysisData;
}

interface Message {
    role: "user" | "model";
    content: string;
    isStreaming?: boolean;
    streamProgress?: number;
    streamStage?: string;
    data?: AnalysisData;
}

interface ChatAnalyzePageProps {
    onNavigate?: (page: ActivePage) => void;
}

// --- Components ---

function HLogo({ className }: { className?: string }) {
    return (
        <span
            className={clsx(
                "flex items-center justify-center rounded-full bg-gradient-to-tr from-hinaing-blue-500 via-hinaing-blue-600 to-violet-500 font-semibold tracking-tight text-white shadow-subtle shrink-0",
                className
            )}
        >
            H
        </span>
    );
}

function ProgressIndicator({ stage, progress, message }: { stage: string; progress: number; message?: string }) {
    const stages = [
        { id: "start", label: "Starting", icon: <Sparkles className="h-4 w-4" /> },
        { id: "query_orchestrator", label: "Query Planning", icon: <FileText className="h-4 w-4" /> },
        { id: "retrieval", label: "Retrieval", icon: <BarChart3 className="h-4 w-4" /> },
        { id: "sentiment", label: "Sentiment", icon: <Sparkles className="h-4 w-4" /> },
        { id: "credibility", label: "Credibility", icon: <Shield className="h-4 w-4" /> },
        { id: "context", label: "Context", icon: <FileText className="h-4 w-4" /> },
        { id: "themes", label: "Insights", icon: <FileText className="h-4 w-4" /> },
    ];

    const currentIndex = stages.findIndex(s => s.id === stage);
    const displayStages = stages.slice(1); // Skip "start" in visual display

    return (
        <div className="w-full max-w-lg mx-auto mb-4 px-2">
            {/* Stage Icons */}
            <div className="flex items-center justify-around mb-4 gap-2">
                {displayStages.map((s, i) => {
                    const isActive = currentIndex > 0 && i <= currentIndex - 1;
                    const isCurrent = currentIndex > 0 && i === currentIndex - 1;
                    return (
                        <div key={s.id} className="flex flex-col items-center gap-1.5 min-w-0">
                            <div
                                className={clsx(
                                    "flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-full transition-all duration-300",
                                    isCurrent
                                        ? "bg-blue-500 text-white ring-2 ring-blue-200 animate-pulse"
                                        : isActive
                                            ? "bg-blue-500 text-white"
                                            : "bg-slate-200 text-slate-400"
                                )}
                            >
                                {s.icon}
                            </div>
                            <span className={clsx(
                                "text-[9px] sm:text-[10px] font-medium transition-colors text-center leading-tight",
                                isActive ? "text-blue-600" : "text-slate-400"
                            )}>
                                {s.label}
                            </span>
                        </div>
                    );
                })}
            </div>
            
            {/* Progress Bar */}
            <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                <div
                    className="h-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-500 ease-out"
                    style={{ width: `${progress * 100}%` }}
                />
            </div>
            
            {/* Current Stage Message */}
            <p className="text-xs text-slate-600 text-center mt-3 font-medium">
                {message || stages.find(s => s.id === stage)?.label || "Initializing..."}
            </p>
        </div>
    );
}

function AnalysisResultCard({ data }: { data: AnalysisData }) {
    const [showSources, setShowSources] = React.useState(false);
    const scores = data.overall_sentiment?.scores;
    const cred = data.credibility;

    return (
        <div className="w-full min-w-0 space-y-4 mt-2 overflow-hidden">
            {/* Overall Sentiment Card */}
            <div className="bg-gradient-to-br from-blue-50 to-violet-50 border border-blue-200 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold uppercase tracking-wide text-blue-700 bg-blue-100 px-2 py-1 rounded-full">
                        Overall Sentiment
                    </span>
                    <span className="text-xs text-blue-600">
                        {data.document_count} documents analyzed
                    </span>
                </div>
                
                <h3 className="text-lg font-bold text-blue-900 mb-2 capitalize">
                    {data.overall_sentiment?.label || "Neutral"}
                </h3>
                
                {data.overall_sentiment?.summary && (
                    <p className="text-sm text-slate-600 mb-4">
                        {data.overall_sentiment.summary}
                    </p>
                )}

                {/* Sentiment Scores */}
                {scores && (
                    <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-xl font-bold text-rose-600">{scores.negative}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Negative</p>
                        </div>
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-xl font-bold text-slate-600">{scores.neutral}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Neutral</p>
                        </div>
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-xl font-bold text-emerald-600">{scores.positive}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Positive</p>
                        </div>
                    </div>
                )}

                {/* Credibility Scores */}
                {cred && (
                    <div className="grid grid-cols-3 gap-2 text-center mt-2">
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-lg font-bold text-slate-700">{cred.avg_score}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Credibility</p>
                        </div>
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-lg font-bold text-emerald-600">{cred.high_percent}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Verified</p>
                        </div>
                        <div className="bg-white/70 rounded-lg p-2 shadow-inner">
                            <p className="text-lg font-bold text-rose-600">{cred.low_percent}%</p>
                            <p className="text-[10px] uppercase text-slate-500">Review</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Actionable Insights */}
            {data.insights && data.insights.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-xl p-4">
                    <h4 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                        <FileText className="h-4 w-4 text-violet-500" />
                        Actionable Insights
                    </h4>
                    <div className="space-y-3">
                        {data.insights.map((insight, i) => (
                            <div key={i} className="border-l-2 border-violet-300 pl-3">
                                <span className="text-[10px] font-semibold uppercase text-violet-600 bg-violet-50 px-2 py-0.5 rounded">
                                    {insight.category}
                                </span>
                                <p className="text-sm font-medium text-slate-800 mt-1">{insight.title}</p>
                                <p className="text-xs text-slate-600 mt-0.5">{insight.detail}</p>
                                {insight.evidence.length > 0 && (
                                    <div className="mt-1 flex flex-col gap-1">
                                        {insight.evidence.map((ev, j) => (
                                            <a
                                                key={j}
                                                href={ev}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="text-[10px] text-blue-600 hover:underline break-all"
                                            >
                                                {ev}
                                            </a>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Sources Toggle */}
            {data.sources && data.sources.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-xl p-4 overflow-hidden">
                    <button
                        onClick={() => setShowSources(!showSources)}
                        className="w-full flex items-center justify-between text-sm font-medium text-slate-700 hover:text-blue-600"
                    >
                        <span className="flex items-center gap-2">
                            <BarChart3 className="h-4 w-4" />
                            Supporting Conversations ({data.sources.length})
                        </span>
                        <span className="text-xs">{showSources ? "Hide" : "Show"}</span>
                    </button>

                    {showSources && (
                        <div className="mt-3 space-y-2 max-h-[300px] overflow-y-auto overflow-x-hidden">
                            {data.sources.map((source, i) => (
                                <div key={i} className="border border-slate-100 rounded-lg p-3 bg-slate-50 overflow-hidden">
                                    <div className="flex items-start justify-between gap-2">
                                        <div className="flex-1 min-w-0 overflow-hidden">
                                            <p className="text-sm font-medium text-slate-800 truncate">{source.title}</p>
                                            <p className="text-xs text-slate-500 line-clamp-2 mt-0.5">{source.snippet}</p>
                                        </div>
                                        <div className="flex flex-col items-end gap-1 shrink-0">
                                            {source.sentiment && (
                                                <span className={clsx(
                                                    "text-[10px] px-2 py-0.5 rounded-full font-medium whitespace-nowrap",
                                                    source.sentiment === "positive" && "bg-emerald-100 text-emerald-700",
                                                    source.sentiment === "negative" && "bg-rose-100 text-rose-700",
                                                    source.sentiment === "neutral" && "bg-slate-100 text-slate-600"
                                                )}>
                                                    {source.sentiment}
                                                </span>
                                            )}
                                            {source.credibility_score && (
                                                <span className="text-[10px] text-slate-500 whitespace-nowrap">
                                                    {Math.round(source.credibility_score * 100)}% cred
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                    {source.url && (
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="text-[10px] text-blue-600 hover:underline mt-1 inline-block truncate max-w-full"
                                        >
                                            View Source →
                                        </a>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Alerts */}
            {data.alerts && data.alerts.length > 0 && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <h4 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-2">
                        ⚠️ Alerts
                    </h4>
                    <ul className="space-y-1">
                        {data.alerts.map((alert, i) => (
                            <li key={i} className="text-xs text-amber-700">• {alert}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

function WelcomeScreen({ onPromptSelect }: { onPromptSelect: (prompt: string) => void }) {
    const [greeting, setGreeting] = React.useState("Hello");
    
    React.useEffect(() => {
        const hour = new Date().getHours();
        setGreeting(hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening");
    }, []);

    const analysisSuggestions = [
        "Analyze public sentiment about safety in Baguio",
        "What's the current sentiment on infrastructure issues?",
    ];

    const simpleSuggestions = [
        "What is the Panagbenga Festival?",
        "How many hospitals are in Baguio City?",
    ];

    return (
        <div className="flex flex-col items-center justify-center h-full max-w-2xl mx-auto px-4 animate-in fade-in zoom-in-95 duration-500">
            <div className="mb-8 relative">
                <div className="absolute inset-0 bg-blue-500/20 blur-2xl rounded-full" />
                <HLogo className="h-16 w-16 text-2xl relative z-10 shadow-xl" />
            </div>

            <h2 className="text-2xl font-semibold text-slate-800 mb-2 text-center">
                {greeting}, Baguio.
            </h2>
            <p className="text-slate-500 text-center mb-2 max-w-md">
                I <span className="font-semibold text-blue-600">intelligently route</span> your questions to the right system.
            </p>
            <p className="text-xs text-slate-400 text-center mb-8 max-w-md">
                Ask for sentiment analysis → 6-agent pipeline | Quick Q&A → Fast search
            </p>

            {/* Analysis Suggestions */}
            <p className="text-xs font-semibold text-violet-600 mb-2 w-full">📊 Run Sentiment Analysis</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full mb-4">
                {analysisSuggestions.map((prompt: string, i: number) => (
                    <button
                        key={`analysis-${i}`}
                        onClick={() => onPromptSelect(prompt)}
                        className="text-left p-4 rounded-xl border border-violet-200 bg-violet-50/50 hover:border-violet-400 hover:shadow-md transition-all group"
                    >
                        <p className="text-sm font-medium text-violet-700 group-hover:text-violet-900 transition-colors">
                            {prompt}
                        </p>
                    </button>
                ))}
            </div>

            {/* Simple Q&A Suggestions */}
            <p className="text-xs font-semibold text-emerald-600 mb-2 w-full">💬 Quick Q&A</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {simpleSuggestions.map((prompt: string, i: number) => (
                    <button
                        key={`simple-${i}`}
                        onClick={() => onPromptSelect(prompt)}
                        className="text-left p-4 rounded-xl border border-emerald-200 bg-emerald-50/50 hover:border-emerald-400 hover:shadow-md transition-all group"
                    >
                        <p className="text-sm font-medium text-emerald-700 group-hover:text-emerald-900 transition-colors">
                            {prompt}
                        </p>
                    </button>
                ))}
            </div>
        </div>
    );
}

function MessageBubble({ msg }: { msg: Message }) {
    const isUser = msg.role === "user";

    return (
        <div className={clsx("flex gap-4 w-full max-w-3xl mx-auto mb-6", isUser ? "justify-end" : "justify-start")}>

            {/* AI Avatar */}
            {!isUser && (
                <div className="mt-1">
                    <HLogo className={clsx("h-8 w-8 text-xs", msg.isStreaming && "animate-pulse")} />
                </div>
            )}

            <div
                className={clsx(
                    "flex flex-col gap-2 rounded-2xl p-4 text-sm shadow-sm transition-all max-w-full overflow-hidden",
                    isUser
                        ? "bg-slate-900 text-slate-50 rounded-tr-none ml-12"
                        : "bg-white border border-slate-100 text-slate-700 rounded-tl-none mr-12 shadow-sm"
                )}
            >
                {/* Progress Bar for Streaming */}
                {msg.isStreaming && msg.streamProgress !== undefined && (
                    <ProgressIndicator
                        stage={msg.streamStage || "start"}
                        progress={msg.streamProgress}
                        message={msg.content}
                    />
                )}

                {/* Hide text content while streaming OR when rich analysis card is shown */}
                {!msg.isStreaming && !(msg.data?.mode === "analyze" && msg.data.overall_sentiment) && (
                <div className="leading-relaxed text-sm space-y-1">
                    {msg.content.split('\n').map((line, i) => {
                        const trimLine = line.trim();

                        // Handle Headers
                        if (trimLine.startsWith('#')) {
                            return (
                                <h3 key={i} className={clsx("font-bold mt-3 mb-1 text-base", isUser ? "text-slate-100" : "text-slate-800")}>
                                    {trimLine.replace(/^#+\s*/, '')}
                                </h3>
                            );
                        }

                        // Handle Bullet Points
                        if (trimLine.startsWith('* ') || trimLine.startsWith('- ')) {
                            const content = trimLine.substring(2);
                            const parts = content.split(/(\*\*.*?\*\*)/g);
                            return (
                                <div key={i} className="flex gap-2 ml-1">
                                    <span className={clsx("mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0", isUser ? "bg-slate-400" : "bg-blue-400")} />
                                    <div>
                                        {parts.map((part, j) => {
                                            if (part.startsWith('**') && part.endsWith('**')) {
                                                return <strong key={j} className={clsx("font-semibold", isUser ? "text-white" : "text-slate-900")}>{part.slice(2, -2)}</strong>;
                                            }
                                            return <span key={j}>{part}</span>;
                                        })}
                                    </div>
                                </div>
                            );
                        }

                        // Handle Normal Text (with bold parser)
                        const parts = line.split(/(\*\*.*?\*\*)/g);
                        return (
                            <div key={i} className={clsx("min-h-[1.2em]", trimLine === "" ? "h-2" : "")}>
                                {parts.map((part, j) => {
                                    if (part.startsWith('**') && part.endsWith('**')) {
                                        return <strong key={j} className={clsx("font-semibold", isUser ? "text-white" : "text-slate-900")}>{part.slice(2, -2)}</strong>;
                                    }
                                    return <span key={j}>{part}</span>;
                                })}
                            </div>
                        );
                    })}
                </div>
                )}

                {/* Sources for Simple Q&A mode */}
                {(msg.data?.mode === "simple" || msg.data?.mode === "simple_fallback") && msg.data.sources && msg.data.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100/50">
                        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Sources</p>
                        <div className="flex flex-wrap gap-2">
                            {(msg.data.sources as SimpleSource[]).map((source, idx) => (
                                source.url && (
                                    <a
                                        key={idx}
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-1.5 rounded-md bg-slate-50 px-2 py-1 text-xs text-slate-600 transition hover:bg-slate-100 hover:text-blue-600 border border-slate-200"
                                    >
                                        <span className="truncate max-w-[150px]">{source.title}</span>
                                        <ArrowRight className="h-3 w-3 opacity-50" />
                                    </a>
                                )
                            ))}
                        </div>
                    </div>
                )}

                {/* Rich Analysis Results Card */}
                {msg.data?.mode === "analyze" && msg.data.overall_sentiment && (
                    <AnalysisResultCard data={msg.data} />
                )}
            </div>

            {/* User Avatar */}
            {isUser && (
                <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-slate-500 shrink-0">
                    <User className="h-4 w-4" />
                </div>
            )}
        </div>
    );
}

// --- Main Page ---

export function ChatAnalyzePage({ onNavigate }: ChatAnalyzePageProps) {
    const [input, setInput] = React.useState("");
    const [messages, setMessages] = React.useState<Message[]>([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);
    const [sessionId, setSessionId] = React.useState<string | null>(null);

    const bottomRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    const handleSubmit = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg: Message = { role: "user", content: input };
        setMessages((prev) => [...prev, userMsg]);
        setInput("");
        setIsLoading(true);

        // Add initial streaming message
        setMessages((prev) => [...prev, {
            role: "model",
            content: "🔄 Starting multi-agent analysis...",
            isStreaming: true,
            streamProgress: 0,
            streamStage: "start"
        }]);

        try {
            const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

            // Build conversation history for context
            const history = messages.map(m => ({
                role: m.role === "model" ? "assistant" : "user",
                content: m.content
            }));

            const response = await fetch(`${apiBase}/chat/analyze`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: userMsg.content,
                    session_id: sessionId,
                    history: history,
                    platforms: ["web"],
                    time_window: "24h"
                })
            });

            if (!response.ok) throw new Error("Analysis failed");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) throw new Error("No response stream");

            let finalResult: StreamEvent | null = null;

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value);
                const lines = text.split('\n').filter(l => l.trim());

                for (const line of lines) {
                    try {
                        const event: StreamEvent = JSON.parse(line);

                        if (event.type === "progress") {
                            setMessages((prev) => {
                                const updated = [...prev];
                                const lastIdx = updated.length - 1;
                                if (updated[lastIdx]?.isStreaming) {
                                    updated[lastIdx] = {
                                        ...updated[lastIdx],
                                        content: event.message,
                                        streamProgress: event.progress,
                                        streamStage: event.stage
                                    };
                                }
                                return updated;
                            });
                        } else if (event.type === "result") {
                            finalResult = event;
                        } else if (event.type === "error") {
                            setMessages((prev) => {
                                const updated = [...prev];
                                const lastIdx = updated.length - 1;
                                if (updated[lastIdx]?.isStreaming) {
                                    updated[lastIdx] = {
                                        role: "model",
                                        content: event.message,
                                        isStreaming: false
                                    };
                                }
                                return updated;
                            });
                        }
                    } catch (parseErr) {
                        console.warn("Failed to parse stream line:", line);
                    }
                }
            }

            // Update with final result
            if (finalResult) {
                // Capture session_id for follow-up questions
                if (finalResult.data?.session_id) {
                    setSessionId(finalResult.data.session_id);
                }

                setMessages((prev) => {
                    const updated = [...prev];
                    const lastIdx = updated.length - 1;
                    if (updated[lastIdx]?.isStreaming) {
                        updated[lastIdx] = {
                            role: "model",
                            content: finalResult!.message,
                            isStreaming: false,
                            data: finalResult!.data
                        };
                    }
                    return updated;
                });
            }

        } catch (err) {
            console.error(err);
            setMessages((prev) => {
                const updated = [...prev];
                const lastIdx = updated.length - 1;
                if (updated[lastIdx]?.isStreaming) {
                    updated[lastIdx] = {
                        role: "model",
                        content: "❌ Analysis failed. Please try again.",
                        isStreaming: false
                    };
                }
                return updated;
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handlePromptSelect = (prompt: string) => {
        setInput(prompt);
    };

    return (
        <>
            {/* Mobile Hamburger */}
            <button
                type="button"
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="fixed top-4 right-4 z-50 inline-flex items-center justify-center rounded-full bg-white p-3 text-slate-700 shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 active:scale-95 transition-all lg:hidden"
                aria-label={isSidebarOpen ? "Close menu" : "Open menu"}
                aria-expanded={isSidebarOpen}
            >
                {isSidebarOpen ? (
                    <X className="h-6 w-6" aria-hidden="true" />
                ) : (
                    <Menu className="h-6 w-6" aria-hidden="true" />
                )}
            </button>

            <div className="min-h-screen bg-slate-50 font-sans selection:bg-blue-100">
                <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-0 sm:px-6 lg:flex-row lg:gap-8 lg:px-8 lg:py-10 xl:px-12">

                    <Sidebar
                        activePage="analyze"
                        isSidebarOpen={isSidebarOpen}
                        onNavigate={onNavigate}
                        onCloseSidebar={() => setIsSidebarOpen(false)}
                        onOpenMobileFilters={() => setIsSidebarOpen(true)}
                    />

                    {/* Main Content Area */}
                    <main className="order-1 flex w-full min-w-0 flex-col gap-4 lg:order-2 lg:flex-1 lg:gap-6 xl:gap-8 lg:h-[calc(100vh-4rem)] h-[85vh] relative">

                        {/* Chat Container */}
                        <div className="flex flex-col h-full bg-white/50 backdrop-blur-sm rounded-3xl border border-slate-200/60 shadow-sm overflow-hidden relative">

                            {/* Scrollable Messages */}
                            <div className="flex-1 overflow-y-auto w-full scroll-smooth p-4 sm:p-6">
                                {messages.length === 0 ? (
                                    <WelcomeScreen onPromptSelect={handlePromptSelect} />
                                ) : (
                                    <div className="w-full max-w-4xl mx-auto pb-4 pt-4">
                                        {messages.map((msg, i) => (
                                            <MessageBubble key={i} msg={msg} />
                                        ))}
                                        <div ref={bottomRef} />
                                    </div>
                                )}
                            </div>

                            {/* Input Area */}
                            <div className="p-4 sm:p-6 bg-white/80 border-t border-slate-100 z-10">
                                <div className="max-w-3xl mx-auto relative group">
                                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-300 via-violet-300 to-blue-300 rounded-2xl opacity-20 group-hover:opacity-40 transition blur duration-500"></div>
                                    <form
                                        onSubmit={handleSubmit}
                                        className="relative flex items-center bg-white rounded-xl shadow-lg border border-slate-100 p-2 transition-all focus-within:ring-2 focus-within:ring-blue-100"
                                    >
                                        <div className="pl-3 pr-2 text-slate-400">
                                            <Sparkles className="h-5 w-5" />
                                        </div>
                                        <input
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            placeholder="Ask about Baguio or analyze sentiment..."
                                            className="flex-1 bg-transparent border-none outline-none text-slate-800 placeholder:text-slate-400 text-sm h-10 px-2"
                                            disabled={isLoading}
                                        />
                                        <button
                                            type="submit"
                                            disabled={!input.trim() || isLoading}
                                            className={clsx(
                                                "p-2 rounded-lg transition-all duration-200",
                                                input.trim() && !isLoading
                                                    ? "bg-blue-600 text-white shadow-md hover:bg-blue-700 hover:scale-105"
                                                    : "bg-slate-100 text-slate-300 cursor-not-allowed"
                                            )}
                                        >
                                            {isLoading ? (
                                                <RefreshCw className="h-5 w-5 animate-spin" />
                                            ) : (
                                                <Send className="h-5 w-5" />
                                            )}
                                        </button>
                                    </form>
                                    <p className="text-center text-[10px] text-slate-400 mt-2 font-medium">
                                        Smart routing: Sentiment analysis → 6-agent pipeline | Q&A → Fast search
                                    </p>
                                </div>
                            </div>

                        </div>
                    </main>
                </div>
            </div>
        </>
    );
}
