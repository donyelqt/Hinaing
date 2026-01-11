import { Card } from "@/components/ui/card";
import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  // Define consistent styling for each step
  const stepStyles = [
    {
      color: "text-violet-500 bg-violet-50 border-violet-100",
      tilt: "-rotate-1",
    },
    {
      color: "text-blue-500 bg-blue-50 border-blue-100",
      tilt: "rotate-1",
    },
    {
      color: "text-amber-500 bg-amber-50 border-amber-100",
      tilt: "-rotate-2",
    }
  ];

  return (
    <section id="how-it-works" className="relative overflow-hidden bg-white bg-grid-pattern py-24 border-t border-slate-200">
      {/* Background Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-to-b from-slate-50 to-transparent rounded-full blur-3xl opacity-50" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center justify-center -space-x-px rounded-md border border-violet-100 bg-white p-1 shadow-sm">
            <span className="px-3 py-1 text-[10px] font-mono font-medium uppercase tracking-widest text-violet-600">Workflow</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            How it <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-600 to-cyan-500">works</span>
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            The console automates the parts of monitoring that are repetitive and fragile, while keeping your team in
            control of interpretation and action.
          </p>
        </div>

        <div className="relative">
          {/* Connecting Arrows */}
          <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex items-center justify-center z-0 pointer-events-none">
            <div className="flex items-center w-full max-w-4xl mx-auto px-8">
              <div className="hidden md:block flex-grow border-t-2 border-slate-400 relative">
                <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-0 h-0 border-y-8 border-l-8 border-r-0 border-solid border-transparent border-l-slate-400"></div>
              </div>
              <div className="hidden md:flex items-center justify-center text-slate-400 mx-4">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
              <div className="hidden md:block flex-grow border-t-2 border-slate-400 relative">
                <div className="absolute right-0 top-1/2 transform -translate-y-1/2 w-0 h-0 border-y-8 border-l-8 border-r-0 border-solid border-transparent border-l-slate-400"></div>
              </div>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3 relative z-10">
            {HOW_IT_WORKS_STEPS.map((step, index) => {
              const style = stepStyles[index];

              return (
                <Card
                  key={step.title}
                  className={`group relative flex flex-col h-full overflow-hidden rounded-2xl border border-slate-200 bg-white/60 p-6 shadow-sm backdrop-blur-sm transition-all duration-500 hover:z-20 hover:-translate-y-2 hover:border-violet-300 hover:shadow-2xl hover:shadow-violet-200/50 hover:rotate-0 hover:scale-[1.02] ${style.tilt}`}
                >
                  {/* Gradient Gloss Effect upon Hover */}
                  <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                  <div className="flex items-start justify-between gap-4 mb-4">
                    <div className="relative z-10 flex h-12 w-12 items-center justify-center rounded-xl border bg-gradient-to-br from-violet-500 to-cyan-500 text-sm font-bold text-white shadow-sm">
                      {index + 1}
                    </div>
                    <span className="relative z-10 text-xs font-bold uppercase tracking-wider text-slate-400">
                      {step.label}
                    </span>
                  </div>

                  <h3 className="relative z-10 text-base font-bold text-slate-900 mb-2 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-violet-600 group-hover:to-cyan-600 transition-all">
                    {step.title}
                  </h3>
                  <p className="relative z-10 text-sm leading-relaxed text-slate-500 group-hover:text-slate-700">
                    {step.description}
                  </p>
                </Card>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
