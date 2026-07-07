import { afterEach, describe, expect, it, vi } from 'vitest';
import { CommandApiError, postCommand } from './api';

function mockFetchOnce(status: number, body: unknown, ok = status < 400): void {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok,
      status,
      json: async () => body,
    }),
  );
}

describe('postCommand', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('devuelve el JSON de la respuesta en éxito (200)', async () => {
    mockFetchOnce(200, { type: 'HELP', commands: [] });
    const result = await postCommand('HELP');
    expect(result).toEqual({ type: 'HELP', commands: [] });
  });

  it('envía el body {"input": raw} al backend', async () => {
    mockFetchOnce(200, { type: 'HELP', commands: [] });
    await postCommand('AAPL');
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const [, requestInit] = call;
    expect(JSON.parse(requestInit.body)).toEqual({ input: 'AAPL' });
  });

  it('incluye resolution en el body cuando se pasa', async () => {
    mockFetchOnce(200, { type: 'GRAPH_PRICE', symbol: 'AAPL', asset_class: 'equity', candles: [] });
    await postCommand('AAPL GP', { resolution: '1W' });
    const call = (fetch as unknown as ReturnType<typeof vi.fn>).mock.calls[0];
    const [, requestInit] = call;
    expect(JSON.parse(requestInit.body)).toEqual({ input: 'AAPL GP', resolution: '1W' });
  });

  it('lanza CommandApiError con detail string en un 400', async () => {
    mockFetchOnce(400, { detail: 'comando vacío' });
    await expect(postCommand('')).rejects.toMatchObject({
      name: 'CommandApiError',
      message: 'comando vacío',
      status: 400,
    });
  });

  it('lanza CommandApiError con detail objeto (message + suggestions)', async () => {
    mockFetchOnce(400, {
      detail: { message: "símbolo 'ZZZZ' no encontrado", suggestions: ['ZZZA', 'ZZZB'] },
    });
    try {
      await postCommand('ZZZZ');
      expect.fail('debía lanzar CommandApiError');
    } catch (err) {
      expect(err).toBeInstanceOf(CommandApiError);
      const apiErr = err as CommandApiError;
      expect(apiErr.message).toBe("símbolo 'ZZZZ' no encontrado");
      expect(apiErr.detail?.suggestions).toEqual(['ZZZA', 'ZZZB']);
    }
  });

  it('lanza CommandApiError con mensaje genérico si fetch rechaza (red caída)', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('network error')),
    );
    await expect(postCommand('AAPL')).rejects.toMatchObject({
      name: 'CommandApiError',
      status: null,
    });
  });
});
