<script lang="ts">
  import { formatMoney, formatPercent, signColor } from '../../lib/format';
  import type { Quote, ValueChainNode, ValueChainResponse } from '../../lib/types';

  interface Props {
    response: ValueChainResponse;
  }

  const { response }: Props = $props();

  const VIEW_W = 620;
  const VIEW_H = 460;
  const CENTER_X = VIEW_W / 2;
  const CENTER_Y = VIEW_H / 2;
  const NODE_R = 42;
  const SIDE_X_OFFSET = 210;
  const ROW_GAP = 100;

  interface PositionedNode {
    node: ValueChainNode;
    x: number;
    y: number;
  }

  function layout(nodes: ValueChainNode[], x: number): PositionedNode[] {
    const n = nodes.length;
    return nodes.map((node, i) => ({
      node,
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

  function priceLine(quote: Quote): string {
    return `$${formatMoney(quote.price)} · ${formatPercent(quote.change_percent)}`;
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

  <div class="layout">
    <svg
      class="mindmap"
      viewBox="0 0 {VIEW_W} {VIEW_H}"
      role="img"
      aria-label="Mapa de cadena de valor de {response.symbol}"
    >
      {#if response.inputs.length > 0}
        <text x={CENTER_X - SIDE_X_OFFSET} y={CENTER_Y - 150} class="col-label" text-anchor="middle">
          ENTRADAS
        </text>
      {/if}
      {#if response.outputs.length > 0}
        <text x={CENTER_X + SIDE_X_OFFSET} y={CENTER_Y - 150} class="col-label" text-anchor="middle">
          SALIDAS
        </text>
      {/if}

      {#each inputNodes as pos (pos.node.quote.symbol)}
        {@const p1 = edgePoint(CENTER_X, CENTER_Y, pos.x, pos.y)}
        {@const p2 = edgePoint(pos.x, pos.y, CENTER_X, CENTER_Y)}
        <line x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y} class="edge" />
      {/each}
      {#each outputNodes as pos (pos.node.quote.symbol)}
        {@const p1 = edgePoint(CENTER_X, CENTER_Y, pos.x, pos.y)}
        {@const p2 = edgePoint(pos.x, pos.y, CENTER_X, CENTER_Y)}
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

      {#each inputNodes as pos (pos.node.quote.symbol)}
        <g class="node">
          <circle cx={pos.x} cy={pos.y} r={NODE_R} />
          <text x={pos.x} y={pos.y - 6} class="node-symbol" text-anchor="middle">{pos.node.quote.symbol}</text>
          <text
            x={pos.x}
            y={pos.y + 14}
            class="node-detail sign-{signColor(pos.node.quote.change_percent)}"
            text-anchor="middle"
          >
            {formatPercent(pos.node.quote.change_percent)}
          </text>
        </g>
      {/each}

      {#each outputNodes as pos (pos.node.quote.symbol)}
        <g class="node">
          <circle cx={pos.x} cy={pos.y} r={NODE_R} />
          <text x={pos.x} y={pos.y - 6} class="node-symbol" text-anchor="middle">{pos.node.quote.symbol}</text>
          <text
            x={pos.x}
            y={pos.y + 14}
            class="node-detail sign-{signColor(pos.node.quote.change_percent)}"
            text-anchor="middle"
          >
            {formatPercent(pos.node.quote.change_percent)}
          </text>
        </g>
      {/each}
    </svg>

    <div class="legend">
      {#if response.inputs.length > 0}
        <div class="legend-group">
          <div class="legend-title dim">MATERIAS PRIMAS DE ENTRADA</div>
          {#each response.inputs as node (node.quote.symbol)}
            <div class="legend-item">
              <div class="legend-item-head">
                <span class="legend-symbol acc">{node.quote.symbol}</span>
                <span class="legend-price tabular sign-{signColor(node.quote.change_percent)}">
                  {priceLine(node.quote)}
                </span>
              </div>
              <div class="legend-desc dim">{node.description}</div>
            </div>
          {/each}
        </div>
      {/if}

      {#if response.outputs.length > 0}
        <div class="legend-group">
          <div class="legend-title dim">SALIDAS A OTRAS EMPRESAS</div>
          {#each response.outputs as node (node.quote.symbol)}
            <div class="legend-item">
              <div class="legend-item-head">
                <span class="legend-symbol acc">{node.quote.symbol}</span>
                <span class="legend-price tabular sign-{signColor(node.quote.change_percent)}">
                  {priceLine(node.quote)}
                </span>
              </div>
              <div class="legend-desc dim">{node.description}</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .value-chain-panel {
    padding: 20px 18px 60px;
    max-width: 1120px;
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
  .layout {
    display: flex;
    gap: 28px;
    flex-wrap: wrap;
    align-items: flex-start;
  }
  .mindmap {
    flex: 1 1 420px;
    min-width: 320px;
    max-width: 620px;
    height: auto;
    display: block;
  }
  .legend {
    flex: 1 1 320px;
    min-width: 280px;
    display: flex;
    flex-direction: column;
    gap: 20px;
  }
  .legend-group {
    display: flex;
    flex-direction: column;
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
  }
  .legend-title {
    font-size: 10px;
    letter-spacing: 0.8px;
    background: var(--panel);
    padding: 8px 12px;
  }
  .legend-item {
    background: var(--panel);
    padding: 10px 12px;
  }
  .legend-item-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 10px;
  }
  .legend-symbol {
    font-weight: 700;
    font-size: 13px;
  }
  .legend-price {
    font-size: 12px;
    font-weight: 600;
    white-space: nowrap;
  }
  .legend-desc {
    font-size: 12px;
    margin-top: 4px;
    line-height: 1.4;
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
    color: var(--pos);
    fill: var(--pos);
  }
  .sign-neg {
    color: var(--neg);
    fill: var(--neg);
  }
  .sign-dim {
    color: var(--dim);
    fill: var(--dim);
  }
</style>
