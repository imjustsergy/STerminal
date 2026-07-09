import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render } from '@testing-library/svelte';
import { tick } from 'svelte';
import WatchlistPanel from './WatchlistPanel.svelte';
import { RECONNECT_DELAY_MS } from '../../lib/config';

vi.mock('../../lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../../lib/api')>();
  return {
    ...actual,
    getWatchlistSymbols: vi.fn(),
    postCommand: vi.fn(),
  };
});

import { getWatchlistSymbols, postCommand } from '../../lib/api';

const TEST_SYMBOLS = ['AAPL', 'NVDA', 'BTC'];

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

/** Simula que el navegador terminó el handshake: `readyState` pasa a OPEN antes de
 * disparar `onopen`, igual que haría un WebSocket real. */
function openWs(ws: FakeWebSocket): void {
  ws.readyState = FakeWebSocket.OPEN;
  ws.onopen?.();
}

describe('WatchlistPanel', () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal('WebSocket', FakeWebSocket);
    vi.mocked(getWatchlistSymbols).mockResolvedValue([...TEST_SYMBOLS]);
    vi.mocked(postCommand).mockResolvedValue({ type: 'HELP', commands: [] });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.unstubAllGlobals();
    vi.mocked(getWatchlistSymbols).mockReset();
    vi.mocked(postCommand).mockReset();
  });

  it('carga la watchlist persistida vía GET /watchlist y se suscribe con esos símbolos', async () => {
    render(WatchlistPanel, { onNavigate: vi.fn() });
    expect(FakeWebSocket.instances).toHaveLength(1);

    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    await tick();

    expect(getWatchlistSymbols).toHaveBeenCalled();
    const sentPayloads = ws.sent.map((s) => JSON.parse(s));
    expect(sentPayloads.at(-1)).toEqual({ subscribe: TEST_SYMBOLS });
  });

  it('reconecta automáticamente tras RECONNECT_DELAY_MS al desconectarse', () => {
    vi.useFakeTimers();
    render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);

    ws.onclose?.();
    expect(FakeWebSocket.instances).toHaveLength(1);

    vi.advanceTimersByTime(RECONNECT_DELAY_MS);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it('muestra el banner de stale antes de conectar, y lo retira al conectar (feat-11)', async () => {
    const { getByText, queryByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    expect(getByText('⚠ EN CACHÉ')).toBeInTheDocument();

    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();

    expect(queryByText('⚠ EN CACHÉ')).not.toBeInTheDocument();
    expect(getByText('● EN VIVO')).toBeInTheDocument();
  });

  it('muestra el badge de EN VIVO tras conectar y los símbolos de la watchlist', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    await tick();

    expect(getByText('● EN VIVO')).toBeInTheDocument();
    expect(getByText('AAPL')).toBeInTheDocument();
  });

  it('feat-18: clicar un símbolo de la watchlist navega a ese símbolo', async () => {
    const onNavigate = vi.fn();
    const { getByText } = render(WatchlistPanel, { onNavigate });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    await tick();

    getByText('AAPL').click();
    expect(onNavigate).toHaveBeenCalledWith('AAPL');
  });

  it('actualiza una fila con la cotización recibida por push', async () => {
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [
          {
            symbol: 'AAPL',
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
    openWs(ws);
    await tick();
    ws.onmessage?.({
      data: JSON.stringify({
        quotes: [{ symbol: 'AAPL', error: 'no encontrado' }],
      }),
    });
    await tick();

    expect(getByText('ERROR')).toBeInTheDocument();
  });

  it('feat-20: muestra un estado vacío explícito cuando la watchlist no tiene símbolos', async () => {
    vi.mocked(getWatchlistSymbols).mockResolvedValue([]);
    const { getByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    await tick();
    await tick();

    expect(getByText(/watchlist vacía/)).toBeInTheDocument();
  });

  it('feat-20: el botón "×" quita el símbolo llamando a WATCH REMOVE', async () => {
    const { getByLabelText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    await tick();

    await getByLabelText('Quitar AAPL de la watchlist').click();
    await tick();

    expect(postCommand).toHaveBeenCalledWith('WATCH REMOVE AAPL');
  });

  it('feat-20: quitar un símbolo lo elimina de la tabla', async () => {
    const { getByLabelText, queryByText } = render(WatchlistPanel, { onNavigate: vi.fn() });
    const ws = FakeWebSocket.instances[0];
    openWs(ws);
    await tick();
    await tick();

    await getByLabelText('Quitar AAPL de la watchlist').click();
    await tick();
    await tick();

    expect(queryByText('AAPL')).not.toBeInTheDocument();
  });
});
