<script lang="ts">
  import { formatMoney, formatPercent, formatUsd, signColor } from '../../lib/format';
  import type { PortfolioResponse } from '../../lib/types';

  interface Props {
    response: PortfolioResponse;
    onNavigate: (symbol: string) => void;
  }

  const { response, onNavigate }: Props = $props();

  const CLASS_LABELS: Record<string, string> = {
    equity: 'ACCIÓN',
    crypto: 'CRIPTO',
    fx: 'FOREX',
  };
</script>

<div class="portfolio-panel">
  <div class="header">
    <span class="title">CARTERA</span>
    <div class="spacer"></div>
    <div class="totals">
      <div class="total-item">
        <div class="label dim">VALOR</div>
        <div class="value tabular">{formatMoney(response.summary.total_market_value)}</div>
      </div>
      <div class="total-item">
        <div class="label dim">P&amp;L TOTAL</div>
        <div class="value tabular sign-{signColor(response.summary.total_pnl)}">
          {formatUsd(response.summary.total_pnl)} ({formatPercent(response.summary.total_pnl_percent)})
        </div>
      </div>
      <div class="total-item">
        <div class="label dim">P&amp;L DÍA</div>
        <div class="value tabular sign-{signColor(response.summary.total_daily_pnl)}">
          {formatUsd(response.summary.total_daily_pnl)}
        </div>
      </div>
    </div>
  </div>
  <table>
    <thead>
      <tr>
        <th>SÍMBOLO</th>
        <th class="num">CANT.</th>
        <th class="num">COSTE MED.</th>
        <th class="num">PRECIO</th>
        <th class="num">VALOR</th>
        <th class="num">P&amp;L</th>
        <th class="num">P&amp;L %</th>
        <th class="num">P&amp;L DÍA</th>
        <th class="num">ASIG. %</th>
      </tr>
    </thead>
    <tbody>
      {#each response.holdings as h (h.symbol + h.asset_class)}
        <tr>
          <td>
            <button type="button" class="symbol-link" onclick={() => onNavigate(h.symbol)}>{h.symbol}</button>
            <span class="cls-badge dimmer">{CLASS_LABELS[h.asset_class] ?? h.asset_class.toUpperCase()}</span>
          </td>
          <td class="num tabular dim">{formatMoney(h.quantity, 4)}</td>
          <td class="num tabular dim">{formatMoney(h.avg_cost_price)}</td>
          <td class="num tabular">{formatMoney(h.current_price)}</td>
          <td class="num tabular">{formatMoney(h.market_value)}</td>
          <td class="num tabular sign-{signColor(h.pnl)}">{formatUsd(h.pnl)}</td>
          <td class="num tabular sign-{signColor(h.pnl_percent)}">{formatPercent(h.pnl_percent)}</td>
          <td class="num tabular sign-{signColor(h.daily_pnl)}">{formatUsd(h.daily_pnl)}</td>
          <td class="num tabular dim">{formatPercent(h.allocation_percent)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
  <div class="footer dimmer">
    Escribe <span class="acc">PORT ADD &lt;SÍMBOLO&gt; &lt;CANTIDAD&gt; &lt;PRECIO&gt;</span>
    para añadir un lote de compra, ej. <span class="acc">PORT ADD AAPL 10 150.50</span>.
  </div>
</div>

<style>
  .portfolio-panel {
    display: flex;
    flex-direction: column;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 11px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    flex-wrap: wrap;
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .spacer {
    flex: 1;
  }
  .totals {
    display: flex;
    gap: 22px;
    font-size: 12px;
  }
  .total-item {
    text-align: right;
  }
  .label {
    font-size: 10px;
    letter-spacing: 0.5px;
  }
  .value {
    font-size: 15px;
    font-weight: 700;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
  }
  th {
    text-align: right;
    color: var(--dimmer);
    font-weight: 400;
    font-size: 10px;
    letter-spacing: 0.5px;
    padding: 6px 14px;
    border-bottom: 1px solid var(--border);
    background: var(--panel2);
  }
  th:first-child {
    text-align: left;
  }
  td {
    padding: 6px 14px;
    border-bottom: 1px solid var(--border);
  }
  td.num {
    text-align: right;
  }
  .cls-badge {
    font-size: 10px;
    margin-left: 6px;
  }
  .footer {
    padding: 10px 18px;
    font-size: 11px;
  }
  .symbol-link {
    background: none;
    border: none;
    padding: 0;
    color: var(--fg);
    font-family: inherit;
    font-size: inherit;
    font-weight: 700;
    cursor: pointer;
  }
  .symbol-link:hover {
    color: var(--acc);
    text-decoration: underline;
  }
  .acc {
    color: var(--acc);
  }
</style>
