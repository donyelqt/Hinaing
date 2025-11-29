import Image from "next/image";

export function PartnerBadges() {
  return (
    <section className="bg-slate-50/80 border-t border-slate-200/50">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-4 py-6 text-xs text-slate-500 sm:px-6 xl:px-8">
        <div className="flex items-center gap-4">
          <div className="relative h-28 w-28 overflow-hidden rounded-full border border-slate-200 bg-white flex-shrink-0 shadow-sm">
            <Image
              src="/baguio-city-seal.png"
              alt="Official seal of Baguio City"
              fill
              sizes="100px"
              className="object-contain p-1.5"
            />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Prototype context</p>
            <p className="text-sm font-medium text-slate-700 leading-snug">
              Concept for Baguio City sentiment monitoring — not an official government product.
            </p>
          </div>
        </div>
        <span className="hidden rounded-full bg-slate-900 px-4 py-1.5 text-xs font-semibold uppercase tracking-wide text-white sm:inline-flex">
          Early prototype
        </span>
      </div>
    </section>
  );
}
