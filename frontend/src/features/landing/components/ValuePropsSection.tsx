import { Card } from "@/components/ui/card";
import { Activity, AlertTriangle, Signal } from "lucide-react";
import { VALUE_PROPS } from "../constants";

export function ValuePropsSection() {
  // Define consistent styling for each value prop
  const valuePropStyles = [
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
      tilt: "-rotate-1",
    }
  ];

  return (
    <section id="product" className="relative bg-slate-50 bg-grid-pattern py-24 border-t border-slate-200">
      {/* Decorative background blob */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-violet-100/40 to-blue-100/40 rounded-full blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-12 max-w-2xl mx-auto text-center space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            What Hinaing <span className="bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] bg-clip-text text-transparent">gives your team</span>
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Instead of scrolling through endless comment threads, you get a concise view of what people are actually
            worried about and how those worries change over time.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {VALUE_PROPS.map((item, index) => {
            const Icon = index === 0 ? Activity : index === 1 ? Signal : AlertTriangle;
            const style = valuePropStyles[index];

            return (
              <Card
                key={item.title}
                className={`group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white/60 p-4 shadow-sm backdrop-blur-sm transition-all duration-500 hover:z-20 hover:-translate-y-2 hover:border-[#5b3cc8]/40 hover:shadow-[0_12px_32px_-16px_rgba(51,72,184,0.25)] hover:rotate-0 hover:scale-[1.02] ${style.tilt} max-w-[22rem] w-full mx-auto`}
              >
                {/* Gradient Gloss Effect upon Hover */}
                <div className="absolute inset-0 bg-gradient-to-br from-violet-50/50 via-transparent to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

                <div className="flex flex-col py-4 px-2">
                  <div className={`relative z-10 mb-3 inline-flex h-14 w-14 items-center justify-center rounded-xl border shadow-sm transition-all duration-300 group-hover:border-[#5b3cc8]/40 group-hover:bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] group-hover:text-white group-hover:scale-110 group-hover:rotate-6 ${style.color}`}>
                    <Icon className="h-10 w-10" aria-hidden="true" />
                  </div>

                  <h3 className="relative z-10 text-xl font-bold text-slate-900 mb-2 group-hover:text-[#3348b8] transition-all px-1">
                    {item.title}
                  </h3>
                  <p className="relative z-10 text-lg leading-relaxed text-slate-600 px-1">
                    {item.description}
                  </p>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}




