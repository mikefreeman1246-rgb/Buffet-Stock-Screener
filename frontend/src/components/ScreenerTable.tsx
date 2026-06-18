import { Table, Tag, Tooltip, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { SorterResult } from "antd/es/table/interface";
import StockDetail from "./StockDetail";
import type {
  ScreenerFilterState, ScreenerResponse, ScreenerRow,
} from "../lib/types";
import {
  money, marketCap, num, pct,
  grahamColor, buffettColor, convictionColor, moatColor, tagColor,
} from "../lib/format";

interface Props {
  data: ScreenerResponse | null;
  loading: boolean;
  filters: ScreenerFilterState;
  allTags: string[];
  onChange: (p: Partial<ScreenerFilterState>) => void;
  onOverrideSaved: () => void;
  onTagsChanged: () => void;
}

const { Text } = Typography;

function marginCell(v: number | null) {
  if (v == null) return <span style={{ color: "#5c6370" }}>—</span>;
  const color = v > 0 ? "#34d399" : v < 0 ? "#f87171" : "#8b919e";
  return <span className="data-mono" style={{ color }}>{v > 0 ? "+" : ""}{v.toFixed(1)}%</span>;
}

export default function ScreenerTable({
  data, loading, filters, allTags, onChange, onOverrideSaved, onTagsChanged,
}: Props) {
  const showGraham = filters.model !== "buffett";
  const showBuffett = filters.model !== "graham";

  const columns: ColumnsType<ScreenerRow> = [
    {
      title: "Ticker", dataIndex: "ticker", fixed: "left", width: 130,
      render: (t: string, r) => (
        <span>
          <span className="ticker-symbol">{t}</span>
          {r.has_override && (
            <Tooltip title="Manual override active">
              <Tag color="cyan" style={{ marginLeft: 6, fontSize: 9, lineHeight: "14px", padding: "0 4px" }}>OV</Tag>
            </Tooltip>
          )}
        </span>
      ),
    },
    {
      title: "Company", dataIndex: "company", ellipsis: true, width: 180,
      render: (c: string) => <Text style={{ fontSize: 12, color: "#8b919e" }}>{c}</Text>,
    },
    { title: "Sector", dataIndex: "sector", width: 150, ellipsis: true,
      render: (s: string) => <Text style={{ fontSize: 11, color: "#5c6370" }}>{s}</Text> },
    { title: "Price", dataIndex: "price", width: 90, align: "right", sorter: true,
      render: (v) => <span className="data-mono">{money(v)}</span> },
    { title: "Cap", dataIndex: "market_cap", width: 80, align: "right", sorter: true,
      render: (v) => <span className="data-mono" style={{ color: "#8b919e" }}>{marketCap(v)}</span> },
    { title: "EPS", dataIndex: "eps_used", width: 72, align: "right",
      render: (v) => <span className="data-mono">{num(v)}</span> },
    { title: "g", dataIndex: "growth_pct", width: 54, align: "right", sorter: true,
      render: (v) => <span className="data-mono" style={{ color: "#8b919e" }}>{pct(v, 0)}</span> },
    { title: "Moat", dataIndex: "moat", width: 96, sorter: true,
      render: (m: string) => <Tag color={moatColor[m]} style={{ textTransform: "capitalize" }}>{m}</Tag> },

    ...(showGraham ? [
      { title: "Graham V", dataIndex: "graham_value", width: 92, align: "right" as const, sorter: true,
        render: (v: number | null) => <span className="data-mono">{money(v)}</span> },
      { title: "G margin", dataIndex: "graham_margin_pct", width: 82, align: "right" as const, sorter: true,
        render: (v: number | null) => marginCell(v) },
      { title: "Graham", dataIndex: "graham_verdict", width: 138, sorter: true,
        render: (v: string) => <Tag color={grahamColor[v as keyof typeof grahamColor]}>{v}</Tag> },
    ] : []),

    ...(showBuffett ? [
      { title: "Buffett V", dataIndex: "buffett_value", width: 92, align: "right" as const, sorter: true,
        render: (v: number | null) => <span className="data-mono">{money(v)}</span> },
      { title: "B margin", dataIndex: "buffett_margin_pct", width: 82, align: "right" as const, sorter: true,
        render: (v: number | null) => marginCell(v) },
      { title: "Buffett", dataIndex: "buffett_verdict", width: 118, sorter: true,
        render: (v: string) => <Tag color={buffettColor[v as keyof typeof buffettColor]}>{v}</Tag> },
    ] : []),

    { title: "My Tags", dataIndex: "tags", width: 170, sorter: true,
      render: (tags: string[]) =>
        tags.length ? (
          <span>{tags.map((t) => <Tag key={t} color={tagColor(t)} style={{ marginInlineEnd: 4 }}>{t}</Tag>)}</span>
        ) : (
          <span style={{ color: "#3a4150" }}>—</span>
        ) },

    { title: "Conviction", dataIndex: "conviction", width: 138, fixed: "right", sorter: true,
      render: (v: string) => <Tag color={convictionColor[v as keyof typeof convictionColor]}>{v}</Tag> },
  ];

  const handleTableChange = (
    pagination: { current?: number; pageSize?: number },
    _filters: unknown,
    sorter: SorterResult<ScreenerRow> | SorterResult<ScreenerRow>[],
  ) => {
    const s = Array.isArray(sorter) ? sorter[0] : sorter;
    const patch: Partial<ScreenerFilterState> = {
      page: pagination.current ?? 1,
      page_size: pagination.pageSize ?? filters.page_size,
    };
    if (s && s.field) {
      patch.sort_by = String(s.field);
      patch.sort_dir = s.order === "ascend" ? "asc" : "desc";
    }
    onChange(patch);
  };

  return (
    <Table<ScreenerRow>
      size="small"
      rowKey="ticker"
      loading={loading}
      columns={columns}
      dataSource={data?.results ?? []}
      scroll={{ x: 1300 }}
      onChange={handleTableChange}
      pagination={{
        current: filters.page,
        pageSize: filters.page_size,
        total: data?.total ?? 0,
        showSizeChanger: true,
        pageSizeOptions: [25, 50, 100, 200],
        size: "small",
        showTotal: (t) => `${t} stocks`,
      }}
      expandable={{
        expandedRowRender: (r) => (
        <StockDetail
          ticker={r.ticker}
          allTags={allTags}
          onSaved={onOverrideSaved}
          onTagsChanged={onTagsChanged}
        />
      ),
        expandRowByClick: true,
      }}
    />
  );
}
