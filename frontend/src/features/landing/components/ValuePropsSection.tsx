import { Card } from "@/components/ui/card";
import { Activity, AlertTriangle, Signal } from "lucide-react";
import { VALUE_PROPS } from "../constants";

export function ValuePropsSection() {
  return (
    <section id="product" className="relative bg-slate-50 py-24">
      {/* Decorative background blob */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-violet-100/40 to-blue-100/40 rounded-full blur-3xl pointer-events-none" />

      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 max-w-2xl mx-auto text-center space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            What Hinaing gives your team
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed">
            Instead of scrolling through endless comment threads, you get a concise view of what people are actually
            worried about and how those worries change over time.
          </p>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {VALUE_PROPS.map((item, index) => {
            const Icon = index === 0 ? Activity : index === 1 ? Signal : AlertTriangle;
            const gradientClass = index === 0
              ? "from-violet-500 to-purple-500"
              : index === 1
                ? "from-blue-500 to-cyan-500"
                : "from-amber-500 to-orange-500";

            const bgClass = index === 0
              ? "bg-violet-50 text-violet-600"
              : index === 1
                ? "bg-blue-50 text-blue-600"
                : "bg-amber-50 text-amber-600";

            return (
              <Card
                key={item.title}
                className="group relative h-full overflow-hidden rounded-3xl border-0 bg-white/80 p-8 shadow-lg shadow-slate-200/50 backdrop-blur-sm transition-all duration-300 hover:-translate-y-2 hover:shadow-xl hover:shadow-slate-200/80 ring-1 ring-slate-100"
              >
                <div className={`mb-6 inline-flex h-14 w-14 items-center justify-center rounded-2xl ${bgClass} transition-transform duration-300 group-hover:scale-110`}>
                  <Icon className="h-7 w-7" aria-hidden="true" />
                </div>

                <h3 className="text-xl font-bold text-slate-900 mb-3 group-hover:text-violet-700 transition-colors">
                  {item.title}
                </h3>
                <p className="text-base leading-relaxed text-slate-600">
                  {item.description}
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
