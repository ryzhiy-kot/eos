import { writable } from "svelte/store";

interface Quote {
  symbol: string;
  bid: number;
  ask: number;
  last: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

interface OHLCVBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const quotes = writable<Record<string, Quote>>({});
export const selectedSymbol = writable<string>("AAPL");
export const ohlcvData = writable<OHLCVBar[]>([]);
export const isLoadingOHLCV = writable(false);
export const marketConnected = writable(false);
export const selectedAssetClass = writable<string>("");

export function updateQuotes(newQuotes: Quote[]) {
  quotes.update((q) => {
    for (const quote of newQuotes) {
      q[quote.symbol] = quote;
    }
    return q;
  });
}
