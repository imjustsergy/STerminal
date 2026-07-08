<script lang="ts">
  import type { FinancialsResponse } from '../../lib/types';

  interface Props {
    response: FinancialsResponse;
  }

  const { response }: Props = $props();

  const NA = 'no disponible';

  function formatCompactUsd(n: number | null): string {
    if (n === null) {
      return NA;
    }
    const abs = Math.abs(n);
    if (abs >= 1e12) {
      return `$${(n / 1e12).toFixed(2)}T`;
    }
    if (abs >= 1e9) {
      return `$${(n / 1e9).toFixed(2)}B`;
    }
    if (abs >= 1e6) {
      return `$${(n / 1e6).toFixed(2)}M`;
    }
    return `$${n.toFixed(2)}`;
  }

  function formatUsdPrice(n: number | null): string {
    return n === null ? NA : `$${n.toFixed(2)}`;
  }

  function formatRatio(n: number | null): string {
    return n === null ? NA : `${n.toFixed(2)}x`;
  }

  function formatPct(n: number | null): string {
    return n === null ? NA : `${n.toFixed(2)}%`;
  }

  function formatText(s: string | null): string {
    return s === null || s === '' ? NA : s;
  }

  const f = $derived(response.financials);

  const rows = $derived([
    { label: 'Capitalización', value: formatCompactUsd(f.market_cap) },
    { label: 'PER', value: formatRatio(f.pe_ratio) },
    { label: 'BPA', value: formatUsdPrice(f.eps) },
    { label: 'Dividendo', value: formatPct(f.dividend_yield) },
    { label: 'Máx. 52 sem.', value: formatUsdPrice(f.week52_high) },
    { label: 'Mín. 52 sem.', value: formatUsdPrice(f.week52_low) },
    { label: 'Beta', value: formatPct(f.beta) },
    { label: 'Sector', value: formatText(f.sector) },
    { label: 'Industria', value: formatText(f.industry) },
  ]);
</script>

<div class="financials-panel">
  <div class="header">
    <span class="title">DATOS FINANCIEROS</span>
    <span class="symbol acc">{response.symbol}</span>
    <span class="dim class-tag">{response.asset_class}</span>
  </div>
  {#if response.asset_class !== 'equity'}
    <div class="notice dimmer">
      solo acciones tienen ratios financieros por ahora — todos los campos aparecen
      como "{NA}" para {response.asset_class}
    </div>
  {/if}
  <div class="grid">
    {#each rows as row (row.label)}
      <div class="cell">
        <div class="label dim">{row.label}</div>
        <div class="value" class:na={row.value === NA}>{row.value}</div>
      </div>
    {/each}
  </div>
</div>

<style>
  .financials-panel {
    padding: 20px 18px 60px;
    max-width: 820px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 18px;
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .symbol {
    font-weight: 700;
  }
  .class-tag {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .notice {
    font-size: 12px;
    margin-bottom: 16px;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
  }
  .cell {
    background: var(--panel);
    padding: 12px 14px;
  }
  .label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }
  .value {
    font-size: 15px;
    font-weight: 600;
  }
  .value.na {
    font-weight: 400;
    opacity: 0.5;
    font-size: 13px;
  }
</style>
