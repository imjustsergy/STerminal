<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { RECONNECT_DELAY_MS, wsUrl } from '../../lib/config';
  import { ageLabel, formatMoney, formatPercent, formatUsd, signColor } from '../../lib/format';
  import { isQuoteError, parseStreamMessage } from '../../lib/wsMessages';
  import type { SummaryResponse } from '../../lib/types';

  interface Props {
    response: SummaryResponse;
    onNavigate: (raw: string) => void;
  }

  const { response, onNavigate }: Props = $props();

  const CLASS_LABELS: Record<string, string> = {
    equity: 'ACCIÓN',
    crypto: 'CRIPTO',
    fx: 'FOREX',
  };

  // feat-22: acciones rápidas — mismo símbolo, distinto comando. Reutiliza el
  // mecanismo de navegación de feat-18 (onNavigate ya reenvía cualquier comando
  // completo a handleSubmit, no solo un símbolo desnudo).
  const QUICK_ACTIONS = [
    { label: 'GP', cmd: 'GP', title: 'Gráfico de precio' },
    { label: 'NEWS', cmd: 'NEWS', title: 'Noticias del activo' },
    { label: 'FA', cmd: 'FA', title: 'Datos financieros' },
    { label: 'CORR', cmd: 'CORR', title: 'Correlaciones de precio' },
    { label: 'REPORTS', cmd: 'REPORTS', title: 'Enlaces a reports' },
    { label: 'MAP', cmd: 'MAP', title: 'Mapa de cadena de valor' },
  ];

  const clsLabel = $derived(CLASS_LABELS[response.asset_class] ?? response.asset_class.toUpperCase());

  // feat-22: cotización en vivo vía WebSocket, mismo patrón que WatchlistPanel
  // (feat-10/feat-20) — arranca con el Quote que ya trajo el comando, y se
  // sustituye en cuanto llega el primer push del stream.
  let quote = $state(response.quote);
  let connected = $state(false);
  let lastUpdateMs: number | null = $state(null);
  let now = $state(Date.now());

  let ws: WebSocket | undefined;
  let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
  let clockTimer: ReturnType<typeof setInterval> | undefined;
  let destroyed = false;

  function connect(): void {
    if (destroyed) {
      return;
    }
    ws = new WebSocket(wsUrl());
    ws.onopen = () => {
      connected = true;
      ws?.send(JSON.stringify({ subscribe: [response.symbol] }));
    };
    ws.onmessage = (event: MessageEvent) => {
      const message = parseStreamMessage(String(event.data));
      if (message.kind !== 'quotes') {
        return;
      }
      const entry = message.quotes.find((q) => q.symbol === response.symbol);
      if (entry && !isQuoteError(entry)) {
        quote = entry;
        lastUpdateMs = Date.now();
      }
    };
    ws.onclose = () => {
      connected = false;
      scheduleReconnect();
    };
    ws.onerror = () => {
      connected = false;
    };
  }

  function scheduleReconnect(): void {
    if (destroyed || reconnectTimer) {
      return;
    }
    reconnectTimer = setTimeout(() => {
      reconnectTimer = undefined;
      connect();
    }, RECONNECT_DELAY_MS);
  }

  onMount(() => {
    lastUpdateMs = Date.now();
    connect();
    clockTimer = setInterval(() => {
      now = Date.now();
    }, 1000);
  });

  onDestroy(() => {
    destroyed = true;
    ws?.close();
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
    }
    if (clockTimer) {
      clearInterval(clockTimer);
    }
  });

  const sign = $derived(signColor(quote.change));
  const arrow = $derived(quote.change > 0 ? '▲' : quote.change < 0 ? '▼' : '■');
</script>

<div class="summary-panel accent-{sign}">
  <div class="header">
    <div>
      <div class="title-row">
        <span class="symbol">{response.symbol}</span>
        <span class="cls-badge dim">{clsLabel}</span>
      </div>
      <div class="quick-actions">
        {#each QUICK_ACTIONS as action (action.cmd)}
          <button
            type="button"
            class="quick-action-btn"
            title={action.title}
            onclick={() => onNavigate(`${response.symbol} ${action.cmd}`)}
          >
            {action.label}
          </button>
        {/each}
      </div>
    </div>
    <div class="spacer"></div>
    <div class="price-block">
      <div class="price sign-{sign} tabular">
        {formatMoney(quote.price, quote.price < 1 ? 4 : 2)}
        <span class="currency dim">{quote.currency}</span>
      </div>
      <div class="change sign-{sign} tabular">
        {arrow}
        {formatUsd(quote.change)} ({formatPercent(quote.change_percent)})
      </div>
      <div class="live-row">
        {#if connected}
          <span class="live-badge">● EN VIVO</span>
        {:else}
          <span class="stale-badge warn">
            ⚠ EN CACHÉ{#if lastUpdateMs !== null} · {ageLabel(lastUpdateMs, now)}{/if}
          </span>
        {/if}
      </div>
    </div>
  </div>
  <div class="stats">
    <div class="stat-row">
      <span class="dim">Última actualización</span>
      <span class="tabular">{lastUpdateMs !== null ? ageLabel(lastUpdateMs, now) : '—'}</span>
    </div>
  </div>
</div>

<style>
  .summary-panel {
    display: flex;
    flex-direction: column;
    border-left: 3px solid var(--border);
  }
  .summary-panel.accent-pos {
    border-left-color: var(--pos);
  }
  .summary-panel.accent-neg {
    border-left-color: var(--neg);
  }
  .header {
    display: flex;
    align-items: flex-end;
    gap: 16px;
    padding: 14px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .title-row {
    display: flex;
    align-items: center;
    gap: 9px;
  }
  .symbol {
    font-size: 28px;
    font-weight: 700;
  }
  .cls-badge {
    font-size: 10px;
    border: 1px solid var(--border);
    padding: 1px 6px;
    letter-spacing: 0.5px;
  }
  .quick-actions {
    display: flex;
    gap: 6px;
    margin-top: 10px;
  }
  .quick-action-btn {
    background: none;
    border: 1px solid var(--border);
    color: var(--dim);
    font-family: inherit;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
    padding: 4px 10px;
    cursor: pointer;
  }
  .quick-action-btn:hover {
    color: var(--acc);
    border-color: var(--acc);
  }
  .spacer {
    flex: 1;
  }
  .price-block {
    text-align: right;
  }
  .price {
    font-size: 34px;
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
  .live-row {
    margin-top: 8px;
  }
  .live-badge {
    color: var(--pos);
    font-size: 11px;
    font-weight: 500;
  }
  .stale-badge {
    font-size: 11px;
    border: 1px solid var(--warn);
    padding: 2px 6px;
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
