import { useCallback, useEffect, useState } from "react";
import { notification } from "antd";
import { useScreener } from "./useScreener";
import { api } from "../lib/api";
import type { PipelineDone } from "./usePipeline";
import type { Assumptions, MetaStats, TagCount } from "../lib/types";

const UNIVERSE_LABEL: Record<string, string> = {
  sp500: "S&P 500",
  sp1500: "S&P 1500",
};

/**
 * Bundles all screener-tab state, meta loading, and the Pull/Assumptions/Tags
 * handlers that previously lived inline in App.tsx. Extracted verbatim so the
 * screener behaves identically after the tabs refactor; consumed by both the
 * layout-level <AppHeader> (via ScreenerContext) and <ScreenerView>.
 */
export function useScreenerController() {
  const { filters, data, loading, patch, reset, reload } = useScreener();
  const [assumptions, setAssumptions] = useState<Assumptions | null>(null);
  const [stats, setStats] = useState<MetaStats | null>(null);
  const [allTags, setAllTags] = useState<TagCount[]>([]);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const loadTags = useCallback(async () => {
    setAllTags(await api.getTags());
  }, []);

  const loadMeta = useCallback(async () => {
    const [a, s] = await Promise.all([api.getAssumptions(), api.stats()]);
    setAssumptions(a);
    setStats(s);
  }, []);

  useEffect(() => {
    loadMeta();
    loadTags();
  }, [loadMeta, loadTags]);

  const handleTagsChanged = useCallback(() => {
    loadTags();
    reload();
  }, [loadTags, reload]);

  const handleAssumptionsSaved = useCallback(
    (a: Assumptions) => {
      setAssumptions(a);
      reload();
    },
    [reload]
  );

  const handlePullDone = useCallback(
    (done: PipelineDone) => {
      loadMeta();
      reload();
      const label = UNIVERSE_LABEL[done.universe] ?? done.universe;
      const loaded = done.completed - done.failed;
      if (done.status === "paused") {
        notification.warning({
          message: "Pull stopped",
          description: `${loaded} ${label} stocks loaded before stopping.`,
          placement: "bottomRight",
        });
      } else if (done.failed > 0) {
        notification.warning({
          message: `${label} loaded`,
          description: `${loaded} of ${done.total} stocks scored · ${done.failed} skipped (missing/rate-limited data).`,
          placement: "bottomRight",
          duration: 6,
        });
      } else {
        notification.success({
          message: `${label} loaded`,
          description: `${loaded} stocks scored with Graham + Buffett valuations.`,
          placement: "bottomRight",
          duration: 5,
        });
      }
    },
    [loadMeta, reload]
  );

  return {
    filters,
    data,
    loading,
    patch,
    reset,
    reload,
    assumptions,
    stats,
    allTags,
    drawerOpen,
    setDrawerOpen,
    handleTagsChanged,
    handleAssumptionsSaved,
    handlePullDone,
  };
}

export type ScreenerController = ReturnType<typeof useScreenerController>;
