import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";
import type { DashboardPayload } from "../lib/types";

export function useWeather() {
  const [payload, setPayload] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.marketRefresh();
      setPayload(res.payload);
    } finally {
      setLoading(false);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.marketDashboard();
      // Accept a cached snapshot only if it's fresh AND well-formed; otherwise
      // (empty, stale, or a malformed/legacy payload) auto-pull on tab open.
      if (res.payload && !res.stale && res.payload.score) setPayload(res.payload);
      else await refresh();
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  useEffect(() => {
    load();
  }, [load]);

  return { payload, loading, refresh, setPayload };
}
