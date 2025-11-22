import { MapPin, Globe2, ShieldAlert } from "lucide-react";

export function TrustBar() {
  return (
    <section className="border-y border-slate-100 bg-white/80">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-4 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 xl:px-8">
        <p className="font-medium text-slate-600">
          Designed with LGU planners, crisis responders, and communications teams in mind.
        </p>
        <div className="flex flex-wrap gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
            <MapPin className="h-3 w-3 text-hinaing-blue-600" />
            <span>Focus: Baguio City & nearby areas</span>
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
            <Globe2 className="h-3 w-3 text-hinaing-blue-600" />
            <span>Facebook & Reddit public posts</span>
          </span>
          <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 font-medium text-slate-700">
            <ShieldAlert className="h-3 w-3 text-hinaing-gold" />
            <span>Includes mis/disinformation signals</span>
          </span>
        </div>
      </div>
    </section>
  );
}
