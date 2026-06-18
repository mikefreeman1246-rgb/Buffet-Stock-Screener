import { createContext, useContext } from "react";
import type { ScreenerController } from "../hooks/useScreenerController";

/**
 * Shares the screener controller with the layout-level <AppHeader>, which lives
 * in Layout.Header — physically outside the tabbed <Content> / <ScreenerView>.
 * App.tsx owns the controller (one instance) and provides it here so the header
 * can still drive the screener (Pull Data, open Assumptions) exactly as before.
 */
export const ScreenerContext = createContext<ScreenerController | null>(null);

export function useScreenerController_ctx(): ScreenerController {
  const ctx = useContext(ScreenerContext);
  if (!ctx) throw new Error("ScreenerContext is missing a provider");
  return ctx;
}
