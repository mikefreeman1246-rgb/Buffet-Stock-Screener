import { Spin } from "antd";
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  MinusOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import type { ReactNode } from "react";
import type { MarketAnalysis } from "../../hooks/useMarketAnalysis";

interface MarketHealthSummaryProps {
  analysis: MarketAnalysis | null;
  loading?: boolean;
}

const GREEN = "#34d399";
const YELLOW = "#fbbf24";
const RED = "#f87171";
const TEXT = "#e8eaed";
const MUTED = "#8b919e";
const DIM = "#5c6370";
const CARD_BG = "rgba(255,255,255,0.04)";
const CARD_BORDER = "rgba(255,255,255,0.08)";

function directionColor(dir: string): string {
  if (dir === "Bullish") return GREEN;
  if (dir === "Bearish") return RED;
  if (dir === "Cautious") return YELLOW;
  return MUTED;
}

function directionIcon(dir: string): ReactNode {
  const color = directionColor(dir);
  if (dir === "Bullish") return <ArrowUpOutlined style={{ color, fontSize: 16 }} />;
  if (dir === "Bearish") return <ArrowDownOutlined style={{ color, fontSize: 16 }} />;
  if (dir === "Cautious") return <ExclamationCircleOutlined style={{ color, fontSize: 16 }} />;
  return <MinusOutlined style={{ color, fontSize: 16 }} />;
}

function regimeBorderColor(health: string): string {
  if (health === "Bullish") return GREEN;
  if (health === "Bearish") return RED;
  return YELLOW;
}

function convictionColor(conviction: string): string {
  if (conviction === "High") return GREEN;
  if (conviction === "Low") return RED;
  return YELLOW;
}

function card(children: ReactNode, extraStyle?: React.CSSProperties): ReactNode {
  return (
    <div
      style={{
        background: CARD_BG,
        border: `1px solid ${CARD_BORDER}`,
        borderRadius: 8,
        padding: "14px 16px",
        ...extraStyle,
      }}
    >
      {children}
    </div>
  );
}

function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        fontSize: 10,
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        color: MUTED,
        marginBottom: 10,
      }}
    >
      {children}
    </div>
  );
}

function BulletList({
  items,
  icon,
  iconColor,
}: {
  items: string[];
  icon: "check" | "warning" | "eye";
  iconColor: string;
}) {
  const IconNode =
    icon === "check" ? CheckCircleOutlined :
    icon === "eye" ? EyeOutlined :
    ExclamationCircleOutlined;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {items.map((item, i) => (
        <div key={i} style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
          <IconNode style={{ color: iconColor, fontSize: 12, marginTop: 2, flexShrink: 0 }} />
          <span style={{ fontSize: 12, color: "#c7ccd6", lineHeight: 1.55 }}>{item}</span>
        </div>
      ))}
    </div>
  );
}

