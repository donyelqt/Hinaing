"use client";

import Link from "next/link";
import { Menu, X, Command } from "lucide-react";
import { useState } from "react";
import { KeyboardButton } from "@/components/ui/keyboard-button";

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
          <span className="flex h-7 w-7 items-center justify-center rounded-full bg-[linear-gradient(135deg,#3348b8_0%,#5b3cc8_100%)] text-[11px] font-semibold tracking-tight text-white shadow-sm">
            H
          </span>
          <div className="flex items-baseline gap-1">
            <span className="text-base font-semibold tracking-tight text-slate-900 sm:text-lg">
              Hinaing
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
          <KeyboardButton
            variant="primary"
            size="sm"
            icon={<Command className="h-3 w-3" />}
            badge="⌘K"
            href="/app"
          >
            Open
          </KeyboardButton>
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
            <KeyboardButton
              variant="primary"
              size="md"
              icon={<Command className="h-4 w-4" />}
              badge="⌘K"
              href="/app"
              fullWidth
              className="mt-3"
              onClick={closeMenu}
            >
              Open Console
            </KeyboardButton>
          </nav>
        </div>
      )}
    </header>
  );
}

