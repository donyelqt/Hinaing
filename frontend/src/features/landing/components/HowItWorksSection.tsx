import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="relative overflow-hidden bg-white bg-grid-pattern py-24">
      {/* Background Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] bg-gradient-to-b from-slate-50 to-transparent rounded-full blur-3xl opacity-50" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            How it works
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            The console automates the parts of monitoring that are repetitive and fragile, while keeping your team in
            control of interpretation and action.
          </p>
        </div>

        <div className="relative mt-8">
          {/* Connecting Line System */}
          <div className="absolute inset-x-0 top-[56px] hidden -translate-y-1/2 md:block z-0">
            <svg
              className="h-20 w-full overflow-visible"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <defs>
                <linearGradient id="flow-gradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
                  <stop offset="20%" stopColor="#8b5cf6" stopOpacity="1" />
                  <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
                  <stop offset="80%" stopColor="#8b5cf6" stopOpacity="1" />
                  <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.2" />
                </linearGradient>
                <filter id="glow-line" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="2" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Base Track */}
              <line
                x1="0"
                y1="50%"
                x2="100%"
                y2="50%"
                stroke="#e2e8f0"
                strokeWidth="4"
              />

              {/* Animated Flow */}
              <line
                x1="0"
                y1="50%"
                x2="100%"
                y2="50%"
                stroke="url(#flow-gradient)"
                strokeWidth="4"
                strokeDasharray="20 20"
                className="animate-dash-flow"
                strokeLinecap="round"
                filter="url(#glow-line)"
              />
            </svg>
          </div>

          <div className="grid gap-8 md:grid-cols-3 relative z-10">
            {HOW_IT_WORKS_STEPS.map((step, index) => (
              <div
                key={step.title}
                className="group relative rounded-3xl border border-slate-100 bg-white p-8 shadow-lg shadow-slate-200/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/80"
              >
                <div className="mb-6 flex items-center gap-4">
                  <div className="relative z-20 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 text-sm font-bold text-white shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-transform duration-300 ring-8 ring-white">
                    {index + 1}
                  </div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    {step.label}
                  </span>
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-blue-600 transition-colors">
                  {step.title}
                </h3>
                <p className="text-base leading-relaxed text-slate-600">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
