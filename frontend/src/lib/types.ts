export type GrahamVerdict =
  | "Undervalued" | "Fair Value" | "Mild Overvalued" | "Overvalued" | "N/A";
export type BuffettVerdict =
  | "Strong Buy" | "Buy" | "Hold" | "Trim" | "Pass" | "N/A";
export type Conviction =
  | "Max Conviction" | "Moat Premium" | "Mixed" | "Value Trap?" | "Avoid";
export type Moat = "wide" | "moderate" | "narrow" | "none";

export interface ScreenerRow {
  ticker: string;
  company: string;
  sector: string;
  price: number | null;
  market_cap: number | null;
  is_financial: boolean;
  eps_used: number | null;
  growth_pct: number;
  moat: Moat;
  discount_rate: number;

  graham_value: number | null;
  graham_sweet_spot: number | null;
  graham_verdict: GrahamVerdict;
  graham_margin_pct: number | null;

  owner_earnings_ps: number | null;
  oe_multiplier: number | null;
  oe_method: string;

  buffett_method: "dcf" | "pb";
  fair_pb: number | null;
  buffett_value: number | null;
  buffett_verdict: BuffettVerdict;
  buffett_ratio: number | null;
  buffett_margin_pct: number | null;

  conviction: Conviction;
  has_override: boolean;
  tags: string[];
}

export interface TagCount {
  tag: string;
  count: number;
}

export interface Assumptions {
  aaa_bond_yield: number;
  graham_base_pe: number;
  graham_growth_multiplier: number;
  graham_g_cap: number;
  margin_of_safety_pct: number;
  r_wide: number;
  r_moderate: number;
  r_narrow: number;
  r_none: number;
  terminal_growth: number;
  high_growth_years: number;
}

export interface ScreenerResponse {
  total: number;
  page: number;
  page_size: number;
  assumptions: Assumptions;
  results: ScreenerRow[];
}

export interface StockOverride {
  growth_override: number | null;
  moat_override: Moat | null;
  oe_multiplier_override: number | null;
  normalized_eps_override: number | null;
  note: string | null;
}

export interface StockDetail extends ScreenerRow {
  raw: Record<string, number | string | null>;
  override: StockOverride | null;
}

export interface MetaStats {
  stock_count: number;
  last_update: string | null;
  sectors: string[];
  last_pull_status: string | null;
}

export interface PipelineStatus {
  is_running: boolean;
  last: {
    status: string;
    total: number;
    completed: number;
    failed: number;
    last_ticker: string | null;
    started_at: string | null;
    completed_at: string | null;
  } | null;
}

export interface ScreenerFilterState {
  model: "graham" | "buffett" | "dual";
  graham_verdict: string[];
  buffett_verdict: string[];
  moat: string[];
  conviction: string[];
  tags: string[];
  sector: string[];
  min_margin: number | null;
  min_price: number | null;
  max_price: number | null;
  min_cap: number | null;
  search: string;
  sort_by: string;
  sort_dir: "asc" | "desc";
  page: number;
  page_size: number;
}
