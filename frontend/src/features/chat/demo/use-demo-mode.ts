"use client";

import * as React from "react";

/**
 * Demo mode UI config.
 *
 * Demo mode is off by default, because the live path is what production ships.
 * When it is on, the analyze page swaps its shortcut prompt for the six-theme
 * sweep and answers from the frozen corpus, so a demo runs with zero network
 * calls and cannot be rate limited.
 *
 * The flag is persisted per browser rather than per account, so a demo laptop
 * keeps its setting across reloads without touching the backend.
 */

export const DEMO_MODE_STORAGE_KEY = "hinaing:demo-mode";

export type DemoModeConfig = {
  enabled: boolean;
  setEnabled: (next: boolean) => void;
};

export function useDemoMode(): DemoModeConfig {
  const [enabled, setEnabledState] = React.useState(false);

  React.useEffect(() => {
    try {
      const stored = window.localStorage.getItem(DEMO_MODE_STORAGE_KEY);
      if (stored === "on") {
        setEnabledState(true);
      }
    } catch {
      // Private mode or a blocked storage partition. The default stays off.
    }
  }, []);

  const setEnabled = React.useCallback((next: boolean) => {
    setEnabledState(next);
    try {
      window.localStorage.setItem(DEMO_MODE_STORAGE_KEY, next ? "on" : "off");
    } catch {
      // The in-memory flag still applies for this session.
    }
  }, []);

  return { enabled, setEnabled };
}