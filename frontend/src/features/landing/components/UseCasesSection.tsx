import clsx from "clsx";
import { USE_CASES } from "../constants";

export function UseCasesSection() {
  return (
    <section id="use-cases" className="bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16 xl:px-8">
        <div className="mb-8 max-w-2xl space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Where it helps most</h2>
          <p className="text-sm text-slate-600 sm:text-base">
            Hinaing is not a generic analytics tool. It is tuned for decisions that affect real communities in and
            around Baguio City.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3">
          {USE_CASES.map((useCase, index) => (
            <div
              key={useCase.title}
              className={clsx(
                "rounded-2xl border border-slate-100 bg-white/90 p-5 text-sm text-slate-700 shadow-subtle transition-transform duration-150 ease-out hover:-translate-y-1 hover:shadow-card",
                index === 0 && "bg-gradient-to-br from-hinaing-blue-50/80 to-violet-50/80 border-transparent"
              )}
            >
              <h3 className="text-base font-semibold text-slate-900">{useCase.title}</h3>
              <ul className="mt-3 space-y-2 list-disc pl-4 text-xs text-slate-600 sm:text-sm">
                {useCase.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
