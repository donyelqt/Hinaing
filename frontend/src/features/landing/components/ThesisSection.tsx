import { Card } from "@/components/ui/card";
import { GraduationCap, BookOpen, Award, Target, Network, ArrowDown, ArrowRight, Sparkles, GitBranch, Database, Cpu, Brain, Layers } from "lucide-react";

export function ThesisSection() {
  const contributions = [
    { label: "Context Engineering", desc: "KEYWORD_CLUSTERS & variable trust tiers", icon: Layers },
    { label: "Self-Learning Cyclic RAG", desc: "Memory persistence + Smart Reuse for 81% API savings", icon: Database },
    { label: "19-Agent Architecture", desc: "Hierarchical & conditional spawning", icon: Network },
    { label: "Agentic AI with ReAct", desc: "Autonomous reasoning & tool use", icon: Brain },
    { label: "Ensemble Sentiment", desc: "RoBERTa + Gemini fusion tracking", icon: Cpu },
    { label: "5-Signal Credibility", desc: "Multi-modal source verification", icon: Award },
  ];

  return (
    <section id="thesis" className="relative bg-slate-50 bg-grid-pattern py-24 border-t border-slate-200 overflow-hidden">
      {/* Ambient Background Glow */}
      <div className="absolute top-0 right-0 -mt-20 -mr-20 w-[500px] h-[500px] bg-violet-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 -mb-20 -ml-20 w-[500px] h-[500px] bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 xl:px-8">
        {/* Header Section */}
        <div className="mb-20 max-w-3xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center justify-center -space-x-px rounded-md border border-violet-100 bg-white p-1 shadow-sm">
            <span className="px-3 py-1 text-[10px] font-mono font-medium uppercase tracking-widest text-violet-600">
              Academic Research
            </span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-cyan-500">
              AgenticHinaing
            </span>
            <br />
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
            A Self-Learning Temporal-Aware Multi-Agent Framework for Cost Efficiency and Truth Discovery in Public Opinion Analysis
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid gap-8 lg:grid-cols-2 lg:gap-12 items-start">

          {/* Left Column: Research Details */}
          <div className="space-y-6">

            {/* Reach Focus Card */}
            <Card className="group relative overflow-hidden p-6 bg-white/60 backdrop-blur-sm border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-violet-200/50 hover:-translate-y-1 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-violet-100 text-violet-600 group-hover:bg-violet-600 group-hover:text-white transition-colors duration-300">
                  <GraduationCap className="h-6 w-6" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-slate-900">Research Focus</h3>
                  <p className="text-sm text-slate-600 leading-relaxed text-justify">
                    This thesis explores the intersection of <strong>multi-agent systems</strong>, <strong>epistemic truth discovery</strong>, and <strong>civic social listening</strong>. Hinaing represents a novel approach to automated public opinion analysis that combines agentic AI with rigorous credibility verification.
                  </p>
                </div>
              </div>
            </Card>

            {/* Novelty Card */}
            <Card className="group relative overflow-hidden p-6 bg-white/60 backdrop-blur-sm border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-emerald-200/50 hover:-translate-y-1 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-50/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative flex items-start gap-4">
                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-100 text-emerald-600 group-hover:bg-emerald-600 group-hover:text-white transition-colors duration-300">
                  <Sparkles className="h-6 w-6" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-lg font-bold text-slate-900">Novelty & Impact</h3>
                  <p className="text-sm text-slate-600 leading-relaxed text-justify">
                    Unlike traditional sentiment analysis tools, Hinaing implements a <strong>federated multi-agent system</strong> where 18 autonomous agents collaborate to provide verified, context-aware insights. The system learns from each analysis, continuously improving its understanding of civic discourse in Baguio City.
                  </p>
                </div>
              </div>
            </Card>

            {/* Contributions List */}
            <Card className="group relative overflow-hidden p-6 bg-white/60 backdrop-blur-sm border border-slate-200 shadow-sm hover:shadow-xl hover:shadow-blue-200/50 hover:-translate-y-1 transition-all duration-300">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative space-y-4">
                <div className="flex items-center gap-3 mb-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600">
                    <Target className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">Key Contributions</h3>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  {contributions.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100 hover:border-blue-200 hover:bg-blue-50/30 transition-colors">
                      <item.icon className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
                      <div>
                        <p className="text-xs font-bold text-slate-800">{item.label}</p>
                        <p className="text-[10px] text-slate-500 leading-tight">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>

          {/* Right Column: Architecture Visualization */}
          <div className="relative h-full">
            <Card className="h-full p-8 bg-gradient-to-br from-white to-slate-50 border border-slate-200 shadow-lg flex flex-col items-center justify-center relative overflow-hidden">
              {/* Decorative Grid on Card */}
              <div className="absolute inset-0 bg-grid-pattern opacity-50" />

              <div className="relative z-10 w-full max-w-md space-y-8">
                <div className="text-center space-y-2">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-cyan-500 text-white shadow-lg mb-4 transform rotate-3 hover:rotate-6 transition-transform duration-300">
                    <BookOpen className="h-8 w-8" />
                  </div>
                  <h3 className="text-xl font-bold text-slate-900">Thesis Architecture</h3>
                  <p className="text-xs text-slate-500 uppercase tracking-widest font-mono">7-Node Orchestration Graph</p>
                </div>

                {/* Flow Chart Visualization */}
                <div className="flex flex-col items-center space-y-4">
                  {/* Node 1: Orchestrator */}
                  <div className="w-full p-3 rounded-lg border border-violet-200 bg-violet-50 text-center shadow-sm relative group cursor-default hover:border-violet-400 transition-colors">
                    <span className="text-xs font-bold text-violet-700 uppercase tracking-wide">1. Query Orchestrator</span>
                    <div className="absolute left-1/2 -bottom-4 w-px h-4 bg-slate-300 transform -translate-x-1/2"></div>
                    <div className="absolute left-1/2 -bottom-4 text-slate-400 transform -translate-x-1/2 translate-y-1"><ArrowDown className="h-3 w-3" /></div>
                  </div>

                  {/* Node 2: Retrieval & Context */}
                  <div className="grid grid-cols-2 gap-4 w-full">
                    <div className="p-3 rounded-lg border border-blue-200 bg-blue-50 text-center shadow-sm relative hover:border-blue-400 transition-colors">
                      <span className="text-[10px] font-bold text-blue-700 uppercase">Retrieval</span>
                    </div>
                    <div className="p-3 rounded-lg border border-amber-200 bg-amber-50 text-center shadow-sm relative hover:border-amber-400 transition-colors">
                      <span className="text-[10px] font-bold text-amber-700 uppercase">Context</span>
                    </div>
                  </div>

                  {/* Connector */}
                  <div className="h-4 w-px bg-slate-300"></div>

                  {/* Node 3: Parallel Processing */}
                  <div className="w-full p-4 rounded-xl border border-slate-200 bg-white shadow-sm space-y-2">
                    <p className="text-[10px] text-center text-slate-400 font-mono mb-2">PARALLEL AGENTS</p>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="p-2 rounded border border-emerald-100 bg-emerald-50 text-center">
                        <span className="text-[9px] font-bold text-emerald-700 block">Sentiment</span>
                      </div>
                      <div className="p-2 rounded border border-rose-100 bg-rose-50 text-center">
                        <span className="text-[9px] font-bold text-rose-700 block">Credibility</span>
                      </div>
                      <div className="p-2 rounded border border-indigo-100 bg-indigo-50 text-center">
                        <span className="text-[9px] font-bold text-indigo-700 block">Themes</span>
                      </div>
                    </div>
                  </div>

                  {/* Connector */}
                  <div className="h-4 w-px bg-slate-300"></div>

                  {/* Node 4: Synthesis */}
                  <div className="w-full p-3 rounded-lg border border-cyan-200 bg-cyan-50 text-center shadow-sm relative hover:border-cyan-400 transition-colors">
                    <span className="text-xs font-bold text-cyan-700 uppercase tracking-wide">Synthesis, Reporting & Faithfulness</span>
                  </div>

                  {/* Loop Back Line (Visual Only) */}
                  <div className="absolute right-[-20px] top-[40%] bottom-[10%] w-[40px] border-r-2 border-dashed border-slate-300 rounded-r-2xl pointer-events-none opacity-50 hidden sm:block"></div>

                  {/* Node 5: Loop */}
                  <div className="w-full mt-2 p-2 rounded-full border border-slate-200 bg-slate-100 text-center flex items-center justify-center gap-2">
                    <GitBranch className="h-3 w-3 text-slate-500" />
                    <span className="text-[10px] font-medium text-slate-600">Self-Learning Feedback Loop</span>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>

        {/* Call to Action */}
        <div className="mt-16 text-center">
          <p className="text-sm text-slate-600 mb-4 font-medium">
            Advancing the field of Automated Social Listening
          </p>
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-white/80 backdrop-blur px-5 py-2 text-xs font-mono font-semibold text-violet-600 shadow-sm hover:shadow-md hover:scale-105 transition-all cursor-default">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            RESEARCH_ACTIVE: Epistemic Truth Discovery
          </div>
        </div>
      </div>
    </section>
  );
}