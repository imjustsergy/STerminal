<script lang="ts">
  import { signColor } from '../../lib/format';
  import type { CorrelationsResponse } from '../../lib/types';

  interface Props {
    response: CorrelationsResponse;
  }

  const { response }: Props = $props();

  function formatCorrelation(n: number | null): string {
    if (n === null) {
      return 'datos insuficientes';
    }
    const sign = n > 0 ? '+' : '';
    return `${sign}${n.toFixed(2)}`;
  }
</script>

<div class="correlations-panel">
  <div class="header">
    <span class="title">CORRELACIONES</span>
    <span class="symbol acc">{response.symbol}</span>
    <span class="dim class-tag">{response.asset_class}</span>
  </div>
  <div class="notice dimmer">
    rendimientos diarios frente a una cesta de referencia fija (SPY, QQQ, GLD, BTC, ETH,
    EURUSD) — coeficiente de Pearson, ventana de ~3 meses
  </div>
  <ul class="rows">
    {#each response.correlations as row (row.symbol)}
      <li class="row">
        <span class="ref-symbol">{row.symbol}</span>
        <span class="ref-class dim">{row.asset_class}</span>
        <span
          class="value tabular"
          class:na={row.correlation === null}
          class:sign-pos={row.correlation !== null && signColor(row.correlation) === 'pos'}
          class:sign-neg={row.correlation !== null && signColor(row.correlation) === 'neg'}
          class:sign-dim={row.correlation === null || signColor(row.correlation) === 'dim'}
        >
          {formatCorrelation(row.correlation)}
        </span>
      </li>
    {/each}
  </ul>
</div>

<style>
  .correlations-panel {
    padding: 20px 18px 60px;
    max-width: 820px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 10px;
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
    margin-bottom: 18px;
  }
  .rows {
    list-style: none;
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border);
  }
  .row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
  }
  .row:last-child {
    border-bottom: none;
  }
  .ref-symbol {
    font-weight: 700;
    min-width: 90px;
  }
  .ref-class {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    min-width: 60px;
  }
  .value {
    margin-left: auto;
    font-weight: 600;
    font-size: 14px;
  }
  .value.na {
    font-weight: 400;
    font-size: 12px;
    opacity: 0.6;
  }
</style>
