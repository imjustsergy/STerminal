<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { DEFAULT_WATCHLIST, RECONNECT_DELAY_MS, wsUrl } from '../../lib/config';
  import { ageLabel, formatMoney, formatPercent, signColor } from '../../lib/format';
  import { isQuoteError, parseStreamMessage } from '../../lib/wsMessages';
  import type { Quote, StreamQuoteEntry } from '../../lib/types';

  let quotes: Record<string, StreamQuoteEntry> = $state({});
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
      ws?.send(JSON.stringify({ subscribe: DEFAULT_WATCHLIST }));
    };
    ws.onmessage = (event: MessageEvent) => {
      const message = parseStreamMessage(String(event.data));
      if (message.kind === 'quotes') {
        const next = { ...quotes };
        for (const entry of message.quotes) {
          next[entry.symbol] = entry;
        }
        quotes = next;
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

  const rows = $derived(DEFAULT_WATCHLIST.map((symbol) => ({ symbol, entry: quotes[symbol] })));
</script>

<div class="watchlist-panel">
  <div class="header">
    <span class="title">WATCHLIST</span>
    <span class="dim hint">actualización en vivo vía WebSocket</span>
    <div class="spacer"></div>
    {#if !connected}
      <span class="stale-badge warn">
        ⚠ EN CACHÉ{#if lastUpdateMs !== null} · {ageLabel(lastUpdateMs, now)}{/if}
      </span>
    {:else}
      <span class="live-badge">● EN VIVO</span>
    {/if}
  </div>
  <table>
    <thead>
      <tr>
        <th>SÍMBOLO</th>
        <th class="num">ÚLTIMO</th>
        <th class="num">CAMBIO</th>
        <th class="num">%</th>
        <th class="num">ESTADO</th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row (row.symbol)}
        <tr>
          <td>{row.symbol}</td>
          {#if row.entry && !isQuoteError(row.entry)}
            {@const q = row.entry as Quote}
            <td class="num tabular">{formatMoney(q.price, q.price < 1 ? 4 : 2)}</td>
            <td class="num tabular sign-{signColor(q.change)}">{formatMoney(q.change)}</td>
            <td class="num tabular sign-{signColor(q.change_percent)}">{formatPercent(q.change_percent)}</td>
            <td class="num status-ok">{connected ? 'EN VIVO' : 'CACHÉ'}</td>
          {:else if row.entry}
            <td class="num" colspan="3">—</td>
            <td class="num status-error">ERROR</td>
          {:else}
            <td class="num dim" colspan="4">esperando…</td>
          {/if}
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .watchlist-panel {
    display: flex;
    flex-direction: column;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .hint {
    font-size: 11px;
  }
  .spacer {
    flex: 1;
  }
  .stale-badge {
    font-size: 11px;
    border: 1px solid var(--warn);
    padding: 3px 7px;
  }
  .live-badge {
    color: var(--pos);
    font-size: 11px;
    font-weight: 500;
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
  .status-ok {
    color: var(--dim);
    font-size: 10px;
  }
  .status-error {
    color: var(--neg);
    font-size: 10px;
  }
</style>
