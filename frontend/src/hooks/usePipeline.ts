import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { PipelineStatus } from "../lib/types";

export interface PipelineProgress {
  completed: number;
  total: number;
  failed: number;
  ticker: string | null;
}

export interface PipelineDone {
  completed: number;
  total: number;
  failed: number;
  universe: string;
  status: string;
}

export function usePipeline(onComplete?: (done: PipelineDone) => void) {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [progress, setProgress] = useState<PipelineProgress | null>(null);
  const [running, setRunning] = useState(false);
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  const refreshStatus = useCallback(async () => {
    try {
      const s = await api.pipelineStatus();
      setStatus(s);
      setRunning(s.is_running);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    let ws: WebSocket | null = null;
    let closed = false;
    let retry: number | undefined;

    const connect = () => {
      refreshStatus(); // resync on every (re)connect, e.g. after a backend restart
      const proto = window.location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${window.location.host}/ws/pipeline`);
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === "progress") {
          setRunning(true);
          setProgress({
            completed: msg.completed, total: msg.total,
            failed: msg.failed, ticker: msg.ticker,
          });
        } else if (msg.type === "done") {
          setRunning(false);
          setProgress({
            completed: msg.completed, total: msg.total,
            failed: msg.failed, ticker: null,
          });
          refreshStatus();
          onCompleteRef.current?.({
            completed: msg.completed, total: msg.total, failed: msg.failed,
            universe: msg.universe ?? "sp500", status: msg.status ?? "completed",
          });
        }
      };
      // auto-reconnect if the socket drops (network blip or backend restart)
      ws.onclose = () => {
        if (!closed) retry = window.setTimeout(connect, 2000);
      };
    };

    connect();
    return () => {
      closed = true;
      window.clearTimeout(retry);
      ws?.close();
    };
  }, [refreshStatus]);

  const start = useCallback(async (limit?: number, universe: string = "sp500") => {
    setRunning(true);
    setProgress({ completed: 0, total: limit ?? 0, failed: 0, ticker: null });
    await api.startPipeline(limit, universe);
  }, []);

  const stop = useCallback(async () => {
    await api.stopPipeline();
  }, []);

  return { status, progress, running, start, stop, refreshStatus };
}
