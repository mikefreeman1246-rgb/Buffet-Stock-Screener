import { useEffect, useState } from "react";
import {
  Button, Col, Descriptions, Divider, InputNumber, Row, Select, Space, Tag, Typography, message,
} from "antd";
import { api } from "../lib/api";
import type { Moat, StockDetail as Detail } from "../lib/types";
import { money, num, pct, marketCap, moatColor, tagColor } from "../lib/format";

const { Text } = Typography;

interface Props {
  ticker: string;
  allTags: string[];
  onSaved: () => void;
  onTagsChanged: () => void;
}

export default function StockDetail({ ticker, allTags, onSaved, onTagsChanged }: Props) {
  const [d, setD] = useState<Detail | null>(null);
  const [growth, setGrowth] = useState<number | null>(null);
  const [moat, setMoat] = useState<Moat | null>(null);
  const [oeMult, setOeMult] = useState<number | null>(null);
  const [normEps, setNormEps] = useState<number | null>(null);
  const [tags, setTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const detail = await api.getStock(ticker);
    setD(detail);
    setGrowth(detail.override?.growth_override ?? null);
    setMoat(detail.override?.moat_override ?? null);
    setOeMult(detail.override?.oe_multiplier_override ?? null);
    setNormEps(detail.override?.normalized_eps_override ?? null);
    setTags(detail.tags ?? []);
  };

  const saveTags = async (next: string[]) => {
    setTags(next);
    const res = await api.setStockTags(ticker, next);
    setTags(res.tags);
    onTagsChanged();
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker]);

  if (!d) return <div style={{ padding: 16, color: "#5c6370" }}>Loading {ticker}…</div>;

  const saveOverride = async () => {
    setSaving(true);
    try {
      await api.setOverride(ticker, {
        growth_override: growth, moat_override: moat,
        oe_multiplier_override: oeMult, normalized_eps_override: normEps,
      });
      message.success(`${ticker} override applied`);
      await load();
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  const clearOverride = async () => {
    setSaving(true);
    try {
      await api.clearOverride(ticker);
      message.success(`${ticker} override cleared`);
      await load();
      onSaved();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ padding: "6px 8px 10px" }}>
      <Row gutter={24}>
        {/* Graham breakdown */}
        <Col span={7}>
          <SectionTitle>Graham Intrinsic Value</SectionTitle>
          <Descriptions column={1} size="small" colon={false}>
            <Descriptions.Item label="EPS used">{money(d.eps_used)}</Descriptions.Item>
            <Descriptions.Item label="Growth g">{pct(d.growth_pct, 0)}</Descriptions.Item>
            <Descriptions.Item label="Graham value">{money(d.graham_value)}</Descriptions.Item>
            <Descriptions.Item label="Sweet spot (MoS)">{money(d.graham_sweet_spot)}</Descriptions.Item>
            <Descriptions.Item label="Margin">{pct(d.graham_margin_pct)}</Descriptions.Item>
            <Descriptions.Item label="Verdict">{d.graham_verdict}</Descriptions.Item>
          </Descriptions>
        </Col>

        {/* Buffett breakdown */}
        <Col span={8}>
          <SectionTitle>
            Buffett {d.buffett_method === "pb" ? "(Justified P/B — financial)" : "(Owner-Earnings DCF)"}
          </SectionTitle>
          <Descriptions column={1} size="small" colon={false}>
            {d.buffett_method === "pb" ? (
              <>
                <Descriptions.Item label="ROE">{pct((d.raw.roe as number) * 100)}</Descriptions.Item>
                <Descriptions.Item label="Book value/sh">{money(d.raw.book_value_ps as number)}</Descriptions.Item>
                <Descriptions.Item label="Fair P/B">{num(d.fair_pb)}×</Descriptions.Item>
              </>
            ) : (
              <>
                <Descriptions.Item label="Owner earnings/sh">{money(d.owner_earnings_ps)}</Descriptions.Item>
                <Descriptions.Item label="OE multiplier">{num(d.oe_multiplier)}× <Text type="secondary" style={{ fontSize: 10 }}>({d.oe_method})</Text></Descriptions.Item>
              </>
            )}
            <Descriptions.Item label="Moat → discount r">
              <Tag color={moatColor[d.moat]} style={{ marginRight: 6 }}>{d.moat}</Tag>{pct(d.discount_rate)}
            </Descriptions.Item>
            <Descriptions.Item label="Buffett value">{money(d.buffett_value)}</Descriptions.Item>
            <Descriptions.Item label="Value/Price ratio">{num(d.buffett_ratio)}</Descriptions.Item>
            <Descriptions.Item label="Verdict">{d.buffett_verdict}</Descriptions.Item>
          </Descriptions>
        </Col>

        {/* Overrides */}
        <Col span={9}>
          <SectionTitle>
            Per-stock overrides {d.has_override && <Tag color="cyan" style={{ marginLeft: 6 }}>active</Tag>}
          </SectionTitle>
          <Text style={{ fontSize: 10.5, color: "#5c6370", display: "block", marginBottom: 10 }}>
            Auto values are heuristics. Override any input to mirror the hand-tuned
            judgment in the formula docs; the row recomputes on apply.
          </Text>
          <Row gutter={[10, 10]}>
            <Col span={12}>
              <MiniLabel>Growth g (%)</MiniLabel>
              <InputNumber size="small" style={{ width: "100%" }} placeholder={`auto ${d.growth_pct.toFixed(0)}`}
                value={growth} min={0} max={40} onChange={(v) => setGrowth(v)} />
            </Col>
            <Col span={12}>
              <MiniLabel>Moat</MiniLabel>
              <Select size="small" style={{ width: "100%" }} allowClear placeholder={`auto ${d.moat}`}
                value={moat} onChange={(v) => setMoat(v ?? null)}
                options={["wide", "moderate", "narrow", "none"].map((m) => ({ label: m, value: m }))} />
            </Col>
            <Col span={12}>
              <MiniLabel>OE multiplier</MiniLabel>
              <InputNumber size="small" style={{ width: "100%" }} step={0.05}
                placeholder={d.oe_multiplier ? `auto ${d.oe_multiplier.toFixed(2)}` : "auto"}
                value={oeMult} min={0.1} max={3} onChange={(v) => setOeMult(v)} />
            </Col>
            <Col span={12}>
              <MiniLabel>Normalized EPS</MiniLabel>
              <InputNumber size="small" style={{ width: "100%" }} step={0.1}
                placeholder={`actual ${d.eps_used != null ? d.eps_used.toFixed(2) : "—"}`}
                value={normEps} onChange={(v) => setNormEps(v)} />
            </Col>
          </Row>
          <Space style={{ marginTop: 14 }}>
            <Button type="primary" size="small" loading={saving} onClick={saveOverride}>Apply override</Button>
            {d.has_override && <Button size="small" loading={saving} onClick={clearOverride}>Clear</Button>}
          </Space>
        </Col>
      </Row>

      <Divider style={{ margin: "12px 0 10px" }} />
      <Row gutter={24} align="middle">
        <Col span={16}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: "#2dd4bf", textTransform: "uppercase",
              letterSpacing: 0.4, whiteSpace: "nowrap" }}>My Tags</span>
            <Select
              mode="tags"
              size="small"
              style={{ flex: 1, maxWidth: 460 }}
              placeholder="Type a tag and press Enter (e.g. Watchlist, Buy zone)…"
              value={tags}
              onChange={saveTags}
              options={allTags.map((t) => ({ label: t, value: t }))}
              tokenSeparators={[","]}
              tagRender={({ label, value, closable, onClose }) => (
                <Tag color={tagColor(String(value))} closable={closable} onClose={onClose}
                  style={{ marginInlineEnd: 4 }}>
                  {label}
                </Tag>
              )}
            />
          </div>
        </Col>
        <Col span={8} style={{ textAlign: "right" }}>
          <Text style={{ fontSize: 10.5, color: "#5c6370" }}>
            {d.sector} · cap {marketCap(d.market_cap)} · {d.conviction}
          </Text>
        </Col>
      </Row>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ fontSize: 11, fontWeight: 600, color: "#2dd4bf", textTransform: "uppercase",
      letterSpacing: 0.4, marginBottom: 8 }}>{children}</div>
  );
}
function MiniLabel({ children }: { children: React.ReactNode }) {
  return <div style={{ fontSize: 10, color: "#5c6370", marginBottom: 3 }}>{children}</div>;
}
