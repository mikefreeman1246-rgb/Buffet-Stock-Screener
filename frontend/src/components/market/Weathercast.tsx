/**
 * Market Weathercast dashboard — weather hero + weighted indicator cards.
 *
 * Auto-pulls a snapshot on mount (via useWeather); shows a spinner until the
 * first payload arrives. Indicator cards are ordered by descending weight and
 * only rendered for keys actually present in the snapshot (graceful for any
 * indicator that degraded to "n/a" upstream).
 */
import { useState } from "react";
import { Row, Col, Spin, Button } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { useWeather } from "../../hooks/useWeather";
import { useMarketAnalysis } from "../../hooks/useMarketAnalysis";
import WeatherHero from "./WeatherHero";
import IndicatorCard from "./IndicatorCard";
import WeatherSettingsDrawer from "./WeatherSettingsDrawer";
import IndicatorDetailsDrawer from "./IndicatorDetailsDrawer";
import MarketHealthSummary from "./MarketHealthSummary";

function Legend() {
  const items: [string, string][] = [
    ["#34d399", "Healthy"],
    ["#fbbf24", "Watch"],
    ["#f87171", "Chaos"],
    ["#5c6370", "No data"],
  ];
  return (
    <div style={{ display: "flex", gap: 14, alignItems: "center", flexWrap: "wrap" }}>
      {items.map(([c, label]) => (
        <span key={label} style={{ display: "inline-flex", alignItems: "center", gap: 5, fontSize: 11, color: "#8b919e" }}>
          <span style={{ width: 9, height: 9, borderRadius: 2, background: c, display: "inline-block" }} />
          {label}
        </span>
      ))}
    </div>
  );
}

export default function Weathercast() {
  const { payload, loading, refresh } = useWeather();
  const { analysis, getIndicatorMetadata, refreshAnalysis } = useMarketAnalysis();
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedIndicator, setSelectedIndicator] = useState<string | null>(null);

  if (!payload) {
    return (
      <div style={{ textAlign: "center", padding: 96, color: "#8b919e" }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, fontSize: 13 }}>Reading the market weather…</div>
      </div>
    );
  }

  // Order indicator cards by descending weight; only render keys present in the
  // snapshot (an indicator that failed upstream simply drops off the grid).
  const order = Object.entries(payload.thresholds)
    .sort((a, b) => b[1].weight - a[1].weight)
    .map(([k]) => k)
    .filter((k) => payload.indicators[k]);

  // Get selected indicator details for the drawer
  const selectedIndKey = selectedIndicator;
  const selectedInd = selectedIndKey ? payload.indicators[selectedIndKey] : null;
  const selectedCfg = selectedIndKey ? payload.thresholds[selectedIndKey] : null;
  const selectedState = selectedIndKey ? payload.score.states[selectedIndKey] : null;
  const selectedMetadata = selectedIndKey ? getIndicatorMetadata(selectedIndKey) : null;

  const handleIndicatorClick = (key: string) => {
    setSelectedIndicator(key);
    setDetailsOpen(true);
  };

  const handleDetailsClose = () => {
    setDetailsOpen(false);
    setSelectedIndicator(null);
  };

  const handleSettingsSaved = () => {
    refresh();
    refreshAnalysis();
  };

  return (
    <div>
      <WeatherHero
        score={payload.score}
        pulledAt={payload.pulled_at}
        loading={loading}
        onRefresh={() => {
          refresh();
          refreshAnalysis();
        }}
      />

      {/* Market Health Summary */}
      <MarketHealthSummary analysis={analysis} loading={false} />

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: 12,
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <Legend />
        <Button icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>
          Adjust ranges
        </Button>
      </div>

      <Row gutter={[12, 12]}>
        {order.map((k) => (
          <Col xs={24} sm={12} md={8} lg={6} xxl={4} key={k}>
            <IndicatorCard
              ind={payload.indicators[k]}
              cfg={payload.thresholds[k]}
              state={payload.score.states[k]}
              onClick={() => handleIndicatorClick(k)}
            />
          </Col>
        ))}
      </Row>

      <WeatherSettingsDrawer
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSaved={handleSettingsSaved}
      />

      <IndicatorDetailsDrawer
        open={detailsOpen}
        onClose={handleDetailsClose}
        ind={selectedInd}
        cfg={selectedCfg}
        state={selectedState}
        metadata={selectedMetadata}
      />
    </div>
  );
}
