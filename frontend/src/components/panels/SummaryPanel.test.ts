import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import SummaryPanel from './SummaryPanel.svelte';
import { RECONNECT_DELAY_MS } from '../../lib/config';
import type { SummaryResponse } from '../../lib/types';

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
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
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
});
