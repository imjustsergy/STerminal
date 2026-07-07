<script lang="ts">
  import type { Range } from '../lib/chartData';
  import type { PanelKind } from '../lib/dispatch';
  import type { CommandResponse } from '../lib/types';
  import ErrorPanel from './panels/ErrorPanel.svelte';
  import ChartPanel from './panels/ChartPanel.svelte';
  import HelpPanel from './panels/HelpPanel.svelte';
  import PortfolioPanel from './panels/PortfolioPanel.svelte';
  import SummaryPanel from './panels/SummaryPanel.svelte';
  import WatchlistPanel from './panels/WatchlistPanel.svelte';

  interface Props {
    kind: PanelKind | 'welcome' | 'watch' | 'error';
    response: CommandResponse | null;
    errorMessage?: string;
    errorSuggestions?: string[];
    activeRange: Range;
    onRangeChange: (range: Range) => void;
  }

  const {
    kind,
    response,
    errorMessage = '',
    errorSuggestions = [],
    activeRange,
    onRangeChange,
  }: Props = $props();
</script>

{#if kind === 'welcome'}
  <div class="welcome">
    <div class="brand">sterminal</div>
    <div class="tag dim">
      Terminal financiero personal · acciones · cripto · forex · tu cartera
    </div>
    <div class="hr"></div>
    <div class="hint dimmer">EMPEZAR — escribe un comando y pulsa ENTER</div>
    <div class="examples">
      <div><span class="acc">AAPL</span> <span class="dim">resumen de activo</span></div>
      <div><span class="acc">AAPL GP</span> <span class="dim">gráfico de precio</span></div>
      <div><span class="acc">PORT</span> <span class="dim">cartera</span></div>
      <div><span class="acc">WATCH</span> <span class="dim">watchlist en vivo</span></div>
      <div><span class="acc">HELP</span> <span class="dim">lista de comandos</span></div>
    </div>
  </div>
{:else if kind === 'error'}
  <ErrorPanel message={errorMessage} suggestions={errorSuggestions} />
{:else if kind === 'summary' && response?.type === 'SUMMARY'}
  <SummaryPanel {response} />
{:else if kind === 'graph_price' && response?.type === 'GRAPH_PRICE'}
  <ChartPanel {response} {activeRange} {onRangeChange} />
{:else if kind === 'portfolio' && response?.type === 'PORTFOLIO'}
  <PortfolioPanel {response} />
{:else if kind === 'help' && response?.type === 'HELP'}
  <HelpPanel {response} />
{:else if kind === 'watch'}
  <WatchlistPanel />
{:else}
  <ErrorPanel message="tipo de respuesta desconocido" />
{/if}

<style>
  .welcome {
    max-width: 840px;
    margin: 0 auto;
    padding: 44px 32px 60px;
  }
  .brand {
    font-size: 46px;
    font-weight: 700;
    letter-spacing: 3px;
    color: var(--acc);
    line-height: 1;
  }
  .tag {
    margin-top: 10px;
    font-size: 13px;
  }
  .hr {
    height: 1px;
    background: var(--border);
    margin: 26px 0;
  }
  .hint {
    font-size: 11px;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
  }
  .examples {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .examples > div {
    display: flex;
    gap: 12px;
    padding: 8px 13px;
    border: 1px solid var(--border);
    background: var(--panel);
  }
  .acc {
    color: var(--acc);
    font-weight: 700;
    min-width: 104px;
    display: inline-block;
  }
</style>
