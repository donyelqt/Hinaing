import { Card } from "@/components/ui/card";
import { Brain, Cpu, Database, Zap, Users, Wrench, Repeat, Search, Sparkles, Award } from "lucide-react";

export function TechniquesSection() {
  const techniques = [
    {
      id: "SYS-01",
      title: "Multi-Agent AI System",
      description: "A 13-agent hierarchical architecture built on a dependency-aware DAG, orchestrating core processes and expandable theme-specific agents.",
      icon: Users,
      color: "text-violet-500 bg-violet-50 border-violet-100",
      tilt: "-rotate-1",
      isNovel: true,
    },
    {
      id: "AGT-02",
      title: "Agentic/Intelligent Search",
      description: "Combines ReAct-based query planning with neural semantic reranking to autonomously formulate strategies and prioritize high-relevance results.",
      icon: Search,
      color: "text-fuchsia-500 bg-fuchsia-50 border-fuchsia-100",
      tilt: "rotate-1",
      isAdvanced: true,
    },
    {
      id: "NLP-03",
      title: "Deep Learning & NLP",
      description: "Hybrid ensemble combining RoBERTa (social media-optimized) with Gemini LLM for sentiment analysis, achieving 60%+ model agreement rate and 98% model ensemble accuracy.",
      icon: Brain,
      color: "text-blue-500 bg-blue-50 border-blue-100",
      tilt: "-rotate-1",
      isAdvanced: true,
    },
    {
      id: "AML-04",
      title: "Advanced Machine Learning",
      description: "Semantic similarity using BGE sentence transformers for efficient document retrieval, enabling real-time content classification and clustering.",
      icon: Cpu,
      color: "text-emerald-500 bg-emerald-50 border-emerald-100",
      tilt: "rotate-2",
      isAdvanced: true,
    },
    {
      id: "CTX-05",
      title: "Context Engineering",
      description: "Research-driven adaptive context conditioning that dynamically tailors AI analysis based on civic domain focus and evolving conversation contexts.",
      icon: Wrench,
      color: "text-amber-500 bg-amber-50 border-amber-100",
      tilt: "-rotate-2",
      isAdvanced: true,
    },
    {
      id: "RAG-06",
      title: "Retrieval Augmented Gen.",
      description: "Knowledge retrieval from internal memory, cross-reference verification, and fact-checking integration with external APIs.",
      icon: Database,
      color: "text-cyan-500 bg-cyan-50 border-cyan-100",
      tilt: "rotate-1",
    },
    {
      id: "CYC-07",
      title: "Self-Learning Cyclic RAG",
      description: "Continuous learning system that consolidates new information into persistent memory, enabling iterative knowledge refinement.",
      icon: Repeat,
      color: "text-indigo-500 bg-indigo-50 border-indigo-100",
      tilt: "-rotate-1",
      isNovel: true,
    },
    {
      id: "CRD-08",
      title: "Multi-Signal Credibility",
      description: "5-signal ensemble for source quality filtering: domain trust, cross-reference, fact-check API, LLM analysis, and web verification.",
      icon: Zap,
      color: "text-rose-500 bg-rose-50 border-rose-100",
      tilt: "rotate-2",
      isNovel: true,
    },
  ];

  return (
    <section id="techniques" className="relative bg-slate-50 bg-grid-pattern py-24 border-t border-slate-200">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 xl:px-8">
        <div className="mb-20 max-w-2xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center justify-center -space-x-px rounded-md border border-violet-100 bg-white p-1 shadow-sm">
            <span className="px-3 py-1 text-[10px] font-mono font-medium uppercase tracking-widest text-violet-600">System Architecture</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Advanced <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-cyan-500">Agentic AI Techniques</span>
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Hinaing leverages neuro-symbolic AI and hierarchical multi-agent orchestration to transform unstructured digital noise into structured, actionable intelligence.
          </p>
        </div>

        <div className="mb-10 flex flex-wrap items-center justify-center gap-4">
          <div className="flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50/30 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-600 backdrop-blur-sm">
            <Sparkles className="h-3 w-3 animate-pulse" />
            <span>Novel Research</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50/30 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-blue-600 backdrop-blur-sm">
            <Award className="h-3 w-3" />
            <span>Advanced Implementation</span>
          </div>
          <div className="h-px w-8 bg-slate-200 hidden sm:block" />
          <p className="text-[10px] font-medium text-slate-400 uppercase tracking-widest">
            Verified by Claude Opus 4.5 and Gemini 3 Pro
          </p>
        </div>

        {/* Technical Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {techniques.map((technique) => {
            const Icon = technique.icon;

            return (
              <Card
                key={technique.id}
                className={`group relative flex flex-col h-full overflow-hidden rounded-2xl border border-slate-200 bg-white/60 p-6 shadow-sm backdrop-blur-sm transition-all duration-500 hover:z-20 hover:-translate-y-2 hover:border-violet-300 hover:shadow-2xl hover:shadow-violet-200/50 hover:rotate-0 hover:scale-[1.02] ${technique.tilt}`}
              >
                {/* Gradient Gloss Effect upon Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                {/* ID & Badge Tags */}
                <div className="absolute top-4 right-4 z-10 flex flex-col items-end gap-1">
                  <span className="font-mono text-[10px] font-bold text-slate-300 group-hover:text-violet-500 transition-colors">
                    {technique.id}
                  </span>
                  {technique.isNovel && (
                    <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-tighter text-emerald-600 ring-1 ring-inset ring-emerald-600/20 group-hover:bg-emerald-500 group-hover:text-white transition-all">
                      <Sparkles className="h-2 w-2" />
                      Novel
                    </span>
                  )}
                  {technique.isAdvanced && (
                    <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-tighter text-blue-600 ring-1 ring-inset ring-blue-600/20 group-hover:bg-blue-500 group-hover:text-white transition-all">
                      <Award className="h-2 w-2" />
                      Advanced
                    </span>
                  )}
                </div>

                <div className={`relative z-10 mb-6 inline-flex h-12 w-12 items-center justify-center rounded-xl border shadow-sm transition-all duration-300 group-hover:border-violet-200 group-hover:bg-gradient-to-br group-hover:from-violet-500 group-hover:to-cyan-500 group-hover:text-white group-hover:scale-110 group-hover:rotate-6 ${technique.color}`}>
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>

                <h3 className="relative z-10 text-base font-bold text-slate-900 mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-violet-600 group-hover:to-cyan-600 transition-all">
                  {technique.title}
                </h3>
                <p className="relative z-10 text-sm leading-relaxed text-slate-500 group-hover:text-slate-700">
                  {technique.description}
                </p>
              </Card>
            );
          })}
        </div>

        <div className="mt-16 flex justify-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/80 backdrop-blur px-4 py-1.5 text-[10px] font-mono font-semibold text-violet-600 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            SYSTEM_STATUS: ONLINE // 99.9% UPTIME
          </span>
        </div>
      </div>
    </section>
  );
}