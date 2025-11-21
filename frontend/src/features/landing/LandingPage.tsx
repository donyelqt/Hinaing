import { LandingHero } from "./components/LandingHero";
import { TrustBar } from "./components/TrustBar";
import { ValuePropsSection } from "./components/ValuePropsSection";
import { LivePreviewSection } from "./components/LivePreviewSection";
import { HowItWorksSection } from "./components/HowItWorksSection";
import { UseCasesSection } from "./components/UseCasesSection";
import { FAQSection } from "./components/FAQSection";
import { FinalCTASection } from "./components/FinalCTASection";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-100">
      <main className="flex flex-col">
        <LandingHero />
        <TrustBar />
        <ValuePropsSection />
        <LivePreviewSection />
        <HowItWorksSection />
        <UseCasesSection />
        <FAQSection />
        <FinalCTASection />
      </main>
    </div>
  );
}
