import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { ScreenerFilterState, ScreenerResponse } from "../lib/types";

export const DEFAULT_FILTERS: ScreenerFilterState = {
  model: "dual",
  graham_verdict: [],
  buffett_verdict: [],
  moat: [],
  conviction: [],
  tags: [],
  sector: [],
  min_margin: null,
  min_price: null,
  max_price: null,
  min_cap: null,
  search: "",
  sort_by: "market_cap",
  sort_dir: "desc",
  page: 1,
  page_size: 50,
};

export function useScreener() {
  const [filters, setFilters] = useState<ScreenerFilterState>(DEFAULT_FILTERS);
  const [data, setData] = useState<ScreenerResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  const fetchNow = useCallback(async (f: ScreenerFilterState) => {
    setLoading(true);
    try {
      setData(await api.screen(f));
    } finally {
      setLoading(false);
    }
  }, []);

  // debounce filter changes (300ms) — matches the Options app UX
  useEffect(() => {
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => fetchNow(filters), 300);
    return () => window.clearTimeout(timer.current);
  }, [filters, fetchNow]);

  const patch = useCallback((p: Partial<ScreenerFilterState>) => {
    setFilters((prev) => ({
      ...prev,
      ...p,
      // any change other than paging resets to page 1
      page: "page" in p ? (p.page as number) : 1,
    }));
  }, []);

  const reset = useCallback(() => setFilters(DEFAULT_FILTERS), []);
  const reload = useCallback(() => fetchNow(filters), [fetchNow, filters]);

  return { filters, data, loading, patch, reset, reload };
}
