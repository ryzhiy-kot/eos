export function formatNumber(value: number, decimals = 2): string {
  if (Math.abs(value) >= 1e9) {
    return (value / 1e9).toFixed(decimals) + "B";
  }
  if (Math.abs(value) >= 1e6) {
    return (value / 1e6).toFixed(decimals) + "M";
  }
  if (Math.abs(value) >= 1e3) {
    return (value / 1e3).toFixed(decimals) + "K";
  }
  return value.toFixed(decimals);
}

export function formatCurrency(value: number, currency = "USD"): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(2)}K`;
  return `${sign}$${abs.toFixed(2)}`;
}

export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatPrice(value: number, symbol?: string): string {
  if (symbol?.includes("USD") || symbol?.includes("JPY")) {
    return value.toFixed(4);
  }
  if (value < 1) return value.toFixed(4);
  if (value < 100) return value.toFixed(2);
  return value.toFixed(2);
}

export function formatTimestamp(ts: string | Date): string {
  const d = typeof ts === "string" ? new Date(ts) : ts;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
