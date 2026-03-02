"use client";

import Link from "next/link";
import { Menu, X, Command } from "lucide-react";
import { useState } from "react";

export function LandingHeader() {
  const [isOpen, setIsOpen] = useState(false);

  const closeMenu = () => setIsOpen(false);

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4 text-sm sm:h-16 sm:px-6 xl:px-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5"
          aria-label="Hinaing home"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-hinaing-blue-500 via-hinaing-blue-600 to-violet-500 text-[11px] font-semibold tracking-tight text-white shadow-subtle">
            H
          </span>
          <div className="flex items-baseline gap-1">
            <span className="bg-gradient-to-r from-hinaing-blue-700 to-violet-500 bg-clip-text text-base font-semibold tracking-tight text-transparent sm:text-lg">
              Hinaing
            </span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-0.5 text-[10px] font-medium uppercase tracking-[0.16em] bg-gradient-to-r from-hinaing-blue-600 to-violet-500 bg-clip-text text-transparent">
              Beta
            </span>
          </div>
        </Link>

        <nav className="hidden items-center gap-6 text-xs font-medium text-slate-600 sm:flex">
          <a href="#product" className="transition hover:text-slate-900">
            Product
          </a>
          <a href="#how-it-works" className="transition hover:text-slate-900">
            How it works
          </a>
          <a href="#techniques" className="transition hover:text-slate-900">
            AI Engineering
          </a>
          <a href="#use-cases" className="transition hover:text-slate-900">
            Use cases
          </a>
          <a href="#faq" className="transition hover:text-slate-900">
            FAQ
          </a>
          <Link
            href="/app"
            className="group relative inline-flex items-center select-none"
          >
            {/* Softer shadow - original color base */}
            <span className="absolute inset-0 rounded-md bg-violet-400/50 translate-y-[2px] translate-x-[1px] transition-transform duration-100 group-hover:translate-y-[1px] group-active:translate-y-[0.5px]" />
            
            {/* Softer keycap - original colors */}
            <span className="relative inline-flex items-center gap-1.5 rounded-md bg-gradient-to-b from-violet-400 via-blue-500 to-cyan-500 px-3 py-1.5 text-xs font-bold text-white border-[1.5px] border-violet-400/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),inset_0_-1px_0_rgba(0,0,0,0.1)] transition-all duration-100 group-hover:translate-y-[0.5px] group-active:translate-y-[1px]">
              {/* Subtle gloss */}
              <span className="absolute inset-x-0 top-0 h-[35%] rounded-t-[2px] bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
              <Command className="relative h-3 w-3 text-white/90" />
              <span className="relative font-bold tracking-tight text-white drop-shadow-sm">Open Console</span>
            </span>
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
              className="py-1 hover:text-slate-900"
              onClick={closeMenu}
            >
              Product
            </a>
            <a
              href="#how-it-works"
              className="py-1 hover:text-slate-900"
              onClick={closeMenu}
            >
              How it works
            </a>
            <a
              href="#techniques"
              className="py-1 hover:text-slate-900"
              onClick={closeMenu}
            >
              AI Engineering
            </a>
            <a
              href="#use-cases"
              className="py-1 hover:text-slate-900"
              onClick={closeMenu}
            >
              Use cases
            </a>
            <a
              href="#faq"
              className="py-1 hover:text-slate-900"
              onClick={closeMenu}
            >
              FAQ
            </a>
            <Link
              href="/app"
              className="group relative mt-2 inline-flex items-center justify-center select-none"
              onClick={closeMenu}
            >
              {/* Softer shadow - original color base */}
              <span className="absolute inset-0 rounded-md bg-violet-400/50 translate-y-[2px] translate-x-[1px] transition-transform duration-100 group-hover:translate-y-[1px] group-active:translate-y-[0.5px]" />
              
              {/* Softer keycap - original colors */}
              <span className="relative inline-flex items-center gap-1.5 rounded-md bg-gradient-to-b from-violet-400 via-blue-500 to-cyan-500 px-4 py-2 text-xs font-bold text-white border-[1.5px] border-violet-400/50 shadow-[inset_0_1px_0_rgba(255,255,255,0.5),inset_0_-1px_0_rgba(0,0,0,0.1)] transition-all duration-100 group-hover:translate-y-[0.5px] group-active:translate-y-[1px]">
                {/* Subtle gloss */}
                <span className="absolute inset-x-0 top-0 h-[35%] rounded-t-[3px] bg-gradient-to-b from-white/40 to-transparent pointer-events-none" />
                <Command className="relative h-3 w-3 text-white/90" />
                <span className="relative font-bold tracking-tight text-white drop-shadow-sm">Open Console</span>
              </span>
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
