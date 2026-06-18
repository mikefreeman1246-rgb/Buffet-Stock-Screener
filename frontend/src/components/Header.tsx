import { useState } from "react";
import { Button, Dropdown, Progress, Space, Tag, Tooltip, Typography } from "antd";
import {
  LineChartOutlined, SlidersOutlined, SyncOutlined,
  PauseCircleOutlined, DownOutlined, LoadingOutlined,
} from "@ant-design/icons";
import { usePipeline } from "../hooks/usePipeline";
import type { PipelineDone } from "../hooks/usePipeline";
import type { Assumptions, MetaStats } from "../lib/types";

interface Props {
  stats: MetaStats | null;
  assumptions: Assumptions | null;
  onOpenAssumptions: () => void;
  onPullDone: (done: PipelineDone) => void;
}

export default function AppHeader({ stats, assumptions, onOpenAssumptions, onPullDone }: Props) {
  const { progress, running, start, stop } = usePipeline(onPullDone);
  const [pulling, setPulling] = useState(false);

  const pct =
    progress && progress.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : 0;

  // Freshness badge
  let statusColor = "default";
  let statusText = "no data";
  if (running) {
    statusColor = "processing";
    statusText = progress
      ? `pulling ${progress.completed}/${progress.total || "…"}${progress.ticker ? ` · ${progress.ticker}` : ""}`
      : "pulling…";
  } else if (stats?.last_update) {
    const d = new Date(stats.last_update);
    statusColor = "success";
    statusText = `${stats.stock_count} stocks · ${d.toLocaleDateString("en-US", {
      month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
    })}`;
  }

  const doStart = async (limit?: number, universe: string = "sp500") => {
    setPulling(true);
    try {
      await start(limit, universe);
    } finally {
      setPulling(false);
    }
  };

  const pullMenu = {
    items: [
      { key: "sp500", label: "Full S&P 500 (~500)" },
      { key: "sp1500", label: "Full S&P 1500 (~1500)" },
      { type: "divider" as const },
      { key: "sample50", label: "Quick sample (50)" },
      { key: "smoke10", label: "Smoke test (10)" },
    ],
    onClick: ({ key }: { key: string }) => {
      if (key === "sp500") doStart(undefined, "sp500");
      else if (key === "sp1500") doStart(undefined, "sp1500");
      else if (key === "sample50") doStart(50, "sp500");
      else if (key === "smoke10") doStart(10, "sp500");
    },
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 14, width: "100%", height: "100%" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <LineChartOutlined style={{ fontSize: 16, color: "#2dd4bf" }} />
        <Typography.Text
          strong
          style={{ color: "#e8eaed", fontSize: 15, fontWeight: 600, letterSpacing: "-0.3px", whiteSpace: "nowrap" }}
        >
          Stock Value Screener
        </Typography.Text>
        <Tag
          style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 10, margin: "0 0 0 4px", color: "#5c6370" }}
        >
          Graham × Buffett
        </Tag>
      </div>

      <div style={{ flex: 1 }} />

      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <Tooltip title={assumptions ? `AAA bond yield Y = ${assumptions.aaa_bond_yield}%` : ""}>
          <Tag
            color={statusColor}
            style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, margin: 0, cursor: "default" }}
          >
            {statusText}
          </Tag>
        </Tooltip>

        {running && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <LoadingOutlined spin style={{ fontSize: 13, color: "#2dd4bf" }} />
            <div className="pipeline-progress" style={{ width: 130 }}>
              <Progress
                percent={pct}
                size="small"
                showInfo={false}
                status={progress && progress.total > 0 ? "active" : "normal"}
                strokeColor="#2dd4bf"
                trailColor="rgba(255,255,255,0.06)"
                style={{ margin: 0 }}
              />
            </div>
            <span
              style={{
                fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                fontWeight: 600, color: "#2dd4bf", minWidth: 30, textAlign: "right",
              }}
            >
              {progress && progress.total > 0 ? `${pct}%` : "…"}
            </span>
          </div>
        )}

        <Tooltip title="Valuation assumptions (bond yield, growth cap, discount rates, margin of safety)">
          <Button size="small" icon={<SlidersOutlined />} onClick={onOpenAssumptions}>
            Assumptions
          </Button>
        </Tooltip>

        <Space.Compact>
          {running ? (
            <Button size="small" icon={<PauseCircleOutlined />} onClick={stop}>Stop</Button>
          ) : (
            <Dropdown menu={pullMenu} trigger={["click"]}>
              <Button size="small" type="primary" icon={<SyncOutlined />} loading={pulling}>
                Pull Data <DownOutlined />
              </Button>
            </Dropdown>
          )}
        </Space.Compact>
      </div>
    </div>
  );
}
