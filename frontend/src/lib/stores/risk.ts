import { writable } from "svelte/store";

interface RiskMetrics {
  var_95: number;
  var_99: number;
  delta: number;
  gamma: number;
  vega: number;
  theta: number;
  pnl: number;
  by_desk: Array<{ name: string; pnl: number; notional: number; var_95: number }>;
  timestamp: string;
}

interface Position {
  id: string;
  symbol: string;
  instrument_name: string;
  book: string;
  strategy: string;
  desk: string;
  quantity: number;
  avg_price: number;
  current_price: number;
  pnl: number;
  pnl_pct: number;
  delta?: number;
  gamma?: number;
  vega?: number;
  theta?: number;
}

export const riskMetrics = writable<RiskMetrics | null>(null);
export const positions = writable<Position[]>([]);
export const varHistory = writable<any[]>([]);
export const isLoadingRisk = writable(false);
export const isLoadingPositions = writable(false);
export const selectedDesk = writable<string>("");
