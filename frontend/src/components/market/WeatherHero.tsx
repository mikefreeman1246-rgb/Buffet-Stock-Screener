import { Button, Space, Tag, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import type { WeatherScore } from "../../lib/types";

// Per-level background tint (subtle gradient) + accent, sunny → hurricane.
const LEVEL: Record<number, { from: string; to: string; accent: string }> = {
  1: { from: "#0f2a1f", to: "#0b1a16", accent: "#34d399" },
  2: { from: "#1f2a0f", to: "#161d0b", accent: "#a3e635" },
  3: { from: "#2a230f", to: "#1d180b", accent: "#fbbf24" },
  4: { from: "#2a160f", to: "#1d0f0b", accent: "#fb923c" },
  5: { from: "#2a0f1a", to: "#1d0b12", accent: "#f87171" },
};

// Human-friendly labels for the divergence rules the engine can fire.
const RULE_LABELS: Record<string, string> = {
  hidden_hedging: "Hidden hedging",
  credit_liquidity: "Credit + liquidity squeeze",
  cascade_floor: "Cross-asset cascade",
};

export default function WeatherHero({
  score,
  pulledAt,
  loading,
  onRefresh,
}: {
  score: WeatherScore;
  pulledAt: string;
  loading: boolean;
  onRefresh: () => void;
}) {
  const lv = LEVEL[score.level] ?? LEVEL[3];
  const updated = pulledAt ? new Date(pulledAt) : null;

  return (
    <div
      style={{
        background: `linear-gradient(135deg, ${lv.from} 0%, ${lv.to} 100%)`,
        border: "1px solid rgba(255,255,255,0.08)",
        borderLeft: `4px solid ${lv.accent}`,
        borderRadius: 8,
        padding: "20px 24px",
        marginBottom: 16,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
        flexWrap: "wrap",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 18, minWidth: 0 }}>
        <span style={{ fontSize: 52, lineHeight: 1 }}>{score.icon}</span>
        <div style={{ minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
            <span style={{ fontSize: 25, fontWeight: 700, color: "#e8eaed" }}>{score.weather}</span>
            <Tooltip title="1 Sunny → 5 Hurricane">
              <span style={{ fontSize: 14, fontWeight: 600, color: lv.accent }}>
                Concern {score.level}/5
              </span>
            </Tooltip>
          </div>
          <div style={{ opacity: 0.9, color: "#c7ccd6", marginTop: 4, maxWidth: 620 }}>
            {score.read}
          </div>
          {score.fired_rules.length > 0 && (
            <div style={{ marginTop: 8 }}>
              {score.fired_rules.map((r) => (
                <Tooltip key={r} title="Divergence rule fired — bumped the concern level">
                  <Tag color="error" style={{ marginInlineEnd: 6 }}>
                    ⚠ {RULE_LABELS[r] ?? r}
                  </Tag>
                </Tooltip>
              ))}
            </div>
          )}
        </div>
      </div>

      <Space direction="vertical" align="end" size={6}>
        <Button icon={<ReloadOutlined />} loading={loading} onClick={onRefresh}>
          Refresh
        </Button>
        {updated && (
          <span style={{ fontSize: 11, color: "#8b919e" }}>
            Updated {updated.toLocaleString()}
          </span>
        )}
      </Space>
    </div>
  );
}
