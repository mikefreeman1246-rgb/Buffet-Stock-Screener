/**
 * Zero-dependency inline SVG sparkline with shaded green/yellow stress bands.
 *
 * Every series here is normalized so HIGHER = MORE STRESS, so the bands read
 * top-to-bottom as red (above yellow_max) → yellow (green_max..yellow_max) →
 * green (at/below green_max). The line is tinted to its latest band.
 */

// Status colors mirror the App.tsx theme tokens.
const GREEN = "#34d399";
const YELLOW = "#fbbf24";
const RED = "#f87171";

interface Props {
  series: number[];
  greenMax: number;
  yellowMax: number;
  width?: number;
  height?: number;
}

export default function Sparkline({
  series,
  greenMax,
  yellowMax,
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
          color: "#5c6370",
          fontStyle: "italic",
        }}
      >
        n/a
      </div>
    );
  }

  const min = Math.min(...series, greenMax);
  const max = Math.max(...series, yellowMax);
  const span = max - min || 1;

  const x = (i: number) => (i / (series.length - 1)) * width;
  const y = (v: number) => height - ((v - min) / span) * height;

  const line = series
    .map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`)
    .join(" ");
  // Closed area under the line for a subtle fill.
  const area = `${line} L${width},${height} L0,${height} Z`;

  const last = series[series.length - 1];
  const stroke = last > yellowMax ? RED : last > greenMax ? YELLOW : GREEN;

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
      {/* faint area fill + line, tinted to the latest band */}
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
