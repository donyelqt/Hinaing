import { HOW_IT_WORKS_STEPS } from "../constants";

export function HowItWorksSection() {
  return (
    <section className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16 xl:px-8">
        <div className="mb-8 max-w-2xl space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">How it works</h2>
          <p className="text-sm text-slate-600 sm:text-base">
            The console automates the parts of monitoring that are repetitive and fragile, while keeping your team in
            control of interpretation and action.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {HOW_IT_WORKS_STEPS.map((step) => (
            <div
              key={step.title}
              className="relative rounded-2xl border border-slate-100 bg-slate-50/80 p-5 text-sm text-slate-700 shadow-subtle"
            >
              <div className="mb-3 inline-flex items-center rounded-full bg-white/90 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                {step.label}
              </div>
              <h3 className="text-base font-semibold text-slate-900">{step.title}</h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-600 sm:text-sm">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
