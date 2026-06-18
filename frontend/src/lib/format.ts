import type { BuffettVerdict, Conviction, GrahamVerdict } from "./types";

export const money = (v: number | null | undefined, dp = 2): string =>
  v == null ? "—" : `$${v.toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp })}`;

export const pct = (v: number | null | undefined, dp = 1): string =>
  v == null ? "—" : `${v.toFixed(dp)}%`;

export const num = (v: number | null | undefined, dp = 2): string =>
  v == null ? "—" : v.toFixed(dp);

export const marketCap = (v: number | null | undefined): string => {
  if (v == null) return "—";
  if (v >= 1e12) return `$${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `$${(v / 1e9).toFixed(1)}B`;
  if (v >= 1e6) return `$${(v / 1e6).toFixed(0)}M`;
  return `$${v}`;
};

// Ant Design Tag color tokens per verdict.
export const grahamColor: Record<GrahamVerdict, string> = {
  "Undervalued": "success",
  "Fair Value": "default",
  "Mild Overvalued": "warning",
  "Overvalued": "error",
  "N/A": "default",
};

export const buffettColor: Record<BuffettVerdict, string> = {
  "Strong Buy": "success",
  "Buy": "cyan",
  "Hold": "default",
  "Trim": "warning",
  "Pass": "error",
  "N/A": "default",
};

export const convictionColor: Record<Conviction, string> = {
  "Max Conviction": "green",
  "Moat Premium": "cyan",
  "Mixed": "default",
  "Value Trap?": "orange",
  "Avoid": "red",
};

export const moatColor: Record<string, string> = {
  wide: "green",
  moderate: "cyan",
  narrow: "gold",
  none: "default",
};

// Deterministic color per user tag so a tag always looks the same.
const TAG_PALETTE = [
  "magenta", "red", "volcano", "orange", "gold", "lime",
  "green", "cyan", "blue", "geekblue", "purple",
];
export function tagColor(tag: string): string {
  let h = 0;
  for (let i = 0; i < tag.length; i++) h = (h * 31 + tag.charCodeAt(i)) >>> 0;
  return TAG_PALETTE[h % TAG_PALETTE.length];
}
