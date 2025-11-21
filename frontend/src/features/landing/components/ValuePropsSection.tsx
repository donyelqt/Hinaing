import { Card } from "@/components/ui/card";
import { VALUE_PROPS } from "../constants";

export function ValuePropsSection() {
  return (
    <section className="bg-slate-50">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16 xl:px-8">
        <div className="mb-8 max-w-2xl space-y-2">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">
            What Hinaing gives your team
          </h2>
          <p className="text-sm text-slate-600 sm:text-base">
            Instead of scrolling through endless comment threads, you get a concise view of what people are actually
            worried about and how those worries change over time.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {VALUE_PROPS.map((item) => (
            <Card key={item.title} className="h-full rounded-2xl bg-white/90 p-5 shadow-subtle">
              <h3 className="text-sm font-semibold text-slate-900 sm:text-base">{item.title}</h3>
              <p className="mt-2 text-xs leading-relaxed text-slate-600 sm:text-sm">{item.description}</p>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
