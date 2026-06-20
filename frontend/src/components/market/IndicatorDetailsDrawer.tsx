import { Drawer, Divider, Tag, Space, Row, Col, Empty } from "antd";
import { CloseOutlined } from "@ant-design/icons";
import type { Indicator, ThresholdCfg } from "../../lib/types";

interface IndicatorDetailsDrawerProps {
  open: boolean;
  onClose: () => void;
  ind: Indicator | null;
  cfg: ThresholdCfg | null;
  state: number | null;
  metadata: Record<string, any> | null;
}

const STATE_LABEL: Record<number, { label: string; color: string; icon: string }> = {
  1: { label: "Healthy", color: "success", icon: "🟢" },
  2: { label: "Watch", color: "warning", icon: "🟡" },
  3: { label: "Chaos", color: "error", icon: "🔴" },
};

function fmt(value: number | null): string {
  if (value == null) return "—";
  const abs = Math.abs(value);
  if (abs !== 0 && abs < 1) return value.toFixed(2);
  if (abs < 100) return value.toFixed(1);
  return Math.round(value).toLocaleString();
}

export default function IndicatorDetailsDrawer({
  open,
  onClose,
  ind,
  cfg,
  state,
  metadata,
}: IndicatorDetailsDrawerProps) {
  if (!ind || !cfg || !metadata) {
    return (
      <Drawer
        title="Indicator Details"
        placement="right"
        onClose={onClose}
        open={open}
        width={500}
      >
        <Empty description="Select an indicator to view details" />
      </Drawer>
    );
  }

  const stateInfo = state ? STATE_LABEL[state] : { label: "No data", color: "default", icon: "?" };

  return (
    <Drawer
      title={cfg.label}
      placement="right"
      onClose={onClose}
      open={open}
      width={500}
      closeIcon={<CloseOutlined />}
    >
      {/* Current Status */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 11, textTransform: "uppercase", color: "#8b919e", fontWeight: 600 }}>
            Current Status
          </span>
        </div>
        <Row gutter={16}>
          <Col span={12}>
            <div
              style={{
                background: "rgba(255,255,255,0.04)",
                padding: 12,
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div style={{ fontSize: 24, fontWeight: 600, color: "#e8eaed" }}>
                {fmt(ind.value)}
                {ind.value != null && cfg.unit && (
                  <span style={{ fontSize: 13, color: "#8b919e", marginLeft: 4 }}>{cfg.unit}</span>
                )}
              </div>
              <div style={{ fontSize: 11, color: "#8b919e", marginTop: 4 }}>{ind.trend}</div>
            </div>
          </Col>
          <Col span={12}>
            <div
              style={{
                background: "rgba(255,255,255,0.04)",
                padding: 12,
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div style={{ fontSize: 28, marginBottom: 4 }}>{stateInfo.icon}</div>
              <Tag color={stateInfo.color} style={{ marginBottom: 4 }}>
                {stateInfo.label}
              </Tag>
              <div style={{ fontSize: 11, color: "#8b919e", marginTop: 2 }}>Weight: {cfg.weight}</div>
            </div>
          </Col>
        </Row>
      </div>

      <Divider />

      {/* What It Measures */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#e8eaed", marginBottom: 8 }}>
          What It Measures
        </div>
        <div style={{ fontSize: 13, color: "#c7ccd6", lineHeight: 1.6 }}>
          {metadata.description}
        </div>
      </div>

      {/* Thresholds & Ranges */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#e8eaed", marginBottom: 8 }}>
          Thresholds &amp; Ranges
        </div>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div style={{ fontSize: 12 }}>
            <span style={{ color: "#34d399", fontWeight: 600 }}>🟢 Healthy:</span>{" "}
            <span style={{ color: "#8b919e" }}>
              {cfg.unit} ≤ {cfg.green_max}
            </span>
          </div>
          <div style={{ fontSize: 12 }}>
            <span style={{ color: "#fbbf24", fontWeight: 600 }}>🟡 Watch:</span>{" "}
            <span style={{ color: "#8b919e" }}>
              {cfg.green_max} &lt; {cfg.unit} ≤ {cfg.yellow_max}
            </span>
          </div>
          <div style={{ fontSize: 12 }}>
            <span style={{ color: "#f87171", fontWeight: 600 }}>🔴 Chaos:</span>{" "}
            <span style={{ color: "#8b919e" }}>{cfg.unit} &gt; {cfg.yellow_max}</span>
          </div>
        </Space>

        {metadata.typical_ranges && (
          <div style={{ marginTop: 12, fontSize: 12 }}>
            <div style={{ color: "#8b919e", marginBottom: 6 }}>Typical Ranges:</div>
            {Object.entries(metadata.typical_ranges).map(([label, range]) => (
              <div key={label} style={{ color: "#5c6370", marginBottom: 4 }}>
                <span style={{ textTransform: "capitalize" }}>{label.replace(/_/g, " ")}:</span> {String(range)}
              </div>
            ))}
          </div>
        )}
      </div>

      <Divider />

      {/* Interpretation Guide */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#e8eaed", marginBottom: 8 }}>
          What It Means
        </div>
        <Space direction="vertical" style={{ width: "100%" }} size="middle">
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#34d399", marginBottom: 4 }}>
              🟢 Healthy Conditions
            </div>
            <div style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.5 }}>
              {metadata.healthy}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#fbbf24", marginBottom: 4 }}>
              🟡 Watch/Caution
            </div>
            <div style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.5 }}>
              {metadata.watch}
            </div>
          </div>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: "#f87171", marginBottom: 4 }}>
              🔴 Chaos/Stress
            </div>
            <div style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.5 }}>
              {metadata.chaos}
            </div>
          </div>
        </Space>
      </div>

      <Divider />

      {/* Component Signals (cascade risk and similar composite indicators) */}
      {metadata.components && Array.isArray(metadata.components) && (
        <>
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#e8eaed", marginBottom: 8 }}>
              Component Signals
            </div>
            <Space direction="vertical" style={{ width: "100%" }} size="small">
              {metadata.components.map((c: { name: string; signal: string; role: string }, i: number) => (
                <div
                  key={i}
                  style={{
                    background: "rgba(255,255,255,0.03)",
                    border: "1px solid rgba(255,255,255,0.07)",
                    borderRadius: 6,
                    padding: "8px 12px",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 3 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "#c7ccd6" }}>{c.name}</span>
                    <span style={{ fontSize: 11, color: "#fbbf24", marginLeft: 8, whiteSpace: "nowrap" }}>{c.signal}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#5c6370", lineHeight: 1.5 }}>{c.role}</div>
                </div>
              ))}
            </Space>

            {/* Scoring legend for composite indicators */}
            {metadata.scoring && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 11, color: "#8b919e", marginBottom: 6, fontWeight: 500 }}>Score Thresholds</div>
                {Object.entries(metadata.scoring).map(([key, desc]) => {
                  const color = key.startsWith("1") ? "#34d399" : key.startsWith("2") ? "#fbbf24" : "#f87171";
                  const icon = key.startsWith("1") ? "🟢" : key.startsWith("2") ? "🟡" : "🔴";
                  return (
                    <div key={key} style={{ fontSize: 11, color: "#8b919e", marginBottom: 4 }}>
                      <span style={{ color }}>{icon} </span>
                      <span style={{ color }}>{String(desc)}</span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Historical examples */}
            {metadata.historical_examples && (
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 11, color: "#8b919e", marginBottom: 6, fontWeight: 500 }}>Historical Examples</div>
                {Object.entries(metadata.historical_examples).map(([key, desc]) => (
                  <div key={key} style={{ fontSize: 11, color: "#5c6370", marginBottom: 4 }}>
                    <span style={{ color: "#8b919e" }}>{key.replace(/_/g, " ")}:</span>{" "}
                    {String(desc)}
                  </div>
                ))}
              </div>
            )}
          </div>
          <Divider />
        </>
      )}

      {/* Market Implications */}
      {metadata.implications && (
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, color: "#e8eaed", marginBottom: 8 }}>
            Market Implications
          </div>
          <Space direction="vertical" style={{ width: "100%" }} size="small">
            <div>
              <div style={{ fontSize: 11, color: "#8b919e", fontWeight: 500 }}>Short-Term (Days–Weeks)</div>
              <div style={{ fontSize: 12, color: "#c7ccd6", marginTop: 4 }}>
                {metadata.implications.short_term}
              </div>
            </div>
            <div>
              <div style={{ fontSize: 11, color: "#8b919e", fontWeight: 500 }}>Long-Term (Months)</div>
              <div style={{ fontSize: 12, color: "#c7ccd6", marginTop: 4 }}>
                {metadata.implications.long_term}
              </div>
            </div>
            {metadata.implications.bullish_threshold && (
              <div>
                <div style={{ fontSize: 11, color: "#34d399", fontWeight: 500 }}>Bullish Threshold</div>
                <div style={{ fontSize: 12, color: "#c7ccd6", marginTop: 2 }}>
                  {metadata.implications.bullish_threshold}
                </div>
              </div>
            )}
            {metadata.implications.bearish_threshold && (
              <div>
                <div style={{ fontSize: 11, color: "#f87171", fontWeight: 500 }}>Bearish Threshold</div>
                <div style={{ fontSize: 12, color: "#c7ccd6", marginTop: 2 }}>
                  {metadata.implications.bearish_threshold}
                </div>
              </div>
            )}
          </Space>
        </div>
      )}
    </Drawer>
  );
}
