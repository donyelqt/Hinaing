"use client";

import dynamic from "next/dynamic";

const AppContainer = dynamic(
  () => import("@/features/app/components/AppContainer").then((m) => m.AppContainer),
  { ssr: false }
);

export default function ChatAnalyzeRoute() {
    return <AppContainer />;
}
