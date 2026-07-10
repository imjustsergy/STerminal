import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, waitFor } from '@testing-library/svelte';
import App from './App.svelte';
import { CommandApiError } from './lib/api';

vi.mock('./lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./lib/api')>();
  return {
    ...actual,
    postCommand: vi.fn(),
  };
});

import { postCommand } from './lib/api';

async function typeAndSubmit(getByLabelText: (label: string) => HTMLElement, text: string) {
  const input = getByLabelText('Barra de comando') as HTMLInputElement;
  await fireEvent.input(input, { target: { value: text } });
  await fireEvent.keyDown(input, { key: 'Enter' });
}

describe('App — flujo de error end-to-end (feat-11)', () => {
  afterEach(() => {
    cleanup();
    vi.mocked(postCommand).mockReset();
  });

  it('un 4xx de postCommand renderiza el panel de error con mensaje y sugerencias', async () => {
    vi.mocked(postCommand).mockRejectedValue(
      new CommandApiError("símbolo 'ZZZZ' no encontrado", 400, {
        message: "símbolo 'ZZZZ' no encontrado",
        suggestions: ['ZZZA'],
      }),
    );

    const { getByLabelText, getByText } = render(App);
    await typeAndSubmit(getByLabelText, 'ZZZZ');

    await waitFor(() => {
      expect(getByText("✕ símbolo 'ZZZZ' no encontrado")).toBeInTheDocument();
      expect(getByText('ZZZA')).toBeInTheDocument();
    });
  });

  it('un fallo de red (sin status) también renderiza el panel de error, nunca blanco', async () => {
    vi.mocked(postCommand).mockRejectedValue(
      new CommandApiError('no se pudo contactar con el backend', null, null),
    );

    const { getByLabelText, getByText } = render(App);
    await typeAndSubmit(getByLabelText, 'AAPL');

    await waitFor(() => {
      expect(getByText('✕ no se pudo contactar con el backend')).toBeInTheDocument();
    });
  });

  it('una respuesta SUMMARY exitosa renderiza el panel de resumen', async () => {
    vi.mocked(postCommand).mockResolvedValue({
      type: 'SUMMARY',
      symbol: 'AAPL',
      asset_class: 'equity',
      quote: {
        symbol: 'AAPL',
        price: 200,
        currency: 'USD',
        change: 1,
        change_percent: 0.5,
        timestamp: '2026-07-07T00:00:00Z',
      },
    });

    const { getByLabelText, getByText } = render(App);
    await typeAndSubmit(getByLabelText, 'AAPL');

    await waitFor(() => {
      expect(getByText('AAPL')).toBeInTheDocument();
    });
  });
});

describe('App — estado de carga durante la ejecución de comandos (feat-23)', () => {
  afterEach(() => {
    cleanup();
    vi.mocked(postCommand).mockReset();
  });

  function deferred<T>() {
    let resolve!: (value: T) => void;
    let reject!: (reason: unknown) => void;
    const promise = new Promise<T>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    return { promise, resolve, reject };
  }

  it('muestra la barra de progreso y el hint "cargando…" mientras la petición está en curso', async () => {
    const { promise, resolve } = deferred<import('./lib/types').CommandResponse>();
    vi.mocked(postCommand).mockReturnValue(promise);

    const { getByLabelText, getByText, queryByText, container } = render(App);
    await typeAndSubmit(getByLabelText, 'AAPL');

    expect(container.querySelector('.progress-track.active')).toBeInTheDocument();
    expect(getByText('cargando…')).toBeInTheDocument();

    resolve({
      type: 'SUMMARY',
      symbol: 'AAPL',
      asset_class: 'equity',
      quote: {
        symbol: 'AAPL',
        price: 200,
        currency: 'USD',
        change: 1,
        change_percent: 0.5,
        timestamp: '2026-07-07T00:00:00Z',
      },
    });

    await waitFor(() => {
      expect(container.querySelector('.progress-track.active')).not.toBeInTheDocument();
      expect(queryByText('cargando…')).not.toBeInTheDocument();
    });
  });

  it('quita la barra de progreso también cuando la petición falla', async () => {
    const { promise, reject } = deferred<import('./lib/types').CommandResponse>();
    vi.mocked(postCommand).mockReturnValue(promise);

    const { getByLabelText, container } = render(App);
    await typeAndSubmit(getByLabelText, 'ZZZZ');

    expect(container.querySelector('.progress-track.active')).toBeInTheDocument();

    reject(new CommandApiError("símbolo 'ZZZZ' no encontrado", 400, null));

    await waitFor(() => {
      expect(container.querySelector('.progress-track.active')).not.toBeInTheDocument();
    });
  });

  it('el panel anterior sigue visible mientras se carga el siguiente comando (sin parpadeo a blanco)', async () => {
    vi.mocked(postCommand).mockResolvedValueOnce({
      type: 'SUMMARY',
      symbol: 'AAPL',
      asset_class: 'equity',
      quote: {
        symbol: 'AAPL',
        price: 200,
        currency: 'USD',
        change: 1,
        change_percent: 0.5,
        timestamp: '2026-07-07T00:00:00Z',
      },
    });
    const { promise } = deferred<import('./lib/types').CommandResponse>();
    const { getByLabelText, getByText } = render(App);
    await typeAndSubmit(getByLabelText, 'AAPL');
    await waitFor(() => expect(getByText('AAPL')).toBeInTheDocument());

    vi.mocked(postCommand).mockReturnValue(promise);
    await typeAndSubmit(getByLabelText, 'MSFT');

    expect(getByText('AAPL')).toBeInTheDocument();
  });
});
