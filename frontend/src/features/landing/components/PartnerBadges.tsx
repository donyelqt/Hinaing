import Image from "next/image";

export function PartnerBadges() {
  return (
    <section className="bg-slate-50/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 text-xs text-slate-500 sm:px-6 xl:px-8">
        <div className="flex items-center gap-3">
          <div className="relative h-28 w-28 overflow-hidden rounded-full border border-slate-200 bg-white">
            <Image
              src="/baguio-city-seal.png"
              alt="Official seal of Baguio City"
              fill
              sizes="90px"
              className="object-contain p-1.5"
            />
          </div>
          <div className="space-y-0.5">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Prototype context</p>
            <p className="text-xs font-medium text-slate-700">
              Concept for Baguio City sentiment monitoring  not an official government product.
            </p>
          </div>
        </div>
        <span className="hidden rounded-full bg-slate-900 px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-white sm:inline-flex">
          Early prototype
        </span>
      </div>
    </section>
  );
}
