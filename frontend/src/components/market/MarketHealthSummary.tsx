import { Card, Row, Col, Empty, Space, Spin } from "antd";
import { ArrowUpOutlined, ArrowDownOutlined } from "@ant-design/icons";
import type { ReactNode } from "react";

interface MarketAnalysis {
  health: string;
  short_term: {
    direction: string;
    reasoning: string;
    horizon: string;
  };
  long_term: {
    direction: string;
    reasoning: string;
    horizon: string;
  };
  signal_breakdown: {
    healthy_count: number;
    watch_count: number;
    chaos_count: number;
    total_count: number;
  };
  top_risks: string[];
  opportunities: string[];
}

interface MarketHealthSummaryProps {
  analysis: MarketAnalysis | null;
  loading?: boolean;
}

function getHealthColor(health: string): string {
  if (health.includes("Bullish")) return "#34d399";
  if (health.includes("Bearish")) return "#f87171";
  return "#fbbf24";
}

function getDirectionIcon(direction: string): ReactNode {
  if (direction.includes("Up")) return <ArrowUpOutlined style={{ color: "#34d399" }} />;
  if (direction.includes("Down")) return <ArrowDownOutlined style={{ color: "#f87171" }} />;
  return null;
}

export default function MarketHealthSummary({
  analysis,
  loading = false,
}: MarketHealthSummaryProps) {
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Spin size="large" />
        <div style={{ marginTop: 16, fontSize: 13, color: "#8b919e" }}>Analyzing market health…</div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <Empty
        description="No analysis available. Refresh the market data first."
        style={{ margin: "48px 0" }}
      />
    );
  }

  const healthColor = getHealthColor(analysis.health);
  const shortTermIcon = getDirectionIcon(analysis.short_term.direction);
  const longTermIcon = getDirectionIcon(analysis.long_term.direction);

  const totalSignals = analysis.signal_breakdown.total_count || 1;
  const healthyPct = Math.round(
    (analysis.signal_breakdown.healthy_count / totalSignals) * 100
  );
  const watchPct = Math.round((analysis.signal_breakdown.watch_count / totalSignals) * 100);
  const chaosPct = Math.round((analysis.signal_breakdown.chaos_count / totalSignals) * 100);

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#e8eaed", margin: 0 }}>Market Health &amp; Direction</h3>
      </div>

      {/* Overall Health */}
      <Card
        style={{
          background: "linear-gradient(135deg, rgba(52, 211, 153, 0.1) 0%, rgba(52, 211, 153, 0.05) 100%)",
          border: `1px solid ${healthColor}40`,
          marginBottom: 16,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: 40, textAlign: "center" }}>
            {analysis.health.includes("Bullish") && "📈"}
            {analysis.health.includes("Bearish") && "📉"}
            {analysis.health === "Neutral" && "➡️"}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, color: "#8b919e", marginBottom: 4 }}>Overall Market Health</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: healthColor, marginBottom: 6 }}>
              {analysis.health}
            </div>
            <div style={{ fontSize: 12, color: "#c7ccd6" }}>
              {analysis.signal_breakdown.healthy_count} healthy • {analysis.signal_breakdown.watch_count} warning •{" "}
              {analysis.signal_breakdown.chaos_count} elevated
            </div>
          </div>
        </div>
      </Card>

      {/* Signal Distribution */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#8b919e", textTransform: "uppercase" }}>
            Signal Breakdown
          </span>
        </div>
        <Row gutter={12}>
          <Col span={8}>
            <div
              style={{
                background: "rgba(52, 211, 153, 0.1)",
                padding: 12,
                borderRadius: 6,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 18, fontWeight: 700, color: "#34d399" }}>
                {analysis.signal_breakdown.healthy_count}
              </div>
              <div style={{ fontSize: 11, color: "#8b919e", marginTop: 4 }}>Healthy</div>
              <div style={{ fontSize: 10, color: "#5c6370" }}>{healthyPct}%</div>
            </div>
          </Col>
          <Col span={8}>
            <div
              style={{
                background: "rgba(251, 191, 36, 0.1)",
                padding: 12,
                borderRadius: 6,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 18, fontWeight: 700, color: "#fbbf24" }}>
                {analysis.signal_breakdown.watch_count}
              </div>
              <div style={{ fontSize: 11, color: "#8b919e", marginTop: 4 }}>Watch</div>
              <div style={{ fontSize: 10, color: "#5c6370" }}>{watchPct}%</div>
            </div>
          </Col>
          <Col span={8}>
            <div
              style={{
                background: "rgba(248, 113, 113, 0.1)",
                padding: 12,
                borderRadius: 6,
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 18, fontWeight: 700, color: "#f87171" }}>
                {analysis.signal_breakdown.chaos_count}
              </div>
              <div style={{ fontSize: 11, color: "#8b919e", marginTop: 4 }}>Elevated</div>
              <div style={{ fontSize: 10, color: "#5c6370" }}>{chaosPct}%</div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Short-Term Direction */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#8b919e", textTransform: "uppercase" }}>
            Short-Term Outlook
          </span>
          <span style={{ fontSize: 11, color: "#5c6370" }}>({analysis.short_term.horizon})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div style={{ fontSize: 24 }}>{shortTermIcon || "🔄"}</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#e8eaed" }}>
            {analysis.short_term.direction}
          </div>
        </div>
        <div style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.6 }}>
          {analysis.short_term.reasoning}
        </div>
      </Card>

      {/* Long-Term Direction */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#8b919e", textTransform: "uppercase" }}>
            Long-Term Outlook
          </span>
          <span style={{ fontSize: 11, color: "#5c6370" }}>({analysis.long_term.horizon})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div style={{ fontSize: 24 }}>{longTermIcon || "📊"}</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#e8eaed" }}>
            {analysis.long_term.direction}
          </div>
        </div>
        <div style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.6 }}>
          {analysis.long_term.reasoning}
        </div>
      </Card>

      {/* Key Risks */}
      <Card style={{ marginBottom: 16 }}>
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#8b919e", textTransform: "uppercase" }}>
            ⚠️ Key Risks
          </span>
        </div>
        <Space direction="vertical" style={{ width: "100%" }}>
          {analysis.top_risks.map((risk, idx) => (
            <div key={idx} style={{ fontSize: 12, color: "#c7ccd6", paddingLeft: 12 }}>
              • {risk}
            </div>
          ))}
        </Space>
      </Card>

      {/* Opportunities */}
      <Card>
        <div style={{ marginBottom: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#34d399", textTransform: "uppercase" }}>
            ✨ Opportunities
          </span>
        </div>
        <Space direction="vertical" style={{ width: "100%" }}>
          {analysis.opportunities.map((opp, idx) => (
            <div key={idx} style={{ fontSize: 12, color: "#c7ccd6", paddingLeft: 12 }}>
              • {opp}
            </div>
          ))}
        </Space>
      </Card>
    </div>
  );
}
