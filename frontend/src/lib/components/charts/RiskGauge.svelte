<script lang="ts">
  let {
    value,
    max,
    label,
    format = "currency",
  }: {
    value: number;
    max: number;
    label: string;
    format?: "currency" | "number" | "pct";
  } = $props();

  const pct = $derived(Math.min((Math.abs(value) / max) * 100, 100));
  const angle = $derived((pct / 100) * 180);

  function formatValue(v: number): string {
    if (format === "currency") {
      if (Math.abs(v) >= 1e6) return `$${(v / 1e6).toFixed(1)}M`;
      if (Math.abs(v) >= 1e3) return `$${(v / 1e3).toFixed(0)}K`;
      return `$${v.toFixed(0)}`;
    }
    return v.toLocaleString();
  }

  const color = $derived(
    pct > 80 ? "var(--red)" : pct > 50 ? "var(--yellow)" : "var(--green)"
  );
</script>

<div class="gauge">
  <svg viewBox="0 0 200 120" class="gauge-svg">
    <!-- Background arc -->
    <path
      d="M 20 100 A 80 80 0 0 1 180 100"
      fill="none"
      stroke="rgba(30, 58, 95, 0.4)"
      stroke-width="12"
      stroke-linecap="round"
    />
    <!-- Value arc -->
    <path
      d={(() => {
        const r = 80;
        const cx = 100;
        const cy = 100;
        const startAngle = Math.PI;
        const endAngle = Math.PI - (angle * Math.PI) / 180;
        const x1 = cx + r * Math.cos(startAngle);
        const y1 = cy + r * Math.sin(startAngle);
        const x2 = cx + r * Math.cos(endAngle);
        const y2 = cy + r * Math.sin(endAngle);
        const largeArc = angle > 180 ? 1 : 0;
        return `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 0 ${x2} ${y2}`;
      })()}
      fill="none"
      stroke={color}
      stroke-width="12"
      stroke-linecap="round"
    />
    <!-- Value text -->
    <text x="100" y="85" text-anchor="middle" fill="var(--text-primary)"
      font-size="20" font-weight="600" font-family="'JetBrains Mono', monospace">
      {formatValue(value)}
    </text>
    <!-- Label -->
    <text x="100" y="110" text-anchor="middle" fill="var(--text-muted)"
      font-size="11" font-weight="500">
      {label}
    </text>
  </svg>
</div>

<style>
  .gauge {
    display: flex;
    justify-content: center;
    padding: 8px;
  }

  .gauge-svg {
    width: 100%;
    max-width: 200px;
  }
</style>
