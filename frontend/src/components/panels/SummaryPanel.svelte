<script lang="ts">
  import { formatMoney, formatPercent, formatUsd, signColor } from '../../lib/format';
  import type { SummaryResponse } from '../../lib/types';

  interface Props {
    response: SummaryResponse;
  }

  const { response }: Props = $props();

  const CLASS_LABELS: Record<string, string> = {
    equity: 'ACCIÓN',
    crypto: 'CRIPTO',
    fx: 'FOREX',
  };

  const clsLabel = $derived(CLASS_LABELS[response.asset_class] ?? response.asset_class.toUpperCase());
  const sign = $derived(signColor(response.quote.change));
  const arrow = $derived(response.quote.change > 0 ? '▲' : response.quote.change < 0 ? '▼' : '■');
</script>

<div class="summary-panel">
  <div class="header">
    <div>
      <div class="title-row">
        <span class="symbol">{response.symbol}</span>
        <span class="cls-badge dim">{clsLabel}</span>
      </div>
    </div>
    <div class="spacer"></div>
    <div class="price-block">
      <div class="price sign-{sign} tabular">
        {formatMoney(response.quote.price, response.quote.price < 1 ? 4 : 2)}
        <span class="currency dim">{response.quote.currency}</span>
      </div>
      <div class="change sign-{sign} tabular">
        {arrow}
        {formatUsd(response.quote.change)} ({formatPercent(response.quote.change_percent)})
      </div>
    </div>
  </div>
  <div class="stats">
    <div class="stat-row">
      <span class="dim">Timestamp</span>
      <span class="tabular">{response.quote.timestamp}</span>
    </div>
  </div>
</div>

<style>
  .summary-panel {
    display: flex;
    flex-direction: column;
  }
  .header {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    padding: 12px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .title-row {
    display: flex;
    align-items: center;
    gap: 9px;
  }
  .symbol {
    font-size: 24px;
    font-weight: 700;
  }
  .cls-badge {
    font-size: 10px;
    border: 1px solid var(--border);
    padding: 1px 6px;
    letter-spacing: 0.5px;
  }
  .spacer {
    flex: 1;
  }
  .price-block {
    text-align: right;
  }
  .price {
    font-size: 30px;
    font-weight: 700;
    line-height: 1;
  }
  .currency {
    font-size: 13px;
    font-weight: 400;
  }
  .change {
    font-size: 14px;
    margin-top: 4px;
  }
  .stats {
    padding: 6px 0;
  }
  .stat-row {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    padding: 6px 18px;
    border-bottom: 1px dashed var(--border);
    font-size: 12px;
  }
</style>
