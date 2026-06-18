import { useEffect, useState } from "react";
import { Drawer, InputNumber, Switch, Button, Space, Divider, Typography, Tooltip, message } from "antd";
import { api } from "../../lib/api";
import type { WeatherSettings } from "../../lib/types";

const { Text } = Typography;

// Plain-English labels + descriptions for the divergence rules.
const RULE_META: Record<string, { label: string; hint: string }> = {
  hidden_hedging: {
    label: "Hidden hedging",
    hint: "SKEW red + VVIX elevated while VIX stays calm → +1 concern.",
  },
  credit_liquidity: {
    label: "Credit + liquidity squeeze",
    hint: "Credit spreads red while net liquidity tightens → +1 concern.",
  },
  cascade_floor: {
    label: "Cross-asset cascade",
    hint: "Stocks, bonds and gold falling together → floor concern at 4.",
  },
};

function NumField({
  label,
  value,
  onChange,
  min,
}: {
  label: string;
  value: number;
  onChange: (v: number | null) => void;
  min?: number;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2, flex: 1 }}>
      <Text style={{ fontSize: 10.5, color: "#5c6370" }}>{label}</Text>
      <InputNumber
        size="small"
        style={{ width: "100%" }}
        value={value}
        min={min}
        onChange={onChange}
      />
    </div>
  );
}

export default function WeatherSettingsDrawer({
  open,
  onClose,
  onSaved,
}: {
  open: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [settings, setSettings] = useState<WeatherSettings | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) api.getWeatherSettings().then(setSettings);
  }, [open]);

  const patchThr = (k: string, field: "green_max" | "yellow_max" | "weight", v: number | null) =>
    setSettings((s) =>
      s
        ? { ...s, thresholds: { ...s.thresholds, [k]: { ...s.thresholds[k], [field]: v ?? 0 } } }
        : s,
    );

  const patchRule = (k: string, v: boolean) =>
    setSettings((s) => (s ? { ...s, rules: { ...s.rules, [k]: v } } : s));

  const save = async () => {
    if (!settings) return;
    setSaving(true);
    try {
      await api.updateWeatherSettings(settings);
      onSaved();
      message.success("Ranges applied — weather recomputed");
      onClose();
    } catch {
      message.error("Could not save settings");
    } finally {
      setSaving(false);
    }
  };

  const reset = async () => {
    try {
      const d = await api.resetWeatherSettings();
      setSettings(d);
      onSaved();
      message.success("Restored default ranges");
    } catch {
      message.error("Could not reset settings");
    }
  };

  return (
    <Drawer
      title="Adjust indicator ranges"
      open={open}
      onClose={onClose}
      width={460}
      extra={
        <Space>
          <Button size="small" onClick={reset}>
            Reset defaults
          </Button>
          <Button type="primary" size="small" loading={saving} onClick={save}>
            Save
          </Button>
        </Space>
      }
    >
      {!settings ? null : (
        <>
          <Text style={{ fontSize: 11, color: "#8b919e" }}>
            Each gauge is normalized so higher = more stress. Green ≤ first
            threshold, yellow ≤ second, red above. Weight sets its pull on the
            overall concern level. Saving recomputes instantly — no data re-pull.
          </Text>

          <Divider titlePlacement="start" style={{ fontSize: 12, margin: "16px 0 12px" }}>
            Indicator thresholds
          </Divider>

          {Object.entries(settings.thresholds).map(([k, cfg]) => (
            <div key={k} style={{ marginBottom: 14 }}>
              <Text strong style={{ fontSize: 12, color: "#e8eaed" }}>
                {cfg.label}
                {cfg.unit ? <span style={{ color: "#5c6370", fontWeight: 400 }}> · {cfg.unit}</span> : null}
              </Text>
              <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
                <NumField
                  label="Green ≤"
                  value={cfg.green_max}
                  onChange={(v) => patchThr(k, "green_max", v)}
                />
                <NumField
                  label="Yellow ≤"
                  value={cfg.yellow_max}
                  onChange={(v) => patchThr(k, "yellow_max", v)}
                />
                <NumField
                  label="Weight"
                  value={cfg.weight}
                  min={0}
                  onChange={(v) => patchThr(k, "weight", v)}
                />
              </div>
            </div>
          ))}

          <Divider titlePlacement="start" style={{ fontSize: 12, margin: "16px 0 12px" }}>
            Divergence rules
          </Divider>

          {Object.entries(settings.rules).map(([k, on]) => {
            const meta = RULE_META[k] ?? { label: k, hint: "" };
            return (
              <div
                key={k}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  justifyContent: "space-between",
                  gap: 12,
                  marginBottom: 12,
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <Tooltip title={meta.hint}>
                    <Text style={{ fontSize: 12, color: "#e8eaed" }}>{meta.label}</Text>
                  </Tooltip>
                  {meta.hint && (
                    <div style={{ fontSize: 10.5, color: "#5c6370", marginTop: 2 }}>{meta.hint}</div>
                  )}
                </div>
                <Switch checked={on} onChange={(v) => patchRule(k, v)} />
              </div>
            );
          })}
        </>
      )}
    </Drawer>
  );
}
