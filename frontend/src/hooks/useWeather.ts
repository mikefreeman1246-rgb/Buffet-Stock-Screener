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
      if (res.payload && !res.stale) setPayload(res.payload);
      else await refresh(); // empty or stale -> auto-pull on tab open
    } finally {
      setLoading(false);
    }
  }, [refresh]);

  useEffect(() => {
    load();
  }, [load]);

  return { payload, loading, refresh, setPayload };
}
