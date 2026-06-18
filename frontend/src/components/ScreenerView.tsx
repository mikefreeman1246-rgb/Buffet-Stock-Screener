import ScreenerFilters from "./ScreenerFilters";
import ScreenerTable from "./ScreenerTable";
import AssumptionsDrawer from "./AssumptionsDrawer";
import { useScreenerController_ctx } from "./ScreenerContext";

/**
 * The "Value Screener" tab. Renders the filters + table + assumptions drawer,
 * reading all state from the shared ScreenerController (provided by App.tsx so
 * the layout-level header can drive the same screener). Behavior is identical
 * to the pre-tabs App.tsx <Content> body.
 */
export default function ScreenerView() {
  const {
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
  } = useScreenerController_ctx();

  return (
    <>
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
      <AssumptionsDrawer
        open={drawerOpen}
        assumptions={assumptions}
        onClose={() => setDrawerOpen(false)}
        onSaved={handleAssumptionsSaved}
      />
    </>
  );
}
