import type { ScreenerRow } from "./types";

const COLUMNS: { key: keyof ScreenerRow; label: string }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "company", label: "Company" },
  { key: "sector", label: "Sector" },
  { key: "price", label: "Price" },
  { key: "market_cap", label: "Market Cap" },
  { key: "eps_used", label: "EPS" },
  { key: "growth_pct", label: "Growth %" },
  { key: "moat", label: "Moat" },
  { key: "graham_value", label: "Graham Value" },
  { key: "graham_margin_pct", label: "Graham Margin %" },
  { key: "graham_verdict", label: "Graham Verdict" },
  { key: "buffett_value", label: "Buffett Value" },
  { key: "buffett_margin_pct", label: "Buffett Margin %" },
  { key: "buffett_verdict", label: "Buffett Verdict" },
  { key: "conviction", label: "Conviction" },
];

export function exportCsv(rows: ScreenerRow[], filename = "stock_screener.csv") {
  const header = COLUMNS.map((c) => c.label).join(",");
  const lines = rows.map((r) =>
    COLUMNS.map((c) => {
      const v = r[c.key];
      if (v == null) return "";
      const s = String(v);
      return s.includes(",") ? `"${s}"` : s;
    }).join(",")
  );
  const csv = [header, ...lines].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
