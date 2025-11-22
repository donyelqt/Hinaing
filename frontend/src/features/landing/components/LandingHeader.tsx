"use client";

import Link from "next/link";
import { Menu, X } from "lucide-react";
import { useState } from "react";

export function LandingHeader() {
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

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

        <button
          type="button"
          className="inline-flex items-center justify-center rounded-md border border-slate-200 bg-white/80 px-2.5 py-1.5 text-slate-700 shadow-subtle sm:hidden"
          onClick={() => setIsOpen((open) => !open)}
          aria-label="Toggle navigation"
          aria-expanded={isOpen}
        >
          {isOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
        </button>
      </div>

      {isOpen && (
        <div className="border-t border-slate-200/70 bg-white/95 px-4 pb-4 pt-3 text-sm text-slate-700 shadow-subtle sm:hidden">
          <nav className="flex flex-col gap-2">
            <a
              href="#product"
              className="py-1 hover:text-hinaing-blue-700"
              onClick={closeMenu}
            >
              Product
            </a>
            <a
              href="#how-it-works"
              className="py-1 hover:text-hinaing-blue-700"
              onClick={closeMenu}
            >
              How it works
            </a>
            <a
              href="#use-cases"
              className="py-1 hover:text-hinaing-blue-700"
              onClick={closeMenu}
            >
              Use cases
            </a>
            <a
              href="#faq"
              className="py-1 hover:text-hinaing-blue-700"
              onClick={closeMenu}
            >
              FAQ
            </a>
            <Link
              href="/app"
              className="mt-2 inline-flex items-center justify-center rounded-xl bg-hinaing-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-subtle transition hover:bg-hinaing-blue-500"
              onClick={closeMenu}
            >
              Open console
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
