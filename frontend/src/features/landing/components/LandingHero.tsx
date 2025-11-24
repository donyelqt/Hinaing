"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { useEffect, useRef, useState } from "react";

function BaguioTeamsPill() {
  const [isAutoPulse, setIsAutoPulse] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const startPulse = () => {
      setIsAutoPulse(true);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => setIsAutoPulse(false), 3000);
    };

    startPulse();
    intervalRef.current = setInterval(startPulse, 6000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="group relative inline-flex cursor-default">
      <div
        className={`pointer-events-none absolute -inset-4 rounded-full bg-gradient-to-r from-hinaing-blue-500/85 via-hinaing-blue-400/65 to-violet-500/85 blur-2xl opacity-80 transition-all duration-300 group-hover:scale-110 group-hover:opacity-100 ${
          isAutoPulse ? "scale-110 opacity-100" : ""
        }`}
        aria-hidden="true"
      />
      <div
        className={`relative z-10 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-3 py-1 text-xs font-medium text-white shadow-sm transition-all duration-300 group-hover:-translate-y-0.5 group-hover:shadow-subtle group-hover:brightness-110 ${
          isAutoPulse ? "-translate-y-0.5 shadow-subtle brightness-110" : ""
        }`}
      >
        <span className="h-1.5 w-1.5 rounded-full bg-hinaing-gold" />
        <span>Built for Baguio City teams</span>
      </div>
    </div>
  );
}

export function LandingHero() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-hinaing-blue-50/70 via-violet-50/70 to-slate-50">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 py-16 sm:px-6 lg:flex-row lg:items-center lg:gap-16 lg:py-20 xl:px-8">
        <div className="space-y-6 lg:max-w-xl">
          <BaguioTeamsPill />

          <div className="space-y-4">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
              Monitor public sentiment
              <span className="block bg-gradient-to-r from-hinaing-blue-700 to-violet-500 bg-clip-text text-transparent">
                before it becomes a crisis.
              </span>
            </h1>
            <p className="max-w-xl text-sm leading-relaxed text-slate-600 sm:text-base">
              Hinaing turns noisy Facebook and Reddit conversations into clear, actionable briefings so Baguio City
              decision-makers can respond faster and plan better.
            </p>

            <div className="grid gap-3 text-xs text-slate-600 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-subtle">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Conversations</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">4.3k+</p>
                <p className="text-[11px] text-slate-500">tracked this month</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-subtle">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Coverage</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">40+</p>
                <p className="text-[11px] text-slate-500">barangays monitored</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white/80 px-3 py-2 shadow-subtle">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Channels</p>
                <p className="mt-1 text-sm font-semibold text-slate-900">3</p>
                <p className="text-[11px] text-slate-500">including Facebook & Reddit</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <Link
              href="/app"
              className="inline-flex items-center justify-center rounded-xl bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-6 py-3 text-sm font-semibold text-white shadow-card shadow-hinaing-blue-600/30 transition hover:brightness-110 hover:shadow-subtle"
            >
              Open console
            </Link>
            <Link
              href="#live-preview"
              className="inline-flex items-center justify-center rounded-xl border border-slate-200 bg-white/70 px-5 py-3 text-sm font-medium text-slate-700 shadow-sm transition hover:border-violet-200 hover:text-slate-900"
            >
              View sample briefing
            </Link>
          </div>

          <p className="text-xs text-slate-400">
            No credit card required. Prototype tuned for Baguio City use cases.
          </p>
        </div>

        <div className="relative lg:flex-1">
          <div
            className="pointer-events-none absolute -right-24 -top-20 hidden h-56 w-56 rounded-full bg-gradient-to-br from-hinaing-blue-300/40 to-violet-400/40 blur-3xl lg:block"
            aria-hidden="true"
          />
          <div
            className="pointer-events-none absolute -right-10 top-16 hidden h-40 w-40 rounded-full border border-violet-300/60 lg:block"
            aria-hidden="true"
          />
          <Card className="relative mx-auto max-w-md rounded-3xl border border-slate-200 bg-gradient-to-br from-white/90 via-hinaing-blue-50/70 to-violet-50/80 p-6 shadow-card transition-transform duration-200 ease-out hover:-translate-y-1 hover:shadow-card">
            <div className="mb-4 flex items-center justify-between text-xs text-slate-500">
              <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-hinaing-blue-600/15 via-hinaing-blue-500/15 to-violet-500/15 px-3 py-1 font-medium text-hinaing-blue-800">
                Live sentiment snapshot
              </span>
              <span>Baguio City · Last 24 hours</span>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Overall mood</p>
                <p className="mt-1 text-lg font-semibold text-slate-900">Cautious but engaged</p>
                <p className="text-xs text-slate-500">
                  Infrastructure and transport issues dominate, but support remains high for cleanup and tourism efforts.
                </p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <div className="rounded-xl bg-rose-50 px-2 py-3">
                  <p className="text-lg font-semibold text-rose-600">52%</p>
                  <p className="text-[11px] uppercase tracking-wide text-rose-700">Negative</p>
                </div>
                <div className="rounded-xl bg-slate-100 px-2 py-3">
                  <p className="text-lg font-semibold text-slate-700">31%</p>
                  <p className="text-[11px] uppercase tracking-wide text-slate-600">Neutral</p>
                </div>
                <div className="rounded-xl bg-emerald-50 px-2 py-3">
                  <p className="text-lg font-semibold text-emerald-600">17%</p>
                  <p className="text-[11px] uppercase tracking-wide text-emerald-700">Positive</p>
                </div>
              </div>

              <div className="mt-2 space-y-1 rounded-2xl bg-white/80 p-3 text-xs text-slate-600 shadow-inner">
                <p className="font-medium text-slate-900">Tonight&apos;s briefing highlights:</p>
                <ul className="mt-1 space-y-1 list-disc pl-4">
                  <li>Rising complaints on evening traffic in Session Road and Naguilian Road.</li>
                  <li>Persistent chatter on water reliability in several barangays.</li>
                  <li>Strong positive sentiment around weekend park cleanup efforts.</li>
                </ul>
              </div>

              <p className="pt-1 text-[11px] text-slate-400">
                Generated layout preview. Actual data and filters are available inside the console.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
