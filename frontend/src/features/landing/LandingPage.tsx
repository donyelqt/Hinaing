import { LandingHeader } from "./components/LandingHeader";
import { LandingHero } from "./components/LandingHero";
import { PartnerBadges } from "./components/PartnerBadges";
import { TrustBar } from "./components/TrustBar";
import { ValuePropsSection } from "./components/ValuePropsSection";
import { LivePreviewSection } from "./components/LivePreviewSection";
import { HowItWorksSection } from "./components/HowItWorksSection";
import { TechniquesSection } from "./components/TechniquesSection";
import { UseCasesSection } from "./components/UseCasesSection";
import { FAQSection } from "./components/FAQSection";
import { FinalCTASection } from "./components/FinalCTASection";
import { ScrollReveal } from "./components/ScrollReveal";

export function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-100">
      <main className="flex flex-col">
        <LandingHeader />
        <ScrollReveal>
          <LandingHero />
        </ScrollReveal>
        <ScrollReveal delay={80}>
          <PartnerBadges />
        </ScrollReveal>
        <ScrollReveal delay={120}>
          <TrustBar />
        </ScrollReveal>
        <ScrollReveal delay={160}>
          <ValuePropsSection />
        </ScrollReveal>
        <ScrollReveal delay={200}>
          <LivePreviewSection />
        </ScrollReveal>
        <ScrollReveal delay={240}>
          <HowItWorksSection />
        </ScrollReveal>
        <ScrollReveal delay={280}>
          <TechniquesSection />
        </ScrollReveal>
        <ScrollReveal delay={320}>
          <UseCasesSection />
        </ScrollReveal>
        <ScrollReveal delay={360}>
          <FAQSection />
        </ScrollReveal>
        <ScrollReveal delay={400}>
          <FinalCTASection />
        </ScrollReveal>
      </main>
    </div>
  );
}
