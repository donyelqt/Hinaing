import type { Metadata } from "next";
import { LandingPage } from "@/features/landing";

export const metadata: Metadata = {
  title: "Hinaing – Public Sentiment Radar for Baguio City",
  description:
    "A subtle, modern landing page for Hinaing that explains how the console turns Web, Facebook, and Reddit chatter into actionable briefings.",
};

export default function Landing() {
  return <LandingPage />;
}
