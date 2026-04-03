import { writable, get } from "svelte/store";
import type { MockConfig } from "$lib/config";
import { mockConfig } from "$lib/config";

function randomWalk(base: number, vol: number): number {
  return base * (1 + (Math.random() - 0.5) * 2 * vol);
}

const INSTRUMENTS = [
  { symbol: "AAPL", name: "Apple Inc.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 185.5 },
  { symbol: "MSFT", name: "Microsoft Corp.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 420.3 },
  { symbol: "GOOGL", name: "Alphabet Inc.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 175.8 },
  { symbol: "AMZN", name: "Amazon.com Inc.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 198.4 },
  { symbol: "NVDA", name: "NVIDIA Corp.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 890.2 },
  { symbol: "TSLA", name: "Tesla Inc.", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 245.6 },
  { symbol: "META", name: "Meta Platforms", exchange: "NASDAQ", asset_class: "equity", currency: "USD", basePrice: 560.1 },
  { symbol: "JPM", name: "JPMorgan Chase", exchange: "NYSE", asset_class: "equity", currency: "USD", basePrice: 210.5 },
  { symbol: "V", name: "Visa Inc.", exchange: "NYSE", asset_class: "equity", currency: "USD", basePrice: 285.7 },
  { symbol: "EURUSD", name: "EUR/USD", exchange: "FX", asset_class: "fx", currency: "USD", basePrice: 1.085 },
  { symbol: "GBPUSD", name: "GBP/USD", exchange: "FX", asset_class: "fx", currency: "USD", basePrice: 1.265 },
  { symbol: "USDJPY", name: "USD/JPY", exchange: "FX", asset_class: "fx", currency: "JPY", basePrice: 149.5 },
  { symbol: "US10Y", name: "US 10Y Treasury", exchange: "CME", asset_class: "fixed_income", currency: "USD", basePrice: 98.5 },
  { symbol: "US30Y", name: "US 30Y Treasury", exchange: "CME", asset_class: "fixed_income", currency: "USD", basePrice: 95.2 },
  { symbol: "CL=F", name: "Crude Oil WTI", exchange: "NYMEX", asset_class: "commodity", currency: "USD", basePrice: 78.5 },
  { symbol: "GC=F", name: "Gold Futures", exchange: "COMEX", asset_class: "commodity", currency: "USD", basePrice: 2350 },
  { symbol: "SPX_CALL_5500", name: "SPX 5500 Call", exchange: "CBOE", asset_class: "derivative", currency: "USD", basePrice: 45.3 },
  { symbol: "SPX_PUT_5200", name: "SPX 5200 Put", exchange: "CBOE", asset_class: "derivative", currency: "USD", basePrice: 38.2 },
];

const DESKS = ["Equity Trading", "Fixed Income", "FX", "Derivatives"];
const STRATEGIES = ["Long/Short Equity", "Momentum", "Curve Trading", "Carry Trade", "Volatility Arb", "Delta Neutral"];
const BOOKS = ["US Large Cap", "Tech Momentum", "UST 2s10s", "G10 Carry", "SPX Vol", "Index Hedging"];

const _prices = new Map<string, number>();

function getPrice(symbol: string): number {
  const inst = INSTRUMENTS.find((i) => i.symbol === symbol);
  if (!_prices.has(symbol) && inst) {
    _prices.set(symbol, inst.basePrice);
  }
  const price = _prices.get(symbol) || inst?.basePrice || 100;
  const vol = inst?.asset_class === "fx" ? 0.002 : 0.02;
  const newPrice = randomWalk(price, vol);
  _prices.set(symbol, newPrice);
  return newPrice;
}

export function getMockQuote(symbol: string) {
  const price = getPrice(symbol);
  const inst = INSTRUMENTS.find((i) => i.symbol === symbol);
  const change = price - (inst?.basePrice || price);
  const changePct = (change / (inst?.basePrice || price)) * 100;
  const spreadPct = inst?.asset_class === "fx" ? 0.0005 : 0.001;

  return {
    symbol,
    bid: price * (1 - spreadPct / 2),
    ask: price * (1 + spreadPct / 2),
    last: price,
    change,
    change_pct: changePct,
    volume: Math.random() * 49000000 + 100000,
    timestamp: new Date().toISOString(),
  };
}

export function getMockOHLCV(symbol: string, days: number = 90) {
  const inst = INSTRUMENTS.find((i) => i.symbol === symbol);
  let price = (inst?.basePrice || 100) * 0.95;
  const data = [];

  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    date.setHours(0, 0, 0, 0);

    const dailyReturn = (Math.random() - 0.48) * 0.03;
    const open = price;
    const close = price * (1 + dailyReturn);
    const high = Math.max(open, close) * (1 + Math.random() * 0.015);
    const low = Math.min(open, close) * (1 - Math.random() * 0.015);
    const volume = Math.random() * 29500000 + 500000;

    data.push({
      timestamp: date.toISOString(),
      open,
      high,
      low,
      close,
      volume,
    });

    price = close;
  }

  return data;
}

export function getMockPositions() {
  const positions = [];

  for (const book of BOOKS) {
    const deskIdx = Math.floor(Math.random() * DESKS.length);
    const desk = DESKS[deskIdx];
    const strategy = STRATEGIES[Math.floor(Math.random() * STRATEGIES.length)];

    const numInst = Math.floor(Math.random() * 3) + 2;
    const selected = [...INSTRUMENTS].sort(() => Math.random() - 0.5).slice(0, numInst);

    for (const inst of selected) {
      const qty = Math.round((Math.random() - 0.5) * 20000);
      const avgPrice = inst.basePrice * (0.9 + Math.random() * 0.2);
      const currentPrice = getPrice(inst.symbol);
      const pnl = (currentPrice - avgPrice) * qty;

      positions.push({
        id: crypto.randomUUID(),
        symbol: inst.symbol,
        instrument_name: inst.name,
        book,
        strategy,
        desk,
        quantity: qty,
        avg_price: avgPrice,
        current_price: currentPrice,
        pnl,
        pnl_pct: (currentPrice / avgPrice - 1) * 100,
        delta: inst.asset_class === "derivative" ? (Math.random() - 0.5) * 10000 : null,
        gamma: inst.asset_class === "derivative" ? (Math.random() - 0.5) * 200 : null,
        vega: inst.asset_class === "derivative" ? (Math.random() - 0.5) * 4000 : null,
        theta: inst.asset_class === "derivative" ? (Math.random() - 1) * 1000 : null,
      });
    }
  }

  return positions;
}

export function getMockRisk() {
  const positions = getMockPositions();
  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);
  const totalNotional = positions.reduce((sum, p) => sum + Math.abs(p.quantity * p.current_price), 0);

  const byDesk: Record<string, { pnl: number; notional: number }> = {};
  for (const p of positions) {
    if (!byDesk[p.desk]) byDesk[p.desk] = { pnl: 0, notional: 0 };
    byDesk[p.desk].pnl += p.pnl;
    byDesk[p.desk].notional += Math.abs(p.quantity * p.current_price);
  }

  return {
    timestamp: new Date().toISOString(),
    var_95: totalNotional * (0.02 + Math.random() * 0.02),
    var_99: totalNotional * (0.035 + Math.random() * 0.025),
    delta: (Math.random() - 0.5) * 2000000,
    gamma: (Math.random() - 0.5) * 100000,
    vega: (Math.random() - 0.5) * 4000000,
    theta: (Math.random() - 0.5) * 1000000,
    pnl: totalPnl,
    by_desk: Object.entries(byDesk).map(([name, v]) => ({
      name,
      pnl: v.pnl,
      notional: v.notional,
      var_95: v.notional * (0.01 + Math.random() * 0.03),
    })),
  };
}

export function getMockRiskHistory(days: number = 30) {
  const data = [];
  let baseVar = 5000000;
  let basePnl = 100000;

  for (let i = days; i >= 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    date.setHours(0, 0, 0, 0);

    baseVar *= 0.9 + Math.random() * 0.2;
    basePnl += (Math.random() - 0.48) * 200000;

    data.push({
      timestamp: date.toISOString(),
      var_95: baseVar,
      var_99: baseVar * 1.5,
      pnl: basePnl,
      delta: (Math.random() - 0.5) * 1600000,
      gamma: (Math.random() - 0.5) * 60000,
      vega: (Math.random() - 0.5) * 3000000,
    });
  }

  return data;
}

export function getMockPnLAttribution() {
  const positions = getMockPositions();
  const totalPnl = positions.reduce((sum, p) => sum + p.pnl, 0);

  const byInstrument = [...positions]
    .sort((a, b) => b.pnl - a.pnl)
    .map((p) => ({ symbol: p.symbol, name: p.instrument_name, pnl: p.pnl }));

  const byDesk: Record<string, number> = {};
  for (const p of positions) {
    byDesk[p.desk] = (byDesk[p.desk] || 0) + p.pnl;
  }

  const factors = ["Delta", "Gamma", "Vega", "Theta", "Rho", "Carry", "Other"];
  const byFactor = factors.map((factor) => ({
    factor,
    pnl: (Math.random() - 0.5) * Math.abs(totalPnl) * 0.4,
  }));

  return {
    timestamp: new Date().toISOString(),
    total_pnl: totalPnl,
    by_instrument: byInstrument.slice(0, 20),
    by_desk: Object.entries(byDesk).map(([name, pnl]) => ({ name, pnl })),
    by_factor: byFactor,
    top_contributors: byInstrument.slice(0, 5).map((i) => ({ symbol: i.symbol, pnl: i.pnl })),
    top_detractors: byInstrument.slice(-5).map((i) => ({ symbol: i.symbol, pnl: i.pnl })),
  };
}

export function getMockInstruments(params?: { asset_class?: string; search?: string }) {
  let results = INSTRUMENTS;

  if (params?.asset_class) {
    results = results.filter((i) => i.asset_class === params.asset_class);
  }
  if (params?.search) {
    const q = params.search.toLowerCase();
    results = results.filter((i) => q === "" || i.symbol.toLowerCase().includes(q) || i.name.toLowerCase().includes(q));
  }

  return results.map((i) => ({
    id: crypto.randomUUID(),
    symbol: i.symbol,
    name: i.name,
    exchange: i.exchange,
    asset_class: i.asset_class,
    currency: i.currency,
  }));
}

export async function mockRequest<T>(fn: () => T): Promise<T> {
  const config = get(mockConfig);
  if (config.dataDelay > 0) {
    await new Promise((r) => setTimeout(r, config.dataDelay));
  }
  return fn();
}
