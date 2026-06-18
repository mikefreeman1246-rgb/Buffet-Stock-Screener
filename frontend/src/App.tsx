import { useCallback, useEffect, useState } from "react";
import { ConfigProvider, Layout, notification, theme } from "antd";
import AppHeader from "./components/Header";
import ScreenerFilters from "./components/ScreenerFilters";
import ScreenerTable from "./components/ScreenerTable";
import AssumptionsDrawer from "./components/AssumptionsDrawer";
import { useScreener } from "./hooks/useScreener";
import { api } from "./lib/api";
import type { PipelineDone } from "./hooks/usePipeline";
import type { Assumptions, MetaStats, TagCount } from "./lib/types";

const UNIVERSE_LABEL: Record<string, string> = {
  sp500: "S&P 500",
  sp1500: "S&P 1500",
};

const { Content } = Layout;

const darkTheme = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: "#2dd4bf",
    colorBgBase: "#0b0e14",
    colorBgContainer: "#111520",
    colorBgElevated: "#161b28",
    colorBgLayout: "#0b0e14",
    colorBorder: "rgba(255, 255, 255, 0.10)",
    colorBorderSecondary: "rgba(255, 255, 255, 0.06)",
    colorText: "#e8eaed",
    colorTextSecondary: "#8b919e",
    colorTextTertiary: "#5c6370",
    colorSuccess: "#34d399",
    colorError: "#f87171",
    colorWarning: "#fbbf24",
    colorInfo: "#60a5fa",
    fontFamily: "'DM Sans', system-ui, -apple-system, sans-serif",
    fontSize: 13,
    borderRadius: 6,
    borderRadiusSM: 4,
    borderRadiusLG: 8,
    controlHeight: 32,
    controlHeightSM: 26,
  },
  components: {
    Layout: { headerBg: "#0d1117", headerHeight: 52, headerPadding: "0 20px", bodyBg: "#0b0e14" },
    Table: {
      headerBg: "#111520", headerColor: "#5c6370", rowHoverBg: "#1c2235",
      borderColor: "rgba(255, 255, 255, 0.06)", cellPaddingBlockSM: 8, cellPaddingInlineSM: 10,
    },
    Tabs: { itemColor: "#5c6370", itemActiveColor: "#2dd4bf", itemSelectedColor: "#2dd4bf", inkBarColor: "#2dd4bf" },
    Slider: {
      trackBg: "#2dd4bf", trackHoverBg: "#5eead4", handleColor: "#2dd4bf",
      handleActiveColor: "#5eead4", railBg: "rgba(255,255,255,0.10)",
    },
    Button: { primaryColor: "#0b0e14", fontWeight: 500 },
  },
};

export default function App() {
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

  return (
    <ConfigProvider theme={darkTheme}>
      <Layout style={{ minHeight: "100vh" }}>
        <Layout.Header
          style={{ display: "flex", alignItems: "center", borderBottom: "1px solid rgba(255,255,255,0.08)" }}
        >
          <AppHeader
            stats={stats}
            assumptions={assumptions}
            onOpenAssumptions={() => setDrawerOpen(true)}
            onPullDone={handlePullDone}
          />
        </Layout.Header>
        <Content style={{ padding: "16px 20px 28px" }}>
          <ScreenerFilters
            filters={filters}
            sectors={stats?.sectors ?? []}
            tags={allTags}
            total={data?.total ?? 0}
            rows={data?.results ?? []}
            onChange={patch}
            onReset={reset}
          />
          <ScreenerTable
            data={data}
            loading={loading}
            filters={filters}
            allTags={allTags.map((t) => t.tag)}
            onChange={patch}
            onOverrideSaved={reload}
            onTagsChanged={handleTagsChanged}
          />
        </Content>
        <AssumptionsDrawer
          open={drawerOpen}
          assumptions={assumptions}
          onClose={() => setDrawerOpen(false)}
          onSaved={handleAssumptionsSaved}
        />
      </Layout>
    </ConfigProvider>
  );
}
