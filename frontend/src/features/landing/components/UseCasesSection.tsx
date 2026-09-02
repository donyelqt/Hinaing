import { Card } from "@/components/ui/card";
import { USE_CASES } from "../constants";
import { Building2, Siren, Megaphone } from "lucide-react";

export function UseCasesSection() {
  // Define consistent styling for each use case
  const useCaseStyles = [
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
    <section id="use-cases" className="relative bg-slate-50 bg-grid-pattern py-24 border-t border-slate-200">
      {/* Background Gradients */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-gradient-to-bl from-violet-100/40 to-transparent rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-gradient-to-tr from-blue-100/40 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <div className="inline-flex items-center justify-center -space-x-px rounded-md border border-violet-100 bg-white p-1 shadow-sm">
            <span className="px-3 py-1 text-[10px] font-mono font-medium uppercase tracking-widest text-[#3348b8]">Use Cases</span>
          </div>
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Where it helps <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#3348b8] to-[#5b3cc8]">most</span>
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Hinaing is not a generic analytics tool. It is tuned for decisions that affect real communities in and
            around Baguio City.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {USE_CASES.map((useCase, index) => {
            const Icon = index === 0 ? Building2 : index === 1 ? Siren : Megaphone;
            const style = useCaseStyles[index];

            return (
              <Card
                key={useCase.title}
                className={`group relative flex flex-col h-full overflow-hidden rounded-2xl border border-slate-200 bg-white/60 p-6 shadow-sm backdrop-blur-sm transition-all duration-500 hover:z-20 hover:-translate-y-2 hover:border-[#5b3cc8]/40 hover:shadow-[0_12px_32px_-16px_rgba(51,72,184,0.25)] hover:rotate-0 hover:scale-[1.02] ${style.tilt}`}
              >
                {/* Gradient Gloss Effect upon Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                <div className={`relative z-10 mb-6 inline-flex h-12 w-12 items-center justify-center rounded-xl border shadow-sm transition-all duration-300 group-hover:border-[#5b3cc8]/40 group-hover:bg-gradient-to-br group-hover:from-[#3348b8] group-hover:to-[#5b3cc8] group-hover:text-white group-hover:scale-110 group-hover:rotate-6 ${style.color}`}>
                  <Icon className="h-6 w-6" aria-hidden="true" />
                </div>

                <h3 className="relative z-10 text-base font-bold text-slate-900 mb-4 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:from-[#3348b8] group-hover:to-[#5b3cc8] transition-all">
                  {useCase.title}
                </h3>

                <ul className="relative z-10 space-y-2 text-sm leading-relaxed text-slate-500 group-hover:text-[#3348b8]">
                  {useCase.items.map((item, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="inline-block mr-2 text-violet-500">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}




