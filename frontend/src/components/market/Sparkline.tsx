/**
 * Zero-dependency inline SVG sparkline.
 *
 * For indicators whose plotted series shares the threshold domain (e.g. VIX,
 * SKEW, credit), we shade green/yellow/red stress bands — series are normalized
 * so HIGHER = MORE STRESS, so bands read top-to-bottom red → yellow → green.
 *
 * For *derived-metric* indicators (e.g. 10Y move in bps/wk, Gold %/mo, Net
 * Liquidity stress score) the plotted series is the raw level, which does NOT
 * share the metric/threshold domain — so bands would be meaningless. There we
 * pass `showBands={false}` and tint the line by the indicator's actual `state`.
 */

// Status colors mirror the App.tsx theme tokens.
const GREEN = "#34d399";
const YELLOW = "#fbbf24";
const RED = "#f87171";
const NEUTRAL = "#5c6370";

const STATE_COLOR: Record<number, string> = { 1: GREEN, 2: YELLOW, 3: RED };

interface Props {
  series: number[];
  greenMax: number;
  yellowMax: number;
  /** Indicator state (1/2/3) — used to tint the line. null = no data. */
  state?: number | null;
  /** Draw threshold bands. Only meaningful when series shares the threshold domain. */
  showBands?: boolean;
  width?: number;
  height?: number;
}

export default function Sparkline({
  series,
  greenMax,
  yellowMax,
  state,
  showBands = true,
  width = 150,
  height = 40,
}: Props) {
  if (!series || series.length < 2) {
    return (
      <div
        style={{
          height,
          width,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
          color: NEUTRAL,
          fontStyle: "italic",
        }}
      >
        n/a
      </div>
    );
  }

  // Bands only make sense when the series is co-domain with the thresholds.
  const min = showBands ? Math.min(...series, greenMax) : Math.min(...series);
  const max = showBands ? Math.max(...series, yellowMax) : Math.max(...series);
  const span = max - min || 1;

  const x = (i: number) => (i / (series.length - 1)) * width;
  const y = (v: number) => height - ((v - min) / span) * height;

  const line = series
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    .join(" ");
  // Closed area under the line for a subtle fill.
  const area = `${line} L${width},${height} L0,${height} Z`;

  const last = series[series.length - 1];
  // Tint by the indicator's real state when known; otherwise fall back to the
  // latest value's band (valid only when series is co-domain with thresholds).
  const stroke =
    state != null
      ? STATE_COLOR[state] ?? NEUTRAL
      : last > yellowMax
      ? RED
      : last > greenMax
      ? YELLOW
      : GREEN;

  // Clamp band boundaries into the drawable area.
  const yYellow = Math.max(0, Math.min(height, y(yellowMax)));
  const yGreen = Math.max(0, Math.min(height, y(greenMax)));

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      style={{ display: "block", overflow: "visible" }}
    >
      {/* stress bands: red on top, yellow middle, green at the floor */}
      {showBands && (
        <>
          <rect x={0} y={0} width={width} height={yYellow} fill={RED} opacity={0.07} />
          <rect
            x={0}
            y={yYellow}
            width={width}
            height={Math.max(0, yGreen - yYellow)}
            fill={YELLOW}
            opacity={0.07}
          />
          <rect
            x={0}
            y={yGreen}
            width={width}
            height={Math.max(0, height - yGreen)}
            fill={GREEN}
            opacity={0.07}
          />
        </>
      )}
      {/* faint area fill + line, tinted to the indicator state */}
      <path d={area} fill={stroke} opacity={0.1} stroke="none" />
      <path
        d={line}
        fill="none"
        stroke={stroke}
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {/* latest-point marker */}
      <circle cx={x(series.length - 1)} cy={y(last)} r={2} fill={stroke} />
    </svg>
  );
}
