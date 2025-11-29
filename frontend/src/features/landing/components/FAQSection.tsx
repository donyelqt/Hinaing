import { FAQ_ITEMS } from "../constants";

export function FAQSection() {
  return (
    <section id="faq" className="bg-white">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 lg:py-16 xl:px-8">
        <div className="mb-8 space-y-2 text-center">
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl">Frequently asked</h2>
          <p className="text-sm text-slate-600 sm:text-base">
            A quick overview of what the prototype does today and how teams can think about using it.
          </p>
        </div>

        <div className="space-y-3">
          {FAQ_ITEMS.map((item) => (
            <details
              key={item.question}
              className="group rounded-2xl border border-slate-100 bg-slate-50/70 p-4 text-sm text-slate-700 shadow-subtle"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-left">
                <span className="text-sm font-semibold text-slate-900 sm:text-base">{item.question}</span>
                <span className="shrink-0 rounded-full border border-slate-200 bg-white px-2 py-1 text-xs text-slate-500 transition group-open:border-hinaing-blue-200 group-open:text-hinaing-blue-700">
                  {""}
                  Show
                </span>
              </summary>
              <div className="mt-3 text-xs leading-relaxed text-slate-600 sm:text-sm">
                {item.answer}
              </div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
