"use client";

import Link from "next/link";
import { Card } from "@/components/ui/card";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, MessageSquare, MapPin, Share2, Sparkles, Command, Eye, Bot } from "lucide-react";
import { KeyboardButton } from "@/components/ui/keyboard-button";

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
        className={`pointer-events-none absolute -inset-4 rounded-full bg-gradient-to-r from-violet-500/40 via-blue-500/40 to-cyan-400/40 blur-xl opacity-0 transition-opacity duration-500 group-hover:opacity-100 ${isAutoPulse ? "opacity-70" : ""
          }`}
        aria-hidden="true"
      />
      <div
        className={`relative z-10 inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 px-4 py-1.5 text-xs font-medium text-white shadow-lg shadow-violet-500/25 transition-all duration-300 hover:shadow-xl hover:shadow-violet-500/30 hover:brightness-110 ${isAutoPulse ? "brightness-110" : ""
          }`}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-white"></span>
        </span>
        <span className="font-semibold text-white">Built for Baguio City teams</span>
      </div>
    </div>
  );
}

function DataScientistBadge() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const target = 18;
    const duration = 1200;
    const stepTime = Math.floor(duration / target);
    let current = 0;
    const timer = setInterval(() => {
      current += 1;
      setCount(current);
      if (current >= target) clearInterval(timer);
    }, stepTime);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="group relative w-full">
      {/* Hover glow */}
      <div
        className="pointer-events-none absolute -inset-2 rounded-2xl bg-gradient-to-r from-violet-500/20 via-blue-500/20 to-cyan-400/20 blur-lg opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        aria-hidden="true"
      />
      {/* Gradient border wrapper — full width */}
      <div className="relative w-full rounded-2xl bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 p-[1.5px] shadow-lg shadow-violet-500/15 group-hover:shadow-xl group-hover:shadow-violet-500/25 transition-all duration-300">
        {/* Inner content */}
        <div className="flex w-full items-center gap-3 rounded-[14px] bg-white/95 backdrop-blur-sm px-4 py-2.5">
          {/* Number badge */}
          <div className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 via-blue-600 to-cyan-500 shadow-md shadow-violet-500/25">
            <span className="text-sm font-black text-white tabular-nums tracking-tight">
              {count}
            </span>
            {/* Live dot */}
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500 border border-white"></span>
            </span>
          </div>
          {/* Text — fills remaining space */}
          <div className="flex flex-col flex-1 min-w-0">
            <span className="text-[11px] font-bold text-slate-900 leading-tight">
              Autonomous Data Scientists
            </span>
            <span className="text-[10px] font-medium text-slate-500 leading-tight">
              Hire your 1st AI team for good governance
            </span>
          </div>
          {/* Bot icon */}
          <Bot className="h-4 w-4 text-violet-400 group-hover:text-violet-600 transition-colors shrink-0" />
        </div>
      </div>
    </div>
  );
}

