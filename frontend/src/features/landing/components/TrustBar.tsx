export function TrustBar() {
  return (
    <section className="border-y border-slate-100 bg-white/80">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 xl:px-8">
        <p className="font-medium text-slate-600">
          Designed with LGU planners, crisis responders, and communications teams in mind.
        </p>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium">
            Focus: Baguio City and nearby areas
          </span>
          <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium">
            Facebook and Reddit public posts
          </span>
          <span className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 font-medium">
            Includes potential mis/disinformation signals
          </span>
        </div>
      </div>
    </section>
  );
}
