import { useEffect, useState } from "react";
import { Button, Divider, Drawer, InputNumber, Space, Typography, message } from "antd";
import { CloudDownloadOutlined, ReloadOutlined } from "@ant-design/icons";
import { api } from "../lib/api";
import type { Assumptions } from "../lib/types";

interface Props {
  open: boolean;
  assumptions: Assumptions | null;
  onClose: () => void;
  onSaved: (a: Assumptions) => void;
}

const { Text } = Typography;

function Field({
  label, hint, value, onChange, min, max, step = 0.1, suffix,
}: {
  label: string; hint?: string; value: number; suffix?: string;
  onChange: (v: number) => void; min?: number; max?: number; step?: number;
}) {
  return (
    <div style={{ marginBottom: 14 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <Text style={{ fontSize: 12, color: "#e8eaed" }}>{label}</Text>
        {suffix && <Text style={{ fontSize: 10, color: "#5c6370", fontFamily: "monospace" }}>{suffix}</Text>}
      </div>
      {hint && <div style={{ fontSize: 10.5, color: "#5c6370", marginBottom: 4 }}>{hint}</div>}
      <InputNumber
        size="small" style={{ width: "100%" }} value={value}
        min={min} max={max} step={step}
        onChange={(v) => v != null && onChange(v)}
      />
    </div>
  );
}

export default function AssumptionsDrawer({ open, assumptions, onClose, onSaved }: Props) {
  const [draft, setDraft] = useState<Assumptions | null>(assumptions);
  const [saving, setSaving] = useState(false);
  const [fetchingYield, setFetchingYield] = useState(false);

  useEffect(() => setDraft(assumptions), [assumptions, open]);

  if (!draft) return <Drawer open={open} onClose={onClose} title="Valuation Assumptions" width={360} />;

  const set = (k: keyof Assumptions) => (v: number) => setDraft({ ...draft, [k]: v });

  const save = async () => {
    setSaving(true);
    try {
      const saved = await api.updateAssumptions(draft);
      onSaved(saved);
      message.success("Assumptions applied — screen updated");
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const refreshYield = async () => {
    setFetchingYield(true);
    try {
      const { aaa_bond_yield } = await api.refreshYield();
      setDraft({ ...draft, aaa_bond_yield });
      message.success(`AAA yield updated to ${aaa_bond_yield}% (FRED)`);
    } catch {
      message.error("Could not reach FRED");
    } finally {
      setFetchingYield(false);
    }
  };

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title="Valuation Assumptions"
      width={360}
      extra={
        <Button type="primary" size="small" loading={saving} onClick={save}>
          Apply
        </Button>
      }
    >
      <Text style={{ fontSize: 11, color: "#8b919e" }}>
        Global inputs to both models. Changing these re-ranks the whole universe
        instantly — no data re-pull. Defaults come from the formula docs.
      </Text>

      <Divider titlePlacement="start" style={{ fontSize: 12, margin: "16px 0 12px" }}>Graham</Divider>
      <Field label="AAA bond yield (Y)" suffix="percent"
        hint="Graham's interest-rate adjustment 4.4 / Y"
        value={draft.aaa_bond_yield} onChange={set("aaa_bond_yield")} min={0.5} max={20} step={0.01} />
      <Button size="small" icon={<CloudDownloadOutlined />} loading={fetchingYield}
        onClick={refreshYield} style={{ marginBottom: 14 }}>
        Fetch live yield from FRED
      </Button>
      <Field label="Base P/E (no growth)" value={draft.graham_base_pe} onChange={set("graham_base_pe")} min={1} max={20} />
      <Field label="Growth multiplier (+ per 1% g)" value={draft.graham_growth_multiplier} onChange={set("graham_growth_multiplier")} min={0.5} max={4} />
      <Field label="Growth cap (g max)" suffix="percent"
        hint="Caps both models' growth rate. Lower it to be stricter."
        value={draft.graham_g_cap} onChange={set("graham_g_cap")} min={0} max={40} step={1} />
      <Field label="Margin of safety" suffix="fraction"
        hint="Sweet spot = value × (1 − this). 0.25 = 25% discount."
        value={draft.margin_of_safety_pct} onChange={set("margin_of_safety_pct")} min={0} max={0.6} step={0.05} />

      <Divider titlePlacement="start" style={{ fontSize: 12, margin: "16px 0 12px" }}>Buffett DCF</Divider>
      <Text style={{ fontSize: 10.5, color: "#5c6370" }}>Discount rate by moat quality (percent):</Text>
      <div style={{ marginTop: 8 }}>
        <Field label="Wide moat (r)" value={draft.r_wide} onChange={set("r_wide")} min={4} max={20} />
        <Field label="Moderate moat (r)" value={draft.r_moderate} onChange={set("r_moderate")} min={4} max={20} />
        <Field label="Narrow moat (r)" value={draft.r_narrow} onChange={set("r_narrow")} min={4} max={20} />
        <Field label="No moat (r)" value={draft.r_none} onChange={set("r_none")} min={4} max={20} />
      </div>
      <Field label="Terminal growth" suffix="percent"
        hint="Perpetuity growth after year 10 (GDP-like)."
        value={draft.terminal_growth} onChange={set("terminal_growth")} min={0} max={5} step={0.1} />

      <Divider style={{ margin: "16px 0" }} />
      <Space>
        <Button size="small" icon={<ReloadOutlined />} onClick={() => setDraft(assumptions)}>
          Revert
        </Button>
        <Button type="primary" size="small" loading={saving} onClick={save}>
          Apply & re-screen
        </Button>
      </Space>
    </Drawer>
  );
}
