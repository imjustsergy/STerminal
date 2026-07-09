<script lang="ts">
  import type { Range } from '../lib/chartData';
  import type { PanelKind } from '../lib/dispatch';
  import type { CommandResponse } from '../lib/types';
  import ErrorPanel from './panels/ErrorPanel.svelte';
  import ChartPanel from './panels/ChartPanel.svelte';
  import HelpPanel from './panels/HelpPanel.svelte';
  import CorrelationsPanel from './panels/CorrelationsPanel.svelte';
  import FinancialsPanel from './panels/FinancialsPanel.svelte';
  import NewsPanel from './panels/NewsPanel.svelte';
  import PortfolioPanel from './panels/PortfolioPanel.svelte';
  import ProvidersPanel from './panels/ProvidersPanel.svelte';
  import ReportsPanel from './panels/ReportsPanel.svelte';
  import SummaryPanel from './panels/SummaryPanel.svelte';
  import ValueChainPanel from './panels/ValueChainPanel.svelte';
  import WatchlistPanel from './panels/WatchlistPanel.svelte';

  interface Props {
    kind: PanelKind | 'welcome' | 'error';
    response: CommandResponse | null;
    errorMessage?: string;
    errorSuggestions?: string[];
    activeRange: Range;
    onRangeChange: (range: Range) => void;
    /** feat-18: navega al SUMMARY de un símbolo clicado dentro de otro panel. */
    onNavigate: (symbol: string) => void;
    /** feat-20: fuerza que WatchlistPanel se remonte (recargue la lista persistida)
     * cuando WATCH ADD/REMOVE tiene éxito desde la barra de comando. */
    watchlistVersion: number;
  }

  const {
    kind,
    response,
    errorMessage = '',
    errorSuggestions = [],
    activeRange,
    onRangeChange,
    onNavigate,
    watchlistVersion,
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
      <div><span class="acc">AAPL NEWS</span> <span class="dim">noticias del activo</span></div>
      <div><span class="acc">AAPL FA</span> <span class="dim">datos financieros</span></div>
      <div><span class="acc">AAPL CORR</span> <span class="dim">correlaciones de precio</span></div>
      <div><span class="acc">AAPL REPORTS</span> <span class="dim">enlaces a reports</span></div>
      <div><span class="acc">AAPL MAP</span> <span class="dim">mapa de cadena de valor</span></div>
      <div><span class="acc">PORT</span> <span class="dim">cartera</span></div>
      <div><span class="acc">PORT ADD AAPL 10 150.50</span> <span class="dim">añadir un lote de compra</span></div>
      <div><span class="acc">WATCH</span> <span class="dim">watchlist en vivo</span></div>
      <div><span class="acc">WATCH ADD MSFT</span> <span class="dim">añadir un símbolo a la watchlist</span></div>
      <div><span class="acc">PROVIDERS</span> <span class="dim">proveedores de datos disponibles</span></div>
      <div><span class="acc">HELP</span> <span class="dim">lista de comandos</span></div>
    </div>
  </div>
{:else if kind === 'error'}
  <ErrorPanel message={errorMessage} suggestions={errorSuggestions} />
{:else if kind === 'summary' && response?.type === 'SUMMARY'}
  {#key response}
    <SummaryPanel {response} {onNavigate} />
  {/key}
{:else if kind === 'graph_price' && response?.type === 'GRAPH_PRICE'}
  <ChartPanel {response} {activeRange} {onRangeChange} />
{:else if kind === 'portfolio' && response?.type === 'PORTFOLIO'}
  <PortfolioPanel {response} {onNavigate} />
{:else if kind === 'help' && response?.type === 'HELP'}
  <HelpPanel {response} />
{:else if kind === 'news' && response?.type === 'NEWS'}
  <NewsPanel {response} />
{:else if kind === 'financials' && response?.type === 'FA'}
  <FinancialsPanel {response} />
{:else if kind === 'correlations' && response?.type === 'CORR'}
  <CorrelationsPanel {response} {onNavigate} />
{:else if kind === 'reports' && response?.type === 'REPORTS'}
  <ReportsPanel {response} />
{:else if kind === 'value_chain' && response?.type === 'MAP'}
  <ValueChainPanel {response} {onNavigate} />
{:else if kind === 'watch'}
  {#key watchlistVersion}
    <WatchlistPanel {onNavigate} />
  {/key}
{:else if kind === 'providers' && response?.type === 'PROVIDERS'}
  {#key response}
    <ProvidersPanel {response} />
  {/key}
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
