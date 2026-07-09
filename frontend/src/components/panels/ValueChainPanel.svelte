<script lang="ts">
  import { formatMoney, formatPercent, signColor } from '../../lib/format';
  import type { Quote, ValueChainResponse } from '../../lib/types';

  interface Props {
    response: ValueChainResponse;
  }

  const { response }: Props = $props();

  const VIEW_W = 900;
  const VIEW_H = 460;
  const CENTER_X = VIEW_W / 2;
  const CENTER_Y = VIEW_H / 2;
  const NODE_R = 42;
  const SIDE_X_OFFSET = 320;
  const ROW_GAP = 100;

  interface PositionedNode {
    quote: Quote;
    x: number;
    y: number;
  }

  function layout(quotes: Quote[], x: number): PositionedNode[] {
    const n = quotes.length;
    return quotes.map((quote, i) => ({
      quote,
      x,
      y: CENTER_Y + (i - (n - 1) / 2) * ROW_GAP,
    }));
  }

  const inputNodes = $derived(layout(response.inputs, CENTER_X - SIDE_X_OFFSET));
  const outputNodes = $derived(layout(response.outputs, CENTER_X + SIDE_X_OFFSET));

  function edgePoint(fromX: number, fromY: number, toX: number, toY: number): { x: number; y: number } {
    const dx = toX - fromX;
    const dy = toY - fromY;
    const dist = Math.sqrt(dx * dx + dy * dy) || 1;
    return { x: fromX + (dx / dist) * NODE_R, y: fromY + (dy / dist) * NODE_R };
  }
</script>

<div class="value-chain-panel">
  <div class="header">
    <span class="title">MAPA DE CADENA DE VALOR</span>
    <span class="symbol acc">{response.symbol}</span>
    <span class="dim class-tag">{response.asset_class}</span>
    {#if response.sector}
      <span class="dim sector-tag">{response.sector}</span>
    {/if}
  </div>
  <div class="notice dimmer">
    taxonomía curada (editorial, no un feed de datos de cadena de suministro real) —
    las cotizaciones de cada nodo sí son datos de mercado reales en vivo
  </div>

  {#if response.sector === null}
    <div class="empty dim">
      sin taxonomía de sector para {response.asset_class} — el mapa de cadena de valor
      solo cubre símbolos de acciones con sector conocido
    </div>
  {:else if response.inputs.length === 0 && response.outputs.length === 0}
    <div class="empty dim">
      sin mapeo de cadena de valor definido todavía para el sector "{response.sector}"
    </div>
  {/if}

  <svg
    class="mindmap"
    viewBox="0 0 {VIEW_W} {VIEW_H}"
    role="img"
    aria-label="Mapa de cadena de valor de {response.symbol}"
  >
    {#if response.inputs.length > 0}
      <text x={CENTER_X - SIDE_X_OFFSET} y={CENTER_Y - 150} class="col-label" text-anchor="middle">
        MATERIAS PRIMAS DE ENTRADA
      </text>
    {/if}
    {#if response.outputs.length > 0}
      <text x={CENTER_X + SIDE_X_OFFSET} y={CENTER_Y - 150} class="col-label" text-anchor="middle">
        SALIDAS A OTRAS EMPRESAS
      </text>
    {/if}

    {#each inputNodes as node (node.quote.symbol)}
      {@const p1 = edgePoint(CENTER_X, CENTER_Y, node.x, node.y)}
      {@const p2 = edgePoint(node.x, node.y, CENTER_X, CENTER_Y)}
      <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} class="edge" />
    {/each}
    {#each outputNodes as node (node.quote.symbol)}
      {@const p1 = edgePoint(CENTER_X, CENTER_Y, node.x, node.y)}
      {@const p2 = edgePoint(node.x, node.y, CENTER_X, CENTER_Y)}
      <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} class="edge" />
    {/each}

    <g class="node center-node">
      <circle cx={CENTER_X} cy={CENTER_Y} r={NODE_R + 6} />
      <text x={CENTER_X} y={CENTER_Y - 4} class="node-symbol" text-anchor="middle">{response.center.symbol}</text>
      <text
        x={CENTER_X}
        y={CENTER_Y + 16}
        class="node-price sign-{signColor(response.center.change_percent)}"
        text-anchor="middle"
      >
        {formatPercent(response.center.change_percent)}
      </text>
    </g>

    {#each inputNodes as node (node.quote.symbol)}
      <g class="node">
        <circle cx={node.x} cy={node.y} r={NODE_R} />
        <text x={node.x} y={node.y - 8} class="node-symbol" text-anchor="middle">{node.quote.symbol}</text>
        <text x={node.x} y={node.y + 8} class="node-detail" text-anchor="middle">${formatMoney(node.quote.price)}</text>
        <text
          x={node.x}
          y={node.y + 24}
          class="node-detail sign-{signColor(node.quote.change_percent)}"
          text-anchor="middle"
        >
          {formatPercent(node.quote.change_percent)}
        </text>
      </g>
    {/each}

    {#each outputNodes as node (node.quote.symbol)}
      <g class="node">
        <circle cx={node.x} cy={node.y} r={NODE_R} />
        <text x={node.x} y={node.y - 8} class="node-symbol" text-anchor="middle">{node.quote.symbol}</text>
        <text x={node.x} y={node.y + 8} class="node-detail" text-anchor="middle">${formatMoney(node.quote.price)}</text>
        <text
          x={node.x}
          y={node.y + 24}
          class="node-detail sign-{signColor(node.quote.change_percent)}"
          text-anchor="middle"
        >
          {formatPercent(node.quote.change_percent)}
        </text>
      </g>
    {/each}
  </svg>
</div>

<style>
  .value-chain-panel {
    padding: 20px 18px 60px;
    max-width: 940px;
  }
  .header {
    display: flex;
    align-items: baseline;
    gap: 10px;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }
  .title {
    font-weight: 700;
    font-size: 15px;
  }
  .symbol {
    font-weight: 700;
  }
  .class-tag,
  .sector-tag {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  .notice {
    font-size: 12px;
    margin-bottom: 12px;
  }
  .empty {
    font-size: 13px;
    padding: 10px 0 16px;
  }
  .mindmap {
    width: 100%;
    height: auto;
    display: block;
  }
  .edge {
    stroke: var(--border);
    stroke-width: 1.5;
  }
  .node circle {
    fill: var(--panel2);
    stroke: var(--border);
    stroke-width: 1.5;
  }
  .center-node circle {
    fill: var(--accdim);
    stroke: var(--acc);
    stroke-width: 2;
  }
  .node-symbol {
    fill: var(--fg);
    font-size: 13px;
    font-weight: 700;
  }
  .node-detail {
    fill: var(--dim);
    font-size: 11px;
  }
  .node-price {
    font-size: 12px;
    font-weight: 600;
  }
  .col-label {
    fill: var(--dimmer);
    font-size: 10px;
    letter-spacing: 0.8px;
  }
  .sign-pos {
    fill: var(--pos);
  }
  .sign-neg {
    fill: var(--neg);
  }
  .sign-dim {
    fill: var(--dim);
  }
</style>
