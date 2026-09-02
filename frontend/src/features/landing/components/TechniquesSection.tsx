import { Card } from "@/components/ui/card";
import { Brain, Cpu, Database, Zap, Users, Wrench, Repeat, Search, Sparkles, Award, Quote, ShieldCheck, Ban } from "lucide-react";

export function TechniquesSection() {
  const techniques = [
    {
      id: "SYS-01",
      title: "Multi-Agent AI System",
      description: "19-agent hierarchical architecture built on a dependency-aware DAG, orchestrating core processes and expandable theme-specific agents.",
      icon: Users,
      isNovel: true,
      color: "text-violet-500 bg-violet-50 border-violet-100",
      tilt: "-rotate-1",
    },
    {
      id: "AGT-02",
      title: "Agentic & Intelligent Search",
      description: "Combines ReAct-based query planning with neural semantic reranking to autonomously formulate strategies and prioritize high-relevance results.",
      icon: Search,
      color: "text-fuchsia-500 bg-fuchsia-50 border-fuchsia-100",
      tilt: "rotate-1",
    },
    {
      id: "NLP-03",
      title: "Hybrid Sentiment Analysis",
      description: "Hybrid ensemble combining RoBERTa (social media-optimized) with Gemini LLM for sentiment analysis, achieving 60%+ model agreement rate and 98% ensemble accuracy.",
      icon: Brain,
      color: "text-blue-500 bg-blue-50 border-blue-100",
      tilt: "-rotate-1",
    },
    {
      id: "AML-04",
      title: "Semantic Similarity",
      description: "Semantic similarity using BGE sentence transformers for efficient document retrieval, enabling real-time content classification and clustering.",
      icon: Cpu,
      color: "text-emerald-500 bg-emerald-50 border-emerald-100",
      tilt: "rotate-2",
    },
    {
      id: "CTX-05",
      title: "Temporal-Aware Context Engineering",
      description: "Agentic seasonal query generation that dynamically tailors search based on civic calendar patterns (Panagbenga in February, typhoons in June).",
      icon: Wrench,
      color: "text-amber-500 bg-amber-50 border-amber-100",
      tilt: "-rotate-2",
      isNovel: true,
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
      description: "Cyclic memory with two learning loops: Memory Persistence consolidates insights to long-term storage, Smart Reuse caches enriched analysis for 81% API savings and 35% speedup.",
      icon: Repeat,
      color: "text-indigo-500 bg-indigo-50 border-indigo-100",
      tilt: "-rotate-1",
      isNovel: true,
    },
    {
      id: "CRD-08",
      title: "Hierarchical Sub-Agent Spawning for Hinaing Verification",
      description: "Parent agent spawns 5 independent sub-agents for source quality filtering: domain trust, cross-reference, fact-check, LLM analysis, and web verification.",
      icon: Zap,
      color: "text-rose-500 bg-rose-50 border-rose-100",
      tilt: "rotate-2",
      isNovel: true,
    },
    {
      id: "FTH-09",
      title: "Contextual Faithfulness Verification Agent",
      description: "FaithfulnessAgent extracts claims and verifies them against source documents using NLI, measuring hallucination rate and source attribution.",
      icon: ShieldCheck,
      isNovel: true,
      color: "text-amber-500 bg-amber-50 border-amber-100",
      tilt: "-rotate-1",
    },
    {
      id: "CIT-10",
      title: "Epistemic Authority Encoding (Neuro-Symbolic)",
      description: "Neuro-symbolic constrained generation: Symbolic rules (VSEE thresholds, prompt constraints) prioritize AI-verified sources (Tavily AI web search, VSEE consensus) for neural LLM generation. Citations include source URL, credibility score, and sentiment: [Src: pia.gov.ph | Cred: 0.95 | Sent: Positive].",
      icon: Quote,
      isNovel: true,
      color: "text-teal-500 bg-teal-50 border-teal-100",
      tilt: "rotate-1",
    },
    //{
      //id: "HAL-11",
      //title: "Hallucination Detection",
      //description: "Multi-layer verification through entailment checking and 5-signal credibility scoring detects and flags unsupported claims.",
      //icon: Ban,
      //isNovel: true,
      //color: "text-slate-500 bg-slate-50 border-slate-100",
      //tilt: "-rotate-2",
    //},
    {
      id: "VSEE-11",
      title: "Vector-Symbolic Epistemic Entailment",
      description: "Mathematical bypass of external APIs when internal consensus is strong (crossref ≥0.70, domain ≥0.45), solving Infused Logic Knowledge Graph by Wuhan University without heavy symbolic logic.",
      icon: Zap,
      isNovel: true,
      color: "text-orange-500 bg-orange-50 border-orange-100",
      tilt: "rotate-1",
    },
    {
      id: "TRF-12",
      title: "Temporal-Aware Rank Fusion",
      description: "Hybrid search combining dense + BM25 with temporal boosting for seasonal relevance (Panagbenga, typhoon season, holidays).",
      icon: Repeat,
      isNovel: true,
      color: "text-lime-500 bg-lime-50 border-lime-100",
      tilt: "-rotate-1",
    },
    {
      id: "MEM-13",
      title: "Self-Learning Concern Memory",
      description: "6 isolated Qdrant collections with 7-day TTL auto-regeneration, creating adaptive agents that learn from previous cycles.",
      icon: Database,
      isNovel: true,
      color: "text-indigo-500 bg-indigo-50 border-indigo-100",
      tilt: "rotate-2",
    },
  ];

  return (
    <section id="techniques" className="relative bg-slate-50 bg-grid-pattern py-24 border-t border-slate-200">
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 xl:px-8">
        <div className="mb-20 max-w-2xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center justify-center -space-x-px rounded-md border border-violet-100 bg-white p-1 shadow-sm">
            <span className="px-3 py-1 text-[10px] font-mono font-medium uppercase tracking-widest text-[#3348b8]">System Architecture</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            <span className="bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] bg-clip-text text-transparent">Agentic AI Engineering</span> for Civic Intelligence
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Hinaing combines hierarchical multi-agent orchestration with temporal-aware context engineering to transform unstructured social media noise into structured, actionable civic intelligence.
          </p>
        </div>

        <div className="mb-10 flex flex-wrap items-center justify-center gap-4">
          <div className="flex items-center gap-2 rounded-full border border-emerald-100 bg-emerald-50/30 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-600 backdrop-blur-sm">
            <Sparkles className="h-3 w-3 animate-pulse" />
            <span>9 Novel Research Contributions</span>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50/30 px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-blue-600 backdrop-blur-sm">
            <Award className="h-3 w-3" />
            <span>Complete Working System</span>
          </div>
          <div className="h-px w-8 bg-slate-200 hidden sm:block" />
          <p className="text-[10px] font-medium text-slate-400 uppercase tracking-widest">
            Verified by Researchers with Claude Opus 4.5 and Gemini 3.1 Pro
          </p>
        </div>

        {/* Technical Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {techniques.map((technique, index) => {
            const Icon = technique.icon;
            // Check if this is the last item and would be alone on its row
            const isLastItem = index === techniques.length - 1;
            const shouldCenter = isLastItem && techniques.length % 4 === 1;
            
            return (
              <Card
                key={technique.id}
                className={`group relative flex flex-col h-full overflow-hidden rounded-2xl border border-slate-200 bg-white/60 p-6 shadow-sm backdrop-blur-sm transition-all duration-500 hover:z-20 hover:-translate-y-2 hover:border-[#5b3cc8]/40 hover:shadow-[0_12px_32px_-16px_rgba(51,72,184,0.25)] hover:rotate-0 hover:scale-[1.02] ${technique.tilt} ${shouldCenter ? 'lg:col-start-2 lg:col-span-2 lg:mx-auto lg:w-full' : ''}`}
              >
                {/* Gradient Gloss Effect upon Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                {/* ID & Badge Tags */}
                <div className="absolute top-4 right-4 z-10 flex flex-col items-end gap-1">
                  <span className="font-mono text-[10px] font-bold text-slate-300 group-hover:text-[#3348b8] transition-colors">
                    {technique.id}
                  </span>
                  <div className="flex flex-col items-end gap-1">
                    {technique.isNovel && (
                      <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-tighter text-emerald-600 ring-1 ring-inset ring-emerald-600/20 group-hover:bg-emerald-500 group-hover:text-white transition-all">
                        <Sparkles className="h-2 w-2" />
                        Novel
                      </span>
                    )}
                    <span className="inline-flex items-center gap-1 rounded bg-blue-50 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-tighter text-blue-600 ring-1 ring-inset ring-blue-600/20 group-hover:bg-blue-500 group-hover:text-white transition-all">
                      <Award className="h-2 w-2" />
                      Completed
                    </span>
                  </div>
                </div>

                <div className={`relative z-10 mb-6 inline-flex h-12 w-12 items-center justify-center rounded-xl border shadow-sm transition-all duration-300 group-hover:border-[#5b3cc8]/40 group-hover:bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] group-hover:text-white group-hover:scale-110 group-hover:rotate-6 ${technique.color}`}>
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>

                <h3 className="relative z-10 text-base font-bold text-slate-900 mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-[#3348b8] group-hover:to-[#5b3cc8] transition-all">
                  {technique.title}
                </h3>
                <p className="relative z-10 text-sm leading-relaxed text-slate-500 group-hover:text-[#3348b8]">
                  {technique.description}
                </p>
              </Card>
            );
          })}
        </div>

        <div className="mt-16 space-y-8">
          {/* Key Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-w-5xl mx-auto">
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-[#3348b8]">98%</div>
              <div className="text-xs text-slate-500 mt-1">Sentiment Accuracy</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-emerald-600">19</div>
              <div className="text-xs text-slate-500 mt-1">Specialized Agents</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-blue-600">5</div>
              <div className="text-xs text-slate-500 mt-1">Verification Signals</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-rose-600">7</div>
              <div className="text-xs text-slate-500 mt-1">Core Pipeline Nodes</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-purple-600">81%</div>
              <div className="text-xs text-slate-500 mt-1">API Cost Reduction (Smart Reuse)</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-cyan-600">35%</div>
              <div className="text-xs text-slate-500 mt-1">Speed Improvement (Smart Reuse)</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-amber-600">100%</div>
              <div className="text-xs text-slate-500 mt-1">Contextual Faithfulness (Production)</div>
            </div>
            <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200">
              <div className="text-2xl font-bold text-amber-600">100%</div>
              <div className="text-xs text-slate-500 mt-1">Citation Rate (Production)</div>
            </div>
            {/* 0% Hallucination and 97% Agentic Verification Rate - Centered, same size as other metrics */}
            <div className="md:col-span-3 lg:col-span-4">
              <div className="flex justify-center gap-4">
                <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200 flex-1 max-w-[245px]">
                  <div className="text-2xl font-bold text-slate-600">0%</div>
                  <div className="text-xs text-slate-500 mt-1">Fabrication Hallucination (Production)</div>
                </div>
                <div className="text-center p-4 rounded-xl bg-white/60 backdrop-blur border border-slate-200 flex-1 max-w-[245px]">
                  <div className="text-2xl font-bold text-indigo-600">97%</div>
                  <div className="text-xs text-slate-500 mt-1">Agentic Verification Rate (Production)</div>
                </div>
              </div>
            </div>
          </div>

          {/* System Status */}
          <div className="flex justify-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/80 backdrop-blur px-4 py-1.5 text-[10px] font-mono font-semibold text-[#3348b8] shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              SYSTEM_STATUS: ONLINE // 99.9% UPTIME
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}




