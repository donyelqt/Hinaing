import { FAQ_ITEMS } from "../constants";
import { Plus, Minus } from "lucide-react";

export function FAQSection() {
  return (
    <section id="faq" className="relative bg-white py-24">
      <div className="relative mx-auto max-w-6xl px-4 sm:px-6 xl:px-8">
        <div className="mb-16 text-center space-y-4">
          <h2 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Frequently asked
          </h2>
          <p className="text-lg text-slate-600 leading-relaxed max-w-2xl mx-auto">
            A quick overview of what the prototype does today and how teams can think about using it.
          </p>
        </div>

        <div className="max-w-3xl mx-auto space-y-4">
          {FAQ_ITEMS.map((item) => (
            <details
              key={item.question}
              className="group rounded-3xl border border-slate-100 bg-slate-50/50 open:bg-white open:shadow-lg open:shadow-slate-200/50 open:border-violet-100 transition-all duration-300"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 p-6 text-left [&::-webkit-details-marker]:hidden">
                <span className="text-base font-bold text-slate-900 group-hover:text-violet-700 transition-colors">
                  {item.question}
                </span>
                <span className="shrink-0 rounded-full border border-slate-200 bg-white p-2 text-slate-400 transition-all group-hover:border-violet-200 group-hover:text-violet-600 group-open:rotate-45 group-open:bg-violet-50 group-open:text-violet-600">
                  <Plus className="h-4 w-4 block group-open:hidden" />
                  <Minus className="h-4 w-4 hidden group-open:block" />
                </span>
              </summary>
              <div className="px-6 pb-6 pt-0 text-base leading-relaxed text-slate-600 animate-fade-in">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
