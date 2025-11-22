import Link from "next/link";

export function LandingHeader() {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 text-sm sm:h-16 sm:px-6 xl:px-8">
        <Link href="/" className="inline-flex items-center gap-2">
          <span className="inline-flex h-7 items-center gap-2 rounded-full bg-slate-900 px-3 text-xs font-semibold text-white">
            <span className="h-1.5 w-1.5 rounded-full bg-hinaing-gold" />
            <span>Hinaing</span>
            <span className="rounded-full bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-100">
              Beta
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-6 text-xs font-medium text-slate-600 sm:flex">
          <a href="#product" className="hover:text-hinaing-blue-700">
            Product
          </a>
          <a href="#how-it-works" className="hover:text-hinaing-blue-700">
            How it works
          </a>
          <a href="#use-cases" className="hover:text-hinaing-blue-700">
            Use cases
          </a>
          <a href="#faq" className="hover:text-hinaing-blue-700">
            FAQ
          </a>
          <Link
            href="/app"
            className="inline-flex items-center rounded-xl bg-hinaing-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-subtle transition hover:bg-hinaing-blue-500"
          >
            Open console
          </Link>
        </nav>

        <Link
          href="/app"
          className="inline-flex items-center rounded-xl bg-hinaing-blue-600 px-3 py-1.5 text-[11px] font-semibold text-white shadow-subtle transition hover:bg-hinaing-blue-500 sm:hidden"
        >
          Open console
        </Link>
      </div>
    </header>
  );
}