export default function MarketHealthSummary({
  analysis,
  loading = false,
}: MarketHealthSummaryProps) {
  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 40 }}>
        <Spin size="large" />
        <div style={{ marginTop: 12, fontSize: 13, color: MUTED }}>Analyzing market conditions…</div>
      </div>
    );
  }

  if (!analysis) return null;

  const { signal_breakdown: sb } = analysis;
  const total = sb.total_count || 1;
  const healthyPct = (sb.healthy_count / total) * 100;
  const watchPct = (sb.watch_count / total) * 100;
  const chaosPct = (sb.chaos_count / total) * 100;
  const borderColor = regimeBorderColor(analysis.health);

  return (
    <div style={{ marginBottom: 24, display: "flex", flexDirection: "column", gap: 10 }}>

      {/* === REGIME BANNER === */}
      <div
        style={{
          background: CARD_BG,
          border: `1px solid ${CARD_BORDER}`,
          borderLeft: `3px solid ${borderColor}`,
          borderRadius: 8,
          padding: "14px 16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ fontSize: 17, fontWeight: 600, color: TEXT, marginBottom: 3 }}>
              {analysis.regime}
            </div>
            <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.5 }}>
              {analysis.regime_detail}
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 5, flexShrink: 0 }}>
            <div style={{ display: "flex", gap: 6 }}>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 9px",
                  borderRadius: 99,
                  background: `${borderColor}20`,
                  color: borderColor,
                  fontWeight: 600,
                }}
              >
                {analysis.health}
              </span>
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 9px",
                  borderRadius: 99,
                  background: `${convictionColor(analysis.conviction)}18`,
                  color: convictionColor(analysis.conviction),
                  fontWeight: 600,
                }}
              >
                {analysis.conviction} conviction
              </span>
            </div>
            <div style={{ fontSize: 11, color: DIM }}>
              {sb.healthy_count} healthy · {sb.watch_count} watch · {sb.chaos_count} stress
            </div>
          </div>
        </div>

        {/* Signal health bar */}
        <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              flex: 1,
              height: 6,
              borderRadius: 99,
              overflow: "hidden",
              background: "rgba(255,255,255,0.08)",
              display: "flex",
            }}
          >
            {healthyPct > 0 && (
              <div
                style={{
                  width: `${healthyPct}%`,
                  background: GREEN,
                  borderRadius: watchPct + chaosPct === 0 ? 99 : "99px 0 0 99px",
                }}
              />
            )}
            {watchPct > 0 && (
              <div style={{ width: `${watchPct}%`, background: YELLOW }} />
            )}
            {chaosPct > 0 && (
              <div
                style={{
                  width: `${chaosPct}%`,
                  background: RED,
                  borderRadius: "0 99px 99px 0",
                }}
              />
            )}
          </div>
          <div style={{ fontSize: 11, color: DIM, whiteSpace: "nowrap" }}>
            {Math.round(healthyPct)}% healthy
          </div>
        </div>
      </div>

      {/* === 3-COLUMN: SHORT-TERM | LONG-TERM | POSITIONING === */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>

        {card(
          <>
            <SectionLabel>Short-term · {analysis.short_term.horizon}</SectionLabel>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              {directionIcon(analysis.short_term.direction)}
              <span style={{ fontSize: 15, fontWeight: 600, color: directionColor(analysis.short_term.direction) }}>
                {analysis.short_term.direction}
              </span>
            </div>
            <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.6 }}>
              {analysis.short_term.reasoning}
            </div>
          </>
        )}

        {card(
          <>
            <SectionLabel>Long-term · {analysis.long_term.horizon}</SectionLabel>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              {directionIcon(analysis.long_term.direction)}
              <span style={{ fontSize: 15, fontWeight: 600, color: directionColor(analysis.long_term.direction) }}>
                {analysis.long_term.direction}
              </span>
            </div>
            <div style={{ fontSize: 12, color: MUTED, lineHeight: 1.6 }}>
              {analysis.long_term.reasoning}
            </div>
          </>
        )}

        {card(
          <>
            <SectionLabel>Positioning</SectionLabel>
            <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
              {analysis.positioning.map((item, i) => {
                const isWarning = item.toLowerCase().includes("hedge") ||
                  item.toLowerCase().includes("avoid") ||
                  item.toLowerCase().includes("reduce") ||
                  item.toLowerCase().includes("defensive") ||
                  item.toLowerCase().includes("caution");
                return (
                  <div key={i} style={{ display: "flex", gap: 7, alignItems: "flex-start" }}>
                    {isWarning
                      ? <ExclamationCircleOutlined style={{ color: YELLOW, fontSize: 11, marginTop: 2, flexShrink: 0 }} />
                      : <CheckCircleOutlined style={{ color: GREEN, fontSize: 11, marginTop: 2, flexShrink: 0 }} />
                    }
                    <span style={{ fontSize: 12, color: MUTED, lineHeight: 1.5 }}>{item}</span>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* === 2-COLUMN: KEY RISKS | OPPORTUNITIES + WATCH LEVELS === */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 10 }}>

        {card(
          <>
            <SectionLabel>
              <ExclamationCircleOutlined style={{ color: RED, fontSize: 11, marginRight: 5 }} />
              Key risks
            </SectionLabel>
            <BulletList items={analysis.top_risks} icon="warning" iconColor={RED} />
          </>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {card(
            <>
              <SectionLabel>
                <CheckCircleOutlined style={{ color: GREEN, fontSize: 11, marginRight: 5 }} />
                Opportunities
              </SectionLabel>
              <BulletList items={analysis.opportunities} icon="check" iconColor={GREEN} />
            </>
          )}

          {analysis.watch_levels.length > 0 && card(
            <>
              <SectionLabel>
                <EyeOutlined style={{ color: YELLOW, fontSize: 11, marginRight: 5 }} />
                Watch levels
              </SectionLabel>
              <BulletList items={analysis.watch_levels} icon="eye" iconColor={YELLOW} />
            </>
          )}
        </div>
      </div>

    </div>
  );
}
