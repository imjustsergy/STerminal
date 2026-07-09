import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import WatchlistPanel from './WatchlistPanel.svelte';
import { DEFAULT_WATCHLIST, RECONNECT_DELAY_MS } from '../../lib/config';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
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

describe('WatchlistPanel', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    vi.useFakeTimers();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('abre una conexión y se suscribe a la watchlist por defecto al conectar', () => {
    render(WatchlistPanel, { onNavigate: vi.fn() });
    expect(FakeWebSocket.instances).toHaveLength(1);

    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    expect(ws.sent).toHaveLength(1);
    expect(JSON.parse(ws.sent[0])).toEqual({ subscribe: DEFAULT_WATCHLIST });
  });

  it('reconecta automáticamente tras RECONNECT_DELAY_MS al desconectarse', () => {
    render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    ws.onclose?.();
    expect(FakeWebSocket.instances).toHaveLength(1);

    vi.advanceTimersByTime(RECONNECT_DELAY_MS);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it('muestra el banner de stale antes de conectar, y lo retira al conectar (feat-11)', async () => {
    const { getByText, queryByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    expect(getByText('⚠ EN CACHÉ')).toBeInTheDocument();

    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    await tick();

    expect(queryByText('⚠ EN CACHÉ')).not.toBeInTheDocument();
    expect(getByText('● EN VIVO')).toBeInTheDocument();
  });

  it('vuelve a mostrar el banner de stale si el WebSocket se desconecta (feat-11)', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    await tick();
    expect(getByText('● EN VIVO')).toBeInTheDocument();

    ws.onclose?.();
    await tick();

    expect(getByText('⚠ EN CACHÉ')).toBeInTheDocument();
  });

  it('no reconecta tras onDestroy (componente desmontado)', () => {
    const { unmount } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();

    unmount();
    ws.onclose?.();
    vi.advanceTimersByTime(RECONNECT_DELAY_MS * 2);

    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it('muestra el badge de EN VIVO tras conectar y el símbolo de la watchlist', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    await tick();

    expect(getByText('● EN VIVO')).toBeInTheDocument();
    expect(getByText(DEFAULT_WATCHLIST[0])).toBeInTheDocument();
  });

  it('feat-18: clicar un símbolo de la watchlist navega a ese símbolo', async () => {
    const onNavigate = vi.fn();
    const { getByText } = render(WatchlistPanel, { onNavigate });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    await tick();

    getByText(DEFAULT_WATCHLIST[0]).click();
    expect(onNavigate).toHaveBeenCalledWith(DEFAULT_WATCHLIST[0]);
  });

  it('actualiza una fila con la cotización recibida por push', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [
          {
            symbol: DEFAULT_WATCHLIST[0],
            price: 123.45,
            currency: 'USD',
            change: 1.5,
            change_percent: 0.8,
            timestamp: '2026-07-07T00:00:00Z',
          },
        ],
      }),
    });
    await tick();

    expect(getByText('123.45')).toBeInTheDocument();
  });

  it('muestra ERROR en la fila de un símbolo roto sin romper el resto', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    ws.onopen?.();
    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [{ symbol: DEFAULT_WATCHLIST[0], error: 'no encontrado' }],
      }),
    });
    await tick();

    expect(getByText('ERROR')).toBeInTheDocument();
  });
});
