<script lang="ts">
  import { onDestroy, onMount } from 'svelte';
  import { CandlestickSeries, createChart, type IChartApi, type ISeriesApi } from 'lightweight-charts';
  import { SUPPORTED_RANGES, nextRangeRequest, toLightweightSeries, type Range } from '../../lib/chartData';
  import { formatMoney, formatPercent, signColor } from '../../lib/format';
  import type { GraphPriceResponse } from '../../lib/types';

  interface Props {
    response: GraphPriceResponse;
    /** Rango de resolución actualmente activo (feat-9: 1D/1W/1M/1Y, ver command_router.py). */
    activeRange: Range;
    /** Reemite `postCommand` con el nuevo `resolution` (App.svelte gestiona el fetch real). */
    onRangeChange: (range: Range) => void;
  }

  const { response, activeRange, onRangeChange }: Props = $props();

  let container: HTMLDivElement | undefined = $state();
  let chart: IChartApi | undefined;
  let series: ISeriesApi<'Candlestick'> | undefined;

  function ensureChart(): void {
    if (chart || !container) {
      return;
    }
    chart = createChart(container, {
      layout: { background: { color: '#0a0f1b' }, textColor: '#cdd8ee' },
      grid: {
        vertLines: { color: '#1b2540' },
        horzLines: { color: '#1b2540' },
      },
      timeScale: { borderColor: '#1b2540' },
      rightPriceScale: { borderColor: '#1b2540' },
      autoSize: true,
    });
    series = chart.addSeries(CandlestickSeries, {
      upColor: '#2fd48b',
      downColor: '#ff5566',
      borderVisible: false,
      wickUpColor: '#2fd48b',
      wickDownColor: '#ff5566',
    });
  }

  function redraw(): void {
    ensureChart();
    series?.setData(toLightweightSeries(response.candles));
  }

  onMount(() => {
    redraw();
  });

  onDestroy(() => {
    chart?.remove();
    chart = undefined;
    series = undefined;
  });

  $effect(() => {
    // Redibuja cuando cambian las velas (nuevo símbolo o nuevo rango).
    response.candles;
    redraw();
  });

  function handleRangeClick(range: Range): void {
    const next = nextRangeRequest(activeRange, range);
    if (next) {
      onRangeChange(next);
    }
  }

  const lastCandle = $derived(response.candles.at(-1));
  const prevCandle = $derived(response.candles.at(-2));
  const change = $derived(lastCandle && prevCandle ? lastCandle.close - prevCandle.close : 0);
  const changePercent = $derived(
    lastCandle && prevCandle && prevCandle.close !== 0 ? (change / prevCandle.close) * 100 : null,
  );
</script>

<div class="chart-panel">
  <div class="header">
    <span class="symbol">{response.symbol}</span>
    {#if lastCandle}
      <span class="price sign-{signColor(change)} tabular">
        {formatMoney(lastCandle.close)}
      </span>
      <span class="change sign-{signColor(change)} tabular">{formatPercent(changePercent)}</span>
    {/if}
    <div class="spacer"></div>
    <div class="ranges">
      {#each SUPPORTED_RANGES as range (range)}
        <button
          type="button"
          class:active={range === activeRange}
          onclick={() => handleRangeClick(range)}
        >
          {range}
        </button>
      {/each}
    </div>
  </div>
  <div class="chart-container" bind:this={container}></div>
</div>

<style>
  .chart-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  .header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 9px 18px;
    border-bottom: 1px solid var(--border);
    background: var(--panel);
    flex-wrap: wrap;
  }
  .symbol {
    font-weight: 700;
    font-size: 16px;
  }
  .price {
    font-size: 14px;
  }
  .change {
    font-size: 13px;
  }
  .spacer {
    flex: 1;
  }
  .ranges {
    display: flex;
    gap: 3px;
  }
  button {
    background: var(--panel2);
    color: var(--fg);
    border: 1px solid var(--border);
    padding: 4px 11px;
    font-size: 11px;
    font-weight: 500;
    cursor: pointer;
  }
  button.active {
    background: var(--acc);
    color: #04101f;
  }
  .chart-container {
    flex: 1;
    min-height: 320px;
    padding: 14px 18px;
  }
</style>
