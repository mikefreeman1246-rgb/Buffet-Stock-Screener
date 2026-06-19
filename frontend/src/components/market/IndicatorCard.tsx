import { Card, Tag, Tooltip } from "antd";
import Sparkline from "./Sparkline";
import type { Indicator, ThresholdCfg } from "../../lib/types";

// Status pill + accent colors mirror the App.tsx theme tokens
// (success / warning / error). state: 1 GREEN, 2 YELLOW, 3 RED, null = no data.
const PILL: Record<number, { color: string; text: string; accent: string }> = {
  1: { color: "success", text: "🟢 Healthy", accent: "#34d399" },
  2: { color: "warning", text: "🟡 Watch", accent: "#fbbf24" },
  3: { color: "error", text: "🔴 Chaos", accent: "#f87171" },
};

const NA = { color: "default", text: "n/a", accent: "#5c6370" };

/** Format a raw display value compactly without dragging in a number lib. */
function fmt(value: number | null): string {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs !== 0 && abs < 1) return value.toFixed(2);
  if (abs < 100) return value.toFixed(1);
  return Math.round(value).toLocaleString();
}

export default function IndicatorCard({
  ind,
  cfg,
  state,
  onClick,
}: {
  ind: Indicator;
  cfg: ThresholdCfg;
  state: number | null;
  onClick?: () => void;
}) {
  const pill = state ? PILL[state] : NA;
  // Threshold bands only make sense when the plotted series is in the same
  // domain as the thresholds — i.e. the metric IS the latest level (vix, skew,
  // credit…). Derived-metric indicators (bps/wk, %/mo, stress score) have
  // metric !== value, so we plot the raw series with bands suppressed.
  const sameDomain = ind.value != null && ind.metric === ind.value;

  return (
    <Card
      size="small"
      styles={{ body: { padding: "10px 12px" } }}
      style={{
        borderLeft: `3px solid ${pill.accent}`,
        height: "100%",
        cursor: "pointer",
        transition: "all 0.2s ease",
      }}
      onMouseEnter={(e) => {
        const elem = e.currentTarget;
        elem.style.boxShadow = "0 4px 12px rgba(0,0,0,0.3)";
        elem.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        const elem = e.currentTarget;
        elem.style.boxShadow = "";
        elem.style.transform = "";
      }}
      onClick={onClick}
      title={
        <Tooltip title={`weight ${cfg.weight} · green ≤ ${cfg.green_max} · yellow ≤ ${cfg.yellow_max}`}>
          <span style={{ fontSize: 12.5 }}>{cfg.label}</span>
        </Tooltip>
      }
      extra={<Tag color={pill.color} style={{ marginInlineEnd: 0 }}>{pill.text}</Tag>}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 8 }}>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 22, fontWeight: 600, lineHeight: 1.1, color: "#e8eaed" }}>
            {fmt(ind.value)}
            {ind.value != null && cfg.unit ? (
              <span style={{ fontSize: 13, fontWeight: 400, color: "#8b919e", marginLeft: 2 }}>
                {cfg.unit}
              </span>
            ) : null}
          </div>
          <div
            style={{
              fontSize: 11,
              color: "#8b919e",
              marginTop: 3,
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: 120,
            }}
          >
            {ind.trend}
          </div>
        </div>
        <Sparkline
          series={ind.series}
          greenMax={cfg.green_max}
          yellowMax={cfg.yellow_max}
          state={state}
          showBands={sameDomain}
          width={120}
          height={38}
        />
      </div>
    </Card>
  );
}