export function LandingHero() {
  const [hoveredElement, setHoveredElement] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    // Auto-cycle through hover states every 3 seconds
    intervalRef.current = setInterval(() => {
      setHoveredElement(prev => {
        if (prev === 'negative') return 'neutral';
        if (prev === 'neutral') return 'positive';
        if (prev === 'positive') return 'card';
        if (prev === 'card') return 'negative';
        return 'negative'; // Start cycle if null
      });
    }, 3000); // 3 seconds

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleMouseEnter = (element: string) => {
    setHoveredElement(element);
    // Pause auto-cycle when user interacts
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const handleMouseLeave = () => {
    setHoveredElement(null);
    // Restart auto-cycle after a delay
    setTimeout(() => {
      intervalRef.current = setInterval(() => {
        setHoveredElement(prev => {
          if (prev === 'negative') return 'neutral';
          if (prev === 'neutral') return 'positive';
          if (prev === 'positive') return 'card';
          if (prev === 'card') return 'negative';
          return 'negative'; // Start cycle if null
        });
      }, 3000);
    }, 1000); // Wait 1 second after leaving before resuming auto-cycle
  };

  return (
    <section className="relative overflow-hidden bg-slate-50 bg-grid-pattern">
      {/* Abstract Background Elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[20%] -left-[10%] w-[70%] h-[70%] rounded-full bg-gradient-to-br from-violet-200/30 via-blue-200/30 to-transparent blur-3xl animate-fade-in" />
        <div className="absolute top-[10%] -right-[10%] w-[60%] h-[60%] rounded-full bg-gradient-to-bl from-cyan-200/30 via-emerald-100/30 to-transparent blur-3xl animate-fade-in" style={{ animationDelay: '0.5s' }} />
      </div>

      <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-12 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:py-16 xl:px-8">
        {/* Left Content */}
        <div className="flex flex-col justify-center space-y-6 lg:max-w-2xl z-10">
          <div className="flex flex-wrap gap-3 items-center">
            <BaguioTeamsPill />
            <div className="group relative inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/50 px-4 py-1.5 text-xs font-semibold text-emerald-700 backdrop-blur-sm transition-all hover:bg-emerald-100/50 hover:shadow-md hover:shadow-emerald-500/10 active:scale-95">
              <Sparkles className="h-3 w-3 text-emerald-500 animate-pulse" />
              <span>Thesis Grade Research AI Architecture</span>
            </div>
          </div>

          <div className="space-y-4">
            <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl leading-[1.1]">
              Monitor public sentiment <br />
              <span className="bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 bg-clip-text text-transparent">
                before it becomes a crisis.
              </span>
            </h1>

            <p className="max-w-lg text-base leading-relaxed text-slate-600">
              Hinaing turns noisy Web, Facebook, and Reddit conversations into clear, actionable briefings so Baguio City
              decision-makers can respond faster and plan better.
            </p>
            <p className="max-w-lg text-[12px] font-bold uppercase tracking-[0.2em] text-violet-600/80 animate-pulse">
              The agentic AI that actually works for your better future — not just hard-coded logic
            </p>

            <div className="grid gap-2.5 sm:grid-cols-3 pt-2">
              <div className="group rounded-2xl border border-white/50 bg-white/40 p-2.5 shadow-lg shadow-slate-200/50 backdrop-blur-sm transition-all hover:bg-white/60 hover:shadow-lg hover:shadow-violet-100/50 hover:-translate-y-1">
                <div className="mb-1.5 inline-flex rounded-lg bg-violet-100 p-1.5 text-violet-600 group-hover:scale-110 transition-transform">
                  <MessageSquare className="h-3 w-3" />
                </div>
                <p className="text-lg font-bold text-slate-900">4.3k+</p>
                <p className="text-[9px] font-medium text-slate-500 uppercase tracking-wide">Conversations</p>
              </div>
              <div className="group rounded-2xl border border-white/50 bg-white/40 p-2.5 shadow-lg shadow-slate-200/50 backdrop-blur-sm transition-all hover:bg-white/60 hover:shadow-lg hover:shadow-blue-100/50 hover:-translate-y-1">
                <div className="mb-1.5 inline-flex rounded-lg bg-blue-100 p-1.5 text-blue-600 group-hover:scale-110 transition-transform">
                  <MapPin className="h-3 w-3" />
                </div>
                <p className="text-lg font-bold text-slate-900">40+</p>
                <p className="text-[9px] font-medium text-slate-500 uppercase tracking-wide">Barangays</p>
              </div>
              <div className="group rounded-2xl border border-white/50 bg-white/40 p-2.5 shadow-lg shadow-slate-200/50 backdrop-blur-sm transition-all hover:bg-white/60 hover:shadow-lg hover:shadow-cyan-100/50 hover:-translate-y-1">
                <div className="mb-1.5 inline-flex rounded-lg bg-cyan-100 p-1.5 text-cyan-600 group-hover:scale-110 transition-transform">
                  <Share2 className="h-3 w-3" />
                </div>
                <p className="text-lg font-bold text-slate-900">3</p>
                <p className="text-[9px] font-medium text-slate-500 uppercase tracking-wide">Major Channels</p>
              </div>
            </div>
            <DataScientistBadge />
          </div>

          <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <KeyboardButton
              variant="primary"
              size="md"
              icon={<Command className="h-4 w-4" />}
              badge="⌘K"
              href="/app"

            >
              Open Console
            </KeyboardButton>
            <KeyboardButton
              variant="secondary"
              size="md"
              icon={<Eye className="h-4 w-4" />}
              badge="Demo"
              href="#live-preview"
            >
              View Sample Briefing
            </KeyboardButton>
          </div>
        </div>

        {/* Right Content (3D Card) */}
        <div className="relative lg:flex-1 w-full perspective-1000 flex items-center justify-center lg:justify-end">
          <div
            className="absolute -right-20 -top-20 h-[500px] w-[500px] rounded-full bg-gradient-to-br from-violet-400/20 to-blue-400/20 blur-[100px]"
            aria-hidden="true"
          />

          <div className="relative w-full max-w-[440px] group">
            <div className={`relative transform transition-all duration-700 ${hoveredElement === 'card' ? 'scale-[1.02] rotate-1' : 'scale-100 rotate-0'
              }`}>
              {/* Animated Rainbow Border - Subtle Glow */}
              <div className="absolute -inset-[6px] rounded-[2.2rem] bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 opacity-30 blur-lg animate-rainbow-border" />

              {/* Gradient Border Wrapper */}
              <div className="relative rounded-[2rem] bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 p-[1.5px] animate-rainbow-border">
                {/* Classic Ribbon Style with Stitched Look - Positioned at top corner */}
                <div className="absolute -top-3 -right-1 z-20">
                  {/* Main ribbon body */}
                  <div className="relative flex items-stretch">
                    {/* Ribbon tail left - stitched edge */}
                    <div className="relative w-5 bg-gradient-to-b from-violet-700 to-violet-600" style={{ clipPath: 'polygon(0 0, 100% 0, 80% 50%, 100% 100%, 0 100%)' }}>
                      <div className="absolute inset-0 border-r-2 border-dashed border-violet-400/50" />
                    </div>
                    {/* Ribbon body with stitched border effect - center text vertically */}
                    <div className="relative flex items-center bg-gradient-to-r from-violet-600 via-blue-600 to-cyan-500 px-5 py-3 shadow-lg">
                      {/* Stitched border effect */}
                      <div className="absolute inset-1 border-2 border-dashed border-white/30 rounded-sm" />
                      <span className="relative z-10 text-[9px] font-bold uppercase tracking-wider text-white whitespace-nowrap">
                        State-of-the-art Agentic AI
                      </span>
                    </div>
                    {/* Ribbon tail right - stitched edge */}
                    <div className="relative w-5 bg-gradient-to-b from-cyan-500 to-cyan-400" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 20% 50%, 0 100%)' }}>
                      <div className="absolute inset-0 border-l-2 border-dashed border-cyan-300/50" />
                    </div>
                  </div>
                </div>
                <Card
                  className="relative h-full w-full rounded-[1.9rem] border-0 bg-white/90 p-6 shadow-2xl shadow-slate-200/50 backdrop-blur-xl"
                  onMouseEnter={() => handleMouseEnter('card')}
                  onMouseLeave={handleMouseLeave}
                >
                  <div className="absolute inset-0 rounded-[1.9rem] bg-gradient-to-br from-white/50 to-white/0 pointer-events-none" />

                  <div className="relative z-10">
                    <div className="mb-5 flex items-center justify-between">
                      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-bold uppercase tracking-wider text-slate-600">
                        <span className="relative flex h-2.5 w-2.5">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                        </span>
                        Live Snapshot
                      </span>
                      <span className="text-xs font-medium text-slate-400">Just now</span>
                    </div>

                    <div className="space-y-5">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-1">Overall Sentiment</p>
                        <p className="text-xl font-bold text-slate-900 tracking-tight">Cautious but engaged</p>
                        <p className="mt-2 text-sm text-slate-600 leading-relaxed">
                          Infrastructure and transport issues dominate, but support remains high for cleanup and tourism efforts.
                        </p>
                      </div>

                      <div className="grid grid-cols-3 gap-2">
                        <div
                          className={`rounded-xl p-3 text-center transition-all duration-500 ${hoveredElement === 'negative' || hoveredElement === 'card'
                            ? 'bg-rose-100'
                            : 'bg-rose-50'
                            }`}
                          onMouseEnter={() => handleMouseEnter('negative')}
                          onMouseLeave={handleMouseLeave}
                        >
                          <p className="text-lg font-bold text-rose-600">52%</p>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-rose-700/70">Negative</p>
                        </div>
                        <div
                          className={`rounded-xl p-3 text-center transition-all duration-500 ${hoveredElement === 'neutral' || hoveredElement === 'card'
                            ? 'bg-slate-100'
                            : 'bg-slate-50'
                            }`}
                          onMouseEnter={() => handleMouseEnter('neutral')}
                          onMouseLeave={handleMouseLeave}
                        >
                          <p className="text-lg font-bold text-slate-700">31%</p>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-600/70">Neutral</p>
                        </div>
                        <div
                          className={`rounded-xl p-3 text-center transition-all duration-500 ${hoveredElement === 'positive' || hoveredElement === 'card'
                            ? 'bg-emerald-100'
                            : 'bg-emerald-50'
                            }`}
                          onMouseEnter={() => handleMouseEnter('positive')}
                          onMouseLeave={handleMouseLeave}
                        >
                          <p className="text-lg font-bold text-emerald-600">17%</p>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-700/70">Positive</p>
                        </div>
                      </div>

                      <div className="rounded-xl bg-slate-50 p-4 border border-slate-100">
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">Tonight's Highlights</p>
                        <ul className="space-y-2.5">
                          <li className="flex items-start gap-2.5 text-sm text-slate-600">
                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-rose-400 flex-shrink-0" />
                            Rising complaints on evening traffic in Session Road.
                          </li>
                          <li className="flex items-start gap-2.5 text-sm text-slate-600">
                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-amber-400 flex-shrink-0" />
                            Persistent chatter on water reliability in barangays.
                          </li>
                          <li className="flex items-start gap-2.5 text-sm text-slate-600">
                            <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-emerald-400 flex-shrink-0" />
                            Strong positive sentiment around cleanup efforts.
                          </li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
