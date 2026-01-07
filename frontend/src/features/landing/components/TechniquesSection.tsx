import { Card } from "@/components/ui/card";
import { Brain, Cpu, Database, Zap, Users, Wrench, Repeat, Search } from "lucide-react";

export function TechniquesSection() {
  const techniques = [
    {
      title: "Multi-Agent AI System",
      description: "A 13-agent hierarchical architecture built on a dependency-aware DAG, orchestrating core processes and expandable theme-specific agents to deliver scalable and intelligent civic analysis.",
      icon: Users,
    },
    {
      title: "Agentic/Intelligent Search",
      description: "Combines ReAct-based query planning with neural semantic reranking to autonomously formulate strategies and prioritize high-relevance results across web and social platforms.",
      icon: Search,
    },
    {
      title: "Deep Learning & NLP",
      description: "Utilizes RoBERTa transformer models fine-tuned on social media datasets, integrated into a robust ensemble framework that combines LLM reasoning with deep learning precision for high-fidelity sentiment analysis.",
      icon: Brain,
    },
    {
      title: "Advanced Machine Learning",
      description: "Semantic similarity using sentence transformers, multi-language support (English, Filipino, Ilocano), and real-time content classification.",
      icon: Cpu,
    },
    {
      title: "Context Engineering",
      description: "Research-driven adaptive context conditioning that dynamically tailors AI analysis based on civic domain focus, issue relevance, and evolving conversation contexts.",
      icon: Wrench,
    },
    {
      title: "Retrieval Augmented Generation (RAG)",
      description: "Knowledge retrieval from internal memory, cross-reference verification, and fact-checking integration with external APIs.",
      icon: Database,
    },
    {
      title: "Self-Learning Cyclic RAG",
      description: "Continuous learning system that consolidates new information into persistent memory, enabling iterative knowledge refinement and improvement.",
      icon: Repeat,
    },
    {
      title: "Multi-Signal Credibility Assessment",
      description: "5-signal ensemble for source quality filtering: domain trust, cross-reference, fact-check API, LLM analysis, and web verification.",
      icon: Zap,
    },
  ];

  return (
    <section id="techniques" className="relative bg-white bg-grid-pattern py-24">
      {/* Decorative background blob */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-violet-100/40 to-blue-100/40 rounded-full blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Advanced <span className="bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 bg-clip-text text-transparent">Agentic AI Techniques</span>
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Hinaing leverages neuro-symbolic AI and hierarchical multi-agent orchestration to transform unstructured digital noise into structured, actionable intelligence.
          </p>
        </div>

        {/* Unified Grid: 4 columns */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {techniques.map((technique, index) => {
            const Icon = technique.icon;

            // 8 distinct colors for the 8 cards
            const bgClasses = [
              "bg-violet-50 text-violet-600",
              "bg-fuchsia-50 text-fuchsia-600", // New for search
              "bg-blue-50 text-blue-600",
              "bg-emerald-50 text-emerald-600",
              "bg-amber-50 text-amber-600",
              "bg-rose-50 text-rose-600",
              "bg-indigo-50 text-indigo-600",
              "bg-cyan-50 text-cyan-600"
            ];

            // Simple cycle if we ever add more
            const colorClass = bgClasses[index % bgClasses.length];

            return (
              <Card
                key={technique.title}
                className="group relative h-full overflow-hidden rounded-3xl border-0 bg-slate-50/80 p-6 shadow-lg shadow-slate-200/50 backdrop-blur-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl hover:shadow-slate-200/80 ring-1 ring-slate-100"
              >
                <div className={`mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl ${colorClass} transition-transform duration-300 group-hover:scale-110`}>
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>

                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-violet-700 transition-colors">
                  {technique.title}
                </h3>
                <p className="text-sm leading-relaxed text-slate-600">
                  {technique.description}
                </p>

                {/* Hover Gradient Border Effect */}
                <div className="absolute inset-x-0 bottom-0 h-1 bg-gradient-to-r from-transparent via-slate-200 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}