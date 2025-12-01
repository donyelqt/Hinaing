import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="relative overflow-hidden bg-white py-24">
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
          {/* Connecting Line */}
          <div
            className="pointer-events-none absolute inset-x-8 top-12 hidden h-0.5 bg-gradient-to-r from-violet-100 via-blue-100 to-violet-100 md:block"
            aria-hidden="true"
          />

          <div className="grid gap-8 md:grid-cols-3">
            {HOW_IT_WORKS_STEPS.map((step, index) => (
              <div
                key={step.title}
                className="group relative rounded-3xl border border-slate-100 bg-white p-8 shadow-lg shadow-slate-200/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-slate-200/80"
              >
                <div className="mb-6 flex items-center gap-4">
                  <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-600 text-sm font-bold text-white shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-transform duration-300">
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
