import clsx from "clsx";
import { USE_CASES } from "../constants";
import { Building2, Siren, Megaphone } from "lucide-react";

export function UseCasesSection() {
  return (
    <section id="use-cases" className="relative bg-slate-50 py-24">
      {/* Background Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-gradient-to-bl from-violet-100/40 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-gradient-to-tr from-blue-100/40 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <p className="text-sm font-bold uppercase tracking-wide text-violet-600">Use cases</p>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Where it helps most
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Hinaing is not a generic analytics tool. It is tuned for decisions that affect real communities in and
            around Baguio City.
          </p>
        </div>

        <div className="relative grid gap-8 md:grid-cols-2 xl:grid-cols-3">
          {USE_CASES.map((useCase, index) => {
            const Icon = index === 0 ? Building2 : index === 1 ? Siren : Megaphone;

            return (
              <div
                key={useCase.title}
                className={clsx(
                  "group relative flex flex-col rounded-3xl border p-8 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl h-full",
                  index === 0
                    ? "bg-gradient-to-br from-violet-600 to-blue-600 border-transparent text-white shadow-lg shadow-blue-500/20"
                    : "bg-white/80 border-slate-100 text-slate-700 shadow-lg shadow-slate-200/50 backdrop-blur-sm hover:shadow-slate-200/80"
                )}
              >
                <div className="flex items-start justify-between gap-4 mb-6">
                  <h3 className={clsx(
                    "text-xl font-bold",
                    index === 0 ? "text-white" : "text-slate-900 group-hover:text-violet-700 transition-colors"
                  )}>
                    {useCase.title}
                  </h3>
                  <span className={clsx(
                    "flex h-12 w-12 shrink-0 items-center justify-center rounded-full transition-colors shadow-sm",
                    index === 0 ? "bg-white/20 text-white" : "bg-slate-100 text-slate-500 group-hover:bg-violet-50 group-hover:text-violet-600"
                  )}>
                    <Icon className="h-6 w-6" />
                  </span>
                </div>

                <ul className={clsx(
                  "space-y-3 list-disc pl-4 text-sm leading-relaxed mt-auto",
                  index === 0 ? "text-white/90" : "text-slate-600"
                )}>
                  {useCase.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
