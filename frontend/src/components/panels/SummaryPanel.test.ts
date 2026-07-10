import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import SummaryPanel from './SummaryPanel.svelte';
import { RECONNECT_DELAY_MS } from '../../lib/config';
import type { SummaryResponse } from '../../lib/types';

// feat-26: lightweight-charts necesita canvas/ResizeObserver reales, que jsdom no
// implementa (mismo motivo por el que ChartPanel tampoco tiene test propio) — se
// mockea por completo para testear solo la lógica de SummaryPanel (fetch, fallback de
// error), no el renderizado real del gráfico.
vi.mock('lightweight-charts', () => ({
  AreaSeries: 'area-series-marker',
  createChart: vi.fn(() => ({
    addSeries: vi.fn(() => ({ setData: vi.fn() })),
    remove: vi.fn(),
  })),
}));

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../lib/api')>();
  return {
    ...actual,
    postCommand: vi.fn(),
  };
});

import { postCommand } from '../../lib/api';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;
  url: string;
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  sent: string[] = [];
  closed = false;

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(): void {
    this.closed = true;
    this.onclose?.();
  }
}

function openWs(ws: FakeWebSocket): void {
  ws.readyState = FakeWebSocket.OPEN;
  ws.onopen?.();
}

function baseResponse(): SummaryResponse {
  return {
    type: 'SUMMARY',
    symbol: 'AAPL',
    asset_class: 'equity',
    quote: {
      symbol: 'AAPL',
      price: 316.22,
      currency: 'USD',
      change: 2.83,
      change_percent: 0.9,
      timestamp: '2026-07-09T22:45:43.518534+00:00',
    },
  };
}

describe('SummaryPanel', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    // Por defecto, el fetch del mini-gráfico (feat-26) devuelve un histórico vacío —
    // los tests centrados en la cotización en vivo no necesitan datos de gráfico
    // reales, solo que la llamada no reviente.
    vi.mocked(postCommand).mockResolvedValue({
      type: 'GRAPH_PRICE',
      symbol: 'AAPL',
      asset_class: 'equity',
      candles: [],
    });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.mocked(postCommand).mockReset();
  });

  it('se suscribe al WebSocket con el símbolo consultado', async () => {
    render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    expect(FakeWebSocket.instances).toHaveLength(1);

    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();

    const sentPayloads = ws.sent.map((s) => JSON.parse(s));
    expect(sentPayloads).toContainEqual({ subscribe: ['AAPL'] });
  });

  it('muestra el badge de caché antes de conectar, y EN VIVO al conectar', async () => {
    const { getByText, queryByText } = render(SummaryPanel, {
      response: baseResponse(),
      onNavigate: vi.fn(),
    });
    expect(getByText(/EN CACHÉ/)).toBeInTheDocument();

    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();

    expect(queryByText(/EN CACHÉ/)).not.toBeInTheDocument();
    expect(getByText('● EN VIVO')).toBeInTheDocument();
  });

  it('actualiza el precio con la cotización recibida por push del símbolo consultado', async () => {
    const { getByText } = render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();

    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [
          {
            symbol: 'AAPL',
            price: 320.5,
            currency: 'USD',
            change: 4.0,
            change_percent: 1.2,
            timestamp: '2026-07-09T22:46:00+00:00',
          },
        ],
      }),
    });
    await tick();

    expect(getByText('320.50')).toBeInTheDocument();
  });

  it('ignora un push de un símbolo distinto al consultado', async () => {
    const { getByText, queryByText } = render(SummaryPanel, {
      response: baseResponse(),
      onNavigate: vi.fn(),
    });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();

    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [{ symbol: 'MSFT', price: 999.99, currency: 'USD', change: 0, change_percent: 0, timestamp: 't' }],
      }),
    });
    await tick();

    expect(getByText('316.22')).toBeInTheDocument();
    expect(queryByText('999.99')).not.toBeInTheDocument();
  });

  it('reconecta automáticamente tras RECONNECT_DELAY_MS al desconectarse', () => {
    vi.useFakeTimers();
    render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);

    ws.onclose?.();
    expect(FakeWebSocket.instances).toHaveLength(1);

    vi.advanceTimersByTime(RECONNECT_DELAY_MS);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it('los 6 botones de acción rápida navegan al comando correcto para el mismo símbolo', () => {
    const onNavigate = vi.fn();
    const { getByText } = render(SummaryPanel, { response: baseResponse(), onNavigate });

    for (const cmd of ['GP', 'NEWS', 'FA', 'CORR', 'REPORTS', 'MAP']) {
      getByText(cmd).click();
      expect(onNavigate).toHaveBeenCalledWith(`AAPL ${cmd}`);
    }
    expect(onNavigate).toHaveBeenCalledTimes(6);
  });

  it('muestra el timestamp legible ("hace Xs"), no el ISO crudo', () => {
    const { getAllByText, queryByText } = render(SummaryPanel, {
      response: baseResponse(),
      onNavigate: vi.fn(),
    });
    expect(queryByText('2026-07-09T22:45:43.518534+00:00')).not.toBeInTheDocument();
    expect(getAllByText(/hace \d+s/).length).toBeGreaterThan(0);
  });

  // --- Mini-gráfico embebido (feat-26) --------------------------------------

  it('pide el histórico de 1 mes del símbolo consultado al montar', async () => {
    render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    await tick();

    expect(postCommand).toHaveBeenCalledWith('AAPL GP', { resolution: '1M' });
  });

  it('muestra "cargando gráfico…" mientras se resuelve el histórico', async () => {
    let resolve!: (value: unknown) => void;
    vi.mocked(postCommand).mockReturnValue(new Promise((res) => (resolve = res)));

    const { getByText } = render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    await tick();

    expect(getByText('cargando gráfico…')).toBeInTheDocument();

    resolve({ type: 'GRAPH_PRICE', symbol: 'AAPL', asset_class: 'equity', candles: [] });
  });

  it('muestra un mensaje de "sin histórico" si el fetch falla, sin romper el resto del panel', async () => {
    vi.mocked(postCommand).mockRejectedValue(new Error('fallo simulado'));

    const { getByText } = render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    await tick();
    await tick();

    expect(getByText('sin histórico disponible para AAPL')).toBeInTheDocument();
    // El resto del panel (precio, acciones rápidas) sigue intacto.
    expect(getByText('316.22')).toBeInTheDocument();
    expect(getByText('GP')).toBeInTheDocument();
  });

  it('muestra un mensaje de "sin histórico" si el histórico viene vacío', async () => {
    vi.mocked(postCommand).mockResolvedValue({
      type: 'GRAPH_PRICE',
      symbol: 'AAPL',
      asset_class: 'equity',
      candles: [],
    });

    const { getByText } = render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    await tick();
    await tick();

    expect(getByText('sin histórico disponible para AAPL')).toBeInTheDocument();
  });

  it('con histórico real, no muestra ningún mensaje de error/carga', async () => {
    vi.mocked(postCommand).mockResolvedValue({
      type: 'GRAPH_PRICE',
      symbol: 'AAPL',
      asset_class: 'equity',
      candles: [
        { timestamp: '2026-06-01T00:00:00Z', open: 1, high: 2, low: 0.5, close: 1.5, volume: 100 },
      ],
    });

    const { queryByText } = render(SummaryPanel, { response: baseResponse(), onNavigate: vi.fn() });
    await tick();
    await tick();

    expect(queryByText('sin histórico disponible para AAPL')).not.toBeInTheDocument();
    expect(queryByText('cargando gráfico…')).not.toBeInTheDocument();
  });
});
