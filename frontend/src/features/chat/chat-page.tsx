"use client";

import React from "react";
import { Send, StopCircle, RefreshCw, Sparkles, User, ArrowRight, Menu, X } from "lucide-react";
import clsx from "clsx";
import { apiPost } from "@/lib/api";
import { Sidebar } from "../shared/components";
import { ActivePage } from "../shared/types/navigation";

// --- Types ---

interface Message {
    role: "user" | "model";
    content: string;
    sources?: Array<{ title: string; url: string }>;
}

interface ChatPageProps {
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

function WelcomeScreen({ onPromptSelect }: { onPromptSelect: (prompt: string) => void }) {
    const hour = new Date().getHours();
    const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";

    const suggestions = [
        "What are the top concerns in Baguio today?",
        "Explain the current sentiment on traffic.",
        "Are there any flood warnings near Irisan?",
        "Summarize recent Reddit discussions about tourism."
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
            <p className="text-slate-500 text-center mb-8 max-w-md">
                I'm your Baguio-specific AI analyst. Ask me anything about local civic updates, sentiment trends, or real-time news.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
                {suggestions.map((prompt, i) => (
                    <button
                        key={i}
                        onClick={() => onPromptSelect(prompt)}
                        className="text-left p-4 rounded-xl border border-slate-200 bg-white hover:border-blue-300 hover:shadow-md transition-all group"
                    >
                        <p className="text-sm font-medium text-slate-700 group-hover:text-blue-700 transition-colors">
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
                    <HLogo className="h-8 w-8 text-xs" />
                </div>
            )}

            <div
                className={clsx(
                    "flex flex-col gap-2 rounded-2xl p-4 text-sm shadow-sm transition-all",
                    isUser
                        ? "bg-slate-900 text-slate-50 rounded-tr-none ml-12"
                        : "bg-white border border-slate-100 text-slate-700 rounded-tl-none mr-12 shadow-sm"
                )}
            >
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

                {/* Sources Footer */}
                {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-100/50">
                        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Sources</p>
                        <div className="flex flex-wrap gap-2">
                            {msg.sources.map((source, idx) => (
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
                            ))}
                        </div>
                    </div>
                )}
            </div>

            {/* User Avatar (Optional, placeholder) */}
            {isUser && (
                <div className="mt-1 flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-slate-500 shrink-0">
                    <User className="h-4 w-4" />
                </div>
            )}
        </div>
    );
}

// --- Main Page ---

export function ChatPage({ onNavigate }: ChatPageProps) {
    const [input, setInput] = React.useState("");
    const [messages, setMessages] = React.useState<Message[]>([]);
    const [isLoading, setIsLoading] = React.useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = React.useState(false);

    // We rely on Main Layout's mobile toggle logic, but keep local state for Sidebar prop compatibility

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

        try {
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            interface ChatPayload {
                message: string;
                history: Array<{ role: string; content: string }>;
                jurisdiction: string;
            }

            interface ChatResponse {
                response: string;
                sources: Array<{ title: string; url: string }>;
            }

            const response = await apiPost<ChatPayload, ChatResponse>("/chat/", {
                message: userMsg.content,
                history,
                jurisdiction: "Baguio City",
            });

            const aiMsg: Message = {
                role: "model",
                content: response.response,
                sources: response.sources
            };
            setMessages((prev) => [...prev, aiMsg]);
        } catch (err) {
            console.error(err);
            setMessages((prev) => [
                ...prev,
                { role: "model", content: "I encountered an error connecting to the knowledge base. Please try again." },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handlePromptSelect = (prompt: string) => {
        // Auto-fill logic
        setInput(prompt);
    };

    return (
        <>
            {/* Mobile Hamburger (Mirrors SentimentGeneratorPage logic) */}
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
                        activePage="chat"
                        isSidebarOpen={isSidebarOpen}
                        onNavigate={onNavigate}
                        onCloseSidebar={() => setIsSidebarOpen(false)}
                        onOpenMobileFilters={() => setIsSidebarOpen(true)}
                    />

                    {/* Main Content Area (Matches Dashboard Layout) */}
                    <main className="order-1 flex w-full min-w-0 flex-col gap-4 lg:order-2 lg:flex-1 lg:gap-6 xl:gap-8 lg:h-[calc(100vh-4rem)] h-[85vh] relative">

                        {/* Chat Container - Card-like appearance to sit nicely in the layout */}
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

                                        {isLoading && (
                                            <div className="flex gap-4 w-full max-w-3xl mx-auto mb-6">
                                                <div className="mt-1">
                                                    <HLogo className="h-8 w-8 text-xs animate-pulse" />
                                                </div>
                                                <div className="flex items-center gap-2 text-slate-400 text-sm italic pt-2">
                                                    <Sparkles className="h-4 w-4 animate-spin text-blue-400" />
                                                    <span>Thinking...</span>
                                                </div>
                                            </div>
                                        )}
                                        <div ref={bottomRef} />
                                    </div>
                                )}
                            </div>

                            {/* Input Area (Pinned to bottom of the card) */}
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
                                            placeholder="Ask about Baguio civic data..."
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
                                        Hinaing AI can make mistakes. Verify important civic information.
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
