import axios from "axios";
import type {
  Assumptions, MetaStats, PipelineStatus, ScreenerFilterState,
  ScreenerResponse, StockDetail, StockOverride, TagCount,
} from "./types";

const http = axios.create({ baseURL: "/api" });

function screenerParams(f: ScreenerFilterState): Record<string, unknown> {
  const p: Record<string, unknown> = {
    model: f.model,
    sort_by: f.sort_by,
    sort_dir: f.sort_dir,
    page: f.page,
    page_size: f.page_size,
  };
  if (f.graham_verdict.length) p.graham_verdict = f.graham_verdict;
  if (f.buffett_verdict.length) p.buffett_verdict = f.buffett_verdict;
  if (f.moat.length) p.moat = f.moat;
  if (f.conviction.length) p.conviction = f.conviction;
  if (f.tags.length) p.tags = f.tags;
  if (f.sector.length) p.sector = f.sector;
  if (f.min_margin != null) p.min_margin = f.min_margin;
  if (f.min_price != null) p.min_price = f.min_price;
  if (f.max_price != null) p.max_price = f.max_price;
  if (f.min_cap != null) p.min_cap = f.min_cap;
  if (f.search) p.search = f.search;
  return p;
}

export const api = {
  async screen(filters: ScreenerFilterState): Promise<ScreenerResponse> {
    const { data } = await http.get<ScreenerResponse>("/screener", {
      params: screenerParams(filters),
      paramsSerializer: { indexes: null }, // repeat keys: verdict=a&verdict=b
    });
    return data;
  },

  async getStock(ticker: string): Promise<StockDetail> {
    const { data } = await http.get<StockDetail>(`/stocks/${ticker}`);
    return data;
  },

  async setOverride(ticker: string, body: Partial<StockOverride>) {
    const { data } = await http.put(`/stocks/${ticker}/override`, body);
    return data;
  },

  async clearOverride(ticker: string) {
    await http.delete(`/stocks/${ticker}/override`);
  },

  async getTags(): Promise<TagCount[]> {
    const { data } = await http.get<TagCount[]>("/tags");
    return data;
  },

  async setStockTags(ticker: string, tags: string[]): Promise<{ ticker: string; tags: string[] }> {
    const { data } = await http.put(`/stocks/${ticker}/tags`, { tags });
    return data;
  },

  async getAssumptions(): Promise<Assumptions> {
    const { data } = await http.get<Assumptions>("/assumptions");
    return data;
  },

  async updateAssumptions(body: Partial<Assumptions>): Promise<Assumptions> {
    const { data } = await http.put<Assumptions>("/assumptions", body);
    return data;
  },

  async refreshYield(): Promise<{ aaa_bond_yield: number }> {
    const { data } = await http.post("/assumptions/refresh-yield");
    return data;
  },

  async stats(): Promise<MetaStats> {
    const { data } = await http.get<MetaStats>("/meta/stats");
    return data;
  },

  async pipelineStatus(): Promise<PipelineStatus> {
    const { data } = await http.get<PipelineStatus>("/pipeline/status");
    return data;
  },

  async startPipeline(limit?: number, universe: string = "sp500") {
    const params: Record<string, unknown> = { universe };
    if (limit) params.limit = limit;
    const { data } = await http.post("/pipeline/start", null, { params });
    return data;
  },

  async stopPipeline() {
    await http.post("/pipeline/stop");
  },
};
