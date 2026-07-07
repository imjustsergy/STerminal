import { describe, expect, it } from 'vitest';
import { nextRangeRequest, toLightweightSeries } from './chartData';
import type { Candle } from './types';

describe('toLightweightSeries', () => {
  it('mapea open/high/low/close y convierte el timestamp ISO a epoch UTC en segundos', () => {
    const candles: Candle[] = [
      {
        timestamp: '2026-07-06T00:00:00Z',
        open: 100,
        high: 110,
        low: 95,
        close: 105,
        volume: 1000,
      },
    ];
    const result = toLightweightSeries(candles);
    expect(result).toEqual([
      {
        time: Date.parse('2026-07-06T00:00:00Z') / 1000,
        open: 100,
        high: 110,
        low: 95,
        close: 105,
      },
    ]);
  });

  it('devuelve una lista vacía para una lista de velas vacía', () => {
    expect(toLightweightSeries([])).toEqual([]);
  });

  it('preserva el orden de entrada', () => {
    const candles: Candle[] = [
      { timestamp: '2026-07-06T00:00:00Z', open: 1, high: 1, low: 1, close: 1, volume: 0 },
      { timestamp: '2026-07-07T00:00:00Z', open: 2, high: 2, low: 2, close: 2, volume: 0 },
    ];
    const result = toLightweightSeries(candles);
    expect(result[0].time).toBeLessThan(result[1].time);
  });
});

describe('nextRangeRequest', () => {
  it('devuelve el rango pulsado si es distinto del activo', () => {
    expect(nextRangeRequest('1D', '1W')).toBe('1W');
  });

  it('devuelve null si se pulsa el rango ya activo (evita refetch innecesario)', () => {
    expect(nextRangeRequest('1M', '1M')).toBeNull();
  });
});
