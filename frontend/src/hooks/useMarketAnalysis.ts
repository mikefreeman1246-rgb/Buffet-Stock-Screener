import { useCallback, useEffect, useState } from "react";

interface IndicatorMetadata {
  label: string;
  unit: string;
  weight: number;
  description: string;
  healthy: string;
  watch: string;
  chaos: string;
  implications: {
    short_term: string;
    long_term: string;
    bullish_threshold?: string;
    bearish_threshold?: string;
  };
  typical_ranges?: Record<string, string>;
}

interface MarketAnalysis {
  health: string;
  short_term: {
    direction: string;
    reasoning: string;
    horizon: string;
  };
  long_term: {
    direction: string;
    reasoning: string;
    horizon: string;
  };
  signal_breakdown: {
    healthy_count: number;
    watch_count: number;
    chaos_count: number;
    total_count: number;
  };
  top_risks: string[];
  opportunities: string[];
}

export function useMarketAnalysis() {
  const [metadata, setMetadata] = useState<Record<string, IndicatorMetadata> | null>(null);
  const [analysis, setAnalysis] = useState<MarketAnalysis | null>(null);
  const [loading, setLoading] = useState(false);

  const loadIndicators = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/market/indicators");
      const data = await res.json();
      setMetadata(data);
    } catch (err) {
      console.error("Failed to load indicator metadata:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/market/health-analysis");
      const data = await res.json();
      if (data.analysis) {
        setAnalysis(data.analysis);
      }
    } catch (err) {
      console.error("Failed to load market analysis:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const getIndicatorMetadata = (key: string): IndicatorMetadata | null => {
    return metadata ? metadata[key] || null : null;
  };

  useEffect(() => {
    loadIndicators();
  }, [loadIndicators]);

  useEffect(() => {
    loadAnalysis();
  }, [loadAnalysis]);

  return {
    metadata,
    analysis,
    loading,
    getIndicatorMetadata,
    refreshAnalysis: loadAnalysis,
  };
}
