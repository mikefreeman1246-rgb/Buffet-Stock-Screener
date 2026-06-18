import { Button, Card, Input, Radio, Select, Slider, Space, Tooltip, Typography } from "antd";
import { DownloadOutlined, ClearOutlined, SearchOutlined } from "@ant-design/icons";
import type { ScreenerFilterState, ScreenerRow, TagCount } from "../lib/types";
import { exportCsv } from "../lib/exportCsv";

const GRAHAM_VERDICTS = ["Undervalued", "Fair Value", "Mild Overvalued", "Overvalued"];
const BUFFETT_VERDICTS = ["Strong Buy", "Buy", "Hold", "Trim", "Pass"];
const CONVICTIONS = ["Max Conviction", "Moat Premium", "Mixed", "Value Trap?", "Avoid"];
const MOATS = ["wide", "moderate", "narrow", "none"];

const CAP_OPTIONS = [
  { label: "Any cap", value: 0 },
  { label: "$1B+", value: 1e9 },
  { label: "$10B+", value: 1e10 },
  { label: "$50B+", value: 5e10 },
  { label: "$100B+", value: 1e11 },
  { label: "$500B+", value: 5e11 },
];

interface Props {
  filters: ScreenerFilterState;
  sectors: string[];
  tags: TagCount[];
  total: number;
  rows: ScreenerRow[];
  onChange: (p: Partial<ScreenerFilterState>) => void;
  onReset: () => void;
}

const { Text } = Typography;

export default function ScreenerFilters({ filters, sectors, tags, total, rows, onChange, onReset }: Props) {
  return (
    <div className="screener-filters" style={{ marginBottom: 14 }}>
      <Card size="small" styles={{ body: { padding: "12px 14px" } }}>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 16, alignItems: "flex-end" }}>
          {/* Model */}
          <div>
            <Label>Model</Label>
            <Radio.Group
              size="small"
              optionType="button"
              buttonStyle="solid"
              value={filters.model}
              onChange={(e) => onChange({ model: e.target.value })}
              options={[
                { label: "Dual", value: "dual" },
                { label: "Graham", value: "graham" },
                { label: "Buffett", value: "buffett" },
              ]}
            />
          </div>

          {/* Graham verdict */}
          <div style={{ minWidth: 160 }}>
            <Label>Graham verdict</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder="Any" maxTagCount="responsive"
              value={filters.graham_verdict}
              onChange={(v) => onChange({ graham_verdict: v })}
              options={GRAHAM_VERDICTS.map((v) => ({ label: v, value: v }))}
            />
          </div>

          {/* Buffett verdict */}
          <div style={{ minWidth: 150 }}>
            <Label>Buffett verdict</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder="Any" maxTagCount="responsive"
              value={filters.buffett_verdict}
              onChange={(v) => onChange({ buffett_verdict: v })}
              options={BUFFETT_VERDICTS.map((v) => ({ label: v, value: v }))}
            />
          </div>

          {/* Conviction */}
          <div style={{ minWidth: 160 }}>
            <Label>Conviction</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder="Any" maxTagCount="responsive"
              value={filters.conviction}
              onChange={(v) => onChange({ conviction: v })}
              options={CONVICTIONS.map((v) => ({ label: v, value: v }))}
            />
          </div>

          {/* Moat */}
          <div style={{ minWidth: 140 }}>
            <Label>Moat</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder="Any" maxTagCount="responsive"
              value={filters.moat}
              onChange={(v) => onChange({ moat: v })}
              options={MOATS.map((v) => ({ label: v, value: v }))}
            />
          </div>

          {/* Tags */}
          <div style={{ minWidth: 160 }}>
            <Label>My tags</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder={tags.length ? "Any tag" : "No tags yet"}
              maxTagCount="responsive"
              value={filters.tags}
              onChange={(v) => onChange({ tags: v })}
              options={tags.map((t) => ({ label: `${t.tag} (${t.count})`, value: t.tag }))}
            />
          </div>

          {/* Sector */}
          <div style={{ minWidth: 200 }}>
            <Label>Sector</Label>
            <Select
              size="small" mode="multiple" allowClear style={{ width: "100%" }}
              placeholder="All sectors" maxTagCount="responsive"
              value={filters.sector}
              onChange={(v) => onChange({ sector: v })}
              options={sectors.map((s) => ({ label: s, value: s }))}
            />
          </div>

          {/* Min margin of safety */}
          <div style={{ width: 180 }}>
            <Label>
              Min margin of safety{" "}
              <Text style={{ color: "#2dd4bf", fontFamily: "monospace" }}>
                {filters.min_margin != null ? `${filters.min_margin}%` : "off"}
              </Text>
            </Label>
            <Slider
              min={-50} max={75} step={5}
              value={filters.min_margin ?? -50}
              onChange={(v) => onChange({ min_margin: v <= -50 ? null : v })}
              tooltip={{ formatter: (v) => `${v}%` }}
            />
          </div>

          {/* Market cap */}
          <div style={{ minWidth: 110 }}>
            <Label>Market cap</Label>
            <Select
              size="small" style={{ width: "100%" }}
              value={filters.min_cap ?? 0}
              onChange={(v) => onChange({ min_cap: v === 0 ? null : v })}
              options={CAP_OPTIONS}
            />
          </div>

          {/* Search */}
          <div style={{ minWidth: 160 }}>
            <Label>Search</Label>
            <Input
              size="small" allowClear prefix={<SearchOutlined style={{ color: "#5c6370" }} />}
              placeholder="Ticker or company"
              value={filters.search}
              onChange={(e) => onChange({ search: e.target.value })}
            />
          </div>

          <div style={{ flex: 1 }} />

          {/* Result count + actions */}
          <Space>
            <Text style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#8b919e" }}>
              {total} match{total === 1 ? "" : "es"}
            </Text>
            <Tooltip title="Export current page to CSV">
              <Button size="small" icon={<DownloadOutlined />} disabled={!rows.length}
                onClick={() => exportCsv(rows)} />
            </Tooltip>
            <Tooltip title="Reset filters">
              <Button size="small" icon={<ClearOutlined />} onClick={onReset} />
            </Tooltip>
          </Space>
        </div>
      </Card>
    </div>
  );
}

function Label({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 10.5, color: "#5c6370", textTransform: "uppercase", letterSpacing: 0.4, marginBottom: 4 }}>
      {children}
    </div>
  );
}
